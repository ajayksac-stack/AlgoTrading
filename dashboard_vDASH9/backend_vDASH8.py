"""
Minimal dashboard backend.
Run with:  uvicorn backend:app --host 0.0.0.0 --port 8000
(install once:  pip install fastapi uvicorn --break-system-packages)

Each bot POSTs a small heartbeat every loop cycle and gets back a command
("run" or "halt"). The dashboard page polls GET /status to display everything.
No database, no disk writes - all in memory, resets if you restart this script.

v-DASH5 (09-Oct-2026): DPCR readings are now kept PER BROKER (Fyers and
RMoney Nifty bots both post to /botg_reading; Sensex likewise) -- before,
both brokers went into one shared series and the chart zig-zagged between
them, and the 150-point cap held only ~3.75 h. Bots from vE5 / Sensex
v-SG-D1 send the SIGNED DPCR (-1..+1) plus raw ratio, broker and no-trade
zone. New read endpoints /botg_series_v2, /sensex_series_v2,
/banknifty_series_v2 return {broker: [points]}. The old endpoints still
work (merged list) so an old dashboard page keeps loading. A bot that
sends no broker is filed under "UNKNOWN".

v-DASH8 (30-Oct-2026): P/L HISTORY for the new "P/L curves" tab.
  - Every bot heartbeat already carries its P/L (booked + open-trade). The
    backend now keeps one sample per bot every PNL_SAMPLE_SEC (30 s) --
    bots heartbeat about once a second, so keeping every heartbeat would be
    ~20,000 points/bot/day; 30 s spacing is ~750 points/bot/day.
  - Each sample is ALSO appended to a daily CSV next to this file:
    pnl_history/pnl_history_YYYYMMDD.csv  (time_ist, epoch, bot_id, pnl).
    On startup today's CSV is loaded back, so restarting the backend
    mid-day no longer wipes the morning's curve. A new day starts a new
    file and an empty in-memory history. This is the ONLY disk write; any
    disk error is printed once and otherwise ignored -- it can never block
    or slow a heartbeat reply to a bot.
  - New read endpoint GET /pnl_history -> {bot_id: [[epoch, pnl], ...]}.
  - Everything else is unchanged: all v-DASH5 endpoints, the run/halt
    command flow and the 8 s stale rule work exactly as before, so the
    older v-DASH6 / v-DASH7 pages also work against this backend.
"""

import csv
import threading
import time
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# Allow the dashboard HTML (opened as a local file, or served separately) to call this.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

bots: dict[str, dict] = {}  # bot_id -> {pnl, status, command, last_seen}
STALE_AFTER_SEC = 8  # if no heartbeat in this long, dashboard should show it as stale

# BOT_G DPCR/Nifty series -- separate from the bots{} dict above (that's
# per-bot pnl/status; this is one shared time series for the small charts).
# Ring buffer, capped so it can't grow unbounded across a session.
# v-G9-FIX4: originally sized for one reading per 10-min candle (~38/day),
# but BOT_G's actual DPCR cadence is every 3-min candle once wired into
# main() -- a full 09:16-15:10 session is ~118 points at that spacing. Cap
# raised to 150 for headroom; same "no disk writes, resets on restart"
# philosophy as the rest of this backend.
botg_series: list[dict] = []          # merged, legacy /botg_series only
BOTG_SERIES_CAP = 150                  # v-DASH5: cap now applies PER BROKER below
botg_by_broker: dict[str, list] = {}   # v-DASH5

# v-SG4 (14-Aug-2026): SEPARATE series for the Sensex BOT_G/BOT_GG process --
# it runs as its own independent process and was about to post to the SAME
# /botg_reading endpoint as Nifty's, which would have mixed both
# instruments' DPCR/spot readings into one shared series. Same cap
# reasoning as botg_series above (~118 points for a full 09:16-15:10
# session at 3-min cadence).
sensex_series: list[dict] = []          # merged, legacy /sensex_series only
SENSEX_SERIES_CAP = 150
sensex_by_broker: dict[str, list] = {}   # v-DASH5
SENSEX_SPOT_STATE: dict = {"sensex_spot": None, "time": None}
SENSEX_SAMPLE_INTERVAL_SEC = 180

