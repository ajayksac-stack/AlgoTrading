"""
option_chain_filter_sensex_fyers_v8_9.py -- BUILT FROM option_chain_filter_nifty_fyers_vE5.py (the
Nifty module the vE6.2 bot imports as ..._vE6). Differences from the Nifty module, all marked
"v8 Sensex": OC_SYMBOL (BSE:SENSEX-INDEX), OC_STRIKE_GAP (100), log file names (*_sensex_fyers_v8_9),
and an optional reanchor_pts argument (weekday floor for the re-anchor distance; None = Nifty rule).
NOTE: the Nifty vE6 module itself was not uploaded; if it differs from vE5, port that diff here.
"""
"""
option_chain_filter_nifty_fyers_vE5.py — copy of option_chain_filter_nifty.py
(Fyers) for the v3 Nifty g_pool bot ONLY (v-G79, 30-Sep-2026). The original
file is untouched so v1/v2 bots keep working exactly as before.
v3 changes (LOG/DIAGNOSTIC ONLY -- the DPCR number itself is computed
exactly as before):
  * log files renamed with a _fyers_vE5 suffix (was _fyers_vE4) (no mixing with old runs)
  * compute_dpcr() snapshot additionally returns, from the SAME cached
    optionchain() response (no extra API call):
      "anchor"             -- alias of anchor_strike (v2 bot looked for it)
      "chain"              -- {strike: {"CE": {oi, ltp, volume, oich},
                                        "PE": {...}}} for every strike in
                              the response (ATM +/- OC_STRIKE_COUNT)
      "spot_at_fetch"      -- index LTP from the same response, if present
      "abs_ce_oi_window" / "abs_pe_oi_window" -- current OI summed over the
                              DPCR window strikes
      "data_time"          -- epoch of the optionchain() fetch
      "stale"              -- always False here (kept for interface parity
                              with the RMoney v3 module)

option_chain_filter_nifty.py — v1.0-LOGONLY

PURPOSE
-------
Phase 1 of the option-chain confirmation layer discussed for BOT_G.
This module does ONE thing: fetch Fyers option-chain data once per 3m
candle and log a bullish/bearish OI-tilt snapshot alongside whatever
your existing price-based signal_bot_X() checks are doing. It NEVER
blocks or gates an entry — same "log first, tune after ~20 days"
discipline you used for BOT_E's freshness filter before it went live.

WHY NO IV/GREEKS (v1 scope decision)
-------------------------------------
Fyers' optionchain() endpoint does not return implied volatility or
Greeks (confirmed against a still-open Fyers feature-request thread
asking for exactly this, as of mid-2025). Computing IV yourself means
a Black-Scholes back-out per strike per candle -- real extra work for
an unvalidated payoff. Cut from v1 on purpose. Revisit only if the
OI/volume signal alone doesn't show anything worth acting on after the
paper-test window.

WHAT'S IN THE SCORE (v1)
-------------------------
  PCR_TOTAL   : sum(PE oi) / sum(CE oi) across a strike window around ATM.
  OI_SHIFT     : compares ATM CE/PE OI to the previous snapshot.
                 BULLISH  = CE OI falling + PE OI rising (writers backing
                            off calls, building puts -- resistance easing)
                 BEARISH  = mirror of the above
                 MIXED    = both moved the same direction, or one held flat
                 NONE     = no prior snapshot yet (first candle of the day)
  *_vol_vs_avg : today's ATM volume on that side vs. a rolling average of
                 the last VOL_LOOKBACK snapshots -- a crude spike detector.

INTEGRATION (do this after the paper-test window, not now)
------------------------------------------------------------
Call compute_oc_snapshot(fyers, spot, atm_strike, bot_name=bot["name"])
once per 3m candle boundary in main(), right where fetch_data() already
runs -- NOT inside allow_trade() or any signal_bot_X(), so it can never
accidentally start gating. Log output goes to a dedicated file (below)
exactly like BOT_E gets its own bot_e_log file, so this can be reviewed
independently of the main bot log.

RATE-LIMIT NOTE
-----------------
Fyers v3 raised the daily cap to 1,00,000 calls/day (10x the old 10k
limit). One call per 3m candle for Nifty alone is ~125 calls/trading
day -- comfortable margin even after adding BankNifty and Sensex later.
OC_CACHE_SEC below still de-dupes calls within the same candle in case
this function gets invoked more than once per bar by accident.
"""

import time
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────
#  CONFIG (move to config_fyers_nifty.py once this graduates past LOGONLY)
# ─────────────────────────────────────────────────────────────────────────
OC_SYMBOL       = "BSE:SENSEX-INDEX"   # v8 Sensex (Nifty: NSE:NIFTY50-INDEX)
OC_STRIKE_COUNT = "10"          # ATM +/- 10 strikes each side from Fyers
OC_WINDOW       = 5             # but only score ATM +/- 5 strikes (250 pts)
OC_STRIKE_GAP   = 100           # v8 Sensex strike spacing (Nifty: 50)
OC_CACHE_SEC    = 170           # de-dupe calls within the same 3m candle
OC_LOG_FILE     = "option_chain_log_sensex_fyers_v8_9.txt"   # v-G79
VOL_LOOKBACK    = 5             # snapshots used for the volume rolling avg
HISTORY_MAX     = 50            # cap in-memory snapshot history

