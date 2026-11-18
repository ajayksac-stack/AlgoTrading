# =============================================================================
#  vE6.6 (02-Nov-2026) v-E42: pre_snapshot() + first baseline from the 09:18 pre-snapshot
#        when the 09:15 reference arrives late (see compute_dpcr). Formula unchanged.
#  option_chain_filter_nifty_rmoney_vE6.py -- copy of the RMoney/XTS
#  option_chain_filter_nifty.py for the v3 Nifty g_pool bot ONLY (v-G79,
#  30-Sep-2026). Original file untouched, v1/v2 bots unaffected.
#  v3 changes (LOG/DIAGNOSTIC ONLY -- DPCR computed exactly as before):
#    * DPCR lines now ALSO written to dpcr_log_nifty_rmoney_vE6.txt /
#      dpcr_window_shift_nifty_rmoney_vE6.txt (before: console only, so
#      RMoney never had a DPCR log file). print() output unchanged.
#    * snapshot additionally returns "anchor", "window_strikes",
#      "oi_by_strike" {strike: {"CE": oi, "PE": oi}},
#      "abs_ce_oi_window" / "abs_pe_oi_window", "data_time", and
#      "stale" (True when compute_dpcr() hands back the previous candle's
#      cached snapshot because it was called outside the :00-:10s window).
#    * new helper fetch_oi_for_strikes() for strikes outside the window
#      (ATM after spot drifts) -- one extra batched call, only when needed.
#
#  option_chain_filter_nifty.py -- DPCR (option-chain OI) data source
#  for RMoney/XTS. Nifty only, for now.
#
#  v-RG2A (27-Aug-2026): brand-new module, built to the SAME interface
#  contract BOT_nifty_g_v1_0_LOGONLY.py's get_current_dpcr()
#  expects (mirrors the Fyers-side option_chain_filter_nifty.py's own
#  compute_dpcr() -> snap dict shape: "dpcr", "net_pe_doi", "net_ce_doi",
#  at minimum). RMoney/XTS-native by explicit instruction -- no Fyers
#  dependency, no cross-broker session.
#
#  ARCHITECTURE, matches the fixed-anchor design already proven on Fyers
#  (v-G-DPCR3 in the DPCR log lines seen this session):
#    - Anchor spot set ONCE per day, at 09:16 (normal day) or 10:00 (gap
#      day) -- NOT re-set every candle. Determines the fixed 9-strike
#      window (ATM +/- 4 strikes) tracked for the rest of the day.
#    - Re-anchors (new ATM, new 9-strike window, new OI baseline) if spot
#      drifts >0.75% from the CURRENT anchor -- matches the real
#      "WINDOW SHIFT" log lines seen in dpcr_window_shift_nifty.txt.
#    - Tracks CUMULATIVE OI change (current OI - baseline OI, summed
#      across the 9 strikes, CE and PE separately) since the anchor/
#      re-anchor moment -- this is "IntradayNetCEdOI"/"IntradayNetPEdOI"
#      in the log format, and exactly what BOT_G's new signed-DPCR
#      formula (compute_signed_dpcr() in the bot file) needs.
#
#  ⚠️ SMOKE-TEST CAVEAT — READ BEFORE TRUSTING ANY OUTPUT FROM THIS FILE:
#  The ONE piece of this module that is genuinely unverified is the OI
#  DATA SOURCE ITSELF (_fetch_oi_batch() below). RMoney's confirmed-
#  working quotes endpoint (xtsMessageCode=1502, used everywhere else in
#  this bot) returns Touchline data ONLY -- LTP/bid/ask, no OI field
#  anywhere in that response (confirmed by reading the existing A-F
#  suite's own getQuotes()). No other message code has been verified
#  against a real RMoney/XTS response. xtsMessageCode=1510 is used below
#  as a best-effort candidate (a commonly-documented code for Open
#  Interest in the standard Symphony Fintech XTS API family RMoney is
#  built on) -- NOT confirmed working. _fetch_oi_batch() logs the FULL
#  raw response on every call specifically so the first live/paper run
#  either confirms this works or shows exactly what needs to change --
#  same diagnostic-first approach used to find the Fyers symbol-
#  construction bug this session. If OI genuinely isn't available this
#  way, every DPCR-dependent decision in BOT_G/BOT_G fails closed
#  (returns None, treated as "gate fails closed" per get_current_dpcr()'s
#  own contract) rather than trading on wrong data.
# =============================================================================

