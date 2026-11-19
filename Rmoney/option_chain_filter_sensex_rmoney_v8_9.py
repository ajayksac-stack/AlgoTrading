"""
option_chain_filter_sensex_rmoney_v8_9.py -- BUILT FROM option_chain_filter_nifty_rmoney_vE5.py (the
Nifty RMoney module the vE6.2 bot imports as ..._vE6). Differences, all marked "v8 Sensex":
  * BSEFO segment 12, strike step 100, option symbols SENSEX<code><strike><CE|PE>,
    log files *_sensex_rmoney_v8_9.txt;
  * _resolve_eid_oc: Nifty exact-match rule first, then the BSEFO display-text rule that resolved
    every Sensex contract in the 15/16-Oct RMoney logs; ambiguity fails closed;
  * _fetch_oi_batch parser: Sensex v7's (also reads the BSE partial format "t:12_<eid>,o:<oi>");
  * compute_dpcr(..., reanchor_pts=None): optional weekday floor for the re-anchor distance.
Everything else (anchor/baseline/3-minute gating, stale copies, diag fields) is Nifty's code.
NOTE: the Nifty vE6 RMoney OC module itself was not uploaded; if it differs from vE5, port that diff here.
"""
# =============================================================================
#  option_chain_filter_nifty_rmoney_vE5.py -- copy of the RMoney/XTS
#  option_chain_filter_nifty.py for the v3 Nifty g_pool bot ONLY (v-G79,
#  30-Sep-2026). Original file untouched, v1/v2 bots unaffected.
#  v3 changes (LOG/DIAGNOSTIC ONLY -- DPCR computed exactly as before):
#    * DPCR lines now ALSO written to dpcr_log_nifty_rmoney_vE5.txt /
#      dpcr_window_shift_nifty_rmoney_vE5.txt (before: console only, so
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
SENSEX_FO_SEGMENT = 12   # v8 Sensex: BSEFO (Nifty: SENSEX_FO_SEGMENT = 2 / NSEFO)

STRIKE_ROUND_UNIT     = 100   # v8 Sensex strike spacing (Nifty: 50)
WINDOW_STRIKES_EACH_SIDE = 4     # ATM +/- 4 = 9 strikes total, matches Fyers
REANCHOR_DRIFT_PCT    = 0.75     # re-anchor if spot moves this % from anchor (REANCHOR_MODE='PCT' only)
# v-E7/v-E8 (vE5): re-anchor when spot has moved HALF the DPCR window's width
# from the SPOT at the last anchor (was: % from the anchor STRIKE) -- same
# rule as the Fyers module. 'PCT' restores the old percentage rule (from spot).
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

