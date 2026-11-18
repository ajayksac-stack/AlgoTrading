"""
exit_whatif_nifty_vE6.py -- vE6.3 (28-Oct-2026) v-E36 EXIT WHAT-IF SHADOW, LOG-ONLY
                            vE6.5 (31-Oct-2026) v-E40 + minimum-stop plans MS4 / MS5
==================================================================================
For every BOT_G / BOT_GE trade, replays the trade's own live LTPs through
several exit plans side by side and logs what each would have made. Places NO
orders, never changes the bot's stop, targets or quantity.

  BASE  the current ladder (replica): stop = initial SL; BE at the bot's BE
        level; P1 books R1 fraction of qty, P2 books R15 fraction; TSL from the
        arm level with the bot's buffer. BASE vs ACTUAL shows how close the
        replica is to the real bot.
  EB    early bank: book WHATIF_EB_LOTS lot(s) at entry + WHATIF_EB_R x R
        (only if at least one more lot stays open); P1 then books its usual
        quantity minus the early lot(s), at least 1 lot always left open.
  TS    time stop: if the trade has not reached entry + WHATIF_TS_R x R within
        WHATIF_TS_MIN minutes (and no target was hit), exit everything.
  EBTS  EB and TS together.
  MSn   (vE6.5) minimum stop: same as BASE but the initial stop is at least
        n points below entry (n in WHATIF_MS_PTS, default 4 and 5). BE level,
        P1/P2, TSL arm and buffer are the bot's own (unchanged). Identical to
        BASE when the bot's stop is already n points or wider.

Fills at the polled LTP (like the paper stop fill, v-E24). Lots still open in a
plan when the real trade closes are closed at the real exit price -- EXCEPT an
MS plan when the real trade was stopped out (SL_EXIT / BROKER_SL_FILLED) and
the wider MS stop was not hit: that plan keeps running on the bot's 30-min
post-exit tracker prices (tail_tick); at the tracker end / shutdown whatever is
left closes at the last price. The trade's log line + CSV row are written once
every plan is closed.
"""
import os
from datetime import datetime

CTX = {}
_T = {}      # trade_id -> state (trade open)
_TAIL = {}   # trade_id -> state (real trade closed, MS plan(s) still running)

BASE_PLANS = ("BASE", "EB", "TS", "EBTS")
STOP_REASONS = ("SL_EXIT", "BROKER_SL_FILLED")


def _ms_name(p):
    return f"MS{int(p)}" if float(p) == int(p) else f"MS{p}"


def _plans():
    return BASE_PLANS + tuple(_ms_name(p) for p in CTX.get("ms_pts", ()))


def _header():
    ms = [_ms_name(p) for p in CTX.get("ms_pts", ())]
    return ("date,trade_id,bot,symbol,side,entry_time,entry,initial_sl,risk_pts,qty0,lot_qty,peak_ltp,peak_r,"
            "actual_pnl,base_pnl,eb_pnl,ts_pnl,ebts_pnl,eb_booked_at,eb_price,ts_exit_at,ts_price,"
            "base_events,eb_events,ts_events,ebts_events,late_start,ticks,"
            "low_stop,real_exit_reason,real_exit_price,"
            + ",".join(f"{m.lower()}_pnl,{m.lower()}_events" for m in ms)
            + ",tail_ticks,tail_end")


def configure(log, cfg, csv_path):
    CTX.clear()
    ms = cfg.get("WHATIF_MS_PTS", (4.0, 5.0)) or ()
    CTX.update(log=log, path=csv_path,
               eb_r=float(cfg.get("WHATIF_EB_R", 0.6)), eb_lots=int(cfg.get("WHATIF_EB_LOTS", 1)),
               ts_min=float(cfg.get("WHATIF_TS_MIN", 5)), ts_r=float(cfg.get("WHATIF_TS_R", 0.3)),
               lot=int(cfg.get("WHATIF_LOT_QTY", 65)),
               ms_pts=tuple(float(x) for x in ms),
               low_stop=float(cfg.get("WHATIF_LOW_STOP_PTS", 4.0)),
               tail_max_sec=float(cfg.get("WHATIF_TAIL_MAX_MIN", 35)) * 60)


def _log(s):
    try:
        CTX["log"](s)
    except Exception:
        pass


def _new_plan(name, stop):
    return dict(name=name, open_q=None, stop=stop, done_eb=False, done1=False, done2=False, armed=False,
                pnl=0.0, closed=False, ev=[], eb_at="", eb_px="", ts_at="", ts_px="")