def _append_capped(store: dict, broker: str, point: dict, cap: int):
    """v-DASH5: append one point to that broker's own ring buffer."""
    lst = store.setdefault(broker or "UNKNOWN", [])
    lst.append(point)
    if len(lst) > cap:
        del lst[0]


def _upsert_sensex_series(dpcr, spot):
    """Maintain one Sensex dashboard sample per ~3-minute candle.
    Spot heartbeats update the current sample; a DPCR reading fills the
    same sample rather than creating a duplicate point."""
    now = time.time()
    if sensex_series and (now - sensex_series[-1].get("time", 0)) < SENSEX_SAMPLE_INTERVAL_SEC:
        sensex_series[-1]["sensex_spot"] = float(spot)
        if dpcr is not None:
            sensex_series[-1]["dpcr"] = float(dpcr)
        return
    sensex_series.append({"time": now, "dpcr": (float(dpcr) if dpcr is not None else None), "sensex_spot": float(spot)})
    if len(sensex_series) > SENSEX_SERIES_CAP:
        del sensex_series[0]

# v-BN3 (14-Aug-2026): SEPARATE series for the BankNifty BOT_G/BOT_GG
# process, same reasoning as sensex_series above -- its own independent
# process, own ring buffer, never mixed with Nifty's or Sensex's.
banknifty_series: list[dict] = []
BANKNIFTY_SERIES_CAP = 150
banknifty_by_broker: dict[str, list] = {}   # v-DASH5


# ─────────────────────────────────────────────────────────────────────
# v-DASH8: P/L history (see module docstring).
PNL_SAMPLE_SEC = 30
PNL_HISTORY_CAP = 1500          # per bot; ~12.5 h at 30 s -- a full day fits
PNL_DIR = Path(__file__).resolve().parent / "pnl_history"
pnl_history: dict[str, list] = {}   # bot_id -> [[epoch, pnl], ...]
_pnl_day = {"key": None}            # YYYYMMDD the in-memory history belongs to
_pnl_disk_warned = {"done": False}
# FastAPI runs these plain (non-async) endpoints on a thread pool, so two
# bots' heartbeats can arrive at the same moment -- one lock keeps the
# in-memory lists and the CSV appends from interleaving.
_pnl_lock = threading.Lock()


def _today_key() -> str:
    return datetime.now().strftime("%Y%m%d")


def _pnl_csv_path(day_key: str) -> Path:
    return PNL_DIR / f"pnl_history_{day_key}.csv"


def _disk_warn(e: Exception):
    if not _pnl_disk_warned["done"]:
        print(f"[v-DASH8] P/L history CSV not writable/readable ({type(e).__name__}: {e}) "
              f"-- charts still work from memory, but a restart will lose them.")
        _pnl_disk_warned["done"] = True


def _load_today_pnl():
    """Reload today's CSV (if any) into memory -- called at startup and at
    the first sample of a new day."""
    key = _today_key()
    _pnl_day["key"] = key
    pnl_history.clear()
    path = _pnl_csv_path(key)
    if not path.exists():
        return
    try:
        with path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    lst = pnl_history.setdefault(row["bot_id"], [])
                    lst.append([float(row["epoch"]), float(row["pnl"])])
                except Exception:
                    continue
        for lst in pnl_history.values():
            lst.sort(key=lambda p: p[0])
            del lst[:-PNL_HISTORY_CAP]
        print(f"[v-DASH8] reloaded today's P/L history: "
              f"{sum(len(v) for v in pnl_history.values())} points, {len(pnl_history)} bots")
    except Exception as e:
        _disk_warn(e)