import json
import time
from datetime import datetime

import requests

MARKETDATA_URL   = "https://xts.rmoneyindia.co.in:3000/apimarketdata"
NIFTY_FO_SEGMENT = 2

STRIKE_ROUND_UNIT     = 50
WINDOW_STRIKES_EACH_SIDE = 4     # ATM +/- 4 = 9 strikes total, matches Fyers
REANCHOR_DRIFT_PCT    = 0.75     # re-anchor if spot moves this % from anchor (REANCHOR_MODE='PCT' only)
# v-E7/v-E8 (vE5): re-anchor when spot has moved HALF the DPCR window's width
# from the SPOT at the last anchor (was: % from the anchor STRIKE) -- same
# rule as the Fyers module. 'PCT' restores the old percentage rule (from spot).
# v-E27 (vE6.2.1): see compute_dpcr() -- same rule as the Fyers module.
ANCHOR_ON_3M_BOUNDARY   = True
ANCHOR_BOUNDARY_MAX_SEC = 10
# v-E39 (vE6.4): with the common 09:15-candle reference, the first anchor and
# its baseline read may come up to this many seconds into the boundary minute.
ANCHOR_REF_GRACE_SEC = 45
REANCHOR_MODE = "HALF_WINDOW"
REANCHOR_HALF_WINDOW_FRACTION = 0.5

_HTTP = requests.Session()

# One shared anchor/window/baseline state per day -- BOT_G and BOT_G read
# the SAME state (matches Fyers' _is_new_shared_dpcr_candle() dedup
# pattern: one real OI fetch per candle, not one per bot).
_STATE = {
    "date": None,
    "anchor": None,
    "anchor_spot": None,      # v-E7: spot when the anchor was set (drift base)
    "strikes": None,          # list of 9 strike prices, fixed until re-anchor
    "baseline_oi": None,      # {(strike, side): oi} captured at anchor time
    "last_fetch_time": 0,
    "baseline_pending": False,
    "last_dpcr_candle_key": None,
}

_EID_CACHE_OC = {}   # separate from the bot file's own _EID_CACHE -- this
                      # module is self-contained, doesn't reach into the
                      # bot file's globals (avoids a circular import)

_OI_FETCH_CACHE_SEC = 999999

DPCR_LOG_FILE       = "dpcr_log_nifty_rmoney_vE6.txt"            # v-G79
DPCR_SHIFT_LOG_FILE = "dpcr_window_shift_nifty_rmoney_vE6.txt"   # v-G79


