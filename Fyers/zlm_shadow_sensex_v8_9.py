# -*- coding: utf-8 -*-
"""
zlm_shadow_sensex_v8_2.py  --  ZLM (Zero-Line Momentum) SHADOW for the Sensex bots.   LOG-ONLY, NO ORDERS.

Port of the Nifty v-E31 shadow (zlm_shadow_nifty_vE6.py), broker-agnostic. Nothing here places, modifies or
cancels an order, and nothing in the trading logic reads its state. Every call from the bot is wrapped in try/except.

Rule (Nifty values in brackets; Sensex points are ~3.3x -- UNTESTED scaling, to be tuned from the shadow results):
  ref    = v8.6: close of today's CLOSED 09:15 3-min candle (V86_ZLM_REF_CANDLE; waits until V86_ZLM_REF_WAIT_UNTIL_HHMM, then the old method);
           old method / fallback: average Sensex spot over 09:15:00-09:19:59 (fallback of that: 09:15 3-min candle OHLC/4).
  band   = 0 at 09:20 rising linearly to ZLM_BAND_MAX_PTS at 15:30 (Nifty 20 pts), margin ZLM_MARGIN_PTS (Nifty 10).
  entry  = on BOT_G's DPCR locked side, when spot is beyond ref +/- (band + margin) on that side, on a FRESH crossing
           or when the lock changes (incl. the first lock), before ZLM_ENTRY_CUTOFF_HHMM. ATM, real LTP.
  exit   = spot back across ref | trail ZLM_TRAIL_PCT from the peak once premium >= entry * (1 + ZLM_TRAIL_ARM_PCT)
           | lock flip against the position | ZLM_EXIT_HHMM.
  Evaluated once per minute. Two shadow books run side by side: "ZLM" (unlimited) and "ZLM-G" (no new entry after
  ZLM_G_MAX_FLIPS lock flips in the day).
Rows go to zlm_shadow_sensex_v8_2_<broker>.csv (one row per ENTRY and per EXIT; P&L in premium points and Rs per lot).
"""
import time
from datetime import datetime, date

_C = {}          # configuration (set by configure())
_S = {"date": None}   # per-day state

CSV_HDR = ("date,book,event,time,side,symbol,spot,ref,band,threshold,locked_side,flips,premium,peak,"
           "pnl_pts,pnl_inr_lot,reason")


def configure(log, ltp_fn, symbol_fn, write_row, broker, cfg):
    """log(str); ltp_fn(symbol)->float|None; symbol_fn(spot, side)->str; write_row(csv_line_with_newline); cfg=dict."""
    _C.update(log=log, ltp=ltp_fn, sym=symbol_fn, write=write_row, broker=broker, cfg=dict(cfg))


def _lg(msg):
    try:
        _C["log"](msg)
    except Exception:
        pass


def candle_915(df3):
    """(open, high, low, close) of TODAY's 09:15 3-min candle in df3, or None."""
    try:
        if df3 is None or len(df3) == 0:
            return None
        today = date.today()
        for ix in df3.index[::-1]:
            ts = ix
            try:
                if getattr(ts, "tzinfo", None) is not None:
                    ts = ts.tz_convert("Asia/Kolkata")
            except Exception:
                pass
            if ts.date() == today and ts.hour == 9 and ts.minute == 15:
                r = df3.loc[ix]
                if hasattr(r, "iloc") and getattr(r, "ndim", 1) > 1:
                    r = r.iloc[-1]
                return float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"])
    except Exception:
        return None
    return None


def candle_915_closed(df3):
    """v8.6: True once the last row of df3 is stamped 09:18 or later TODAY, i.e. today's 09:15 3m candle has closed."""
    try:
        last = df3.index[-1]
        if getattr(last, "tzinfo", None) is not None:
            last = last.tz_convert("Asia/Kolkata")
        return last.date() == date.today() and (last.hour * 60 + last.minute) >= 9 * 60 + 18
    except Exception:
        return False


def _new_book(name, max_flips):
    return {"name": name, "max_flips": max_flips, "pos": None, "prev_beyond": None, "last_lock": None, "flips": 0,
            "n_trades": 0}


def _reset_day(day):
    _S.clear()
    _S.update(date=day, ref=None, samples=[], ref_src="", no_ref_logged=False, last_min=None,
              books=[_new_book("ZLM", None), _new_book("ZLM-G", _C["cfg"].get("ZLM_G_MAX_FLIPS", 2))],
              ltp_warn_t=0.0)