def _record_pnl_sample(bot_id: str, pnl: float, now: float):
    """Called from every heartbeat; stores at most one point per bot per
    PNL_SAMPLE_SEC. Cheap when it skips (one dict lookup)."""
    if _pnl_day["key"] != _today_key():
        _load_today_pnl()            # new day -> fresh history (and file)
    lst = pnl_history.setdefault(bot_id, [])
    if lst and now - lst[-1][0] < PNL_SAMPLE_SEC:
        return
    lst.append([now, float(pnl)])
    if len(lst) > PNL_HISTORY_CAP:
        del lst[0]
    try:
        PNL_DIR.mkdir(parents=True, exist_ok=True)
        path = _pnl_csv_path(_pnl_day["key"])
        new_file = not path.exists()
        with path.open("a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new_file:
                w.writerow(["time_ist", "epoch", "bot_id", "pnl"])
            w.writerow([datetime.fromtimestamp(now).strftime("%H:%M:%S"),
                        f"{now:.0f}", bot_id, f"{float(pnl):.2f}"])
    except Exception as e:
        _disk_warn(e)


_load_today_pnl()


class Heartbeat(BaseModel):
    pnl: float
    status: str = "running"  # whatever label your bot wants to report


class BotGReading(BaseModel):
    dpcr: Optional[float] = None    # v-DASH5: signed DPCR from vE5 bots (raw ratio from older bots)
    nifty_spot: float
    raw: Optional[float] = None     # v-DASH5
    broker: str = "UNKNOWN"         # v-DASH5
    zone: Optional[float] = None    # v-DASH5: upper edge of no-trade zone


class SensexReading(BaseModel):
    # DPCR is optional so the Sensex spot series can keep flowing even
    # during a temporary option-chain/DPCR outage.
    dpcr: Optional[float] = None
    sensex_spot: float
    raw: Optional[float] = None     # v-DASH5
    broker: str = "UNKNOWN"         # v-DASH5
    zone: Optional[float] = None    # v-DASH5


class SensexSpotReading(BaseModel):
    sensex_spot: float


class BankNiftyReading(BaseModel):
    dpcr: Optional[float] = None
    banknifty_spot: float
    raw: Optional[float] = None     # v-DASH5
    broker: str = "UNKNOWN"         # v-DASH5
    zone: Optional[float] = None    # v-DASH5


@app.post("/status/{bot_id}")
def post_status(bot_id: str, hb: Heartbeat):
    entry = bots.setdefault(bot_id, {"command": "run"})
    entry["pnl"] = hb.pnl
    entry["status"] = hb.status
    entry["last_seen"] = time.time()
    try:
        with _pnl_lock:
            _record_pnl_sample(bot_id, hb.pnl, entry["last_seen"])   # v-DASH8
    except Exception:
        pass   # history must never break the heartbeat reply
    return {"command": entry["command"]}


@app.get("/pnl_history")
def get_pnl_history():
    """v-DASH8: {bot_id: [[epoch, pnl], ...]} for today, one point per ~30 s."""
    with _pnl_lock:
        return {k: list(v) for k, v in pnl_history.items()}


@app.get("/status")
def get_status():
    now = time.time()
    out = {}
    for bot_id, e in bots.items():
        out[bot_id] = {
            **e,
            "stale": (now - e.get("last_seen", 0)) > STALE_AFTER_SEC,
        }
    return out


@app.post("/botg_reading")
def post_botg_reading(r: BotGReading):
    """Call this once per DPCR candle (10-min), from BOT_G only -- not the
    per-loop-cycle heartbeat the other bots use. Appends to the shared
    ring buffer the dashboard's two small charts read from."""
    now = time.time()
    botg_series.append({
        "time": now,
        "dpcr": r.dpcr,
        "nifty_spot": r.nifty_spot,
    })
    if len(botg_series) > BOTG_SERIES_CAP:
        del botg_series[0]
    _append_capped(botg_by_broker, r.broker, {"time": now, "dpcr": r.dpcr, "raw": r.raw,
                   "spot": r.nifty_spot, "zone": r.zone}, BOTG_SERIES_CAP)   # v-DASH5
    return {"ok": True}


@app.get("/botg_series")
def get_botg_series():
    return botg_series


@app.get("/botg_series_v2")
def get_botg_series_v2():
    """v-DASH5: {broker: [{time, dpcr, raw, spot, zone}, ...]}"""
    return botg_by_broker


@app.post("/sensex_reading")
def post_sensex_reading(r: SensexReading):
    """v-SG4: same pattern as /botg_reading, but for the separate Sensex
    BOT_G/BOT_GG process -- call this once per DPCR candle from that
    process only, never from the Nifty one. Kept as its own endpoint and
    own ring buffer specifically so the two instruments' series never mix."""
    _upsert_sensex_series(r.dpcr, r.sensex_spot)
    _append_capped(sensex_by_broker, r.broker, {"time": time.time(), "dpcr": r.dpcr, "raw": r.raw,
                   "spot": r.sensex_spot, "zone": r.zone}, SENSEX_SERIES_CAP)   # v-DASH5
    return {"ok": True}


@app.get("/sensex_series")
def get_sensex_series():
    return sensex_series


@app.get("/sensex_series_v2")
def get_sensex_series_v2():
    """v-DASH5: {broker: [{time, dpcr, raw, spot, zone}, ...]}"""
    return sensex_by_broker


@app.post("/sensex_spot")
def post_sensex_spot(r: SensexSpotReading):
    SENSEX_SPOT_STATE["sensex_spot"] = r.sensex_spot
    SENSEX_SPOT_STATE["time"] = time.time()
    _upsert_sensex_series(None, r.sensex_spot)
    return {"ok": True}


@app.get("/sensex_spot")
def get_sensex_spot():
    return SENSEX_SPOT_STATE


@app.post("/banknifty_reading")
def post_banknifty_reading(r: BankNiftyReading):
    """v-BN3: same pattern as /sensex_reading, for the separate BankNifty
    BOT_G/BOT_GG process -- call this once per DPCR candle from that
    process only. Own endpoint and own ring buffer, never mixed with
    Nifty's or Sensex's series."""
    now = time.time()
    banknifty_series.append({
        "time": now,
        "dpcr": r.dpcr,
        "banknifty_spot": r.banknifty_spot,
    })
    if len(banknifty_series) > BANKNIFTY_SERIES_CAP:
        del banknifty_series[0]
    _append_capped(banknifty_by_broker, r.broker, {"time": now, "dpcr": r.dpcr, "raw": r.raw,
                   "spot": r.banknifty_spot, "zone": r.zone}, BANKNIFTY_SERIES_CAP)   # v-DASH5
    return {"ok": True}


@app.get("/banknifty_series")
def get_banknifty_series():
    return banknifty_series


@app.get("/banknifty_series_v2")
def get_banknifty_series_v2():
    """v-DASH5: {broker: [{time, dpcr, raw, spot, zone}, ...]}"""
    return banknifty_by_broker


@app.post("/kill/{bot_id}")
def kill(bot_id: str):
    if bot_id in bots:
        bots[bot_id]["command"] = "halt"
    return {"ok": True}


@app.post("/kill_all")
def kill_all():
    for e in bots.values():
        e["command"] = "halt"
    return {"ok": True}


@app.post("/clear/{bot_id}")
def clear(bot_id: str):
    """Optional: call this if you want the dashboard to stop showing a bot as
    'halted' after you've manually restarted it in IntelliJ."""
    if bot_id in bots:
        bots[bot_id]["command"] = "run"
    return {"ok": True}


if __name__ == "__main__":
    # Lets you start this the same way you start your bots - by pressing
    # Run in IntelliJ - instead of typing the uvicorn command in a terminal.
    # access_log=False stops it printing a line for every single
    # heartbeat/status poll - you'll only see startup + real errors now.
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, access_log=False)