_OC_CACHE   = {"time": 0, "data": None}
_OC_HISTORY = []   # list of snapshot dicts, oldest first


def _oc_log(msg):
    """Same append-only, fail-soft pattern as the main bot's log()."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{ts} | {msg}"
    print(line)
    try:
        with open(OC_LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def fetch_option_chain(fyers, force_refresh=False):
    """
    v1.0-OCFETCH1: thin wrapper around fyers.optionchain(), cached per
    candle. Returns the raw optionsChain list, or None on any failure --
    never raises, mirrors fetch_data()'s fail-soft pattern elsewhere in
    this bot so a bad option-chain call can't take down the main loop.
    """
    now = time.time()
    if not force_refresh and _OC_CACHE["data"] is not None and \
       (now - _OC_CACHE["time"]) < OC_CACHE_SEC:
        return _OC_CACHE["data"]

    try:
        resp = fyers.optionchain(data={
            "symbol": OC_SYMBOL,
            "strikecount": OC_STRIKE_COUNT,
            "timestamp": "",
        })
        if not isinstance(resp, dict) or resp.get("s") == "error":
            _oc_log(f"[OC FETCH ERROR] {resp.get('message', 'unknown error') if isinstance(resp, dict) else resp}")
            return None
        chain = resp.get("data", {}).get("optionsChain")
        if not chain:
            _oc_log("[OC FETCH ERROR] empty optionsChain in response")
            return None
        _OC_CACHE["data"] = chain
        _OC_CACHE["time"] = now
        return chain
    except Exception as e:
        _oc_log(f"[OC FETCH ERROR] exception: {e}")
        return None


def _parse_chain(chain, atm_strike):
    """
    v1.0-OCPARSE1: reshape the flat optionsChain list into
    {strike: {"CE": {...}, "PE": {...}}}, restricted to the scoring
    window. Skips rows that aren't CE/PE (Fyers includes an index/futures
    row in the same list with option_type == "").
    """
    by_strike = {}
    for row in chain:
        opt_type = row.get("option_type")
        if opt_type not in ("CE", "PE"):
            continue
        strike = row.get("strike_price")
        if strike is None or abs(strike - atm_strike) > OC_WINDOW * OC_STRIKE_GAP:
            continue
        by_strike.setdefault(strike, {})[opt_type] = {
            "ltp":    row.get("ltp"),
            "oi":     row.get("oi"),
            "volume": row.get("volume"),
            "oich":   row.get("oich"),   # v-G-DPCR1: OI change vs previous
                                          # close, per Fyers' own field --
                                          # additive, doesn't affect the
                                          # existing PCR_TOTAL/OI_SHIFT path
                                          # above, which never reads this key.
        }
    return by_strike


def compute_oc_snapshot(fyers, spot, atm_strike, bot_name="MAIN"):
    """
    v1.0-OCSNAP1: LOG-ONLY. Fetches the chain, computes the PCR/OI-shift/
    volume snapshot, logs it, and returns the dict for the caller to
    optionally cross-reference against its own signal log line. Does
    NOT return a pass/fail or gate anything -- there is no threshold
    logic here on purpose. That comes later, once ~20 days of this
    output exists to validate against.
    """
    chain = fetch_option_chain(fyers)
    if chain is None:
        return None

    by_strike = _parse_chain(chain, atm_strike)
    if not by_strike:
        _oc_log(f"OC SNAPSHOT  | {bot_name} — no strikes in window, skipping (v1.0-LOGONLY)")
        return None

    total_ce_oi = sum((v.get("CE") or {}).get("oi") or 0 for v in by_strike.values())
    total_pe_oi = sum((v.get("PE") or {}).get("oi") or 0 for v in by_strike.values())
    pcr_total   = round(total_pe_oi / total_ce_oi, 3) if total_ce_oi else None

    atm_row    = by_strike.get(atm_strike, {})
    atm_ce_oi  = (atm_row.get("CE") or {}).get("oi")
    atm_pe_oi  = (atm_row.get("PE") or {}).get("oi")
    atm_ce_vol = (atm_row.get("CE") or {}).get("volume")
    atm_pe_vol = (atm_row.get("PE") or {}).get("volume")

    snapshot = {
        "time": time.time(), "spot": spot, "atm_strike": atm_strike,
        "pcr_total": pcr_total,
        "atm_ce_oi": atm_ce_oi, "atm_pe_oi": atm_pe_oi,
        "atm_ce_vol": atm_ce_vol, "atm_pe_vol": atm_pe_vol,
    }

    # ── OI shift vs. previous snapshot ──────────────────────────────────
    oi_shift = "NONE"
    if _OC_HISTORY:
        prev = _OC_HISTORY[-1]
        if None not in (prev.get("atm_ce_oi"), prev.get("atm_pe_oi"), atm_ce_oi, atm_pe_oi):
            ce_delta = atm_ce_oi - prev["atm_ce_oi"]
            pe_delta = atm_pe_oi - prev["atm_pe_oi"]
            snapshot["ce_oi_delta"] = ce_delta
            snapshot["pe_oi_delta"] = pe_delta
            if ce_delta < 0 and pe_delta > 0:
                oi_shift = "BULLISH"
            elif ce_delta > 0 and pe_delta < 0:
                oi_shift = "BEARISH"
            else:
                oi_shift = "MIXED"
    snapshot["oi_shift"] = oi_shift

    # ── volume vs. rolling average of last VOL_LOOKBACK snapshots ──────
    for side, vol_now, key in (("CE", atm_ce_vol, "ce_vol_vs_avg"),
                                ("PE", atm_pe_vol, "pe_vol_vs_avg")):
        recent = [s[f"atm_{side.lower()}_vol"] for s in _OC_HISTORY[-VOL_LOOKBACK:]
                  if s.get(f"atm_{side.lower()}_vol") is not None]
        if recent and vol_now is not None:
            avg = sum(recent) / len(recent)
            snapshot[key] = round(vol_now / avg, 2) if avg else None

    _OC_HISTORY.append(snapshot)
    if len(_OC_HISTORY) > HISTORY_MAX:
        _OC_HISTORY.pop(0)

    _oc_log(
        f"OC SNAPSHOT  | {bot_name} Spot:{spot} ATM:{atm_strike} "
        f"PCR:{pcr_total} ATM_CE_OI:{atm_ce_oi} ATM_PE_OI:{atm_pe_oi} "
        f"OI_SHIFT:{oi_shift} "
        f"CE_vol_x_avg:{snapshot.get('ce_vol_vs_avg')} "
        f"PE_vol_x_avg:{snapshot.get('pe_vol_vs_avg')} "
        f"(v1.0-LOGONLY, never gates entries)"
    )
    return snapshot


# =============================================================================
#  DPCR — DYNAMIC PCR FOR BOT_G  (v-G-DPCR1, LOG-ONLY)
#
#  Distinct from PCR_TOTAL above (total PE OI / total CE OI, a static-
#  window absolute-OI ratio). DPCR is what the BOT_G strategy design
#  actually calls for:
#
#    - Window is ATM +/- DPCR_WINDOW strikes (9 total at DPCR_WINDOW=4),
#      RECOMPUTED FROM CURRENT SPOT ON EVERY CALL -- never locked to the
#      ATM strike at day-open. ATM drifts with spot; the window drifts
#      with it.
#    - Uses Fyers' own `oich` field per strike (OI change vs previous
#      day's CLOSE, computed by Fyers -- confirmed via Fyers API docs,
#      not something this module snapshots/diffs itself).
#    - Net_CE_dOI = sum of oich across the CE side of the window.
#      Net_PE_dOI = sum of oich across the PE side of the window.
#      DPCR = Net_PE_dOI / Net_CE_dOI (guarded against a zero/near-zero
#      denominator -- logged as "undefined", not divided).
#    - Bias: >1.10 bullish, <0.90 bearish, 0.90-1.10 no-trade (confirmed
#      thresholds, tighter than the doc's original 0.8-1.2 draft).
#
#  TWO LOG STREAMS (both log-only, neither gates anything yet):
#    1. Per-candle snapshot -- every call, regardless of trade activity.
#    2. Window-shift events -- only when ATM differs from the previous
#       call, logging old ATM -> new ATM and DPCR just before/after, so
#       the strike-boundary jump behavior discussed earlier is visible
#       in the log rather than inferred.
#
#  SMOOTHING: a rolling average of the last DPCR_SMOOTH_N raw DPCR values
#  is computed and logged ALONGSIDE the raw value -- NOT used for the
#  bias label, NOT used to gate anything. Purely so real data exists to
#  decide later whether smoothing actually helps.
# =============================================================================

DPCR_WINDOW       = 4      # ATM +/- 4 strikes = 9 total, per the strategy doc.
                            # v-G37: this is now just the DEFAULT/fallback --
                            # compute_dpcr()'s own `dpcr_window` param
                            # overrides it per-call (bot file passes a DTE-
                            # scaled value; see config_fyers_nifty_g_pool_v1.
                            # BOTG_DPCR_WINDOW_BY_WEEKDAY). Untouched here.
DPCR_BULLISH_MIN  = 1.20   # v-G-DPCR3: widened from 1.10 (no-trade zone 0.8-1.2)
DPCR_BEARISH_MAX  = 0.80   # v-G-DPCR3: widened from 0.90
DPCR_SMOOTH_N      = 3      # rolling-average window, logged alongside raw
DPCR_LOG_FILE      = "dpcr_log_sensex_fyers_v8_9.txt"          # per-candle snapshots (v-G79)
DPCR_SHIFT_LOG_FILE = "dpcr_window_shift_sensex_fyers_v8_9.txt"  # window-shift / re-anchor events (v-G79)

_DPCR_HISTORY  = []          # raw DPCR values, oldest first (for smoothing)
_DPCR_LAST_ATM = {"atm": None, "dpcr": None}   # for window-shift detection

# ─────────────────────────────────────────────────────────────────────────
#  FIXED-ANCHOR WINDOW (v-G-DPCR3)
#  ---------------------------------------------------------------------
#  Spec (locked with Anu, 10-Aug-2026 session):
#    - Normal day : anchor strike is set from spot at/after 09:16 IST.
#    - Gap day    : anchor strike is set from spot at/after 10:00 IST
#                    (gap = spot open vs prior close >= GAP_THRESHOLD_PCT,
#                    same definition already used for BOT_G's own entry
#                    gate). Delayed anchor avoids baking first-hour
#                    trapped-position unwind noise into the OI baseline.
#    - Once anchored, the 9-strike window (anchor +/- DPCR_WINDOW) is
#      FIXED -- it does NOT walk with spot on every call, unlike the old
#      v-G-DPCR1 behavior.
#    - RE-ANCHOR: if spot drifts >= ANCHOR_DRIFT_PCT from the MOST RECENT
#      anchor's spot (not the original 09:16/10:00 anchor), the window
#      re-anchors to a new ATM strike computed from current spot. This can
#      happen any number of times in a day (uncapped). On re-anchor:
#        * _DPCR_HISTORY (smoothing) is cleared and restarts fresh, same
#          as it would at the original 09:16/10:00 anchor.
#        * A RE-ANCHOR event is logged (old anchor -> new anchor, DPCR
#          just before/after) to DPCR_SHIFT_LOG_FILE, same log used for
#          the old window-shift events.
#    - Scope: this fixed-anchor window applies ONLY to the DPCR bias calc
#      in compute_dpcr(). It does NOT affect which strike BOT_G actually
#      trades -- live/current ATM is used for option-contract selection
#      elsewhere, untouched by any of this.
#    - Still log-only: none of this gates entries yet.
# ─────────────────────────────────────────────────────────────────────────
ANCHOR_DRIFT_PCT      = 0.75   # re-anchor trigger, % move from most recent anchor spot (REANCHOR_MODE='PCT' only)
# v-E8 (vE5): re-anchor when spot has moved HALF the DPCR window's width
# from the spot at the last anchor (Wed +/-5 -> 125 pts ... Mon/Tue +/-2 -> 50).
# Same rule in the RMoney module. 'PCT' restores the old ANCHOR_DRIFT_PCT rule.
REANCHOR_MODE = "HALF_WINDOW"
REANCHOR_HALF_WINDOW_FRACTION = 0.5
ANCHOR_TIME_NORMAL    = (9, 16)   # (hour, minute) IST -- normal day anchor time
ANCHOR_TIME_GAP       = (10, 0)   # (hour, minute) IST -- gap day anchor time

_ANCHOR_STATE = {
    "anchor_strike": None,   # fixed ATM strike currently in use for DPCR window
    "anchor_spot":   None,   # spot at the moment this anchor was set (drift base)
    "anchor_time":   None,   # datetime the anchor was set, for the log
    # v-G-DPCR4: baseline INTERDAY (prev-close-relative, i.e. raw oich) totals
    # captured at the FIRST compute_dpcr() call after each (re-)anchor. None
    # means "not captured yet" -- the next compute_dpcr() call captures it
    # and reports an undefined (0/0) DPCR that one time, same as any other
    # cold start. Every reading after that is baselined against this, turning
    # the always-interday oich feed into a genuinely intraday-only number:
    # DPCR_intraday(t) = (interday(t) - interday(anchor)) ratio, CE vs PE.
    "baseline_net_ce": None,
    "baseline_net_pe": None,
}


def _reset_dpcr_anchor(spot, atm_strike, bot_name, reason):
    """
    v-G-DPCR3: (re)sets the fixed anchor and clears smoothing history so
    it restarts fresh from this point -- same behavior whether this is
    the original 09:16/10:00 anchor or a later 0.75%-drift re-anchor.
    v-G-DPCR4: also clears the intraday OI baseline -- the next
    compute_dpcr() call recaptures it fresh, so DPCR after a re-anchor
    measures change since THAT re-anchor, not since 09:16/10:00.
    """
    old_anchor = _ANCHOR_STATE["anchor_strike"]
    _ANCHOR_STATE["anchor_strike"] = atm_strike
    _ANCHOR_STATE["anchor_spot"]   = spot
    _ANCHOR_STATE["anchor_time"]   = datetime.now()
    _ANCHOR_STATE["baseline_net_ce"] = None
    _ANCHOR_STATE["baseline_net_pe"] = None
    _DPCR_HISTORY.clear()
    if old_anchor is not None:
        _dpcr_log(
            f"RE-ANCHOR    | {bot_name} {reason} "
            f"OldAnchor:{old_anchor} -> NewAnchor:{atm_strike} "
            f"Spot:{spot} (smoothing history + intraday OI baseline reset, v-G-DPCR4)",
            file=DPCR_SHIFT_LOG_FILE,
        )
    else:
        _dpcr_log(
            f"ANCHOR SET   | {bot_name} {reason} "
            f"Anchor:{atm_strike} Spot:{spot} (v-G-DPCR3)",
            file=DPCR_SHIFT_LOG_FILE,
        )


def _maybe_anchor_or_reanchor(spot, bot_name, gap_day, dpcr_window=None, reanchor_pts=None, anchor_ref=None):   # v8 Sensex: reanchor_pts; v8.3.3: anchor_ref
    """
    v-G-DPCR3: decides whether to (a) set the initial anchor once the
    09:16/10:00 threshold has passed, or (b) re-anchor if drift from the
    most recent anchor's spot has hit ANCHOR_DRIFT_PCT. Returns the
    anchor strike to use this call, or None if no anchor should exist
    yet (before 09:16 normal / before 10:00 gap day).
    """
    now = datetime.now()
    anchor_hm = ANCHOR_TIME_GAP if gap_day else ANCHOR_TIME_NORMAL
    threshold = now.replace(hour=anchor_hm[0], minute=anchor_hm[1], second=0, microsecond=0)

    if _ANCHOR_STATE["anchor_strike"] is None:
        if now < threshold:
            return None   # too early -- no anchor yet, caller should skip
        # v8.3.3: normal day + a reference (closed 09:15 3m candle close, same on both brokers) -> anchor AND drift base come from it
        _use_ref = bool(anchor_ref) and not gap_day
        _base = anchor_ref if _use_ref else spot
        atm_strike = round(_base / OC_STRIKE_GAP) * OC_STRIKE_GAP
        _reset_dpcr_anchor(_base, atm_strike, bot_name,
                            reason=f"initial anchor ({'gap-day 10:00' if gap_day else '09:16'})"
                                   + (f" [v8.3.3 common anchor: closed 09:15 candle close {anchor_ref}, live spot {spot}]" if _use_ref else ""))
        return atm_strike

    drift_pts = abs(spot - _ANCHOR_STATE["anchor_spot"])
    drift_pct = drift_pts / _ANCHOR_STATE["anchor_spot"] * 100
    if REANCHOR_MODE == "HALF_WINDOW":   # v-E8
        _w = dpcr_window if dpcr_window is not None else DPCR_WINDOW
        _limit_pts = (reanchor_pts if reanchor_pts is not None   # v8 Sensex: weekday floor supplied by the bot
                      else _w * OC_STRIKE_GAP * REANCHOR_HALF_WINDOW_FRACTION)
        _hit = drift_pts >= _limit_pts
        _why = f"drift {drift_pts:.1f}pts ({drift_pct:.2f}%) >= {_limit_pts:.0f}pts (half of window +/-{_w}, v-E8)"
    else:
        _hit = drift_pct >= ANCHOR_DRIFT_PCT
        _why = f"drift {drift_pct:.2f}% >= {ANCHOR_DRIFT_PCT}%"
    if _hit:
        atm_strike = round(spot / OC_STRIKE_GAP) * OC_STRIKE_GAP
        _reset_dpcr_anchor(spot, atm_strike, bot_name, reason=_why)
        return atm_strike

    return _ANCHOR_STATE["anchor_strike"]


def _dpcr_log(msg, file=DPCR_LOG_FILE):
    """Same append-only, fail-soft pattern as _oc_log(), separate file."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{ts} | {msg}"
    print(line)
    try:
        with open(file, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _dpcr_log_table(by_strike, anchor_strike, bot_name):
    """
    v-G-DPCR3: prints/logs the per-strike CE_oich/PE_oich breakdown as a
    fixed-width table instead of one free-text line per strike -- same
    data as before (verbose per-strike cross-check against the broker
    terminal), just easier to scan. Column widths sized for Nifty OI
    change magnitudes (up to ~8 digits); widen COL_OICH if needed for
    BankNifty/Sensex later.
    """
    COL_STRIKE, COL_OICH = 8, 13
    header = (f"{'Strike':<{COL_STRIKE}}{'CE_oich':>{COL_OICH}}{'PE_oich':>{COL_OICH}}   Note")
    rule   = "-" * len(header)
    _dpcr_log(f"DPCR STRIKES TABLE | {bot_name} Anchor:{anchor_strike} (fixed window)")
    _dpcr_log(f"    {header}")
    _dpcr_log(f"    {rule}")
    for strike in sorted(by_strike.keys()):
        ce_oich = by_strike[strike].get("CE")
        pe_oich = by_strike[strike].get("PE")
        note = "<-- ANCHOR" if strike == anchor_strike else ""
        ce_str = "None" if ce_oich is None else str(ce_oich)
        pe_str = "None" if pe_oich is None else str(pe_oich)
        _dpcr_log(f"    {strike:<{COL_STRIKE}}{ce_str:>{COL_OICH}}{pe_str:>{COL_OICH}}   {note}")


def compute_dpcr(fyers, spot, bot_name="BOT_G", verbose=False, gap_day=False, dpcr_window=None, reanchor_pts=None, anchor_ref=None):   # v8 Sensex: reanchor_pts; v8.3.3: anchor_ref
    """
    v-G-DPCR4: LOG-ONLY. DPCR is now genuinely INTRADAY-ONLY. Fyers' oich
    field (like NSE's own published "CHNG IN OI") is always measured since
    the previous close, no matter when in the day it's polled -- confirmed
    against real NSE data, there's no native "since today's open" number
    available from either source. So this function captures the interday
    total once, at the first call after each (re-)anchor, as a baseline,
    and every later call subtracts it off before computing DPCR. What's
    left reflects only OI change since that anchor/re-anchor -- nothing
    carried over from yesterday or from pre-market positioning.

    v-G37 (05-Sep-2026): `dpcr_window` param added, explicit instruction --
    lets the caller scale the OI window by days-to-expiry instead of always
    using the fixed module constant DPCR_WINDOW (still the default when
    None, so any other/older caller is unaffected). IMPORTANT: this window
    is about the NEAREST/front-week option chain -- fetch_option_chain()
    passes no expiry to Fyers, so it always gets the imminent Tuesday's
    chain, which is a DIFFERENT contract from whatever BOT_G itself is
    actually holding that day (BOT_G deliberately always rolls to NEXT
    week's contract -- see the main bot file's _next_nifty_weekly_expiry_
    date()). The two are unrelated by design: this window controls what
    OI data feeds the DPCR direction signal, not which strike gets traded.
    Caller is expected to pass an already-fetched-wide-enough window --
    OC_STRIKE_COUNT=10 above comfortably covers every value this is
    actually called with (max 5).

    Window is a FIXED anchor strike (v-G-DPCR3), not live ATM recomputed
    every call. Anchor set from spot at/after 09:16 normal day / 10:00 gap
    day, and re-anchors any time spot drifts >= ANCHOR_DRIFT_PCT from the
    most recent anchor's spot (uncapped through the day). Both the
    smoothing history AND the intraday OI baseline reset on every
    (re-)anchor -- see the FIXED-ANCHOR WINDOW block above for the full
    spec. Returns None (skips silently, one line in the log) if called
    before the anchor threshold has passed -- expected before 09:16/10:00,
    not an error.

    The very first call after any (re-)anchor returns DPCR=None (UNDEFINED)
    by design -- baseline == current reading, so there's zero intraday
    change to report yet. This is not a bug; it builds from the next call.

    Still does NOT gate any entry -- no threshold-driven pass/fail return
    here, only data. `gap_day` must be passed by the caller (main bot
    already computes this for its own entry gate -- same flag, don't
    recompute it here).

    v-G-DPCR2 carryover: `verbose` param still supported -- when True,
    logs the per-strike CE_oich/PE_oich breakdown, now as a table
    (_dpcr_log_table) instead of one line per strike. NOTE: that table
    still shows raw (interday) oich per strike -- it's a cross-check aid
    against the broker terminal, not the intraday-baselined number.
    """
    anchor_strike = _maybe_anchor_or_reanchor(spot, bot_name, gap_day, dpcr_window, reanchor_pts, anchor_ref)   # v-E8 / v8 Sensex / v8.3.3
    if anchor_strike is None:
        anchor_hm = ANCHOR_TIME_GAP if gap_day else ANCHOR_TIME_NORMAL
        _dpcr_log(f"DPCR SNAPSHOT | {bot_name} — before anchor time "
                  f"({anchor_hm[0]:02d}:{anchor_hm[1]:02d}"
                  f"{' gap-day' if gap_day else ''}), no window yet, skipping")
        return None

    chain = fetch_option_chain(fyers)
    if chain is None:
        return None

    window = dpcr_window if dpcr_window is not None else DPCR_WINDOW   # v-G37

    by_strike = {}
    chain_rows = {}          # v-G81: every strike in the response, diagnostics only
    abs_oi = {"CE": 0.0, "PE": 0.0}
    spot_at_fetch = None
    for row in chain:
        opt_type = row.get("option_type")
        if opt_type not in ("CE", "PE"):
            if spot_at_fetch is None and row.get("ltp") is not None:
                spot_at_fetch = row.get("ltp")   # index/underlying row
            continue
        strike = row.get("strike_price")
        if strike is not None:
            chain_rows.setdefault(strike, {})[opt_type] = {
                "oi": row.get("oi"), "ltp": row.get("ltp"),
                "volume": row.get("volume"), "oich": row.get("oich")}
        if strike is None or abs(strike - anchor_strike) > window * OC_STRIKE_GAP:
            continue
        by_strike.setdefault(strike, {})[opt_type] = row.get("oich")
        abs_oi[opt_type] += (row.get("oi") or 0)

    # v-G-DPCR4: these two sums are still INTERDAY (prev-close-relative) --
    # that's just what Fyers' own oich field is, unavoidably. Renamed
    # explicitly so nothing downstream mistakes them for the real thing.
    net_ce_doi_interday = sum((v.get("CE") or 0) for v in by_strike.values())
    net_pe_doi_interday = sum((v.get("PE") or 0) for v in by_strike.values())

    if not by_strike:
        _dpcr_log(f"DPCR SNAPSHOT | {bot_name} — no strikes in window at Anchor:{anchor_strike}, skipping")
        return None

    if verbose:
        _dpcr_log_table(by_strike, anchor_strike, bot_name)

    # v-G-DPCR4: intraday-only DPCR. Fyers' oich (and NSE's own published
    # "CHNG IN OI") is ALWAYS measured since the previous close, no matter
    # how often it's polled -- confirmed against real NSE data, there is no
    # native "since today's open" figure available anywhere. So we build
    # our own: capture the interday total ONCE, at the first call after
    # each (re-)anchor, as a baseline, then every later reading subtracts
    # it off. What's left is change that happened only since that anchor
    # (or re-anchor) -- genuinely intraday, nothing carried over from
    # yesterday or from before market open.
    if _ANCHOR_STATE["baseline_net_ce"] is None:
        _ANCHOR_STATE["baseline_net_ce"] = net_ce_doi_interday
        _ANCHOR_STATE["baseline_net_pe"] = net_pe_doi_interday
        _dpcr_log(
            f"DPCR BASELINE | {bot_name} Anchor:{anchor_strike} captured intraday "
            f"baseline InterdayNetCEdOI:{net_ce_doi_interday} "
            f"InterdayNetPEdOI:{net_pe_doi_interday} (v-G-DPCR4) -- DPCR undefined "
            f"this reading, builds from the next one"
        )

    net_ce_doi = net_ce_doi_interday - _ANCHOR_STATE["baseline_net_ce"]
    net_pe_doi = net_pe_doi_interday - _ANCHOR_STATE["baseline_net_pe"]

    if abs(net_ce_doi) < 1e-9:
        dpcr, bias = None, "UNDEFINED"
    else:
        dpcr = round(net_pe_doi / net_ce_doi, 3)
        if dpcr > DPCR_BULLISH_MIN:
            bias = "BULLISH"
        elif dpcr < DPCR_BEARISH_MAX:
            bias = "BEARISH"
        else:
            bias = "NO_TRADE"

    # ── smoothing (logged alongside raw, not used for `bias` above) ────
    # NOTE: _DPCR_HISTORY is cleared inside _reset_dpcr_anchor() on every
    # (re-)anchor event, so this always restarts fresh from that point --
    # no separate reset logic needed here.
    smoothed = None
    if dpcr is not None:
        _DPCR_HISTORY.append(dpcr)
        if len(_DPCR_HISTORY) > max(DPCR_SMOOTH_N, HISTORY_MAX):
            _DPCR_HISTORY.pop(0)
        recent = [v for v in _DPCR_HISTORY[-DPCR_SMOOTH_N:] if v is not None]
        if recent:
            smoothed = round(sum(recent) / len(recent), 3)

    _DPCR_LAST_ATM["atm"]  = anchor_strike
    _DPCR_LAST_ATM["dpcr"] = dpcr

    snapshot = {
        "time": time.time(), "spot": spot, "anchor_strike": anchor_strike,
        "net_ce_doi": net_ce_doi, "net_pe_doi": net_pe_doi,
        "net_ce_doi_interday": net_ce_doi_interday, "net_pe_doi_interday": net_pe_doi_interday,
        "dpcr": dpcr, "dpcr_smoothed": smoothed, "bias": bias,
        "window_strikes": sorted(by_strike.keys()),
        # v-G81 diagnostics (see module header) -- not used by DPCR itself
        "anchor": anchor_strike, "chain": chain_rows, "spot_at_fetch": spot_at_fetch,
        "abs_ce_oi_window": abs_oi["CE"], "abs_pe_oi_window": abs_oi["PE"],
        "data_time": _OC_CACHE.get("time"), "stale": False,
    }

    _dpcr_log(
        f"DPCR SNAPSHOT | {bot_name} Spot:{spot} Anchor:{anchor_strike} "
        f"Window:{window*2+1}strikes(ATM+/-{window}, v-G37 DTE-scaled) "
        f"IntradayNetCEdOI:{net_ce_doi} IntradayNetPEdOI:{net_pe_doi} "
        f"DPCR:{dpcr} Smoothed:{smoothed} Bias:{bias} "
        f"[InterdayNetCEdOI:{net_ce_doi_interday} InterdayNetPEdOI:{net_pe_doi_interday}] "
        f"(v-G-DPCR4-LOGONLY, never gates entries)"
    )
    return snapshot


# =============================================================================
#  STANDALONE SMOKE TEST — run this file directly to verify the Fyers
#  optionchain() call + auth path work, independent of the main bot.
#
#  Requires fyers_client_id.txt / fyers_access_token.txt in the SAME
#  folder you run this from -- same files, same format, same
#  fyers_login.py you already run each morning for the main bot. This
#  does not touch the main bot's cache/state in any way; it's a
#  completely separate process reading the same two token files.
#
#  Only useful during market hours (roughly 09:15-15:30 IST) -- outside
#  that window the API will most likely return empty/stale OI, which is
#  expected and not a bug in this script.
#
#  v-G-DPCR2 (09-Aug-2026): VERIFICATION MODE added, for the 09:15-09:45
#  cross-check-against-broker-terminal window specifically, before this
#  feeds into BOT_G paper trading. Two changes from the original smoke
#  test, both purely additive:
#    1. POLL_SEC tightened to 60s (was 180s) -- more data points inside
#       a 30-min window to compare against the terminal, not tied to the
#       3-min candle cadence this uses once actually wired into main().
#    2. compute_dpcr(..., verbose=True) -- per-strike CE_oich/PE_oich
#       breakdown printed every poll (see compute_dpcr()'s v-G-DPCR2
#       docstring note above), so each strike can be checked individually,
#       not just the aggregate DPCR number.
#  Everything else (fetch_option_chain, compute_oc_snapshot, the DPCR
#  formula/thresholds themselves) is completely unchanged -- this is a
#  verification run of the real logic, not a separate test harness.
# =============================================================================
if __name__ == "__main__":
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    import sys
    from fyers_apiv3 import fyersModel

    POLL_SEC = 60   # v-G-DPCR2: tightened from 180s for the 09:15-09:45
                     # verification window -- change back to 180 (or read
                     # from config) once this graduates to running inside
                     # the main bot's 3m candle loop.

    # v-G-DPCR3: smoke test now needs to know if today is a gap day, since
    # that changes the DPCR anchor time (09:16 vs 10:00). This mirrors
    # main bot's own gap-day flag -- it is NOT recomputed here from spot,
    # just asked once at startup so this smoke test doesn't need its own
    # prior-close lookup. Answer "n" for a normal verification run.
    _gap_day = input("Is today a gap day (spot open vs prior close >= 1%)? [y/N]: ").strip().lower() == "y"

    try:
        _APP_ID       = open("fyers_client_id.txt").read().strip()
        _ACCESS_TOKEN = open("fyers_access_token.txt").read().strip()
    except FileNotFoundError as e:
        print(f"[SMOKE TEST] Missing token file: {e}")
        print("[SMOKE TEST] Run fyers_login.py first, or copy this script into "
              "the same folder as the main bot's token files.")
        raise SystemExit(1)

    _fyers = fyersModel.FyersModel(
        token=_ACCESS_TOKEN,
        is_async=False,
        client_id=_APP_ID,
    )

    print(f"[VERIFICATION MODE] Polling every {POLL_SEC}s — Ctrl+C to stop "
          f"whenever you're done comparing against the broker terminal "
          f"(e.g. around 09:45). Per-strike CE_oich/PE_oich will print "
          f"every poll below the aggregate DPCR line -- cross-check those "
          f"against what the terminal shows for the same strikes. "
          f"OI_SHIFT and vol_x_avg stay None on the first snapshot, then "
          f"populate from the second poll onward.")

    _poll_count = 0
    try:
        while True:
            _poll_count += 1
            # Re-fetch spot each poll -- it moves, ATM strike can shift too.
            _quote = _fyers.quotes({"symbols": OC_SYMBOL})
            if _quote.get("s") == "error" or not _quote.get("d"):
                print(f"[SMOKE TEST] Could not fetch spot quote: {_quote}")
                time.sleep(POLL_SEC)
                continue
            _spot = _quote["d"][0]["v"]["lp"]
            _atm  = round(_spot / OC_STRIKE_GAP) * OC_STRIKE_GAP

            print(f"[SMOKE TEST] Poll #{_poll_count}  Spot:{_spot}  ATM:{_atm}  fetching option chain...")
            # force_refresh=True: we WANT a fresh call every poll, not the
            # 170s de-dupe cache -- that cache exists to protect against
            # multiple bots calling this within the same candle, not
            # against this deliberate polling loop.
            _snap = compute_oc_snapshot(_fyers, spot=_spot, atm_strike=_atm,
                                         bot_name="SMOKE_TEST")

            if _snap is None:
                print("[SMOKE TEST] compute_oc_snapshot() returned None -- check "
                      f"{OC_LOG_FILE} above for the specific "
                      "[OC FETCH ERROR] or 'no strikes in window' reason.")
            else:
                print(f"[SMOKE TEST] OK -- snapshot: {_snap}")

            # v-G-DPCR1: also exercise the new DPCR function every poll,
            # same cadence, same shared fetch_option_chain() cache -- no
            # extra Fyers call cost beyond what compute_oc_snapshot()
            # above already made this cycle.
            # v-G-DPCR2: verbose=True for the verification window (see
            # header comment above this __main__ block).
            _dpcr_snap = compute_dpcr(_fyers, spot=_spot, bot_name="SMOKE_TEST", verbose=True, gap_day=_gap_day)
            if _dpcr_snap is None:
                print("[SMOKE TEST] compute_dpcr() returned None -- check "
                      f"{DPCR_LOG_FILE} above for the reason.")
            else:
                print(f"[SMOKE TEST] DPCR OK -- {_dpcr_snap}")

            time.sleep(POLL_SEC)
    except KeyboardInterrupt:
        print(f"\n[VERIFICATION MODE] Stopped after {_poll_count} poll(s). "
              f"Full history in {OC_LOG_FILE} (OI/PCR snapshots) and "
              f"{DPCR_LOG_FILE} (DPCR + per-strike breakdown). "
              f"Once you've cross-checked these against the broker "
              f"terminal, send me what you found and I'll wire "
              f"get_current_dpcr() in the main bot file to call "
              f"compute_dpcr() for real, instead of the current stub.")
        sys.exit(0)
