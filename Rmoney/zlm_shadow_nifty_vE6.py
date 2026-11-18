"""
zlm_shadow_nifty_vE6.py -- ZLM (Zero-Line Momentum) SHADOW, vE6.2.3 (22-Oct-2026)
==================================================================================
LOG-ONLY. Places NO orders, reads but never changes any BOT_G / BOT_GE state.
Shared by BOT_fyers_nifty_g_pool_vE6.py and BOT_rmoney_nifty_g_pool_vE6.py
(the bot passes in its own log / LTP / symbol functions via configure()).

Rule (study: claude/nifty-spot-momentum-study.md, main setting):
  ref   = average Nifty spot 09:15:00-09:19:59 (bot readings; fallback: the
          09:15 3-min candle (O+H+L+C)/4 when fewer than ZLM_REF_MIN_TICKS)
  band  = ZLM_BAND_END * (minutes since 09:20) / 370   (0 at 09:20, 20 at 15:30)
  state = CE if spot > ref + band + margin, PE if spot < ref - band - margin
  ENTRY (flat, before ZLM_LAST_ENTRY_HHMM): BOT_G's DPCR locked side == state,
        and either state just changed (fresh crossing) or the lock just
        changed (incl. first lock with Nifty already beyond the line).
  EXIT  : SPOT_BACK  Nifty back across ref (CE: spot < ref, PE: spot > ref)
          TRAIL      peak LTP >= entry*(1+ARM) and LTP < peak*(1-TRAIL)
          LOCK_FLIP  BOT_G locked side changed
          EOD        ZLM_EOD_HHMM
  Evaluated once per minute (first tick of each minute), like the study.
  Option = ATM 100-multiple strike, REAL LTP from the bot's own quote call.

Variants (run side by side, independent):
  ZLM    the rule above
  ZLM-G  same, but no NEW entry after ZLM_GUARD_MAX_FLIPS lock flips

v-E33 (vE6.2.4): a change of BOT_G's locked side inside the current minute is
acted on immediately (re-check in the same minute) instead of at the next
minute -- 26-Oct Fyers: lock at 10:15:06, ZLM checked 10:15:0x, entered 10:16.
"""
import os
from datetime import datetime

CTX = {}
_ST = {}


def configure(log, ltp, symbol, broker, cfg):
    """log(str); ltp(list_of_symbols) -> {symbol: ltp}; symbol(spot, side) -> (symbol, strike)."""
    CTX.update(log=log, ltp=ltp, symbol=symbol, broker=broker,
               margin=float(cfg.get("ZLM_MARGIN_PTS", 10)),
               band_end=float(cfg.get("ZLM_BAND_END_PTS", 20)),
               arm=float(cfg.get("ZLM_TRAIL_ARM_PCT", 0.10)),
               trail=float(cfg.get("ZLM_TRAIL_PCT", 0.10)),
               last_entry=int(cfg.get("ZLM_LAST_ENTRY_HHMM", 1500)),
               eod=int(cfg.get("ZLM_EOD_HHMM", 1510)),
               lot=int(cfg.get("ZLM_LOT_QTY", 65)),
               charges=float(cfg.get("ZLM_CHARGES_PER_TRADE", 65)),
               guard=int(cfg.get("ZLM_GUARD_MAX_FLIPS", 2)),
               status_min=int(cfg.get("ZLM_STATUS_EVERY_MIN", 3)),
               ref_min_ticks=int(cfg.get("ZLM_REF_MIN_TICKS", 3)),
               csv_dir=cfg.get("ZLM_CSV_DIR", "."),
               write_csv=bool(cfg.get("ZLM_WRITE_CSV", True)),   # v-E41 (vE6.5)
               ref_mode=str(cfg.get("ZLM_REF_MODE", "TICKAVG")).upper())   # v-E44 (vE6.7)


def _log(s):
    try:
        CTX["log"](s)
    except Exception:
        pass


def _hm(t):
    return t.hour * 100 + t.minute


def state_now():
    """v-E43 (vE6.6): ZLM state at the last evaluation: "CE"/"PE"/"-", or None before the reference."""
    if not _ST or _ST.get("ref") is None:
        return None
    return _ST.get("prev_state") or "-"


def candle_915(df3, day=None):
    """Today's 09:15 3-min candle as a dict (open/high/low/close), or None."""
    try:
        if df3 is None or len(df3) == 0:
            return None
        day = day or datetime.now().date()
        idx = df3.index
        for i in range(len(df3)):
            ts = idx[i]
            if ts.date() == day and ts.hour == 9 and ts.minute == 15:
                r = df3.iloc[i]
                return {k: float(r[k]) for k in ("open", "high", "low", "close") if k in r}
    except Exception:
        return None
    return None


def _new_day(d):
    _ST.clear()
    _ST.update(date=d, ticks=[], late=[], ref=None, ref_src="", ref2=None, last_min=None,
               prev_state=None, last_lock=None, n_locks=0, started=None,
               v={n: {"pos": None, "trades": []} for n in ("ZLM", "ZLM-G")},
               last_status=None, summary_done=False)