def _dpcr_file_log(msg, file=DPCR_LOG_FILE):
    """v-G79: print (as before) AND append to a log file. Fail-soft."""
    print(msg)
    try:
        with open(file, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {msg}\n")
    except Exception:
        pass


def _stale_copy(snap):
    """v-G80: previous candle's snapshot handed back again -- mark it so
    the bot's diagnostics don't treat it as a fresh reading."""
    if snap is None:
        return None
    s = dict(snap)
    s["stale"] = True
    return s


def fetch_oi_for_strikes(md_headers, expiry_code, strikes):
    """
    v-G81: current OI for arbitrary strikes (both sides) -- used only by
    the bot's ATM diagnostic when the ATM strike is outside the DPCR
    window. Same EID resolver + same 1510 quote call as the DPCR path.
    Returns {(strike, side): oi}; {} on any failure. Never raises.
    """
    try:
        instruments, eid_map = [], {}
        for strike in strikes:
            for side in ("CE", "PE"):
                eid = _resolve_eid_oc(md_headers, f"NIFTY{expiry_code}{strike}{side}")
                if eid is None:
                    continue
                instruments.append({"exchangeSegment": NIFTY_FO_SEGMENT, "exchangeInstrumentID": eid})
                eid_map[eid] = (strike, side)
        oi_by_eid = _fetch_oi_batch(md_headers, instruments)
        return {eid_map[e]: oi for e, oi in oi_by_eid.items() if e in eid_map}
    except Exception as e:
        print(f"[OC_FILTER_RMONEY v3 fetch_oi_for_strikes ERROR] {e}")
        return {}
# v-G2A: do NOT use a free-running seconds cache for DPCR.  OI snapshots are
# synchronized to the 3-minute DPCR candle boundary, matching the Fyers flow.


def _round_strike(spot):
    return int(round(spot / STRIKE_ROUND_UNIT)) * STRIKE_ROUND_UNIT


def _build_strike_window(anchor, window=None):
    """Build a fixed symmetric DPCR OI window around the anchor.
    v-G37: window can be scaled by days-to-nearest-weekly-expiry; falls back
    to the legacy WINDOW_STRIKES_EACH_SIDE when omitted.
    """
    atm = _round_strike(anchor)
    n = WINDOW_STRIKES_EACH_SIDE if window is None else int(window)
    return [atm + i * STRIKE_ROUND_UNIT
            for i in range(-n, n + 1)]


def _resolve_eid_oc(md_headers, symbol):
    """Resolve the exact requested option contract; never accept an ambiguous first result."""
    if symbol in _EID_CACHE_OC:
        return _EID_CACHE_OC[symbol]
    try:
        resp = _HTTP.get(f"{MARKETDATA_URL}/search/instruments",
                          headers=md_headers, params={"searchString": symbol}, timeout=5)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get("type") != "success":
            return None
        items = data.get("result", [])
        if not isinstance(items, list) or not items:
            return None
        exact = []
        for item in items:
            eid = item.get("ExchangeInstrumentID") or item.get("exchangeInstrumentID")
            if not eid:
                continue
            names = [str(item.get(k, "")) for k in
                     ("TradingSymbol", "Name", "DisplayName", "Description", "Symbol")]
            if any(v.upper() == symbol.upper() for v in names if v):
                exact.append(int(eid))
        if len(exact) != 1:
            # Also allow one unique exact-looking textual containment match only when
            # the broker returned a single candidate; multiple/ambiguous results fail closed.
            if len(items) == 1:
                eid = items[0].get("ExchangeInstrumentID") or items[0].get("exchangeInstrumentID")
                if eid:
                    names = [str(items[0].get(k, "")) for k in
                             ("TradingSymbol", "Name", "DisplayName", "Description", "Symbol")]
                    if any(symbol.upper() in v.upper() or v.upper() in symbol.upper() for v in names if v):
                        _EID_CACHE_OC[symbol] = int(eid)
                        return int(eid)
            print(f"[OC_FILTER_RMONEY EID ERROR] exact contract not uniquely resolved: {symbol}; results={items}")
            return None
        _EID_CACHE_OC[symbol] = exact[0]
        return exact[0]
    except Exception as e:
        print(f"[OC_FILTER_RMONEY EID EXCEPTION] {symbol}: {e}")
        return None


def _fetch_oi_batch(md_headers, instruments):
    """
    v-RG2: SMOKE TEST -- see module header. xtsMessageCode=1510 is an
    UNVERIFIED candidate for per-instrument Open Interest. Logs the full
    raw response every call so the actual field name/shape can be
    confirmed (or corrected) from the first real run.

    Returns {exchangeInstrumentID: oi_float} or {} on any failure --
    fails closed, never raises into the caller.
    """
    if not instruments:
        return {}
    try:
        resp = _HTTP.post(
            f"{MARKETDATA_URL}/instruments/quotes",
            headers=md_headers,
            json={"instruments": instruments, "xtsMessageCode": 1510, "publishFormat": "JSON"},
            timeout=5)
        print(f"[OC_FILTER_RMONEY OI DIAG] xtsMessageCode=1510 raw response: "
              f"status={resp.status_code} body={resp.text[:800]}")
        if resp.status_code != 200:
            return {}
        data = resp.json()
        if data.get("type") != "success":
            return {}
        result = {}
        for item in data["result"].get("listQuotes", []):
            q = json.loads(item) if isinstance(item, str) else item
            eid = q.get("ExchangeInstrumentID")
            # v-RG2: trying the most plausible field names for OI in an
            # XTS-family response -- UNVERIFIED which of these (if any)
            # is correct. The diagnostic print above is what actually
            # resolves this once real data comes back.
            oi = (q.get("OpenInterest") or q.get("OI")
                  or q.get("Touchline", {}).get("OpenInterest")
                  or q.get("Touchline", {}).get("OI"))
            if eid is not None and oi is not None:
                result[eid] = float(oi)
        return result
    except Exception as e:
        print(f"[OC_FILTER_RMONEY OI EXCEPTION] {e}")
        return {}


def _capture_baseline(md_headers, strikes, expiry_code):
    """Fetch current OI for all 9 strikes x 2 sides, store as the new
    baseline (anchor/re-anchor moment -- intraday change is measured
    FROM this point forward)."""
    instruments = []
    eid_map = {}
    for strike in strikes:
        for side in ("CE", "PE"):
            symbol = f"NIFTY{expiry_code}{strike}{side}"
            eid = _resolve_eid_oc(md_headers, symbol)
            if eid is None:
                continue
            instruments.append({"exchangeSegment": NIFTY_FO_SEGMENT, "exchangeInstrumentID": eid})
            eid_map[eid] = (strike, side)

    if len(eid_map) != len(strikes) * 2:
        print(f"[OC_FILTER_RMONEY BASELINE ERROR] expected {len(strikes)*2} option contracts "
              f"(window=+/-{(len(strikes)-1)//2} strikes), resolved {len(eid_map)}")
        return {}, {}
    oi_by_eid = _fetch_oi_batch(md_headers, instruments)
    if len(oi_by_eid) != len(eid_map):
        print(f"[OC_FILTER_RMONEY BASELINE ERROR] OI coverage incomplete: got {len(oi_by_eid)}/{len(eid_map)}")
        return {}, {}
    baseline = {}
    for eid, (strike, side) in eid_map.items():
        baseline[(strike, side)] = oi_by_eid[eid]
    return baseline, eid_map


def _diag_fields(oi_by_eid, now_ts):
    """v-G81: extra snapshot fields for the bot's diagnostics only."""
    oi_by_strike = {}
    abs_oi = {"CE": 0.0, "PE": 0.0}
    for eid, (strike, side) in (_STATE.get("eid_map") or {}).items():
        if eid in oi_by_eid:
            oi_by_strike.setdefault(strike, {})[side] = oi_by_eid[eid]
            abs_oi[side] += oi_by_eid[eid]
    return {"anchor": _STATE.get("anchor"), "window_strikes": list(_STATE.get("strikes") or []),
            "oi_by_strike": oi_by_strike, "abs_ce_oi_window": abs_oi["CE"],
            "abs_pe_oi_window": abs_oi["PE"], "data_time": now_ts, "stale": False}


# v-E42 (vE6.6): 09:18 OI pre-snapshot (see compute_dpcr)
_V42_PRE = {}


def pre_snapshot(md_headers, spot, expiry_code, dpcr_window=None, bot_name="BOT_G"):
    """v-E42: at a 3-min boundary BEFORE today's first anchor, read the OI of the
    strikes round(spot) +/- (window + 1) and keep it. compute_dpcr() uses it as
    the first baseline when the 09:15 reference arrives before 09:21. Returns a
    log message when a reading was taken (or failed), else None."""
    now = datetime.now()
    today = now.date()
    if spot is None or now.minute % 3 != 0 or now.second > ANCHOR_BOUNDARY_MAX_SEC:
        return None
    if _STATE.get("date") == today and _STATE.get("anchor") is not None:
        return None
    key = f"{today.isoformat()} {now.hour:02d}:{now.minute:02d}"
    if _V42_PRE.get("key") == key:
        return None
    _V42_PRE.clear()
    _V42_PRE["key"] = key   # one attempt per boundary
    n = (WINDOW_STRIKES_EACH_SIDE if dpcr_window is None else int(dpcr_window)) + 1
    strikes = _build_strike_window(_round_strike(spot), n)
    instruments, eid_map = [], {}
    for strike in strikes:
        for side in ("CE", "PE"):
            eid = _resolve_eid_oc(md_headers, f"NIFTY{expiry_code}{strike}{side}")
            if eid is None:
                continue
            instruments.append({"exchangeSegment": NIFTY_FO_SEGMENT, "exchangeInstrumentID": eid})
            eid_map[eid] = (strike, side)
    if len(eid_map) != len(strikes) * 2:
        return f"PRE-SNAPSHOT | {bot_name} resolved {len(eid_map)}/{len(strikes) * 2} contracts -> not used (v-E42)"
    oi = _fetch_oi_batch(md_headers, instruments)
    if len(oi) != len(eid_map):
        return f"PRE-SNAPSHOT | {bot_name} OI {len(oi)}/{len(eid_map)} -> not used (v-E42)"
    _V42_PRE.update(date=today, t=now.strftime("%H:%M:%S"), spot=spot, oi={eid_map[e]: oi[e] for e in eid_map})
    msg = (f"PRE-SNAPSHOT | {bot_name} OI of strikes {strikes[0]}-{strikes[-1]} read at {now:%H:%M:%S} "
           f"(spot {spot}), kept as the first baseline while the 09:15 reference is awaited (v-E42)")
    _dpcr_file_log(msg, file=DPCR_SHIFT_LOG_FILE)
    return msg


def _v42_use_pre(bot_name):
    """v-E42: first anchor just set -> baseline = the pre-snapshot (if it covers the window)."""
    pre = _V42_PRE
    oi_by_eid = {}
    for eid, k in _STATE["eid_map"].items():
        if k not in pre["oi"]:
            _dpcr_file_log(f"PRE-SNAPSHOT | {bot_name} does not cover {k} -> baseline on the next 3-min "
                           f"boundary (old rule, v-E42)", file=DPCR_SHIFT_LOG_FILE)
            return None
        oi_by_eid[eid] = pre["oi"][k]
    _STATE["baseline_oi"] = {k: pre["oi"][k] for k in _STATE["eid_map"].values()}
    _STATE["baseline_pending"] = False
    _STATE["last_fetch_time"] = time.time()
    _STATE["_last_dpcr"] = None
    _STATE["last_dpcr_candle_key"] = pre["key"]
    snap = {"dpcr": None, "dpcr_smoothed": None, "net_pe_doi": 0.0, "net_ce_doi": 0.0, "bias": "UNDEFINED"}
    snap.update(_diag_fields(oi_by_eid, time.time()))
    _STATE["_last_snap"] = snap
    msg = (f"DPCR BASELINE | {bot_name} Anchor:{_STATE['anchor']} OI baseline = pre-snapshot read at "
           f"{pre['t']} (spot {pre['spot']}) (v-E42)")
    _dpcr_file_log(msg)
    _dpcr_file_log(msg, file=DPCR_SHIFT_LOG_FILE)
    return snap


def compute_dpcr(md_headers, spot, expiry_code, bot_name="BOT_G", gap_day=False, dpcr_window=None, anchor_ref=None):
    """
    v-RG2: RMoney/XTS-native DPCR computation. Mirrors the Fyers-side
    option_chain_filter_nifty.py's compute_dpcr() interface -- returns a
    snap dict with (at minimum) "dpcr", "net_pe_doi", "net_ce_doi".

    `md_headers` -- the bot file's own _md_headers() dict, passed in
    directly rather than this module managing its own session (avoids
    duplicate/possibly-stale token state -- same reasoning as passing
    the `fyers` client object on the Fyers side, adapted to RMoney's
    headers-based auth instead of a client object).

    `expiry_code` -- the bot file's own _bot_g_symbol_expiry_code()
    result, passed in rather than duplicated here (single source of
    truth for the month-end-week symbol-format fix, v-G29/v-RG1).

    Returns None if spot is unavailable, or a snap dict on success:
      snap["dpcr"]          -- raw ratio (net_pe_doi/net_ce_doi), for
                                the dashboard chart ONLY (v-G31 note in
                                the bot file) -- NOT used for any
                                trading decision.
      snap["net_pe_doi"]    -- cumulative PE OI change since anchor
      snap["net_ce_doi"]    -- cumulative CE OI change since anchor
      snap["dpcr_smoothed"] -- currently == dpcr (no separate smoothing
                                implemented yet, unlike the Fyers module
                                which the DPCR log shows has one --
                                UNVALIDATED gap, not yet needed since
                                nothing in the bot file reads this key).
    """
    if spot is None:
        return None

    today = datetime.now().date()
    now_hhmm = int(datetime.now().strftime("%H%M"))
    anchor_hhmm = 1000 if gap_day else 916
    # v-E27 (vE6.2.1): first anchor only on a 3-min boundary reading (same
    # reading as the baseline), identical rule to the Fyers module.
    _v27_now = datetime.now()
    _v39_ref = anchor_ref if (anchor_ref and not gap_day) else None   # v-E39 (vE6.4)
    _v27_ok = (not ANCHOR_ON_3M_BOUNDARY) or (_v27_now.minute % 3 == 0
                                               and _v27_now.second <= (ANCHOR_REF_GRACE_SEC if _v39_ref else ANCHOR_BOUNDARY_MAX_SEC))
    # v-E42 (vE6.6): a 09:18 pre-snapshot lets the first anchor be set as soon as the reference arrives (before 09:21)
    _v42 = _V42_PRE if (_v39_ref and _V42_PRE.get("date") == today and now_hhmm < 921) else None

    # ── Anchor management ──────────────────────────────────────────────
    need_new_anchor = False
    if _STATE["date"] != today:
        need_new_anchor = (now_hhmm >= anchor_hhmm) and (_v27_ok or _v42 is not None)   # v-E42
        if not need_new_anchor:
            return None   # v-E27: no anchor yet today (never serve yesterday's window)
    elif _STATE["anchor"] is None:
        need_new_anchor = (now_hhmm >= anchor_hhmm) and (_v27_ok or _v42 is not None)   # v-E42
    else:   # v-E7/v-E8: drift measured from the spot at anchor time
        _base = _STATE.get("anchor_spot") or _STATE["anchor"]
        _drift_pts = abs(spot - _base)
        if REANCHOR_MODE == "HALF_WINDOW":
            _w = (len(_STATE["strikes"]) - 1) // 2 if _STATE.get("strikes") else WINDOW_STRIKES_EACH_SIDE
            _limit_pts = _w * STRIKE_ROUND_UNIT * REANCHOR_HALF_WINDOW_FRACTION
            need_new_anchor = _drift_pts >= _limit_pts
        else:
            need_new_anchor = _drift_pts / _base * 100 >= REANCHOR_DRIFT_PCT

    if need_new_anchor:
        old_dpcr = None
        if _STATE["baseline_oi"] is not None and _STATE.get("_last_dpcr") is not None:
            old_dpcr = _STATE["_last_dpcr"]

        _v39_first = _v39_ref is not None and not (_STATE["anchor"] is not None and _STATE["date"] == today)
        _anchor_base = _v39_ref if _v39_first else spot   # v-E39: closed 09:15 candle close = anchor + drift base
        new_anchor = _round_strike(_anchor_base)
        window = dpcr_window if dpcr_window is not None else WINDOW_STRIKES_EACH_SIDE
        new_strikes = _build_strike_window(new_anchor, window)
        # v-G2A: anchor/window is established at the configured anchor time,
        # but the OI baseline is captured only on the next eligible 3-minute
        # DPCR candle boundary. This mirrors Fyers: anchor at 09:16, baseline
        # at 09:18, first usable delta/DPCR at 09:21.
        instruments_eid = {}
        for strike in new_strikes:
            for side in ("CE", "PE"):
                symbol = f"NIFTY{expiry_code}{strike}{side}"
                eid = _resolve_eid_oc(md_headers, symbol)
                if eid is None:
                    continue
                instruments_eid[eid] = (strike, side)
        if len(instruments_eid) != len(new_strikes) * 2:
            print(f"[OC_FILTER_RMONEY ANCHOR ERROR] expected {len(new_strikes)*2} option contracts "
                  f"(window=+/-{window} strikes), resolved {len(instruments_eid)}")
            return None

        was_reanchor = _STATE["anchor"] is not None and _STATE["date"] == today   # v-E27: new day = initial anchor
        _STATE["date"] = today
        _STATE["anchor"] = new_anchor
        _STATE["anchor_spot"] = _anchor_base   # v-E7, v-E39
        _STATE["v39_grace"] = _v39_first   # v-E39: baseline read may use the 45 s grace
        _STATE["strikes"] = new_strikes
        _STATE["baseline_oi"] = None
        _STATE["eid_map"] = instruments_eid
        _STATE["baseline_pending"] = True
        _STATE["last_fetch_time"] = 0
        _STATE["last_dpcr_candle_key"] = None

        if was_reanchor:
            _dpcr_file_log(f"WINDOW SHIFT | {bot_name} ATM -> {new_anchor}  "
                  f"DPCR before:{old_dpcr} Spot:{spot} (v-E7/E8 half-window rule)", file=DPCR_SHIFT_LOG_FILE)   # v-G79
        else:
            _dpcr_file_log(f"ANCHOR SET   | {bot_name} initial anchor "
                  f"({'10:00' if gap_day else '09:16'}) Anchor:{new_anchor} "
                  f"Spot:{_anchor_base} Window:±{(len(new_strikes)-1)//2} (v-G37/RG2)"
                  + (f" [vE6.4 common anchor: closed 09:15 candle close {_v39_ref}, live spot {spot}]" if _v39_first else ""),
                  file=DPCR_SHIFT_LOG_FILE)   # v-G79, v-E39
        if _v42 is not None and _v39_first and not was_reanchor:   # v-E42: baseline = the 09:18 pre-snapshot
            _v42_snap = _v42_use_pre(bot_name)
            if _v42_snap is not None:
                return _v42_snap

    if _STATE["anchor"] is None:
        return None   # before anchor time, no data yet -- same as Fyers' None-before-anchor contract

    # ── Exact 3-minute DPCR candle synchronization (v-G2A) ─────────────
    now = datetime.now()
    now_ts = time.time()
    _sync_max = ANCHOR_REF_GRACE_SEC if (_STATE.get("v39_grace") and _STATE.get("baseline_oi") is None) else 10   # v-E39
    if now.minute % 3 != 0 or now.second > _sync_max:
        return _stale_copy(_STATE.get("_last_snap"))   # v-G80: marked stale
    candle_key = f"{today.isoformat()} {now.hour:02d}:{now.minute:02d}"
    if _STATE.get("last_dpcr_candle_key") == candle_key:
        return _stale_copy(_STATE.get("_last_snap"))   # v-G80: marked stale
    _STATE["last_dpcr_candle_key"] = candle_key

    instruments = [{"exchangeSegment": NIFTY_FO_SEGMENT, "exchangeInstrumentID": eid}
                   for eid in _STATE["eid_map"]]
    oi_by_eid = _fetch_oi_batch(md_headers, instruments)
    if len(oi_by_eid) != len(_STATE["eid_map"]):
        print(f"[OC_FILTER_RMONEY OI ERROR] incomplete OI snapshot: got {len(oi_by_eid)}/{len(_STATE['eid_map'])}; DPCR unavailable")
        return None

    # First 3-minute snapshot after anchor = baseline only. Do not turn it
    # into an artificial zero-delta DPCR; keep the decision metric undefined
    # until the following DPCR candle, exactly like Fyers.
    if _STATE.get("baseline_oi") is None:
        baseline = {}
        for eid, (strike, side) in _STATE["eid_map"].items():
            baseline[(strike, side)] = oi_by_eid[eid]
        _STATE["baseline_oi"] = baseline
        _STATE["baseline_pending"] = False
        _STATE["last_fetch_time"] = time.time()
        _STATE["_last_dpcr"] = None
        snap = {
            "dpcr": None,
            "dpcr_smoothed": None,
            "net_pe_doi": 0.0,
            "net_ce_doi": 0.0,
            "bias": "UNDEFINED",
        }
        snap.update(_diag_fields(oi_by_eid, now_ts))   # v-G81
        _STATE["_last_snap"] = snap
        _dpcr_file_log(f"DPCR BASELINE | {bot_name} Anchor:{_STATE['anchor']} captured OI baseline at {candle_key} (v-G2A)")   # v-G79
        return snap

    net_ce = 0.0
    net_pe = 0.0
    for eid, (strike, side) in _STATE["eid_map"].items():
        current_oi = oi_by_eid[eid]
        delta = current_oi - _STATE["baseline_oi"].get((strike, side), 0.0)
        if side == "CE":
            net_ce += delta
        else:
            net_pe += delta

    dpcr = (net_pe / net_ce) if net_ce != 0 else None
    _STATE["_last_dpcr"] = dpcr
    _STATE["last_fetch_time"] = now_ts

    snap = {
        "dpcr": dpcr,
        "dpcr_smoothed": dpcr,   # v-RG2: no separate smoothing yet, see docstring
        "net_pe_doi": net_pe,
        "net_ce_doi": net_ce,
        "bias": "UNDEFINED",     # v-RG2: not computed here -- get_vix_regime()-
                                 # style bias labeling isn't used by BOT_G/BOT_G
                                 # (the bot file's own compute_signed_dpcr()
                                 # replaces this entirely), kept only for
                                 # snap-shape parity with the Fyers module.
    }
    snap.update(_diag_fields(oi_by_eid, now_ts))   # v-G81
    _STATE["_last_snap"] = snap

    _dpcr_file_log(f"DPCR SNAPSHOT | {bot_name} Spot:{spot} Anchor:{_STATE['anchor']} "
          f"Window:{len(_STATE['strikes'])}strikes (±{(len(_STATE['strikes'])-1)//2}) IntradayNetCEdOI:{net_ce:.0f} "
          f"IntradayNetPEdOI:{net_pe:.0f} DPCR:{dpcr} (v-RG2, RMoney-native, "
          f"OI field=OpenInterest; full {len(_STATE['strikes'])*2}-contract coverage required)")

    return snap