def start(tid, bot_name, symbol, side, entry, initial_sl, qty0, be_level, p1, p2, arm_level, buffer_pts,
          r1_frac, r15_frac, entry_dt, late=False):
    """Register a trade. qty0 = full quantity at entry."""
    R = float(entry) - float(initial_sl)
    plans = {n: _new_plan(n, float(initial_sl)) for n in BASE_PLANS}
    for p in CTX.get("ms_pts", ()):
        plans[_ms_name(p)] = _new_plan(_ms_name(p), float(entry) - max(R, p))
    st = dict(tid=tid, bot=bot_name, symbol=symbol, side=side, entry=float(entry), sl=float(initial_sl), R=R,
              qty0=int(qty0), be=float(be_level), p1=float(p1), p2=float(p2), arm=float(arm_level),
              buf=float(buffer_pts), r1=float(r1_frac), r15=float(r15_frac), t0=entry_dt, peak=float(entry),
              late=late, ticks=0, tail_ticks=0, plans=plans, actual="", reason="", exit_px="", last=None,
              closed_at=None, tail_end="")
    for p in st["plans"].values():
        p["open_q"] = st["qty0"]
    _T[tid] = st
    return st


def low_stop(R):
    return R < CTX.get("low_stop", 4.0)


def _sell(st, p, q, px, why, now):
    q = min(q, p["open_q"])
    if q <= 0:
        return 0
    p["pnl"] += (px - st["entry"]) * q
    p["open_q"] -= q
    p["ev"].append(f"{why}@{now:%H:%M:%S}:{q}x{round(px, 2)}")
    if p["open_q"] <= 0:
        p["closed"] = True
    return q


def _step(st, ltp, now):
    e, R, lot = st["entry"], st["R"], CTX["lot"]
    st["peak"] = max(st["peak"], ltp)
    st["last"] = ltp
    el_min = (now - st["t0"]).total_seconds() / 60.0 if st["t0"] else 0.0
    for name, p in st["plans"].items():
        if p["closed"]:
            continue
        use_eb, use_ts = name in ("EB", "EBTS"), name in ("TS", "EBTS")
        if ltp <= p["stop"]:
            _sell(st, p, p["open_q"], ltp, "STOP" if p["stop"] < e else ("BE" if p["stop"] == e else "TSL"), now)
            continue
        if use_ts and not (p["done1"] or p["done_eb"]) and el_min >= CTX["ts_min"] \
                and st["peak"] < e + CTX["ts_r"] * R:
            _sell(st, p, p["open_q"], ltp, "TIME", now)
            p["ts_at"], p["ts_px"] = now.strftime("%H:%M:%S"), round(ltp, 2)
            continue
        if use_eb and not p["done_eb"] and R > 0 and ltp >= e + CTX["eb_r"] * R and p["open_q"] > CTX["eb_lots"] * lot:
            _sell(st, p, CTX["eb_lots"] * lot, ltp, "EARLY", now)
            p["done_eb"] = True
            p["eb_at"], p["eb_px"] = now.strftime("%H:%M:%S"), round(ltp, 2)
        if not p["done1"] and ltp >= st["p1"]:
            q1 = int(round(st["qty0"] * st["r1"] / lot)) * lot
            if p["done_eb"]:
                q1 -= CTX["eb_lots"] * lot
            q1 = max(0, min(q1, p["open_q"] - lot))
            _sell(st, p, q1, ltp, "P1", now)
            p["done1"] = True
        if not p["done2"] and ltp >= st["p2"]:
            q2 = int(round(st["qty0"] * st["r15"] / lot)) * lot
            q2 = max(0, min(q2, p["open_q"] - lot))
            _sell(st, p, q2, ltp, "P2", now)
            p["done2"] = True
        if ltp >= st["be"]:
            p["stop"] = max(p["stop"], e)
        if ltp >= st["arm"]:
            p["armed"] = True
        if p["armed"]:
            p["stop"] = max(p["stop"], st["peak"] - st["buf"], e)


def tick(tid, ltp, now=None):
    st = _T.get(tid)
    if st is None or not ltp or ltp <= 0:
        return
    st["ticks"] += 1
    _step(st, ltp, now or datetime.now())


def close(tid, exit_price, actual_pnl, now=None, reason=""):
    """The real trade closed. Plans still open close at the real exit price, except
    MS plans after a real stop-out (they continue on post-exit prices, see tail_tick)."""
    st = _T.pop(tid, None)
    if st is None:
        return None
    now = now or datetime.now()
    st.update(actual=actual_pnl, reason=reason or "", exit_px=exit_price, closed_at=now)
    stopped = (reason or "").strip() in STOP_REASONS   # exact: "TSL_EXIT" is not a stop-out
    tail = []
    for name, p in st["plans"].items():
        if p["closed"] or p["open_q"] <= 0:
            continue
        if name.startswith("MS") and stopped and float(exit_price) > p["stop"]:
            tail.append(name)
            continue
        _sell(st, p, p["open_q"], float(exit_price), "REAL_EXIT", now)
    _log_base(st)
    if tail:
        _TAIL[tid] = st
        _log(f"{st['bot']} WHATIF MIN-STOP | {st['symbol']} real stop-out @{exit_price} | "
             + " / ".join(f"{n} stop {round(st['plans'][n]['stop'], 2)}" for n in tail)
             + " not hit -> following post-exit prices (v-E40, log-only)")
        return None
    return _finalize(st, now)