def on_tick(spot, locked_side, df3=None, now=None):
    if not CTX or not spot or spot <= 0:
        return
    now = now or datetime.now()
    if _ST.get("date") != now.date():
        _new_day(now.date())
    hm = _hm(now)
    if hm < 915:
        return
    if _ST["started"] is None:
        _ST["started"] = hm
        _log(f"ZLM SHADOW | started {now:%H:%M:%S} broker {CTX['broker']} | margin {CTX['margin']} "
             f"band 0->{CTX['band_end']} | trail {int(CTX['arm']*100)}%/{int(CTX['trail']*100)}% | "
             f"guard ZLM-G max {CTX['guard']} flips | LOG-ONLY, no orders (v-E31)")
    if hm < 920:
        _ST["ticks"].append(spot)
        return
    if 921 <= hm <= 923:
        _ST["late"].append(spot)
    if _ST["ref"] is None:
        _set_ref(df3, now)
        if _ST["ref"] is None:
            return
    if _ST["ref2"] is None and hm >= 924 and _ST["late"]:
        _ST["ref2"] = round(sum(_ST["late"]) / len(_ST["late"]), 2)
        _log(f"ZLM REF2 | study-style avg 09:21-09:23 = {_ST['ref2']} (n={len(_ST['late'])}) vs REF {_ST['ref']} "
             f"(diff {round(_ST['ref2'] - _ST['ref'], 2)}) (v-E31, log-only)")
    mk = now.strftime("%H:%M")
    if mk == _ST["last_min"] and not (hm >= CTX["eod"] and not _ST["summary_done"]):
        # v-E33: same minute, but re-check if the lock changed since the last check
        if (locked_side if locked_side in ("CE", "PE") else None) == _ST["last_lock"]:
            return
    first_eval = _ST["last_min"] is None
    _ST["last_min"] = mk
    _evaluate(spot, locked_side, now, hm, first_eval)


def _set_ref(df3, now):
    t = _ST["ticks"]
    if CTX.get("ref_mode", "TICKAVG") == "CLOSE915":   # v-E44 (vE6.7)
        old = f"{round(sum(t) / len(t), 2)} (n={len(t)})" if t else "none"
        c = candle_915(df3, now.date())
        if c and c.get("close"):
            _ST["ref"], _ST["ref_src"] = round(c["close"], 2), "closed 09:15 3m candle close"
            _log(f"ZLM REF | opening level {_ST['ref']} ({_ST['ref_src']}) | old avg 09:15-09:19 spot {old}"
                 + (f" diff {round(_ST['ref'] - sum(t) / len(t), 2)}" if t else "") + " (v-E44, log-only)")
            return
        if _hm(now) < 925:
            return   # wait for the candle (RMoney history can lag ~1 min)
        _log("ZLM REF | no 09:15 3m candle by 09:25 -> old spot average (v-E44)")
    if len(t) >= CTX["ref_min_ticks"]:
        _ST["ref"], _ST["ref_src"] = round(sum(t) / len(t), 2), f"avg 09:15-09:19 spot n={len(t)}"
    else:
        c = candle_915(df3, now.date())
        if c and len(c) == 4:
            _ST["ref"] = round((c["open"] + c["high"] + c["low"] + c["close"]) / 4, 2)
            _ST["ref_src"] = f"FALLBACK 09:15 3m candle OHLC/4 (only {len(t)} ticks before 09:20)"
        else:
            return
    _log(f"ZLM REF | opening level {_ST['ref']} ({_ST['ref_src']}) (v-E31, log-only)")


def _band(now):
    m = now.hour * 60 + now.minute
    return max(0.0, CTX["band_end"] * (m - 560) / 370.0)