def _band(hm_minutes):
    cfg = _C["cfg"]
    t0 = 9 * 60 + 20
    t1 = 15 * 60 + 30
    frac = (hm_minutes - t0) / float(t1 - t0)
    return max(0.0, min(1.0, frac)) * cfg["ZLM_BAND_MAX_PTS"]


def _row(book, event, now, side, symbol, spot, ref, band, thr, locked, prem, peak, pnl_pts, reason):
    cfg = _C["cfg"]
    inr = "" if pnl_pts == "" else round(pnl_pts * cfg.get("ZLM_LOT_QTY", 20), 0)
    line = ",".join(str(x) for x in [
        date.today().isoformat(), book["name"], event, now.strftime("%H:%M:%S"), side, symbol, round(spot, 2),
        round(ref, 2), round(band, 1), round(thr, 1), locked or "", book["flips"],
        "" if prem is None else round(prem, 2), "" if peak is None else round(peak, 2),
        "" if pnl_pts == "" else round(pnl_pts, 2), inr, reason]) + "\n"
    try:
        _C["write"](line)
    except Exception as e:
        _lg(f"ZLM | csv write failed (ignored): {e}")


def _ltp(symbol):
    try:
        v = _C["ltp"](symbol)
        return float(v) if v else None
    except Exception:
        return None


def _close(book, now, spot, ref, band, thr, locked, reason, prem=None):
    p = book["pos"]
    if p is None:
        return
    if prem is None:
        prem = _ltp(p["symbol"])
    if prem is None:
        prem = p["last"]          # last known premium if the quote is unavailable
    pts = prem - p["entry"]
    _lg(f"ZLM EXIT [{book['name']}] | {p['side']} {p['symbol']} entry {p['entry']} -> {round(prem, 2)} "
        f"({round(pts, 2)} pts, Rs{round(pts * _C['cfg'].get('ZLM_LOT_QTY', 20), 0)}/lot) | {reason} | "
        f"spot {round(spot, 2)} ref {round(ref, 2)} (log-only shadow)")
    _row(book, "EXIT", now, p["side"], p["symbol"], spot, ref, band, thr, locked, prem, p["peak"], pts, reason)
    book["pos"] = None