DPCR_LOG_FILE       = "dpcr_log_sensex_rmoney_v8_9.txt"            # v-G79
DPCR_SHIFT_LOG_FILE = "dpcr_window_shift_sensex_rmoney_v8_9.txt"   # v-G79


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
                eid = _resolve_eid_oc(md_headers, f"SENSEX{expiry_code}{strike}{side}")
                if eid is None:
                    continue
                instruments.append({"exchangeSegment": SENSEX_FO_SEGMENT, "exchangeInstrumentID": eid})
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
    """v8 Sensex: resolve the exact requested BSEFO option contract.
    1) Nifty rule: exactly one search result whose name field equals the symbol -> use it.
    2) Sensex v7 rule (proven in the 15/16-Oct RMoney logs): among BSEFO results, the contract whose
       display text contains the symbol (or whose Name equals it). Only BSEFO (segment 12) rows are
       ever considered. Ambiguity (two different EIDs) fails closed."""
    if symbol in _EID_CACHE_OC:
        return _EID_CACHE_OC[symbol]
    try:
        resp = _HTTP.get(f"{MARKETDATA_URL}/search/instruments",
                          headers=md_headers, params={"searchString": symbol}, timeout=5)
        if resp.status_code != 200:
            print(f"[OC_FILTER_RMONEY EID ERROR] HTTP {resp.status_code} for {symbol}")
            return None
        data = resp.json()
        if data.get("type") != "success":
            return None
        items = data.get("result", [])
        if not isinstance(items, list) or not items:
            return None
        fo = [it for it in items if it.get("ExchangeSegment") == SENSEX_FO_SEGMENT
              and (it.get("ExchangeInstrumentID") or it.get("exchangeInstrumentID")) is not None]
        target = symbol.replace("BSE:", "")
        exact, contain = set(), set()
        for item in fo:
            eid = int(item.get("ExchangeInstrumentID") or item.get("exchangeInstrumentID"))
            names = [str(item.get(k, "")) for k in
                     ("TradingSymbol", "Name", "DisplayName", "Description", "Symbol")]
            if any(v.upper() == target.upper() for v in names if v):
                exact.add(eid)
            disp = str(item.get("DisplayName") or item.get("Description") or item.get("Name") or "")
            if target in disp or str(item.get("Name", "")) == target:
                contain.add(eid)
        for pick in (exact, contain):
            if len(pick) == 1:
                eid = next(iter(pick))
                _EID_CACHE_OC[symbol] = eid
                return eid
            if len(pick) > 1:
                print(f"[OC_FILTER_RMONEY EID ERROR] ambiguous BSEFO match for {symbol}: {sorted(pick)}")
                return None
        if len(items) == 1 and len(fo) == 1:   # Sensex v7 fallback: a single FO result
            eid = int(fo[0].get("ExchangeInstrumentID") or fo[0].get("exchangeInstrumentID"))
            _EID_CACHE_OC[symbol] = eid
            return eid
        print(f"[OC_FILTER_RMONEY EID ERROR] contract not resolved: {symbol}; results={items}")
        return None
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
            json={"instruments": instruments, "xtsMessageCode": 1510, "publishFormat": "JSON"},   # v8 Sensex: same call, BSEFO instruments
            timeout=5)
        print(f"[OC_FILTER_RMONEY OI DIAG] xtsMessageCode=1510 raw response: "
              f"status={resp.status_code} body={resp.text[:800]}")
        if resp.status_code != 200:
            return {}
        data = resp.json()
        if data.get("type") != "success":
            return {}
        result = {}
        payload = data.get("result", {}) or {}
        items = payload.get("listQuotes", [])
        if isinstance(items, dict):
            items = [items]
        elif isinstance(items, str):
            # Some XTS/RMoney deployments return the JSON list/object as a
            # string even when publishFormat=JSON.
            try:
                parsed = json.loads(items)
                items = parsed if isinstance(parsed, list) else [parsed]
            except Exception:
                items = [items]
        elif not isinstance(items, list):
            items = []

        def _extract_oi(q):
            if not isinstance(q, dict):
                return None
            for key in ("OpenInterest", "openInterest", "OI", "oi"):
                if q.get(key) is not None:
                    return q.get(key)
            # Be tolerant of an OI packet nested under a standard quote
            # wrapper.
            for key in ("Touchline", "touchline", "OpenInterestData", "openInterestData"):
                nested = q.get(key)
                if isinstance(nested, dict):
                    value = _extract_oi(nested)
                    if value is not None:
                        return value
            return None

        for item in items:
            q = item
            if isinstance(q, str):
                try:
                    q = json.loads(q)
                except Exception:
                    # XTS partial 1510 format: t:12_<eid>,o:<open_interest>
                    fields = {}
                    for part in q.split(","):
                        if ":" in part:
                            k, v = part.split(":", 1)
                            fields[k.strip()] = v.strip()
                    token = fields.get("t", "")
                    oi_value = fields.get("o")
                    if token and oi_value is not None and "_" in token:
                        try:
                            eid = int(token.rsplit("_", 1)[1])
                            result[eid] = float(oi_value)
                        except (TypeError, ValueError):
                            pass
                    continue
            if not isinstance(q, dict):
                continue
            eid = q.get("ExchangeInstrumentID") or q.get("exchangeInstrumentID")
            oi = _extract_oi(q)
            if eid is not None and oi is not None:
                try:
                    result[int(eid)] = float(oi)
                except (TypeError, ValueError):
                    continue

        if not result:
            print("[OC_FILTER_RMONEY OI DIAG] 1510 response parsed but no OI values extracted")
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
            symbol = f"SENSEX{expiry_code}{strike}{side}"
            eid = _resolve_eid_oc(md_headers, symbol)
            if eid is None:
                continue
            instruments.append({"exchangeSegment": SENSEX_FO_SEGMENT, "exchangeInstrumentID": eid})
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