def tail_tick(tid, ltp, now=None):
    """Post-exit tracker price for a trade whose MS plan(s) are still running."""
    st = _TAIL.get(tid)
    if st is None or not ltp or ltp <= 0:
        return
    now = now or datetime.now()
    st["tail_ticks"] += 1
    _step(st, float(ltp), now)
    if all(p["closed"] for p in st["plans"].values()):
        _TAIL.pop(tid, None)
        st["tail_end"] = "RESOLVED"
        _finalize(st, now)
    elif st["closed_at"] and (now - st["closed_at"]).total_seconds() > CTX.get("tail_max_sec", 2100):
        tail_end(tid, now, "TIMEOUT")


def tail_end(tid, now=None, why="TRACK_END"):
    """Tracker finished (or shutdown): close what is left at the last price seen."""
    st = _TAIL.pop(tid, None)
    if st is None:
        return None
    now = now or datetime.now()
    px = st["last"] if st["last"] else float(st["exit_px"])
    for p in st["plans"].values():
        if not p["closed"] and p["open_q"] > 0:
            _sell(st, p, p["open_q"], float(px), why, now)
    st["tail_end"] = why
    return _finalize(st, now)


def flush_tails(now=None):
    for tid in list(_TAIL):
        tail_end(tid, now, "SHUTDOWN")


def _log_base(st):
    P = st["plans"]
    r = {n: round(P[n]["pnl"], 2) for n in BASE_PLANS}
    peak_r = round((st["peak"] - st["entry"]) / st["R"], 2) if st["R"] > 0 else ""
    _log(f"{st['bot']} WHATIF | {st['symbol']} actual Rs{st['actual']} | replica BASE Rs{r['BASE']} | "
         f"EARLY-BANK {CTX['eb_lots']} lot @{CTX['eb_r']}R Rs{r['EB']}"
         + (f" (booked {P['EB']['eb_at']} @{P['EB']['eb_px']})" if P['EB']['eb_at'] else " (not reached)")
         + f" | TIME-STOP {CTX['ts_min']:g}m/+{CTX['ts_r']}R Rs{r['TS']}"
         + (f" (exit {P['TS']['ts_at']} @{P['TS']['ts_px']})" if P['TS']['ts_at'] else " (not hit)")
         + f" | BOTH Rs{r['EBTS']} | peak {round(st['peak'], 2)} ({peak_r}R) (v-E36, log-only)")


def _finalize(st, now):
    P = st["plans"]
    res = {n: round(P[n]["pnl"], 2) for n in P}
    peak_r = round((st["peak"] - st["entry"]) / st["R"], 2) if st["R"] > 0 else ""
    ms = [_ms_name(p) for p in CTX.get("ms_pts", ())]
    ls = low_stop(st["R"])
    if ms:
        _log(f"{st['bot']} WHATIF MIN-STOP | {st['symbol']} R {round(st['R'], 2)} pts"
             + (" LOW STOP" if ls else "") + f" | actual Rs{st['actual']} | BASE Rs{res['BASE']} | "
             + " | ".join(f"min {n[2:]}pt stop Rs{res[n]}" + ("" if st['R'] < float(n[2:]) else " (same as BASE)")
                          for n in ms)
             + (f" | post-exit {st['tail_end']} after {st['tail_ticks']} prices" if st["tail_end"] else "")
             + " (v-E40, log-only)")
    row = [now.strftime("%Y-%m-%d"), st["tid"], st["bot"], st["symbol"], st["side"],
           st["t0"].strftime("%H:%M:%S") if st["t0"] else "", st["entry"], st["sl"], round(st["R"], 2), st["qty0"],
           CTX["lot"], round(st["peak"], 2), peak_r, st["actual"], res["BASE"], res["EB"], res["TS"], res["EBTS"],
           P["EB"]["eb_at"], P["EB"]["eb_px"], P["TS"]["ts_at"], P["TS"]["ts_px"],
           " ".join(P["BASE"]["ev"]), " ".join(P["EB"]["ev"]), " ".join(P["TS"]["ev"]), " ".join(P["EBTS"]["ev"]),
           int(bool(st["late"])), st["ticks"], int(ls), st["reason"], st["exit_px"]]
    for n in ms:
        row += [res[n], " ".join(P[n]["ev"])]
    row += [st["tail_ticks"], st["tail_end"]]
    try:
        path = CTX["path"]
        hdr = _header()
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                first = f.readline().rstrip("\n")
            if first != hdr:   # vE6.3 file with the old columns: keep it aside, start a new one
                os.replace(path, path[:-4] + f"_old_{datetime.now():%Y%m%d_%H%M%S}.csv")
        new = not os.path.exists(path)
        with open(path, "a", encoding="utf-8") as f:
            if new:
                f.write(hdr + "\n")
            f.write(",".join(str(x).replace(",", ";") for x in row) + "\n")
    except Exception as ex:
        _log(f"WHATIF | CSV write failed (ignored): {ex}")
    return res