def on_tick(spot, locked_side, df3, now=None):
    """Call every main-loop pass. Does its work at most once per clock minute. Never raises into the bot."""
    cfg = _C["cfg"]
    if not cfg.get("ZLM_SHADOW_ENABLED", True) or not spot or spot <= 0:
        return
    now = now or datetime.now()
    if _S.get("date") != now.date():
        _reset_day(now.date())
    hm = now.hour * 100 + now.minute
    mins = now.hour * 60 + now.minute
    if hm < 915:
        return
    # ---- reference level ----
    if hm < 920:
        _S["samples"].append(float(spot))
        return
    if _S["ref"] is None and cfg.get("V86_ZLM_REF_CANDLE", False):
        # v8.6: reference = close of the CLOSED 09:15 3m candle (identical on both brokers, survives a restart)
        c915 = candle_915(df3)
        if c915 and candle_915_closed(df3):
            _S["ref"] = c915[3]
            if len(_S["samples"]) >= 5:
                _avg = sum(_S["samples"]) / len(_S["samples"])
                _S["ref_src"] = (f"closed 09:15 3m candle close (v8.6) | old avg-of-{len(_S['samples'])}-spot-readings ref {round(_avg, 2)}, "
                                 f"diff {round(c915[3] - _avg, 2):+}")
            else:
                _S["ref_src"] = "closed 09:15 3m candle close (v8.6) | old avg-of-spots ref n/a (restart)"
            _lg(f"ZLM | ref {round(_S['ref'], 2)} = {_S['ref_src']} | margin {cfg['ZLM_MARGIN_PTS']} "
                f"band 0->{cfg['ZLM_BAND_MAX_PTS']} pts (log-only shadow, Sensex scaling untested)")
        elif hm < cfg.get("V86_ZLM_REF_WAIT_UNTIL_HHMM", 930):
            if not _S.get("wait_logged"):
                _S["wait_logged"] = True
                _lg("ZLM | waiting for the closed 09:15 3m candle (v8.6) -- reference not set yet")
            return
        else:
            _lg("ZLM | closed 09:15 candle not available by %s -- using the old reference method (v8.6)" % cfg.get("V86_ZLM_REF_WAIT_UNTIL_HHMM", 930))
    if _S["ref"] is None:
        if len(_S["samples"]) >= 5:
            _S["ref"] = sum(_S["samples"]) / len(_S["samples"])
            _S["ref_src"] = f"avg of {len(_S['samples'])} spot readings 09:15-09:20"
        else:
            c = candle_915(df3)
            if c:
                _S["ref"] = (c[0] + c[1] + c[2] + c[3]) / 4.0
                _S["ref_src"] = "09:15 3m candle OHLC/4 (fallback" + (", restart)" if not _S["samples"] else ")")
        if _S["ref"] is not None:
            _lg(f"ZLM | ref {round(_S['ref'], 2)} = {_S['ref_src']} | margin {cfg['ZLM_MARGIN_PTS']} "
                f"band 0->{cfg['ZLM_BAND_MAX_PTS']} pts (log-only shadow, Sensex scaling untested)")
        elif not _S["no_ref_logged"]:
            _S["no_ref_logged"] = True
            _lg("ZLM | no reference level available today -- shadow idle")
            return
    ref = _S["ref"]
    if ref is None:
        return
    key = (now.hour, now.minute)
    if _S["last_min"] == key:
        return
    _S["last_min"] = key

    band = _band(mins)
    thr = band + cfg["ZLM_MARGIN_PTS"]
    beyond = "CE" if spot > ref + thr else ("PE" if spot < ref - thr else None)
    lock_ok = locked_side in ("CE", "PE")

    for bk in _S["books"]:
        lock_changed = False
        if lock_ok:
            if bk["last_lock"] is None:
                lock_changed = True                      # first lock of the day
            elif bk["last_lock"] != locked_side:
                lock_changed = True
                bk["flips"] += 1
            bk["last_lock"] = locked_side
        p = bk["pos"]
        # ---- manage an open shadow position ----
        if p is not None:
            prem = _ltp(p["symbol"])
            if prem is not None:
                p["last"] = prem
                p["peak"] = max(p["peak"], prem)
            reason = None
            if hm >= cfg["ZLM_EXIT_HHMM"]:
                reason = "FORCE_EXIT"
            elif lock_ok and locked_side != p["side"]:
                reason = "LOCK_FLIP"
            elif (p["side"] == "CE" and spot <= ref) or (p["side"] == "PE" and spot >= ref):
                reason = "REF_CROSSED_BACK"
            elif (prem is not None and p["peak"] >= p["entry"] * (1 + cfg["ZLM_TRAIL_ARM_PCT"] / 100.0)
                  and prem <= p["peak"] * (1 - cfg["ZLM_TRAIL_PCT"] / 100.0)):
                reason = "TRAIL"
            if reason:
                _close(bk, now, spot, ref, band, thr, locked_side, reason, prem)
            p = bk["pos"]
        # ---- entry ----
        if (p is None and lock_ok and beyond == locked_side and hm < cfg["ZLM_ENTRY_CUTOFF_HHMM"]
                and (bk["prev_beyond"] != beyond or lock_changed)
                and (bk["max_flips"] is None or bk["flips"] < bk["max_flips"])):
            try:
                sym = _C["sym"](spot, beyond)
                prem = _ltp(sym)
            except Exception as e:
                sym, prem = None, None
                _lg(f"ZLM | symbol/LTP error (ignored): {e}")
            if sym and prem:
                bk["pos"] = {"side": beyond, "symbol": sym, "entry": prem, "peak": prem, "last": prem}
                bk["n_trades"] += 1
                _lg(f"ZLM ENTRY [{bk['name']}] | {beyond} {sym} @ {round(prem, 2)} | spot {round(spot, 2)} "
                    f"ref {round(ref, 2)} threshold {round(thr, 1)} (band {round(band, 1)} + margin {cfg['ZLM_MARGIN_PTS']}) "
                    f"| lock {locked_side} flips {bk['flips']} (log-only shadow)")
                _row(bk, "ENTRY", now, beyond, sym, spot, ref, band, thr, locked_side, prem, prem, "", "ENTRY")
            elif time.time() - _S["ltp_warn_t"] > 600:
                _S["ltp_warn_t"] = time.time()
                _lg(f"ZLM | entry signal {beyond} but no option LTP -- skipped (log-only)")
        bk["prev_beyond"] = beyond