def _evaluate(spot, lock, now, hm, first_eval):
    ref, b, mg = _ST["ref"], _band(now), CTX["margin"]
    state = "CE" if spot > ref + b + mg else ("PE" if spot < ref - b - mg else None)
    lock = lock if lock in ("CE", "PE") else None
    lock_changed = lock != _ST["last_lock"]
    if lock_changed and lock:
        _ST["n_locks"] += 1
    flips = max(0, _ST["n_locks"] - 1)
    late_start = first_eval and hm > 925
    if late_start:
        _log(f"ZLM | late start {now:%H:%M} -- current lock/state taken as already seen, "
             f"no entry until a fresh crossing or lock change (v-E31)")
    # one quote call for open shadow positions
    open_syms = list({p["symbol"] for v in _ST["v"].values() for p in [v["pos"]] if p})
    ltps = {}
    if open_syms:
        try:
            ltps = CTX["ltp"](open_syms) or {}
        except Exception as e:
            _log(f"ZLM | LTP error (ignored): {e}")
    for name, v in _ST["v"].items():
        p = v["pos"]
        if p:
            l = ltps.get(p["symbol"])
            if l:
                if p["entry_ltp"] is None:
                    p["entry_ltp"] = p["peak"] = l
                    _log(f"{name} ENTRY FILL | {p['symbol']} first LTP {l} (quote missing at entry)")
                p["last_ltp"] = l
                p["peak"] = max(p["peak"], l)
            why = None
            if (p["side"] == "CE" and spot < ref) or (p["side"] == "PE" and spot > ref):
                why = "SPOT_BACK"
            elif p["entry_ltp"] and p.get("last_ltp") and p["peak"] >= p["entry_ltp"] * (1 + CTX["arm"]) \
                    and p["last_ltp"] < p["peak"] * (1 - CTX["trail"]):
                why = "TRAIL"
            elif lock != p["side"]:
                why = "LOCK_FLIP"
            elif hm >= CTX["eod"]:
                why = "EOD"
            if why:
                _exit(name, v, spot, now, why, flips)
        elif lock and state == lock and hm < CTX["last_entry"] and not late_start \
                and (state != _ST["prev_state"] or lock_changed):
            if name == "ZLM-G" and flips >= CTX["guard"]:
                if state != _ST["prev_state"] or lock_changed:
                    _log(f"ZLM-G SKIP | {lock} signal at {now:%H:%M} blocked: {flips} lock flips >= {CTX['guard']}")
            else:
                _enter(name, v, lock, spot, now, b, flips, "LOCK" if lock_changed else "CROSS")
    _ST["prev_state"], _ST["last_lock"] = state, lock
    if hm >= CTX["eod"] and not _ST["summary_done"]:
        _summary()
    m = now.hour * 60 + now.minute
    if _ST["last_status"] is None or m - _ST["last_status"] >= CTX["status_min"]:
        _ST["last_status"] = m
        parts = []
        for name, v in _ST["v"].items():
            p = v["pos"]
            parts.append(f"{name}: " + (f"IN {p['side']} {p['strike']} @{p['entry_ltp']} ltp {p.get('last_ltp')} "
                                        f"pk {p['peak']}" if p else f"FLAT ({len(v['trades'])} done)"))
        _log(f"ZLM | {now:%H:%M} spot {spot} ref {ref} band {round(b, 1)} dist {round(spot - ref, 1)} "
             f"state {state or '-'} lock {lock or '-'} flips {flips} | " + " | ".join(parts))


def _enter(name, v, side, spot, now, band, flips, why):
    sym, strike = CTX["symbol"](spot, side)
    l = None
    try:
        l = (CTX["ltp"]([sym]) or {}).get(sym)
    except Exception as e:
        _log(f"{name} | LTP error at entry (ignored): {e}")
    v["pos"] = dict(side=side, symbol=sym, strike=strike, t=now.strftime("%H:%M:%S"), spot=spot,
                    entry_ltp=l, peak=l or 0.0, last_ltp=l, why=why, flips=flips)
    _log(f"{name} ENTRY | {side} {sym} strike {strike} LTP {l} | spot {spot} ref {_ST['ref']} "
         f"band {round(band, 1)} margin {CTX['margin']} | on {why} | flips {flips} (SHADOW, no order)")


def _exit(name, v, spot, now, why, flips):
    p = v["pos"]
    l = p.get("last_ltp")
    pts = round(l - p["entry_ltp"], 2) if (l and p["entry_ltp"]) else None
    rs = round(pts * CTX["lot"] - CTX["charges"], 0) if pts is not None else None
    v["trades"].append(rs)
    v["pos"] = None
    _log(f"{name} EXIT | {p['side']} {p['symbol']} {p['entry_ltp']} -> {l} (peak {p['peak']}) pts {pts} "
         f"Rs/lot {rs} | {why} | spot {p['spot']} -> {spot} ref {_ST['ref']} | held {p['t']}->{now:%H:%M:%S} (SHADOW)")
    row = [now.strftime("%Y-%m-%d"), name, CTX["broker"], p["t"], p["side"], p["strike"], p["symbol"],
           p["spot"], p["entry_ltp"], now.strftime("%H:%M:%S"), spot, l, p["peak"], pts, rs, why,
           p["why"], _ST["ref"], _ST["ref_src"].replace(",", ";"), _ST["ref2"], p["flips"], flips]
    if not CTX.get("write_csv", True):   # v-E41 (vE6.5): CSV off, the EXIT line above has the same data
        return
    path = os.path.join(CTX["csv_dir"], f"zlm_shadow_{now:%Y%m%d}_{CTX['broker']}.csv")
    try:
        new = not os.path.exists(path)
        with open(path, "a", encoding="utf-8") as f:
            if new:
                f.write("date,variant,broker,entry_time,side,strike,symbol,entry_spot,entry_ltp,exit_time,"
                        "exit_spot,exit_ltp,peak_ltp,pts,rs_per_lot,exit_reason,entry_on,ref,ref_src,ref2,"
                        "flips_at_entry,flips_at_exit\n")
            f.write(",".join("" if x is None else str(x) for x in row) + "\n")
    except Exception as e:
        _log(f"ZLM | CSV write failed (ignored): {e}")


def _summary():
    _ST["summary_done"] = True
    for name, v in _ST["v"].items():
        t = [x for x in v["trades"] if x is not None]
        _log(f"{name} DAY SUMMARY | trades {len(v['trades'])} | Rs/lot after charges {round(sum(t))} "
             f"| ref {_ST['ref']} ({_ST['ref_src']}) ref2 {_ST['ref2']} | locks {_ST['n_locks']} (SHADOW)")