def compute_dpcr(md_headers, spot, expiry_code, bot_name="BOT_G", gap_day=False, dpcr_window=None, reanchor_pts=None, anchor_ref=None):   # v8 Sensex: reanchor_pts; v8.3.3: anchor_ref
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

    # ── Anchor management ──────────────────────────────────────────────
    need_new_anchor = False
    if _STATE["date"] != today:
        need_new_anchor = (now_hhmm >= anchor_hhmm)
    elif _STATE["anchor"] is None:
        need_new_anchor = (now_hhmm >= anchor_hhmm)
    else:   # v-E7/v-E8: drift measured from the spot at anchor time
        _base = _STATE.get("anchor_spot") or _STATE["anchor"]
        _drift_pts = abs(spot - _base)
        if REANCHOR_MODE == "HALF_WINDOW":
            _w = (len(_STATE["strikes"]) - 1) // 2 if _STATE.get("strikes") else WINDOW_STRIKES_EACH_SIDE
            _limit_pts = (reanchor_pts if reanchor_pts is not None   # v8 Sensex: weekday floor supplied by the bot
                          else _w * STRIKE_ROUND_UNIT * REANCHOR_HALF_WINDOW_FRACTION)
            need_new_anchor = _drift_pts >= _limit_pts
        else:
            need_new_anchor = _drift_pts / _base * 100 >= REANCHOR_DRIFT_PCT

    if need_new_anchor:
        old_dpcr = None
        if _STATE["baseline_oi"] is not None and _STATE.get("_last_dpcr") is not None:
            old_dpcr = _STATE["_last_dpcr"]

        # v8.3.3: first anchor of the day on a normal day + a reference (closed 09:15 3m candle close, same on both brokers)
        # -> anchor AND drift base come from it
        _first = (_STATE["anchor"] is None) or (_STATE["date"] != today)
        _use_ref = bool(anchor_ref) and (not gap_day) and _first
        _base_spot = anchor_ref if _use_ref else spot
        new_anchor = _round_strike(_base_spot)
        window = dpcr_window if dpcr_window is not None else WINDOW_STRIKES_EACH_SIDE
        new_strikes = _build_strike_window(new_anchor, window)
        # v-G2A: anchor/window is established at the configured anchor time,
        # but the OI baseline is captured only on the next eligible 3-minute
        # DPCR candle boundary. This mirrors Fyers: anchor at 09:16, baseline
        # at 09:18, first usable delta/DPCR at 09:21.
        instruments_eid = {}
        for strike in new_strikes:
            for side in ("CE", "PE"):
                symbol = f"SENSEX{expiry_code}{strike}{side}"
                eid = _resolve_eid_oc(md_headers, symbol)
                if eid is None:
                    continue
                instruments_eid[eid] = (strike, side)
        if len(instruments_eid) != len(new_strikes) * 2:
            print(f"[OC_FILTER_RMONEY ANCHOR ERROR] expected {len(new_strikes)*2} option contracts "
                  f"(window=+/-{window} strikes), resolved {len(instruments_eid)}")
            return None

        was_reanchor = _STATE["anchor"] is not None
        _STATE["date"] = today
        _STATE["anchor"] = new_anchor
        _STATE["anchor_spot"] = _base_spot   # v-E7 / v8.3.3
        _STATE["sync_grace"] = bool(_use_ref)   # v8.3.3: first-anchor baseline may be taken up to 45 s into the 3-min boundary minute
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
                  f"Spot:{_base_spot} Window:±{(len(new_strikes)-1)//2} (v-G37/RG2)"
                  + (f" [v8.3.3 common anchor: closed 09:15 candle close {anchor_ref}, live spot {spot}]" if _use_ref else ""),
                  file=DPCR_SHIFT_LOG_FILE)   # v-G79

    if _STATE["anchor"] is None:
        return None   # before anchor time, no data yet -- same as Fyers' None-before-anchor contract

    # ── Exact 3-minute DPCR candle synchronization (v-G2A) ─────────────
    now = datetime.now()
    now_ts = time.time()
    if now.minute % 3 != 0 or now.second > (45 if (_STATE.get("sync_grace") and _STATE.get("baseline_oi") is None) else 10):   # v8.3.3
        return _stale_copy(_STATE.get("_last_snap"))   # v-G80: marked stale
    candle_key = f"{today.isoformat()} {now.hour:02d}:{now.minute:02d}"
    if _STATE.get("last_dpcr_candle_key") == candle_key:
        return _stale_copy(_STATE.get("_last_snap"))   # v-G80: marked stale
    _STATE["last_dpcr_candle_key"] = candle_key

    instruments = [{"exchangeSegment": SENSEX_FO_SEGMENT, "exchangeInstrumentID": eid}
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
