# =============================================================================
#  NIFTY WEEKLY OPTIONS BOT -- BOT_G, MULTI-STRIKE POOL (DPCR + Option-VWAP)
#  Broker  : RMoney/XTS
#  Updated : 2026-11-18 (vE6.14 v-E54 end-of-day cleanup; vE6.13 v-E52 ATM-OTM2 pool, v-E53 VIX gate; vE6.12 v-E51 exit bid/ask log-only; vE6.11 v-E49 BOT_G 10-min setup candle, v-E50 3m ST filter; vE6.10 v-E48 CE call-add skip log-only; vE6.9 v-E46 shadow lock, v-E47 option tape; vE6.8 v-E45 entry context line; vE6.7 v-E44 ZLM zero line = 09:15 3m close; vE6.6 v-E42 RMoney 09:18 OI pre-snapshot, v-E43 ZLM check at entry; vE6.5 v-E40 min-stop what-if, v-E41 upload zip / fewer files; vE6.4 v-E39 common first DPCR anchor; vE6.3 v-E36 exit what-if, v-E37 brokerage; vE6.2.4 log-only v-E33..v-E35; vE6.2.3 log-only v-E31 ZLM shadow, v-E32 day open; vE6.2.2 hotfix v-E28..v-E30; vE6.2.1 hotfix v-E23..v-E27; vE6.2: rollover fix + log-only trackers, day type, DATA_LOST, live-vs-paper; v-E18..v-E22)
#
#  v3 (30-Sep-2026) -- LOGGING/DIAGNOSTIC BUILD ONLY. Renamed from the v2
#  files so v2 data stays clean. NOTHING in entry / exit / SL / BE / P1 /
#  P2 / TSL / VWAP / DPCR lock / veto logic changed (verified by diff).
#  v-G79  Names: BOT_rmoney_nifty_g_pool_v3.py + config_rmoney_nifty_g_pool_v3.py,
#         output files <kind>_nifty_g_pool_v3_<series>_rmoney.*, and a
#         broker-specific DPCR module copy option_chain_filter_nifty_rmoney_v3.py
#         (DPCR logs dpcr_log_nifty_rmoney_v3.txt). Old module untouched.
#  v-G80  Flow-history fixes: anchor read from "anchor"/"anchor_strike"
#         (v2 looked only for "anchor"); snapshots the module marks
#         "stale" (RMoney: re-served previous candle) are not recorded.
#  v-G81  New "BOT_G OI DIAG" + "BOT_G ATM DIAG" lines every DPCR snapshot:
#         window absolute CE/PE OI + absolute-OI PCR (context only), 9-min
#         flow per minute (raw and % of window OI), driver label
#         (PUT_ADD/PUT_UNWIND/PUT_FLAT + CALL_ADD/CALL_UNWIND/CALL_FLAT),
#         tiers, ATM strike + anchor strike CE/PE OI and LTP with SAME/
#         CHANGED/NEW status, change vs previous snapshot, ATM premium
#         residual (dLTP -/+ BOTG_ATM_DELTA_APPROX x dSpot) and an
#         OI+residual reading (WRITING / BUYING / SHORT_COVERING /
#         LONG_UNWINDING / ...). Raw inputs logged so everything can be
#         recomputed later. Source: DPCR option chain = NEAREST weekly
#         expiry (on Mon/Tue that is not the contract BOT_G trades).
#  vE6.14 (18-Nov-2026) -- same file names. Housekeeping only (no trading-logic change).
#  v-E54 END-OF-DAY CLEANUP: after the normal 15:10 shutdown the upload zip is written,
#        re-opened and verified; only then the bot deletes its own daily output files.
#        Kept: .py, configs, token files, upload_*.zip (never deleted). Mid-day stops
#        (Ctrl+C / crash / dashboard KILL) delete nothing, so a restart still restores.
#        Config: V54_EOD_CLEANUP (True/False).
#  vE6.13 (15-Nov-2026) -- same file names. PAPER-ONLY FORWARD TEST BUILD.
#  v-E52 strike pool ATM/OTM1/OTM2 at every VIX level (config BOTG_STRIKE_POOL_MID/HIGH).
#  v-E53 VIX GATE: VIX at the 10:15 OPEN lock <= BOTG_VIX_GATE_MAX (13.0) -> no new BOT_G
#        entries that day ("VIX GATE" log). Decided once per day, survives restart.
#  Backtest basis (realistic costs, 4 lots): 2025 -20.6k -> +15.6k, 2026 +35.4k -> +31.7k.
#  Frozen for the forward paper test -- see nifty-forward-test-vE6.13.md. Do not tune.
#  vE6.12 (10-Nov-2026) -- same file names. LOG-ONLY, no trading change.
#  v-E51 EXIT QUOTE: at every BOT_G exit leg (PARTIAL / FINAL) the bot fetches the
#        live bid/ask and logs "EXIT QUOTE" + a row in exit_quotes_nifty_<broker>.csv
#        (paper exit price vs bid = what a real SELL would get). Added to the upload
#        zip. Switch V51_EXIT_QUOTES. Purpose: measure real exit costs (the 10-month
#        backtest showed vE6.11 breaks even at ~Rs0.38/unit of exit cost).
#  vE6.11 (09-Nov-2026) -- same file names. Backtest-led (205 days Jan-Oct 2026):
#  v-E49 BOT_G option setup candle = BOTG_OPT_TF_MIN (10) minutes: rejection,
#        next-candle confirmation and option VWAP all on 10-min bars. BOT_GE
#        keeps 5-min. BOTG_OPT_TF_MIN = 5 restores the old behaviour exactly.
#  v-E50 BOT_G entry only WITH the 3-min spot Supertrend(10,3) (last CLOSED
#        3-min candle, from the bot's own df3): CE needs ST up, PE needs ST
#        down, else "ST SKIP". Not enough bars / error -> entry allowed.
#  Config: BOTGE_ENABLED = False; BOTG_CE_CALLADD_SKIP_LOGONLY = False.
#  Backtest: -34.9k -> +26.4k net @4 lots (H1 +23.5k / H2 +2.9k), max DD 21.3k.
#  vE6.10 (06-Nov-2026) -- same file names. ONE trading change:
#  v-E48 CE call-add skip (v-E15) is now LOG-ONLY (BOTG_CE_CALLADD_SKIP_LOGONLY
#        = True): when 9m carried dCE > 500,000 the bot logs
#        "CE SKIP WOULD-HAVE (log-only)" and TAKES the entry. Reason: SKIP
#        tracker 26-Oct..6-Nov: 12 blocked setups went to P1 first, 7 to SL
#        first (missed winners on up-trend days 29/30-Oct, 3/6-Nov). The
#        entry row keeps ce_skip_check = "WOULD_SKIP" so the result can be
#        compared later. Set the switch False to restore the real skip.
#  vE6.9 (04-Nov-2026) -- same file names. LOG-ONLY additions (trading unchanged).
#  v-E46 SHADOW LOCK (Anu's zone +/-0.10 + DPCR/spot sync idea): every 3-min
#        candle the bot also computes the side lock it WOULD have with a
#        +/-V46_ZONE no-trade zone, accepting a lock/flip only when the Nifty
#        spot 30-min change agrees by >= V46_SYNC_PTS (CE up / PE down), from
#        the normal trade start. "SHADOW LOCK |" line per candle (DIFFERS when
#        it is not the real lock). ENTRY CONTEXT also shows the shadow lock and
#        the entry-gate verdict (SKIP when spot is >= 20 pts against in 15 min
#        AND against over 30 min). Study: nifty-zone010-sync-study.md.
#  v-E47 OPTION TAPE: every 3-min candle the CE+PE strikes ATM +/-V47_STEPS are
#        noted; at shutdown their 1-min OHLCV for the day is fetched from the
#        broker and written to option_tape_YYYYMMDD_<broker>.csv (added to the
#        upload zip) -- replaces the evening Zerodha downloads for replays.
#        Switches V46_SHADOW_LOCK, V47_OPTION_TAPE.
#  vE6.8 (02-Nov-2026) -- same file names. LOG-ONLY addition.
#  v-E45 ENTRY CONTEXT: one line per BOT_G/BOT_GE entry with the four
#        candidate filters side by side -- signed DPCR, ZLM state + verdict,
#        Nifty spot change over the last 15 / 30 min (WITH / FLAT / AGAINST the
#        trade side, +/- V45_SPOT_AGAINST_PTS), OI flow tier -- and a warning
#        count (ZLM not agreeing, spot against, tier not MOST). Why: 2-Nov
#        review (23-Oct..2-Nov, 39 trades): ZLM not agreeing 4/4 lost; spot
#        >= 20 pts against in 15 min 9 trades -9.3k (2 wins); tier below MOST
#        20 trades -19.7k (4 wins). Filters may overlap -> collect 2-3 weeks
#        before any rule. Switch V45_ENTRY_CONTEXT.
#  vE6.7 (02-Nov-2026) -- same file names. LOG-ONLY change.
#  v-E44 ZLM ZERO LINE from the exchange candle: the ZLM reference is now the
#        CLOSED 09:15 3-min candle close (same number as the DPCR common anchor
#        reference, identical on both brokers) instead of the average of the
#        bot's own spot polls 09:15-09:19 -- those start only when the bot's
#        loop starts (~09:16, so 09:15 is missed) and differ per broker
#        (2-Nov: 23,258.9 Fyers n=33 vs 23,264.7 RMoney n=27; candle close
#        23,248.1). The old average is still logged next to it for comparison.
#        If the candle is not there by 09:25 -> old average (logged). Affects
#        only the ZLM shadow and the v-E43 ZLM check. Switch ZLM_REF_MODE.
#  vE6.6 (02-Nov-2026) -- same file names.
#  v-E43 ZLM CHECK AT ENTRY (log-only, both brokers): each BOT_G/BOT_GE entry
#        logs "ZLM CHECK | entry <side> | ZLM state <CE/PE/-> -> AGREE /
#        NEUTRAL / AGAINST" and adds "zlm <state> <verdict>" to the ENTRY
#        setup-tag detail. Why: 23-Oct..2-Nov all 4 entries without ZLM
#        agreement lost (-6.4k); too few to enforce. Switch V43_ZLM_TAG.
#  v-E42 (RMoney) 09:18 OI PRE-SNAPSHOT: RMoney's 3-min history brings the
#        closed 09:15 candle about 1 min late (09:19:03 on 30-Oct and 2-Nov),
#        so its first anchor + OI baseline fell to 09:21 while Fyers used
#        09:18; the missing 09:18-09:21 OI change stayed in the carried DPCR
#        all day (2-Nov: RMoney DPCR +0.04..+0.09 higher -> CE lock 10:18 vs
#        10:36). Now, while waiting for the reference at the 09:18 boundary,
#        RMoney reads the OI of the strikes around the live spot (DPCR window
#        + 1 each side); when the reference arrives (before 09:21) the anchor
#        is set at once and that 09:18 reading is its baseline -- first DPCR
#        at 09:21, same as Fyers. Not covered / no snapshot -> old rule.
#        Switch V42_RMONEY_PRE_SNAPSHOT. DPCR formula/thresholds unchanged.
#  vE6.5 (31-Oct-2026) -- same file names. LOG / FILE changes only; entry, exit, stop and size rules unchanged.
#  v-E40 MIN-STOP WHAT-IF (log-only, exit_whatif_nifty_vE6.py): two more plans
#        next to BASE/EB/TS/EBTS -- MS4 / MS5 = the same ladder with the initial
#        stop at least 4 / 5 points below entry (WHATIF_MS_PTS). After a real
#        stop-out the MS plans keep running on the 30-min post-exit tracker
#        prices until their own stop/targets/trail resolve. New log lines
#        "WHATIF MIN-STOP |", new CSV columns (old vE6.3 CSV is kept aside as
#        exit_whatif_..._old_<time>.csv). WHATIF START flags "LOW STOP" when
#        R < WHATIF_LOW_STOP_PTS (4). Why: 30-Oct 23200CE stops of 3.2-3.4 pts;
#        October study of 8 such trades was too small to decide.
#  v-E41 FEWER FILES: at shutdown each bot writes upload_YYYYMMDD_<broker>.zip
#        (bot_log + rotations, trades, livecmp, trade_paths, exit_whatif,
#        setup_tags, dpcr_window_shift, post_exit_summary) -- upload that one zip.
#        Switched off: summary_*.csv (same as livecmp + the log summary block),
#        post_exit_paths_*.csv (post_exit_summary kept), zlm_shadow_*.csv (same
#        lines in the log). Switches: V40_DAILY_ZIP, V40_WRITE_SUMMARY_CSV,
#        V40_WRITE_POST_EXIT_PATHS, ZLM_WRITE_CSV.
#  vE6.4 (29-Oct-2026) -- same file names. ONE behaviour change (DPCR start), trading rules unchanged.
#  v-E39 COMMON FIRST DPCR ANCHOR (Sensex v8.3.3 rule): on normal days the first
#        anchor comes from the CLOSED 09:15 3-min candle's close (read from
#        09:18), on both brokers, instead of each broker's own live 09:16-09:18
#        reading -- the live readings straddled a rounding midpoint on 16, 19,
#        23, 28, 29-Oct (29-Oct: 22,725.75 vs 22,723.55 -> anchors 22,750 /
#        22,700 -> RMoney took an early-slot trade Fyers did not). That close is
#        also the drift base for the first half-window re-anchor; later
#        re-anchors, gap days (10:00 live spot) and every threshold unchanged.
#        The DPCR fetch waits (no 3-min bucket used) until the reference exists,
#        gives up at 09:20 (live spot, logged); a restart after 09:30 anchors
#        on the live spot. The first-anchor/baseline read may be up to 45 s
#        into the 09:18 minute (ANCHOR_REF_GRACE_SEC). Switch: V39_COMMON_ANCHOR.
#  vE6.3 (28-Oct-2026) -- same file names. Entry/exit RULES unchanged.
#  v-E36 EXIT WHAT-IF (log-only): new shared file exit_whatif_nifty_vE6.py. Every
#        BOT_G/BOT_GE trade's live LTPs are replayed through 4 exit plans --
#        BASE (replica of the current ladder), EB (early bank: 1 lot at +0.6R),
#        TS (time stop: out if not +0.3R within 5 min), EBTS (both) -- and the
#        result is logged ("WHATIF |" line at each close) and written to
#        exit_whatif_nifty_g_pool_vE6_<broker>.csv. No orders, no change to the
#        real stop/targets/qty. Switch: WHATIF_ENABLED. Week of logging first;
#        switching EB/TS ON for real trades is a separate small build.
#  v-E37 charge estimate uses the real brokerage per order (config CHG_BROKERAGE_PER_ORDER).
#  vE6.2.4 (26-Oct-2026) -- LOG-ONLY additions, same file names. No trading rule changed.
#  v-E33 ZLM shadow reacts to a lock change inside the same minute (26-Oct Fyers
#        entered at 10:16 instead of 10:15 because the lock came 1 s after the check).
#  v-E34 (Fyers) pre-open gate until 09:15:00 (was 09:14:30): removes the harmless
#        "[DATA FETCH ERROR] Last 3m candle ... old" lines before the first candle.
#  v-E35 SETUP TAGS (Sensex v8.3 parity): new shared file setup_tags_nifty_vE6.py and
#        CSV setup_tags_nifty_g_pool_vE6_<broker>.csv -- one row per ARM / ARM_EXPIRED /
#        ARM_DROPPED / ENTRY_ABORT / CE_SKIP / ENTRY with gap, ext_1015, stop pts/%,
#        5-8 % cap distances, lots under 3 rupee-risk budgets, would-skip flags for
#        11:30/12:00/13:00 starts and the big-morning (|gap| or |ext_1015| >= 0.5/0.75 %)
#        rules. ext_1015 = % move from the day open to the first reading at/after 10:15,
#        captured once a day in _day_track. Hooks are wrapped; no state/order change.
#        Off switch: TAG_SETUP_ENABLED = False.
#  vE6.2.3 (22-Oct-2026) -- LOG-ONLY additions, same file names. No trading rule changed.
#  v-E31 ZLM (Zero-Line Momentum) SHADOW: new shared file zlm_shadow_nifty_vE6.py.
#        Nifty vs its 09:15-09:19 opening level + time-decay band, on BOT_G's
#        DPCR locked side; would-be entries/exits logged with REAL ATM
#        100-strike LTPs ("ZLM ..." / "ZLM-G ..." lines) + zlm_shadow_YYYYMMDD_<broker>.csv.
#        Places NO orders, never changes BOT_G/BOT_GE state; any error -> log line only.
#        Off switch: ZLM_SHADOW_ENABLED = False in the config.
#  v-E32 Day open (v-E20 day type, log/CSV only) = today's 09:15 3-min candle
#        open on both brokers (was the first spot reading: 22-Oct Fyers
#        22657.75 @09:15:02 vs RMoney 22590.3 @09:16).
#  vE6.2.2 (21-Oct-2026) -- hotfix, same file names. No strategy rule changed.
#  v-E28 (RMoney) _prev_trading_day() now skips NSE_TRADING_HOLIDAYS. 21-Oct
#        (after the 20-Oct holiday) the spot history started on the holiday,
#        returned only today's candles ("only N ticks") and the bot had no
#        data until 09:24 -> late DPCR anchor (09:24, 23,100 vs Fyers 09:18,
#        23,050), gap check undetermined, wrong day open.
#  v-E29 (Fyers) spot 3m history lookback = calendar days back to the
#        previous NSE trading day + 1 (min 2). Normal Tue-Fri = 2 (unchanged);
#        Monday = 4, day after a holiday = 3. Before, Monday's 2-day lookback
#        covered only Sat/Sun -> gap check "Insufficient history" (19-Oct).
#  v-E30 Gap check: while undetermined it is re-tried every 3 min until
#        BOTG_GAP_RECHECK_UNTIL_HHMM (09:30) instead of staying NORMAL all day.
#  vE6.2.1 (20-Oct-2026) -- hotfix, same file names. No entry/exit rule changed.
#  v-E23 Stop-type exits (SL / BREAKEVEN / TSL / BROKER_SL_FILLED): the exit
#        signal price is the STOP LEVEL, so exit slippage = fill - stop (was
#        always 0 because signal = fill). 19-Oct Fyers: ~Rs465 hidden.
#  v-E24 Paper stop fills identical on both brokers: booked at the polled
#        trigger LTP (RMoney G4.1 stop-level fill switched OFF). The stop
#        level is still in the row (exit_signal_price / leg_signal_price).
#  v-E25 Fyers pre-open gate: no data calls before 09:14:30 (19-Oct: 550
#        failed calls 08:17-09:15). One PRE-OPEN line per 10 min. RMoney
#        already waits until 09:16 (G4.4). Never gates with an open trade.
#  v-E26 Startup expiry lines describe the v-E18 trading-day rollover.
#  v-E27 (DPCR module) first anchor of the day only on a 3-min DPCR boundary
#        reading (same reading as the baseline) on BOTH brokers. 19-Oct:
#        RMoney anchored 09:16 (23,100), Fyers 09:18 (23,150) on identical
#        OI -> RMoney DPCR ~0.3 weaker all day, paused 10:30-11:39.
#  vE6.2 (17-Oct-2026) -- same file names as vE6 (vE6.1 was never built).
#  v-E18 ROLLOVER FIX (rule change): roll to the next expiry when <= 1 NSE
#        TRADING day is left to the actual (holiday-adjusted) expiry. Before,
#        it counted calendar days to the nominal Tuesday, so a Friday before a
#        holiday-shifted Monday expiry (16-Oct, 6-Nov, 20-Nov-2026) traded the
#        1-day-left contract. Normal Tuesday weeks unchanged (Mon/Tue roll).
#  v-E19 TRACKERS (log-only): after every final exit, and after every CE
#        skip, the option keeps being polled for 30 min -> post_exit_paths_*.csv
#        (price path) + post_exit_summary_*.csv (max/min, 5/15/30-min prices;
#        for skips: would-have outcome P1_FIRST / SL_FIRST / NEITHER).
#  v-E20 DAY TYPE (log-only): day open/high/low, % from open, position in
#        range, 30-min spot change, TREND_UP / TREND_DOWN / RANGE at every
#        entry (trade CSV) and skip.
#  v-E21 DATA LOST: data stale >= 5 min with an open trade -> PAPER: trade
#        closed at the last known LTP, reason DATA_LOST (so it is in the CSV);
#        LIVE: no exit is sent (broker SL protects) -- log + Telegram alert.
#  v-E22 LIVE vs PAPER (Option A, log-only): every trade row also carries the
#        signal price, ask/bid at signal, entry slippage, order latency, each
#        leg's signal price + slippage, estimated charges, net P&L and the
#        signal-price ("paper") P&L. Daily LIVE-vs-PAPER block at shutdown
#        -> livecmp_*.csv. Charges use config CHG_* rates (VERIFY vs contract
#        note). In PAPER mode fills = signal prices, so slippage is 0 and the
#        logged spread shows what a real fill would have cost.
#  vE6 (15-Oct-2026) -- CE CALL-ADD SKIP + STOP BAND. Renamed to
#  BOT_rmoney_nifty_g_pool_vE6.py / config_rmoney_nifty_g_pool_vE6.py /
#  option_chain_filter_nifty_rmoney_vE6.py; outputs *_nifty_g_pool_vE6_*.
#  Agreed 15-Oct (replay of 42 BOT_G trades 6-14 Oct: -Rs5,189 -> +Rs14,758):
#  v-E14 CARRIED FLOW: OI flow measured on the carried totals (window deltas
#        + B' carry), kept in a SEPARATE history that never resets at a
#        re-anchor (resets daily). _BOTG_FLOW_HISTORY and BOT_GE's flow
#        tiers are untouched.
#  v-E15 MAIN-SLOT CE SKIP: BOT_G (10:15 slot) skips a CE entry when the
#        9-min carried flow shows calls being added (dCE > 500,000).
#        Flow NA -> entry allowed, logged "flow NA". BOT_GE (early slot)
#        and PE entries are not affected.
#  v-E16 STOP BAND (BOT_G + BOT_GE, CE + PE): chart stop -> distance held to
#        3%..6% of entry premium -> separate hard limit (points) -> tick
#        rounding -> THEN R, BE, TSL arm, P1/P2 from the adjusted stop.
#        Logged STOP CAPPED / STOP WIDENED / STOP OK.
#  v-E17 CE PROFIT LOCK (config, OFF): at +0.5R move CE SL to entry+0.1R.
#  Log/CSV only: carried flow 3/6/9/12/15 min at entry, quiet-flow flag,
#        chart/adjusted stop columns. Trailing buffer stays 8 pts.
#  vE5.2 (14-Oct-2026) -- same file names.
#  v-E13 BOT_GE now posts its own dashboard heartbeat (NIFTY_<BROKER>_GE);
#        before, only BOT_G reported, so early-slot P&L never reached the
#        dashboard. A KILL from either cell still stops the whole process.
#  vE5.1 (12-Oct-2026) -- HOTFIX, same file names.
#  v-E11 BUG FIX (vE5): carry-forward never applied. _snap_is_stale() records
#        the fetch time as a side effect; vE5 called it a second time for the
#        same snapshot, which then always looked "re-served", so the carry was
#        never updated (and a spurious "snapshot reuses..." line was logged on
#        every reading). Now checked ONCE per reading and passed along.
#  v-E12 NSE-holiday-aware expiry: an expiry Tuesday that is an NSE holiday
#        moves to the previous trading day (config NSE_TRADING_HOLIDAYS).
#        Tue 20-Oct-2026 (Dussehra) -> Mon 19-Oct (symbol 26O19...). Fixes
#        "Invalid symbol provided" for every option on 12-Oct. Month-end
#        (monthly-format) detection uses the nominal Tuesday, so a holiday-
#        shifted last-Tuesday (e.g. 24-Nov-2026 -> 23-Nov) stays monthly.
#  vE5 (09-Oct-2026) -- DPCR RE-ANCHOR + DASHBOARD. Renamed to BOT_rmoney_nifty_g_pool_vE5.py
#  / config_rmoney_nifty_g_pool_vE5.py / option_chain_filter_nifty_rmoney_vE5.py;
#  outputs *_nifty_g_pool_vE5_<series>_rmoney.*. Agreed 09-Oct:
#  v-E7  (A) Same re-anchor trigger on both brokers: distance of spot from
#        the spot AT THE MOMENT OF ANCHORING (RMoney used the anchor strike).
#  v-E8  Re-anchor distance = HALF the DPCR window's width (module setting
#        REANCHOR_MODE="HALF_WINDOW"): Wed +/-5 -> 125 pts, Thu +/-4 -> 100,
#        Fri +/-3 -> 75, Mon/Tue +/-2 -> 50. Was a fixed 0.75%.
#  v-E9  (B') CARRY-FORWARD: at a re-anchor the old window's intraday
#        totals are carried and the new window's changes are added on top,
#        so the decision DPCR keeps meaning "today's flow so far" (was: score
#        reset to zero). Config BOTG_DPCR_CARRY_ENABLED. Every reading after
#        a re-anchor logs BOTH values: "BOT_G DPCR CARRY | reset=.. carried=.."
#        for the 20-Oct comparison. Decisions (lock/veto/flip/BOT_GE
#        direction/CSV dpcr_signed_at_entry) use the carried value.
#  v-E10 Dashboard payload: signed DPCR (was raw PE/CE ratio) + raw ratio +
#        broker + no-trade zone. Needs backend.py/dashboard_live.html v-DASH5.
#  vE4 (05-Oct-2026) -- EARLY-ENTRY SLOT. Renamed to BOT_rmoney_nifty_g_pool_vE4.py
#  / config_rmoney_nifty_g_pool_vE4.py / option_chain_filter_nifty_rmoney_vE4.py;
#  outputs *_nifty_g_pool_vE4_<series>_rmoney.*. Spec agreed 05-Oct:
#  v-E1  Second bot slot BOT_GE (early entry), 09:45-10:14 (BOTGE_* in
#        config). SAME entry mechanics as BOT_G (rejection at option VWAP,
#        confirmation, candle quality, VPC, strike pool, VIX lot size --
#        VIX locked at 09:45). No early slot on gap days. No daily lock:
#        direction checked on every tick while arming AND confirming --
#        CE only if signed DPCR > 0 (raw ratio > 1) AND the 9-min flow
#        tier for CE is MOST/HALF; PE only if signed DPCR < 0 AND the PE
#        tier is MOST/HALF; otherwise no early trade. No no-trade zone.
#        No limit on early trades (re-arm is the only gate).
#  v-E2  BOT_GE exits: BE 0.6R, P1 50% @ max(0.75R,3%), P2 25% @
#        max(1.25R,6%), trailing from 1.25R with buffer
#        max(3, min(8, 1.0R)) pts, 30-min cap while below BE, DPCR-flip
#        exit below BE = signed DPCR changes sign against the trade. No
#        hard exit -- an early trade runs to its normal end, even after
#        10:15.
#  v-E3  BOT_G (10:15 slot) UNCHANGED except option (B): it opens no new
#        trade while a BOT_GE trade is open (BOTG_WAIT_FOR_EARLY_TRADE).
#        Its DPCR update, 10:15 lock and VIX lock keep running meanwhile.
#  v-E4  Exit parameters made per-bot (bot dict override -> config
#        default). BOT_G has no overrides, so its numbers are exactly the
#        v3.2 ones.
#  v-E5  Rejection-candle scan memory keyed per bot+symbol (was symbol).
#  v-E6  Dispatch / summary include BOT_GE; trades, paths, logs tagged
#        by bot name.
#  v-G84  (v3.2, same file names) PRICE-PATH LOG, LOG-ONLY: every manage
#         tick of an open trade appends a row to
#         trade_paths_nifty_g_pool_v3_<series>_<broker>.csv (ts, trade_id,
#         elapsed_sec, ltp, r_now, mfe/mae so far, qty_open, stage,
#         active_sl). Written when LTP changes or every
#         BOTG_PATH_HEARTBEAT_SEC; buffered, flushed every
#         BOTG_PATH_FLUSH_ROWS rows and on every partial/final exit. Lets
#         BE / P1 / P2 / trailing-buffer variants be replayed on the exact
#         path the bot saw. Recorded BEFORE that tick's exit decision, so
#         stage/active_sl are the values in force when the tick arrived.
#  v-G85  Diagnostics skip a DPCR snapshot whose option-chain fetch time
#         equals the previous one (Fyers 1-Oct 11:54 reused the 11:51
#         cached chain after a late call). Diagnostics only -- the trading
#         DPCR history is unchanged (frozen).
#  v-G83  (v3.1, same file names -- v3 had not collected data yet)
#         Post-entry response, LOG/CSV ONLY: lowest and highest option
#         price after entry with seconds-from-entry (MAE/MFE, in points
#         and R), and the option price at +1/+3/+5/+9 min
#         (BOTG_POST_ENTRY_MARKS_MIN) from the LTP the manage loop already
#         reads every tick -- no extra API call. Written on the FINAL row.
#         Purpose: tell "failed from the start" (entry problem) apart from
#         "moved up, then gave it back" (profit-management problem).
#  v-G82  Trade CSV: the latest diagnostic at entry appended as extra
#         columns (_ENTRY_DIAG_KEYS).
#  All tunables live in config_rmoney_nifty_g_pool_v2.py (v2 header note
#  below supersedes the older file names mentioned further down).
#
#  v2 (28-Sep-2026) -- renamed from BOT_rmoney_nifty_g_pool_v1.py /
#  config_nifty_g_pool_v1.py so the new build cannot mix with the old
#  one. Motivated by the 28-Sep paper session (Fyers vs RMoney):
#  v-G70  File naming: every file this bot writes is now
#         <kind>_nifty_g_pool_v2_<series>_rmoney.<ext> (bot_log / trades /
#         summary / bot_state) + heartbeat_nifty_g_pool_v2_rmoney.txt --
#         identical to the Fyers v2 bot except the broker suffix (was
#         ..._G4_ALLFIX_5M_VWAP).
#         dpcr_log_nifty.txt / dpcr_window_shift_nifty.txt are written by
#         option_chain_filter_nifty.py (shared module) -- NOT renamed here.
#  v-G71  SL-VWAP clamp made continuous (config
#         BOTG_SL_VWAP_CLAMP_CONTINUOUS): SL = min(rej_low, VWAP-buffer).
#  v-G72  v-G28 early-warning pause made side-aware (config
#         BOTG_DPCR_FALLING_BLOCK_SIDE_AWARE).
#  v-G73  Losing-streak counter counts SL/TSL exits only when the whole
#         trade lost (config BOTG_STREAK_COUNT_LOSSES_ONLY).
#  v-G74  Summary: whole trades, not legs; max_drawdown measured from 0.
#  v-G75  DPCR FLOW diagnostics (LOG/CSV ONLY): 9-min change in window CE/
#         PE OI each DPCR snapshot, tier at entry (MOST/HALF/MIXED/NOT).
#  v-G76  Trade CSV v2 schema: trade_id, run_id, symbol, entry_time,
#         initial_sl, risk_pts, pnl_pts, r_multiple, leg_type, trade_pnl,
#         sl_clamped, DPCR flow fields; legacy BOT_A-F columns dropped.
#  v-G78  XTS closed-candle lag fix (see fetch_option_history_5m()).
#  Entry logic unchanged except v-G72 and v-G78 (which strikes may ARM while the
#  early-warning pause is active); exits unchanged except v-G71 (initial
#  SL can be up to BOTG_SL_VWAP_BUFFER lower when the rejection low sits
#  within buffer below VWAP).
#  Group    : G4.1 G6/G7/G10 — hybrid profit booking + per-bot profit cap (cumulative G4 fixes)
#
#  Two bots, one process: BOT_G and BOT_G share every function (DPCR daily-
#  bias lock, option-own-VWAP rejection/live-trigger entry, points-based
#  SL/BE/TSL, two-stage partial booking). They differ ONLY in their VIX-based
#  strike-depth ladder (BOTG_VIX_PROFILE vs BOTGG_VIX_PROFILE) and entry-
#  window start times. All tunables live in config_nifty_g_pool_v1_v1_0.py.
#
#  v-G13 (12-Aug-2026): split out from the original BOT_A-F multi-bot suite
#  into this standalone process -- ACTIVE_BOTS/BOTS[] contain only BOT_G and
#  BOT_G here, with zero shared files/state/dashboard cell with A-F.
#
#  KEY HISTORY (BOT_G only):
#  ─────────────────────────────────────────────────────────────────────────
#  v-G1        BOT_G's own option-symbol constructor and OTM-depth ladder,
#              fully independent of the legacy get_option_symbol() path.
#  v-G2        Option-own-VWAP bounce concept (log-only) -- gate uses the
#              CANDIDATE OPTION CONTRACT's own VWAP, not spot's.
#  v-G6        Full entry/exit spec: ONE rejection candle (close within
#              BOTG_NEAR_VWAP_PTS of VWAP) arms the NEXT candle for a
#              LIVE/intrabar buy.
#  v-G7        Daily direction bias: DPCR locks ONE side, once, for the
#              whole day, then only ever vetoes or confirms.
#  v-G8        Real DPCR feed wired in (option_chain_filter_nifty.py).
#  v-G9        Full paper-trade wiring into BOTS[]/main() dispatch.
#    FIX3      DPCR update/lock/veto gated to once per 3m candle (was
#              re-logging identical values every ~1-3s main-loop tick).
#    FIX5      Deliberately does NOT use can_enter()/BASE_REENTRY_COOLDOWN_
#              SEC -- BOT_G's own rejection-candle re-arm is its reentry
#              gate, not a fixed timer.
#    FIX6      today_open/yesterday_close cast to native float/bool before
#              reaching a bot dict field -- numpy.bool_ isn't JSON-
#              serializable and crashed save_state().
#    FIX7      Entry must abort if live price has already fallen through the
#              rejection candle's own low before fill (inverted SL/BE/TSL).
#    FIX8      No reentry cooldown of any kind for BOT_G -- neither the flat
#              timer nor the tiered v-CD2 lock.
#  v-G12       BOT_G added -- shares 100% of BOT_G's logic (same functions,
#              two BOTS[] dicts), differs only in VIX-based strike depth.
#              Shared DPCR fetch deduplicated via
#              _is_new_shared_dpcr_candle() (one fetch per 3-min candle
#              regardless of how many bots share the reading).
#  v-G15       BOT_G's own trade_start_override (11:00/13:00 vs BOT_G's
#              10:30/12:30).
#  v-G16       QTY reduced 10->8->4 lots so two-stage partial booking
#              (50%@1R, 25%@1.5R, remainder trails) divides into whole lots.
#  v-G18       Candle-alignment fix: resample(origin="09:15"), was
#              midnight-anchored (confirmed wrong against Fyers' native
#              API). "Option 1" consistency filter added -- rejection
#              candle requires >=BOTG_CONSISTENCY_MIN_PCT of its 3-min
#              sub-bars to close on the majority side of their own
#              contemporaneous VWAP.
#    FIX1      Config import was missing entirely -- every BOTG_/BOTGG_
#              constant was relying on a wildcard import that never existed.
#    FIX2      Fyers client initialization was also missing entirely.
#  v-G20       entry_timeframe_minutes standardised to 5 for both bots.
#  v-G2A      Option history uses native RMoney/XTS 5-minute candles directly;
#             no 1-minute strategy feed and no client-side 1m->5m resampling.
#  v-G23       write_summary()/save_state() moved into a try/finally so they
#              run on ANY exit path (IDE stop, Ctrl+C, crash), not just the
#              two narrow paths that existed before.
#  v-G24       VIX-based OTM depth/qty AND the DPCR no-trade zone width now
#              lock TWICE per day (own trade_start, then 14:00), to capture
#              real intraday VIX moves.
#  v-G25       DPCR crossing label is sticky when there's no fresh crossing
#              (preserved, not reset to None).
#  v-G26       DIAG1: diagnostic-only logging of Fyers' raw 's'/'message'
#              response on option-history KeyError('candles') failures.
#  v-G28       Dynamic DPCR side-flip (CE<->PE, was permanent once-locked),
#              force-exits an open position ONLY if still below breakeven
#              at the flip moment -- at/above breakeven runs to natural
#              completion untouched. New falling-DPCR early-warning gate
#              pauses fresh entries only. Both bots standardised on 5-min
#              candles; the 10-min path removed. No losing-streak halt,
#              no re-entry cooldown of any kind for BOT_G.
#  v-G56 (16-Sep-2026) NOTE: the line above is a historical record of
#              v-G28's own change, not current truth -- a separate,
#              dedicated BOT_G streak counter/cooldown (LOSING_STREAK_
#              LIMIT/_COOLDOWN_SEC) was added later and is genuinely
#              active. But "losing_streak_exempt": True (in BOT_DEFAULTS
#              below) made allow_trade() -- the only place that actually
#              enforces this lock during entry -- skip the check
#              entirely for BOT_G, confirmed via full trace on the Fyers
#              file and identical here. The counter still incremented
#              and logged "HALTED"/cooldown timing correctly, but
#              nothing stopped a new entry before the cooldown expired
#              unless some OTHER gate (DPCR zone, etc.) independently
#              blocked it too. Resolved: exemption removed (now False),
#              so this gate genuinely enforces for BOT_G going forward.
#  v-G27       BOTG_DPCR_FLAT_BAND (locked-side veto's slope check) is now
#              VIX-scaled -- must stay below each tier's own no-trade-zone
#              half-width to have any early-warning value at all.
#  v-G29       ROOT-CAUSE FIX: the week the weekly expiry coincides with
#              the monthly expiry (last Tuesday of the month), Fyers
#              rejects the ordinary weekly-format symbol outright
#              (confirmed live, 20/21-Aug-2026: 'Invalid symbol provided'
#              on every strike/side tried). This alone silently blocked
#              100% of option-history fetches for two full trading days --
#              not a DPCR calibration issue, though that was investigated
#              first and genuinely also needs fixing. Real symbol now
#              switches to monthly format (YY+3-letter-month) for that one
#              week per month; _SERIES_CODE/log-file naming unaffected.
#  v-G30       Confirmation candle must land within a VIX-scaled asymmetric
#              band around VWAP (small dip below allowed, more room above)
#              -- not just "touched the band at some point". Root cause:
#              real 20-Aug losing trades confirmed 2.7-3.0 points below
#              VWAP the whole window, never a genuine reclaim of the
#              pivot; real winners confirmed within +0.07 to +3.54.
#              Theta-decay time cap: an INITIAL-stage position (no SL, no
#              BE, no partial yet) that's shown no real progress within
#              BOTG_MAX_HOLD_MINUTES_INITIAL force-exits rather than
#              letting theta keep eroding it. ARM EXPIRED now logs the
#              actual failure reason and VWAP distance, not just "no
#              confirmation".
#  v-WEEKLY1   Switched from monthly to weekly expiry
#              (getNiftyWeeklyExpiry() replaces the old monthly path).
#
#  NIFTY LOT SIZE : 65 (effective January 2026, NSE circular Oct 2025)
#  STRIKE ROUND   : nearest 50
#  EXPIRY         : WEEKLY (Tuesday, unconditional next-week rollover)
#  DEPENDENCIES   : helper_rmoney, requests, pandas, option_chain_filter_rmoney
# =============================================================================

import json
import os
# Keep relative logs, state, data, and archive paths inside this broker folder.
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import csv
import shutil
import time
import threading
import math
import requests
from datetime import date, datetime, timedelta
from logging.handlers import RotatingFileHandler
import logging

import pandas as pd

# v-RG1 (23-Aug-2026): NOT helper_fyers -- RMoney/XTS uses its own token-file
# + interactive/marketdata-token session pattern, no client-object wrapper
# the way fyersModel provides. helper_rmoney.py's own EID-search/order/
# historical functions are NOT reused directly here (they're written for
# the A-F suite's own global session dict) -- this file has its own,
# self-contained versions of the same XTS calls, verified against the
# A-F suite's working implementation (BOT_nifty_v3_16_LOGONLY.py)
# before being adapted here.

# v-RG2 (23-Aug-2026): DPCR/OI feed for BOT_G -- RMoney/XTS-native, NOT
# Fyers-sourced (explicit instruction, no cross-broker dependency). See
# that module's own header for the UNVALIDATED-smoke-test caveat on the
# OI message code used.
import setup_tags_nifty_vE6 as _v35   # v-E35 (vE6.2.4) setup tags, log-only
import exit_whatif_nifty_vE6 as _wi   # v-E36 (vE6.3) exit what-if, log-only
import zlm_shadow_nifty_vE6 as _zlm   # v-E31 (vE6.2.3) ZLM shadow, log-only
_ZLM_SYM_PREFIX = "NIFTY"   # v-E31
import option_chain_filter_nifty_rmoney_vE6 as _oc_filter   # vE6 (was option_chain_filter_nifty_rmoney_vE5)

from config_rmoney_nifty_g_pool_vE6 import *   # vE6

# =============================================================================
#  G4 ALL-FIX — RISK / PROFIT / STARTUP NORMALIZATION
#  Applied cumulatively in this bot file only; helper/config files untouched.
# =============================================================================
# G4.1 Paper stop execution: paper STOP/BE/TSL exits are booked at the stop
# level that triggered the exit, not at a later observed LTP. LIVE mode still
# uses the actual broker fill inside log_trade().
# v-E24 (vE6.2.1): OFF -- paper stop exits booked at the trigger LTP, same as
# Fyers. The stop level is still logged as the exit signal price (v-E23).
G4_PAPER_STOP_AT_TRIGGER = False

# v-RG-FIX3 (bug fix, this session): G4.2 and the profit-cap/partial-target
# half of G4.3 REMOVED -- explicit instruction ("make the two bots similar").
# This block used to recompute MAX_DAILY_LOSS/MAX_DAILY_PROFIT/PROFIT_
# PROTECT_THRESHOLD/PROFIT_PROTECT_TIERS a second time here, immediately
# after config already computed them correctly from the shared LOTS_PER_
# BOT/ACTIVE_BOT_COUNT -- via its own separate G4_ACTUAL_LOTS_PER_BOT/
# G4_ACTIVE_BOT_COUNT constants. Numerically identical today, but two
# independent sources of truth for the same numbers, in two different
# files -- confirmed already drifting: this block's own comment said "2
# active bots" while its own code set G4_ACTIVE_BOT_COUNT=1, a leftover
# from before BOT_GG was removed that never got cleaned up. Likewise
# G4_PER_BOT_PROFIT_CAP duplicated BOTG_DAILY_PROFIT_CAP_PER_BOT (config),
# and G4_PARTIAL_1_PCT/G4_PARTIAL_2_PCT/G4_PARTIAL_1_FRACTION/G4_PARTIAL_
# 2_FRACTION duplicated BOTG_PARTIAL_R1_PCT_FLOOR/R15_PCT_FLOOR/R1_
# FRACTION/R15_FRACTION (config). All of these now come from config only,
# matching the Fyers file's structure exactly -- see check_bot_g_partial_
# booking(), allow_trade(), log_trade(), log_partial_trade(), and the
# startup banner for the updated call sites.

# G4.4 Startup readiness: do not hammer stale history before the market opens.
# Keep candle alignment anchored at 09:15, but begin live readiness polling at
# 09:16 and retain the current first forming 3-minute bar so gap/anchor state can
# become available before the first closed 3-minute candle (the signal functions
# themselves use closed bars).
G4_STARTUP_DATA_HHMM = 916
G4_DATA_ALIGNMENT_HHMM = 915

# =============================================================================
#  GROUP 1 — BROKER INPUT HARDENING (Fyers-reference migration)
#  Scope: exact option-contract EID matching + validated India VIX input.
#  Strategy/config/helper files are intentionally untouched.
# =============================================================================

# =============================================================================
#  SECTION 1 — BROKER LOGIN
# =============================================================================
# v-RG1: RMoney/XTS session -- loads interactive_token/marketdata_token from
# rmoney_tokens.json (written by rmoney_login.py, run once each morning,
# same pattern as the existing A-F suite). Rejects tokens older than 8
# hours -- prevents silent failures from a stale overnight token.
INTERACTIVE_URL = "https://xts.rmoneyindia.co.in:3000/interactive"
MARKETDATA_URL  = "https://xts.rmoneyindia.co.in:3000/apimarketdata"

NIFTY_EXCHANGE_SEGMENT = 1    # NSECM (cash/index segment)
NIFTY_FO_SEGMENT       = 2    # NSEFO (futures & options segment)
NIFTY_INSTRUMENT_ID    = 26000   # Nifty 50 index, confirmed from A-F suite

_HTTP = requests.Session()
_SESSION = {"interactive_token": None, "marketdata_token": None, "userID": ""}


def initialize():
    """
    v-RG1: ported from the A-F suite's own initialize() unchanged -- same
    token-file convention, same 8-hour staleness check.
    """
    token_file = "rmoney_tokens.json"
    if not os.path.exists(token_file):
        raise FileNotFoundError(
            "rmoney_tokens.json not found. "
            "Please run rmoney_login.py first, then start this bot."
        )
    with open(token_file, "r") as f:
        tokens = json.load(f)

    token_age_hrs = (time.time() - tokens.get("timestamp", 0)) / 3600
    if token_age_hrs > 8:
        raise ValueError(
            f"rmoney_tokens.json is {round(token_age_hrs, 1)} hours old. "
            "Re-run rmoney_login.py before starting the bot."
        )

    _SESSION["interactive_token"] = tokens.get("interactive_token")
    _SESSION["marketdata_token"]  = tokens.get("marketdata_token")
    _SESSION["userID"]            = tokens.get("userID", "")

    if not _SESSION["marketdata_token"]:
        raise ValueError("marketdata_token missing in rmoney_tokens.json. Re-run rmoney_login.py.")
    if not _SESSION["interactive_token"]:
        raise ValueError("interactive_token missing in rmoney_tokens.json. Re-run rmoney_login.py.")

    print(f"API connected successfully | token age: {round(token_age_hrs, 1)}h")


def _md_headers():
    return {"Content-Type": "application/json", "authorization": _SESSION["marketdata_token"]}


def _int_headers():
    return {"Content-Type": "application/json", "authorization": _SESSION["interactive_token"]}


initialize()


# =============================================================================
#  SECTION 2 — WEEKLY EXPIRY
# =============================================================================



def _nse_trading_day_on_or_before(d):
    """v-E12 (vE5.1): step back from d over weekends and NSE_TRADING_HOLIDAYS
    (config). An expiry that falls on a holiday moves to the previous
    trading day, e.g. Tue 20-Oct-2026 (Dussehra) -> Mon 19-Oct-2026."""
    _hol = set(NSE_TRADING_HOLIDAYS)
    while d.weekday() >= 5 or d.isoformat() in _hol:
        d -= timedelta(days=1)
    return d


def _nse_trading_days_between(d, exp):
    """v-E18 (vE6.2): NSE trading days strictly after d, up to and including
    exp (weekends and NSE_TRADING_HOLIDAYS skipped). 0 when d == exp."""
    _hol = set(NSE_TRADING_HOLIDAYS)
    n, x = 0, d
    while x < exp:
        x += timedelta(days=1)
        if x.weekday() < 5 and x.isoformat() not in _hol:
            n += 1
    return n


def _nominal_expiry_tuesday(d):
    """v-E12: the Tuesday of the expiry week that d belongs to (d itself
    if Tuesday; for a holiday-shifted Monday/Friday expiry, the Tuesday it
    replaced)."""
    return d + timedelta(days=(1 - d.weekday()) % 7)


def is_nifty_expiry_day():
    """
    Returns True if today is THIS WEEK's Nifty weekly expiry (Tuesday).

    BUG FOUND while converting to weekly (v-WEEKLY1): the old monthly-expiry
    version did `int(expiry_code[:2])` on a code like "26AUG" -- which parses
    the YEAR PREFIX "26" as if it were the expiry day-of-month. That's only
    accidentally correct for months where the expiry day happens to BE the
    26th. Fixed by comparing actual date objects, not substrings of a
    formatted code.
    """
    _d = date.today()   # v-E12: holiday-aware (Mon 19-Oct-2026 is an expiry day)
    return _d == _nse_trading_day_on_or_before(_nominal_expiry_tuesday(_d))


def _verify_expiry_at_startup():
    """
    Startup sanity check for weekly expiry. Logs sample symbol for visual
    confirmation before first trade.
    """
    try:
        expiry_code, expiry_date = getNiftyWeeklyExpiry()
    except Exception as e:
        raise ValueError(f"STARTUP ABORT | {e}")
    symbol_expiry_code = _bot_g_symbol_expiry_code(expiry_date)
    sample = f"NIFTY{symbol_expiry_code}24000CE"
    log(f"EXPIRY CHECK  | Weekly expiry code: {expiry_code} ({expiry_date.isoformat()})")
    log(f"EXPIRY CHECK  | Sample symbol: {sample}")
    if _is_month_end_weekly(expiry_date):
        log(f"EXPIRY CHECK  | NOTE: this week's expiry ({expiry_date.isoformat()}) is the "
            f"last Tuesday of its month -- monthly-format symbol code "
            f"({symbol_expiry_code}) used for actual fetches/orders, not the "
            f"ordinary weekly code ({expiry_code}) shown above (v-RG1, same root "
            f"cause as Fyers v-G29 -- confirmed present in RMoney's own weekly "
            f"convention too, see helper_rmoney.py's table)")
    # The traded contract is always the one with >1 day of runway left
    # (getNiftyWeeklyExpiry() never returns a symbol expiring today or
    # tomorrow -- see _next_nifty_weekly_expiry_date(), v-G38), so being
    # within 1 day of the underlying index's own weekly expiry carries no
    # elevated gamma/pin risk for the contract actually held. Informational
    # log line only.
    # v-E26 (vE6.2.1): describe the actual v-E18 rule (old text said
    # "unconditional" and used calendar days).
    _d0 = date.today()
    _near = _nse_trading_day_on_or_before(_nominal_expiry_tuesday(_d0))
    if _near < _d0:
        _near = _nse_trading_day_on_or_before(_nominal_expiry_tuesday(_d0) + timedelta(days=7))
    _tdl = _nse_trading_days_between(_d0, _near)
    if expiry_date != _near:
        log(f"EXPIRY CHECK  | NOTE: nearest expiry {_near.isoformat()} has {_tdl} NSE trading "
            f"day(s) left (<= {BOTG_ROLLOVER_MAX_DAYS_LEFT}) -> trading the next expiry "
            f"{expiry_date.isoformat()} (v-E18)")
    else:
        log(f"EXPIRY CHECK  | trading the nearest expiry: {_tdl} NSE trading day(s) left "
            f"(rolls at <= {BOTG_ROLLOVER_MAX_DAYS_LEFT}, v-E18)")


_BOTG_WEEKLY_MONTH_CODE = {
    1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6",
    7: "7", 8: "8", 9: "9", 10: "O", 11: "N", 12: "D",
}   # Fyers weekly symbology: Jan-Sep = digit, Oct/Nov/Dec = O/N/D.
    # Collision-free by construction — no two months share a code, unlike
    # a naive first-letter scheme (which would clash on June/July, and on
    # January/June/July if 'J' were used for all three).


def _next_nifty_weekly_expiry_date(from_date=None):
    """
    v-G1: Returns the date of the next Nifty WEEKLY expiry (Tuesday, per
    the same SEBI restructuring that moved monthly expiry to the last
    Tuesday — confirmed earlier that weekly also moved to Tuesday, not
    Thursday).

    Deliberately rolls PAST the imminent Tuesday to next week's, per the
    strategy design's own rule (avoid trading a contract with too little
    runway left — elevated theta/gamma risk close to expiry).

    v-G38 (this session): rollover threshold widened from "today IS
    expiry Tuesday" to "the imminent Tuesday is <=BOTG_ROLLOVER_MAX_DAYS_
    LEFT days away" — explicit instruction. Default (1) means Monday now
    rolls forward too, not just Tuesday itself: Mon/Tue both trade next
    week's contract, Wed/Thu/Fri trade the imminent one (unchanged from
    before). Confirmed example: Mon 24-Aug-2026 and Tue 25-Aug-2026 both
    resolve to 1-Sep-2026, not 25-Aug-2026. Kept identical to the Fyers
    file's copy of this function.
    """
    d = from_date or date.today()
    days_to_tue = (1 - d.weekday()) % 7   # Tuesday = weekday index 1
    nominal = d + timedelta(days=days_to_tue)
    exp = _nse_trading_day_on_or_before(nominal)   # v-E12: holiday -> previous trading day
    if exp < d:   # this week's (holiday-shifted) expiry already passed
        nominal += timedelta(days=7)
        exp = _nse_trading_day_on_or_before(nominal)
    # v-E18 (vE6.2): runway counted in NSE TRADING days to the ACTUAL expiry
    # (was calendar days to the nominal Tuesday -> Fri 16-Oct-2026 traded the
    # Mon 19-Oct contract with 1 trading day left).
    if _nse_trading_days_between(d, exp) <= BOTG_ROLLOVER_MAX_DAYS_LEFT:
        exp = _nse_trading_day_on_or_before(nominal + timedelta(days=7))
    return exp


def _nearest_nifty_weekly_expiry_date(from_date=None):
    """
    v-RG-FIX1 (bug fix, this session): DPCR must read OI off the NEAREST/
    front-week option chain -- the contract the whole market is actually
    watching that week -- completely independent of which contract BOT_G
    itself trades. That's a deliberately different question from
    _next_nifty_weekly_expiry_date()/getNiftyWeeklyExpiry() above, which
    intentionally SKIPS the imminent Tuesday (elevated theta/gamma risk on
    the actual expiring week's own contract) and always resolves to next
    week's Tuesday instead.

    This function does NOT skip anything -- it returns the nearest
    upcoming Tuesday, including TODAY itself if today is Tuesday (the
    front-week chain on expiry day is still today's chain, right up until
    it expires). Confirmed against how Fyers' own BOT_G gets this right by
    construction: its fetch_option_chain() passes no expiry parameter at
    all, so Fyers' API defaults to the nearest chain automatically. RMoney/
    XTS's option-chain endpoint requires an explicit expiry code, which is
    what surfaced this as a real bug here -- get_current_dpcr() was
    passing getNiftyWeeklyExpiry()'s NEXT-WEEK code instead, silently
    pulling DPCR's OI data from the wrong contract entirely.

    Only used to build the expiry code passed into compute_dpcr() --
    never for anything related to which contract BOT_G actually trades.
    """
    d = from_date or date.today()
    days_to_tue = (1 - d.weekday()) % 7   # Tuesday = weekday index 1
    return _nse_trading_day_on_or_before(d + timedelta(days=days_to_tue))   # v-E12


def getNiftyWeeklyExpiry(from_date=None):
    """
    v-G1: Returns (fyers_code, expiry_date) for BOT_G's weekly contract.
    fyers_code format: YY + single-char month + DD, e.g. "26811" for
    11-Aug-2026 (26=year, 8=August, 11=day). Matches Fyers' documented
    weekly symbology — verified against real working examples (e.g.
    "24D19..." for 19-Dec-2024, "26113..." for 13-Jan-2026), NOT the
    2-digit-month convention some other tools/exports use.

    NOTE: this code is used for _SERIES_CODE / log-file naming and for
    display purposes (startup banner, expiry-check log line) -- it is
    intentionally left unchanged here even for a month-end week (see
    v-G29 below), so existing log filenames and dashboards keep their
    established naming convention. The SYMBOL actually sent to Fyers for
    a real order/history fetch does NOT use this code directly when the
    week is month-end -- see _bot_g_symbol_expiry_code().
    """
    exp_date = _next_nifty_weekly_expiry_date(from_date)
    yy = exp_date.strftime("%y")
    mchar = _BOTG_WEEKLY_MONTH_CODE[exp_date.month]
    dd = f"{exp_date.day:02d}"
    return f"{yy}{mchar}{dd}", exp_date


_BOTG_MONTHLY_MONTH_ABBR = {
    1: "JAN", 2: "FEB", 3: "MAR", 4: "APR", 5: "MAY", 6: "JUN",
    7: "JUL", 8: "AUG", 9: "SEP", 10: "OCT", 11: "NOV", 12: "DEC",
}


def _is_month_end_weekly(exp_date):
    """
    v-G29 (22-Aug-2026): True if exp_date is the LAST Tuesday of its
    month -- i.e. this week's weekly expiry is simultaneously the
    month's own monthly expiry (adding 7 days would roll into next
    month). NSE/Fyers list that one specific contract under the MONTHLY
    symbol format (YY+3-letter-month, e.g. "26AUG"), not the ordinary
    weekly numeric-date format (YY+M+DD, e.g. "26825") -- there being
    only one contract for that date, exchanges publish it as "the
    monthly," not as a weekly that happens to coincide.
    """
    _tue = _nominal_expiry_tuesday(exp_date)   # v-E12: judge on the nominal Tuesday
    return (_tue + timedelta(days=7)).month != _tue.month


def _bot_g_symbol_expiry_code(exp_date):
    """
    v-G29 (22-Aug-2026): ROOT-CAUSE FIX. getNiftyWeeklyExpiry()'s ordinary
    weekly code (YY+M+DD) is what Fyers actually expects for a normal
    week, but for the one week per month where the weekly expiry IS the
    monthly expiry (_is_month_end_weekly() True), Fyers rejects that code
    outright: confirmed live, 20/21-Aug-2026, `fyers.history()` returning
    `{'code': -300, 'message': 'Invalid symbol provided'}` for EVERY
    strike and side tried (24000 PE, 24200 PE, 24400 CE) against the
    25-Aug-2026 expiry -- which is the last Tuesday of August. Every
    single option-history fetch failed silently (fetch_option_history_5m
    returning None -> find_bot_g_rejection_5m never even running), so
    BOT_G could not arm a single rejection candle across two full
    trading days despite favorable price action and an open DPCR gate at
    the exact moments checked -- this, not the DPCR zone/threshold
    calibration, was the actual reason no trade fired on 19-Aug or
    20-Aug.

    Returns the code to use for the SYMBOL actually sent to Fyers
    (history fetch, order placement) -- YY+3-letter-month (e.g. "26AUG")
    for a month-end week, otherwise identical to getNiftyWeeklyExpiry()'s
    ordinary YY+M+DD code.

    UNVALIDATED beyond the fact that it fixes the documented failure mode
    -- verify the resulting symbol against Fyers' own symbol
    search/contract master before this goes anywhere near live trading.
    """
    if _is_month_end_weekly(exp_date):
        yy = exp_date.strftime("%y")
        return f"{yy}{_BOTG_MONTHLY_MONTH_ABBR[exp_date.month]}"
    yy = exp_date.strftime("%y")
    mchar = _BOTG_WEEKLY_MONTH_CODE[exp_date.month]
    dd = f"{exp_date.day:02d}"
    return f"{yy}{mchar}{dd}"


def get_option_symbol_bot_g(spot, side, otm_steps=None, bot_name="BOT_G"):
    """
    v-G1: BOT_G's own symbol constructor -- ATM calc, logging, WEEKLY
    expiry, always-OTM depth (unsigned -- see config comment). Fully
    independent of the deleted BOT_A-F get_option_symbol() path (monthly
    expiry, signed ITM/OTM via STRIKE_ITM_STEPS) that used to live in
    this file.

    v-G40 (this session): the liquid-grid snap this docstring used to
    mention is gone -- see the removal note inline below for why.

    v-G11: otm_steps is now a parameter, not a hardcoded constant --
    lock_bot_g_vix_regime() sets it once daily from VIX (1-4 steps).
    Defaults to BOTG_STRIKE_OTM_STEPS (the original fixed OTM4) if not
    passed, so any other caller that hasn't been updated still works.

    v-G12: bot_name added so BOT_G (shares this function with BOT_G) gets
    correctly-labeled log lines instead of always saying "BOT_G".
    """
    if otm_steps is None:
        otm_steps = BOTG_STRIKE_OTM_STEPS
    atm_strike = round50(spot)
    offset = otm_steps * STRIKE_ROUND_UNIT
    # OTM direction: CE OTM strikes sit ABOVE spot, PE OTM strikes sit BELOW.
    if side == "CE":
        strike = atm_strike + offset
    else:
        strike = atm_strike - offset

    # v-G40 (this session): liquid-grid snap REMOVED. Explicit instruction --
    # found live, this session (today's real log): with the pool spaced
    # 50pts apart (STRIKE_ROUND_UNIT) but the old grid snapping to the
    # nearest 100, ATM/OTM1/OTM2 collapsed onto the SAME strike on every
    # VIX<=13 day (confirmed directly: OTM_STEPS 0/1/2 all resolving to
    # strike 23600 at 11:20/14:15/14:20 today). Silently neutered the
    # whole pool on exactly the VIX regime it's most often used in.
    # Strikes are natively listed every 50pts on NIFTY and liquid enough
    # at that spacing -- the pool needs genuinely distinct strikes to do
    # what it's for, so this snap doesn't belong here regardless of grid
    # size chosen. Kept identical to the Fyers file's copy of this function.

    expiry_code, expiry_date = getNiftyWeeklyExpiry()
    # v-RG1: the REAL symbol sent to RMoney uses _bot_g_symbol_expiry_code(),
    # not expiry_code directly -- they differ exactly one week per month
    # (the month-end week), see that function's docstring for why. Format
    # confirmed against helper_rmoney.py's getOptionFormat(): stock + expiry
    # + strike + side, NO exchange prefix, NO separator (unlike Fyers'
    # "NSE:NIFTY..." convention).
    symbol_expiry_code = _bot_g_symbol_expiry_code(expiry_date)
    symbol = f"NIFTY{symbol_expiry_code}{strike}{side}"
    log(f"{bot_name} OPTION SYMBOL | Spot:{spot} ATM:{atm_strike} Strike:{strike} "
        f"(OTM_STEPS:{otm_steps}) Expiry:{expiry_date.isoformat()} "
        f"Symbol:{symbol}"
        + (" [MONTH-END WEEK -- monthly-format code, v-RG1]" if _is_month_end_weekly(expiry_date) else ""))
    return symbol


# =============================================================================
#  SECTION 3 — OPTION-OWN-VWAP REJECTION/LIVE-TRIGGER  (v-G2/v-G18)
#     Confirmed this session: gate uses the CANDIDATE OPTION CONTRACT's
#     own VWAP, not spot's -- spot's VWAP (add_ind() above) falls back to
#     an unweighted cumulative-typical-price average because the Nifty
#     index carries no real volume; options do carry real volume (seen
#     directly in the Zerodha CE/PE CSVs reviewed this session), so their
#     own VWAP is a genuine volume-weighted number.
#
#     10-min candles, per the same-session finding: touch-then-bounce-back
#     quality was strongest at 10-min (60% on the PE side, both full
#     4-timeframe and today-only re-checks) and weakest at 15-min (43-44%)
#     -- single-day, single-strike, NOT yet validated at scale. Treat as a
#     working assumption to revalidate once real BOT_G logs accumulate,
#     not a settled conclusion.
#
#     LOG-ONLY for now: computes and logs touch/bounce, does not gate any
#     entry yet -- same discipline as everything else in BOT_G so far.
# =============================================================================

_BOTG_OPT_CACHE = {}   # v-RG-FIX2 (bug fix, this session): was a single-
# symbol slot -- regressed back to the pre-v-G37 shape during this port.
# With the multi-strike pool, up to 3 different symbols now get checked
# per tick, and a single-slot cache means each one evicts the last, so
# ALL of them would miss cache on EVERY tick (real RMoney/XTS history
# call every ~1-3s instead of once per ~170s, per symbol). Now keyed by
# symbol: {symbol: {"time5":.., "df5":..}}, matching the Fyers fix exactly
# -- each pool strike gets its own independent cache slot.


def _prev_trading_day():
    """v-RG1: ported unchanged from the A-F suite. Skips weekends only --
    does NOT account for NSE holidays, same limitation as the original."""
    # v-E28 (vE6.2.2): NSE holidays skipped too (21-Oct: the 20-Oct holiday
    # was returned -> history held only today's candles until 09:24).
    _hol = set(NSE_TRADING_HOLIDAYS)
    d = datetime.now().date() - timedelta(days=1)
    while d.weekday() >= 5 or d.isoformat() in _hol:
        d -= timedelta(days=1)
    return d


def _parse_ticks(raw_str):
    """v-RG1: ported unchanged from the A-F suite. Parses RMoney XTS's
    pipe-delimited OHLC response into a list of tick dicts. Timestamps are
    Unix seconds already in IST (confirmed by the A-F suite's own live probe)."""
    rows = []
    for candle_str in raw_str.split(","):
        candle_str = candle_str.strip().rstrip("|")
        if not candle_str:
            continue
        parts = candle_str.split("|")
        if len(parts) < 5:
            continue
        try:
            rows.append({
                "ts": int(parts[0]), "open": float(parts[1]), "high": float(parts[2]),
                "low": float(parts[3]), "close": float(parts[4]),
                "volume": float(parts[5]) if len(parts) > 5 else 0.0,
            })
        except (ValueError, IndexError):
            continue
    return rows


_EID_CACHE: dict = {}


def _normalize_symbol_text(value):
    """Group 1: normalize broker contract text for exact EID matching."""
    if value is None:
        return ""
    return "".join(ch for ch in str(value).upper().strip() if ch.isalnum())


def _resolve_option_eid(symbol: str):
    """
    Group 1 / EID-EXACT: resolve the exact requested Nifty option contract.

    The old implementation accepted the first XTS search result and only
    emitted a warning when its symbol-like fields did not match.  That can
    silently attach an EID for a different contract.  This version keeps the
    same XTS search endpoint and cache, but requires an exact normalized symbol
    match in at least one broker-provided name field.  If no exact match is
    found, it fails closed and the caller does not trade on a guessed EID.

    No helper/config/strategy logic is changed.
    """
    if symbol in _EID_CACHE:
        return _EID_CACHE[symbol]

    requested = _normalize_symbol_text(symbol)
    try:
        resp = _HTTP.get(
            f"{MARKETDATA_URL}/search/instruments",
            headers=_md_headers(),
            params={"searchString": symbol},
            timeout=5,
        )
        if resp.status_code != 200:
            log(f"[EID SEARCH ERROR] HTTP {resp.status_code} for {symbol}")
            return None

        data = resp.json()
        if data.get("type") != "success":
            log(f"[EID SEARCH ERROR] {data.get('description')} for {symbol}")
            return None

        items = data.get("result", [])
        if not isinstance(items, list) or not items:
            log(f"[EID SEARCH EMPTY] no results for {symbol}")
            return None

        match_fields = ("TradingSymbol", "Name", "DisplayName", "Description", "Symbol")
        matches = []
        for item in items:
            eid = item.get("ExchangeInstrumentID") or item.get("exchangeInstrumentID")
            if not eid:
                continue
            values = [_normalize_symbol_text(item.get(k, "")) for k in match_fields]
            if requested and any(v == requested for v in values if v):
                matches.append((int(eid), item))

        if len(matches) == 1:
            eid, item = matches[0]
            _EID_CACHE[symbol] = eid
            log(f"[EID EXACT] {symbol} -> {eid}")
            return eid

        if len(matches) > 1:
            log(f"[EID SEARCH AMBIGUOUS] {symbol}: {len(matches)} exact matches returned -- refusing to guess")
            log(f"[EID SEARCH MATCHES] {matches}")
            return None

        log(f"[EID SEARCH MISMATCH] {symbol}: no exact contract match in {len(items)} result(s) -- refusing to guess")
        log(f"[EID SEARCH RESULTS] {items}")
        return None

    except Exception as e:
        log(f"[EID EXCEPTION] {symbol}: {e}")
        return None

_BOTG_LAST_FORCED_5M_BOUNDARY = {}   # symbol -> bucket number of its last forced refresh
_BOTG_SYNTH_LOGGED = {}              # v-G78: symbol -> last synthetic bucket logged

def _v50_st_dir(df3):
    """v-E50 (vE6.11): direction of the 3-min spot Supertrend(N, MULT) on CLOSED
    candles only (a bar counts as closed once start + 3 min <= now). Wilder ATR
    seeded with the mean of the first N true ranges; standard final-band rule.
    Returns +1 (up), -1 (down) or None (not enough bars / bad data)."""
    try:
        if df3 is None or len(df3) == 0:
            return None
        idx = pd.DatetimeIndex(df3.index)
        if idx.tz is not None:
            idx = idx.tz_convert("Asia/Kolkata").tz_localize(None)
        closed = (idx + pd.Timedelta(minutes=3)) <= pd.Timestamp(datetime.now())
        g = df3[closed]
        n, mult = int(BOTG_ST_FILTER_N), float(BOTG_ST_FILTER_MULT)
        if len(g) < n + 5:
            return None
        h = g["high"].astype(float).values; l = g["low"].astype(float).values; c = g["close"].astype(float).values
        tr = [h[0] - l[0]] + [max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1])) for i in range(1, len(c))]
        atr = [0.0] * len(c); atr[n - 1] = sum(tr[:n]) / n
        for i in range(n, len(c)):
            atr[i] = (atr[i - 1] * (n - 1) + tr[i]) / n
        fu = [(h[i] + l[i]) / 2 + mult * atr[i] for i in range(len(c))]
        fl = [(h[i] + l[i]) / 2 - mult * atr[i] for i in range(len(c))]
        d = 1
        for i in range(1, len(c)):
            ub, lb = fu[i], fl[i]
            fu[i] = ub if (ub < fu[i - 1] or c[i - 1] > fu[i - 1]) else fu[i - 1]
            fl[i] = lb if (lb > fl[i - 1] or c[i - 1] < fl[i - 1]) else fl[i - 1]
            d = 1 if c[i] > fu[i - 1] else (-1 if c[i] < fl[i - 1] else d)
        return d
    except Exception as e:
        log(f"vE6.11 ST FILTER | error (entry allowed): {e}")
        return None


def _v49_opt_tf(bot):
    """v-E49 (vE6.11): option setup candle minutes -- BOT_G uses BOTG_OPT_TF_MIN, others 5."""
    return int(BOTG_OPT_TF_MIN) if bot.get("name") == "BOT_G" else 5


def _v49_ckey(symbol, tf):
    return symbol if tf == 5 else (symbol, tf)   # 5-min keeps the old cache key


def _bot_g_should_force_5m_refresh(symbol, tf=5):
    """
    v-G48 (bug fix): confirmed via independent review, this session --
    BOTG_OPT_HIST_CACHE_SEC (170s) has no candle-boundary awareness at
    all; force_refresh was defined on fetch_option_history_5m() but
    never actually called anywhere. Worst case, the bot could take up
    to ~170 seconds after a 5-min candle genuinely closes before its
    own cache reflects that -- compressing more than half of that
    candle's 300-second confirm window in the worst case. Rather than
    blindly shortening the cache duration (more API load for the same
    fundamental gap), this detects a genuine 5-min boundary crossing
    per-symbol using candle-key comparison (not wall-clock seconds --
    same proven pattern as the v-G45 arm-expiry fix) and forces exactly
    one fresh fetch right when it happens, so the very next scan/
    confirm check always sees the truly-latest closed candle. Every
    other tick within that same boundary still uses the normal cache,
    so this doesn't meaningfully increase API call volume -- at most
    one extra forced fetch per pool symbol per 5-min boundary.
    """
    global _BOTG_LAST_FORCED_5M_BOUNDARY
    now = datetime.now()
    elapsed = (now.hour * 60 + now.minute) - (9 * 60 + 15)
    if elapsed < 0:
        return False
    bucket = elapsed // tf   # v-E49
    if _BOTG_LAST_FORCED_5M_BOUNDARY.get(_v49_ckey(symbol, tf)) == bucket:
        return False
    _BOTG_LAST_FORCED_5M_BOUNDARY[_v49_ckey(symbol, tf)] = bucket
    return True

def fetch_option_history_5m(symbol, force_refresh=False, tf=5):   # v-E49: tf = candle minutes
    """
    G2A: fetch the CANDIDATE OPTION CONTRACT and build closed 5-minute
    candles for BOT_G's decision logic.

    v-G62 (this session): ROOT-CAUSE FIX, supersedes v-G61's fix as
    incomplete. Confirmed live, 23-Sep-2026, against real Zerodha 1-minute
    ground truth for the same contract (NIFTY26SEP23550CE): compared
    RMoney's 11 reported "5-minute" rejection candles directly against
    Zerodha's 1-minute bars for the same timestamps. 7 of 11 matched a
    SINGLE 1-minute bar almost exactly (within paise-level rounding); the
    remaining 4 were still far closer to one minute's range than to any
    genuine 5-bar aggregate (e.g. the 13:57 candle: RMoney reported a
    62.65-64.35 range; five real consecutive 1-minute bars from 13:57
    span 62.0-65.1 -- nowhere close).

    Conclusion: RMoney/XTS's compressionValue=5 does NOT return genuine
    5-minute aggregated candles -- it returns data that behaves like
    single-minute snapshots, mislabeled as 5-minute. v-G61 (re-bucketing
    these onto a clean 09:15-anchored grid) correctly fixed the candle-
    KEY drift that was causing instant ARM EXPIRED -- that diagnosis and
    fix stand -- but it re-anchored values that were never really
    5-minute aggregates in the first place, so confirmation checks
    (VWAP touch/close) would still have been evaluated against
    artificially narrow, over-volatile "5-minute" candles even after
    v-G61.

    Real fix: request NATIVE 1-MINUTE candles from RMoney/XTS
    (compressionValue=1 -- confirmed reliable, matches Zerodha's own
    1-minute bars almost exactly) and build GENUINE 5-minute candles by
    resampling those 1-minute bars with origin=today_open. This is the
    case that actually divides evenly (1->5), unlike the ORIGINAL 3->5
    resample problem this file's design note below was written to avoid
    -- so it does not reintroduce that risk, it produces real 5-bar
    aggregates instead of relabeled 1-minute data.

    The 3-minute DPCR path is completely separate and unaffected by this
    fix either way.
    """
    now = time.time()
    slot = _BOTG_OPT_CACHE.get(_v49_ckey(symbol, tf))   # v-E49
    if (not force_refresh and slot is not None and slot.get("df5") is not None and
            (now - slot["time5"]) < BOTG_OPT_HIST_CACHE_SEC):
        return slot["df5"]

    eid = _resolve_option_eid(symbol)
    if eid is None:
        log(f"[G2A 5M HIST ERROR] {symbol}: EID resolution failed")
        return None

    try:
        start_dt = datetime.combine(_prev_trading_day(), datetime.min.time()).replace(hour=9, minute=15)
        end_dt = datetime.now()
        fmt = "%b %d %Y %H%M%S"
        resp = _HTTP.get(
            f"{MARKETDATA_URL}/instruments/ohlc",
            headers=_md_headers(),
            params={"exchangeSegment": NIFTY_FO_SEGMENT, "exchangeInstrumentID": eid,
                    "startTime": start_dt.strftime(fmt), "endTime": end_dt.strftime(fmt),
                    "compressionValue": 1},
            timeout=10)
        if resp.status_code != 200:
            log(f"[G2A 5M HIST ERROR] {symbol}: HTTP {resp.status_code}")
            return None
        data = resp.json()
        if data.get("type") != "success":
            log(f"[G2A 5M HIST ERROR] {symbol}: {data.get('description')}")
            return None
        raw_str = data.get("result", {}).get("dataReponse", "")
        if not raw_str:
            log(f"[G2A 5M HIST ERROR] {symbol}: empty dataReponse")
            return None
        rows = _parse_ticks(raw_str)
        if not rows:
            log(f"[G2A 5M HIST ERROR] {symbol}: no 1-minute candles parsed")
            return None
    except Exception as e:
        log(f"[G2A 5M HIST ERROR] {symbol}: {e}")
        return None

    df_raw = pd.DataFrame(rows)
    df_raw["datetime"] = pd.to_datetime(df_raw["ts"], unit="s")
    df_raw = df_raw.set_index("datetime").sort_index().drop(columns=["ts"])
    df_raw = df_raw[~df_raw.index.duplicated(keep="last")]

    # v-G62: aggregate NATIVE 1-minute bars into genuine 5-minute candles,
    # anchored at session open -- same pattern as df3's resample two
    # functions away. Unlike v-G61 (which only re-anchored already-fake
    # "5-minute" values), this resample is a REAL interval conversion
    # from confirmed-accurate 1-minute data, so the resulting OHLCV
    # genuinely reflects 5 minutes of real trading, not 1.
    today_open = pd.Timestamp(datetime.now().date()) + pd.Timedelta(hours=9, minutes=15)
    df5 = df_raw.resample(f"{tf}min", origin=today_open).agg({   # v-E49
        "open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum",
    }).dropna(subset=["close"])

    # Keep today's bars only (post-aggregation, now genuine 5-minute).
    if len(df5):
        df5 = df5[df5.index.date == df5.index[-1].date()].copy()
    if len(df5) == 0:
        return None

    tp = (df5["high"] + df5["low"] + df5["close"]) / 3
    vol = df5["volume"].fillna(0)
    df5["vwap"] = (tp * vol).cumsum() / vol.cumsum().replace(0, float("nan"))

    # v-G78 (28-Sep-2026): XTS CLOSED-CANDLE LAG FIX. Every caller treats
    # df5.iloc[-2] as "latest CLOSED candle" and df5.iloc[-1] as "the one
    # forming now" -- true for Fyers (native 5m includes the forming bar),
    # but NOT here: XTS only returns a 1-minute bar once a trade prints in
    # that minute, so right after a 5-min boundary the new bucket often
    # has NO rows yet. The just-closed candle then sits at iloc[-1], is
    # skipped as "forming", and is only scanned once the next bucket's
    # first 1-min bar appears AND the 170s cache expires. Confirmed 28-Sep:
    # 13:25 22750PE rejection candle -- Fyers armed 13:30:04, RMoney only
    # at 13:32:57 (fetch at 13:30:05 had bars=51, next fetch 172s later);
    # by then the option was +9 above VWAP -> ARM EXPIRED NOT_TOUCHED,
    # a trade Fyers booked for +Rs597 was missed. Same ~2m50s lag on the
    # 13:30 candle (scanned 13:37:53).
    # Fix: once the last bucket's 5 minutes are over, append a placeholder
    # row for the CURRENT bucket (OHLC = last close, volume 0, VWAP =
    # unchanged cumulative VWAP -- exactly what a zero-volume bar gives),
    # so iloc[-2] is the just-closed candle immediately. Guard: the closed
    # candle's LAST minute (T+4) must be present, else we wait up to
    # BOTG_XTS_LAST_MIN_GRACE_SEC (an illiquid minute may never print) and
    # re-fetch every BOTG_XTS_RETRY_SEC meanwhile instead of caching 170s.
    # Only the placeholder is synthetic -- every real candle is untouched.
    _cache_time = now
    if BOTG_XTS_SYNTH_FORMING_BAR:
        _now_dt = datetime.now()
        _last_ts = df5.index[-1]
        _bucket_end = _last_ts + pd.Timedelta(minutes=tf)
        _session_open = _now_dt.hour * 60 + _now_dt.minute < 15 * 60 + 30
        if _now_dt >= _bucket_end and _last_ts.date() == _now_dt.date() and _session_open:
            _last_min_ok = df_raw.index.max() >= _last_ts + pd.Timedelta(minutes=tf - 1)
            _grace_over = _now_dt >= _bucket_end + pd.Timedelta(seconds=BOTG_XTS_LAST_MIN_GRACE_SEC)
            if _last_min_ok or _grace_over:
                _n = int((pd.Timestamp(_now_dt) - today_open).total_seconds() // (60 * tf))
                _cur_ts = today_open + pd.Timedelta(minutes=tf * _n)
                if _cur_ts > _last_ts:
                    _lc = float(df5["close"].iloc[-1])
                    _lv = df5["vwap"].iloc[-1]
                    _synth = pd.DataFrame({"open": [_lc], "high": [_lc], "low": [_lc], "close": [_lc],
                                           "volume": [0.0], "vwap": [_lv]}, index=pd.DatetimeIndex([_cur_ts]))
                    df5 = pd.concat([df5, _synth[df5.columns]])
                    _bk = _cur_ts.strftime("%H:%M")
                    if _BOTG_SYNTH_LOGGED.get(_v49_ckey(symbol, tf)) != _bk:
                        _BOTG_SYNTH_LOGGED[_v49_ckey(symbol, tf)] = _bk
                        log(f"[G2A 5M SYNTH] {symbol} | no XTS bar yet for forming {_bk} bucket -- "
                            f"placeholder added so {_last_ts.strftime('%H:%M')} is treated as CLOSED now "
                            f"(last-minute bar {'present' if _last_min_ok else 'missing, grace over'}) (v-G78)")
            else:
                _cache_time = now - BOTG_OPT_HIST_CACHE_SEC + BOTG_XTS_RETRY_SEC   # re-fetch soon

    _BOTG_OPT_CACHE[_v49_ckey(symbol, tf)] = {"time5": _cache_time, "df5": df5}
    log(f"[G2A 5M DATA] {symbol} | source=RMoney/XTS native 1-minute, resampled to {tf}-min (v-G62/v-E49) | bars={len(df5)}")
    return df5

def find_bot_g_rejection_5m(df5, bot_name="BOT_G"):
    """v-G41: identify a VWAP-near rejection candle with side-aware candle quality."""
    if df5 is None or len(df5) < 2:
        return None
    row = df5.iloc[-2]
    vwap = row.get("vwap")
    if vwap is None or pd.isna(vwap) or pd.isna(row.get("close")):
        return None

    o = float(row.get("open"))
    h = float(row.get("high"))
    l = float(row.get("low"))
    close = float(row.get("close"))
    dist = close - float(vwap)
    rejection = bool(abs(dist) <= BOTG_NEAR_VWAP_PTS)

    # Candle geometry -- calculated for every candidate so the log gives us
    # the evidence needed to calibrate vG41/vG42 from live paper data.
    body = abs(close - o)
    rng = max(0.0, h - l)
    if close < o:
        upper_shadow = max(0.0, h - o)
        lower_shadow = max(0.0, close - l)
        direction = "RED"
    elif close > o:
        upper_shadow = max(0.0, h - close)
        lower_shadow = max(0.0, o - l)
        direction = "GREEN"
    else:
        upper_shadow = max(0.0, h - close)
        lower_shadow = max(0.0, close - l)
        direction = "DOJI"
    close_location = ((close - l) / rng) if rng > 0 else 0.5

    # v-G51/v-G52: "green volume candle" research metric -- relative
    # volume vs. this SAME day's own recent 5-min candles (session-
    # scoped df5 already guarantees "today only", per
    # fetch_option_history_5m()). LOGGING ONLY -- see config comment for
    # the evidence this is based on and why it isn't a gate yet.
    #
    # v-G52: three baseline windows computed and logged (3/5/20 prior
    # candles), not just one -- we don't yet know which is most
    # predictive. The 5-candle ratio drives the actual tier below, as a
    # reasonable middle ground between the noisier 3-candle and smoother
    # 20-candle windows.
    vol = float(row.get("volume") or 0)
    def _rel_vol(n):
        baseline = df5.iloc[:-2].tail(n)
        avg = float(baseline["volume"].mean()) if len(baseline) else None
        return (vol / avg) if avg else None, avg
    rel_vol_3, baseline_vol_3 = _rel_vol(BOTG_VOLUME_BASELINE_CANDLES_SHORT)
    rel_vol_5, baseline_vol_5 = _rel_vol(BOTG_VOLUME_BASELINE_CANDLES_MID)
    rel_vol_20, baseline_vol_20 = _rel_vol(BOTG_VOLUME_BASELINE_CANDLES_LONG)
    rel_vol = rel_vol_5   # primary ratio for tier classification below

    # Level 1 -- volume strength tier
    if rel_vol is None:
        volume_tier = "UNKNOWN"
    elif rel_vol < BOTG_VOLUME_TIER_WEAK_MAX:
        volume_tier = "WEAK"
    elif rel_vol < BOTG_VOLUME_TIER_NORMAL_MAX:
        volume_tier = "NORMAL"
    elif rel_vol < BOTG_VOLUME_TIER_STRONG_MAX:
        volume_tier = "STRONG"
    else:
        volume_tier = "VERY_STRONG"
    is_high_volume = volume_tier in ("STRONG", "VERY_STRONG")

    # Level 2 -- price response (reuses the direction already computed above)
    price_response = {"GREEN": "POSITIVE", "RED": "NEGATIVE", "DOJI": "FLAT"}[direction]

    # Level 3 -- close-location tier
    if close_location >= BOTG_VOLUME_CLOSE_LOC_STRONG_MIN:
        close_loc_tier = "STRONG"
    elif close_location >= BOTG_VOLUME_CLOSE_LOC_WEAK_MAX:
        close_loc_tier = "ACCEPTABLE"
    else:
        close_loc_tier = "WEAK"

    # Combined classification. Only meaningful when volume is genuinely
    # elevated -- anything WEAK/NORMAL stays LOW_VOLUME regardless of
    # price action, since the hypothesis has nothing to say there.
    if not is_high_volume:
        volume_signal = "LOW_VOLUME"
    elif price_response == "POSITIVE" and close_loc_tier == "STRONG":
        volume_signal = "GREEN_VOLUME"
    elif price_response == "NEGATIVE" or close_loc_tier == "WEAK":
        volume_signal = "RED_VOLUME"
    else:
        volume_signal = "NEUTRAL_VOLUME"

    # v-G64: LOGGING-ONLY low-liquidity flag -- see config comment on
    # BOTG_LOW_LIQUIDITY_WARN_MAX for the full rationale. Computed from
    # the same rel_vol (=rel_vol_5) already driving VolTier/VPC above,
    # so this is a genuinely new question about the SAME metric, not a
    # new data source. Deliberately does NOT touch quality_pass,
    # quality_reason, or any other gating variable -- this can only ever
    # add a log field, never change a trading decision, until a future,
    # separate change explicitly wires it into a gate or size-scaling
    # factor once real evidence justifies it.
    low_liquidity_warning = (rel_vol is not None and rel_vol < BOTG_LOW_LIQUIDITY_WARN_MAX)

    # Side-aware setup classification.
    above_vwap = o > vwap and close > vwap
    below_vwap_reclaim = o < vwap and close > vwap
    type_a = above_vwap and close < o        # red pullback (doji excluded, v-G48 fix)
    type_b = below_vwap_reclaim

    quality_pass = rejection
    quality_reason = "VWAP_DISTANCE" if not rejection else "PASS"
    setup_type = "NONE"

    if rejection and BOTG_CANDLE_QUALITY_ENABLED:
        if type_a and BOTG_CQ_ABOVE_VWAP_RED_ENABLED:
            setup_type = "A_ABOVE_VWAP_RED_PULLBACK"
        elif type_b and BOTG_CQ_BELOW_VWAP_RECLAIM_ENABLED:
            setup_type = "B_BELOW_VWAP_RECLAIM"
        else:
            # v-G46 (bug fix): this branch used to set quality_pass=False,
            # making setup_type an active hard filter -- contradicting the
            # spec's own "Hard filter now? No" for this check. Tested
            # against 14 already-validated real trades (proper 1-minute
            # P&L): rejected 7, of which 6 were wins worth +19.07 combined
            # and only 1 was a genuine loss avoided (-3.65) -- net harmful,
            # not neutral. setup_type is still classified and logged below
            # for calibration; quality_pass no longer changes here, so the
            # ±4 VWAP-distance check remains the only thing gating arming,
            # matching original behavior and the spec's stated intent.
            setup_type = "C_OTHER_VWAP_NEAR"
    elif rejection:
        setup_type = "LEGACY_VWAP_NEAR"

    # Shadow/range hard gates remain OFF for now; warnings are diagnostic only.
    upper_warning = upper_shadow > BOTG_CQ_UPPER_SHADOW_WARN_PTS
    upper_very_large = upper_shadow > BOTG_CQ_UPPER_SHADOW_VERY_LARGE_PTS
    range_warning = rng > BOTG_CQ_RANGE_WARN_PTS
    if quality_pass and BOTG_CQ_SHADOW_HARD_FILTER_ENABLED and upper_warning:
        quality_pass = False
        quality_reason = "UPPER_SHADOW_TOO_LARGE"
    if quality_pass and BOTG_CQ_RANGE_HARD_FILTER_ENABLED and range_warning:
        quality_pass = False
        quality_reason = "RANGE_TOO_LARGE"
    # v-G52 (was v-G51's HIGH_VOL_RED): hard filter stays OFF
    # (BOTG_VOLUME_HARD_FILTER_ENABLED=False) until this has a real
    # multi-day sample -- see config comment. Wired the same way as the
    # shadow/range gates above so flipping it on later, if the evidence
    # supports it, is a one-line config change.
    if quality_pass and BOTG_VOLUME_HARD_FILTER_ENABLED and volume_signal == "RED_VOLUME":
        quality_pass = False
        quality_reason = "RED_VOLUME"

    # v-G53: "Volume-Price Confirmation" (VPC) -- a separate, independently-
    # validated gate. See config comment (BOTG_VPC_VETO_ENABLED) for the
    # full 18-trade evidence this threshold set is based on, and why it's
    # deliberately different from v-G52's tier system above.
    bear_pressure = ((o - close) / rng) if rng > 0 else 0.0   # logged always, not used in the veto itself
    vpc_condition = (
        rel_vol_5 is not None and rel_vol_5 >= BOTG_VPC_MIN_REL_VOL
        and close_location <= BOTG_VPC_MAX_CLOSE_LOCATION
        and close < o
    )
    if vpc_condition:
        vpc_state = "ADVERSE"
    elif (rel_vol_5 is not None and rel_vol_5 >= BOTG_VPC_MIN_REL_VOL
          and close_location >= (1 - BOTG_VPC_MAX_CLOSE_LOCATION) and close > o):
        vpc_state = "DEMAND"
    else:
        vpc_state = "NEUTRAL"
    vpc_veto = False
    vpc_reason = "NONE"
    if quality_pass and BOTG_VPC_VETO_ENABLED and vpc_condition:
        quality_pass = False
        quality_reason = "VPC_ADVERSE_VOLUME"
        vpc_veto = True
        vpc_reason = (f"RelVol5={round(rel_vol_5,2)}>={BOTG_VPC_MIN_REL_VOL} AND "
                       f"CloseLoc={round(close_location,2)}<={BOTG_VPC_MAX_CLOSE_LOCATION} AND "
                       f"Close<Open")

    # v-G54: VWAP penetration depth -- explicit instruction, from reviewing
    # 16-Sep's three real trades. How far the rejection candle's own low
    # sits relative to VWAP: positive means the low never reached VWAP
    # (the SL-VWAP clamp's own trigger condition, so this reuses that
    # exact boundary rather than inventing a new one); negative means the
    # low penetrated below VWAP, and how far. LOGGING ONLY -- no gate,
    # thresholds unknown, needs a real multi-day sample the same way
    # every other metric here did. Symmetric for CE and PE: this reads
    # the option's own premium/VWAP relationship, not the underlying's
    # direction, so no side-specific formula is needed. Kept identical
    # to the Fyers file.
    vwap_penetration = round(l - float(vwap), 2)
    rejection_structure = "ABOVE_VWAP" if vwap_penetration > 0 else "BELOW_VWAP"

    log(f"{bot_name} 5M CANDLE QUALITY | type={setup_type} dir={direction} "
        f"O:{o:.2f} H:{h:.2f} L:{l:.2f} C:{close:.2f} VWAP:{float(vwap):.2f} "
        f"Dist:{dist:+.2f} Body:{body:.2f} Range:{rng:.2f} "
        f"UpperW:{upper_shadow:.2f} LowerW:{lower_shadow:.2f} "
        f"CloseLoc:{close_location:.0%} Rejection:{rejection} "
        f"Pass:{quality_pass} Reason:{quality_reason} "
        f"UpperWarn:{upper_warning} RangeWarn:{range_warning} "
        f"Volume:{vol:.0f} "
        f"RelVol3:{round(rel_vol_3,2) if rel_vol_3 is not None else 'NA'} "
        f"RelVol5:{round(rel_vol_5,2) if rel_vol_5 is not None else 'NA'} "
        f"RelVol20:{round(rel_vol_20,2) if rel_vol_20 is not None else 'NA'} "
        f"VolTier:{volume_tier} PriceResp:{price_response} CloseLocTier:{close_loc_tier} "
        f"VolumeSignal:{volume_signal} LowLiquidityWarning:{low_liquidity_warning} "
        f"BearPressure:{round(bear_pressure,2)} VPCState:{vpc_state} "
        f"VPCVeto:{vpc_veto} VPCReason:{vpc_reason} "
        f"VWAPPenetration:{vwap_penetration:+.2f} Structure:{rejection_structure} (v-G52/v-G53/v-G54/v-G64)")

    return {
        "rejection": bool(quality_pass),
        "dist": round(dist, 2),
        "vwap": round(float(vwap), 2),
        "low": l,
        "close": close,
        "open": o,
        "high": h,
        "body": body,
        "range": rng,
        "upper_shadow": upper_shadow,
        "lower_shadow": lower_shadow,
        "close_location": close_location,
        "direction": direction,
        "setup_type": setup_type,
        "quality_reason": quality_reason,
        "volume": vol,                       # v-G51
        "rel_volume_3": rel_vol_3,           # v-G52
        "rel_volume_5": rel_vol_5,           # v-G52 (primary, drives volume_tier)
        "rel_volume_20": rel_vol_20,         # v-G52
        "volume_tier": volume_tier,          # v-G52
        "price_response": price_response,    # v-G52
        "close_location_tier": close_loc_tier,  # v-G52
        "volume_signal": volume_signal,      # v-G51/v-G52
        "bear_pressure": bear_pressure,      # v-G53
        "vpc_state": vpc_state,              # v-G53
        "vpc_veto": vpc_veto,                # v-G53
        "vpc_reason": vpc_reason,            # v-G53
        "vwap_penetration": vwap_penetration,      # v-G54
        "rejection_structure": rejection_structure, # v-G54
        "low_liquidity_warning": low_liquidity_warning,  # v-G64, diagnostic only
    }


def compute_bot_g_confirm_vwap_tolerance(vix_value):
    """
    v-G30 (22-Aug-2026): VIX-scaled asymmetric tolerance band for the
    confirmation candle's distance to VWAP. See the config comment on
    BOTG_CONFIRM_VWAP_LOWER_TIGHT/MID/WIDE/XWIDE for the real-trade
    evidence behind this. Same tier structure as compute_dpcr_no_trade_
    zone() / compute_bot_g_dpcr_falling_block() / compute_bot_g_flat_band().

    Returns (lower_tol, upper_tol) -- lower_tol is negative (small dip
    below VWAP still allowed), upper_tol is positive (room to confirm
    well above VWAP on a strong breakout).
    """
    if vix_value is None:
        return BOTG_CONFIRM_VWAP_LOWER_TOL, BOTG_CONFIRM_VWAP_UPPER_TOL
    if vix_value < BOTG_DPCR_ZONE_VIX_LOW_MAX:
        return BOTG_CONFIRM_VWAP_LOWER_TIGHT, BOTG_CONFIRM_VWAP_UPPER_TIGHT
    elif vix_value < BOTG_DPCR_ZONE_VIX_MID_MAX:
        return BOTG_CONFIRM_VWAP_LOWER_MID, BOTG_CONFIRM_VWAP_UPPER_MID
    elif vix_value < BOTG_DPCR_ZONE_VIX_HIGH_MAX:
        return BOTG_CONFIRM_VWAP_LOWER_WIDE, BOTG_CONFIRM_VWAP_UPPER_WIDE
    else:
        return BOTG_CONFIRM_VWAP_LOWER_XWIDE, BOTG_CONFIRM_VWAP_UPPER_XWIDE


def check_bot_g_5m_confirmation(ltp, vwap, rejection_close, vwap_touched=False, vix_value=None):
    """
    v-G20: next 5m candle must touch VWAP band, then exceed rejection close.

    v-G30 (22-Aug-2026): confirmation must ALSO land within a VIX-scaled
    asymmetric band around VWAP (compute_bot_g_confirm_vwap_tolerance) --
    filters out confirmations that are really just noise while price stays
    meaningfully below VWAP the whole window (real 20-Aug losers: -2.68 to
    -3.00 pts below VWAP at "confirmation" -- never a genuine reclaim of
    the pivot). Real winners confirmed within +0.07 to +3.54 of VWAP,
    solidly inside this band. Only checked once touched+crossed are both
    already true -- doesn't change when a candle is considered "touched".

    Returns (touched, confirmed, fail_reason). fail_reason is None when
    confirmed, else one of "NOT_TOUCHED", "BELOW_REJECTION_CLOSE",
    "OUTSIDE_VWAP_BAND" -- for logging (v-G30).
    """
    if ltp is None or vwap is None or rejection_close is None:
        return bool(vwap_touched), False, "NO_DATA"
    touched = bool(vwap_touched or abs(ltp-vwap) <= BOTG_NEAR_VWAP_PTS)
    if not touched:
        return touched, False, "NOT_TOUCHED"
    if ltp <= rejection_close:
        return touched, False, "BELOW_REJECTION_CLOSE"
    lower_tol, upper_tol = compute_bot_g_confirm_vwap_tolerance(vix_value)
    dist = ltp - vwap
    if not (lower_tol <= dist <= upper_tol):
        return touched, False, "OUTSIDE_VWAP_BAND"
    return touched, True, None


_BOTG_DPCR_HISTORY = []   # v-G8: oldest first, module-level accumulator --
                          # nothing built this before; check_bot_g_dpcr_gate()/
                          # lock_bot_g_daily_bias()/etc. all take dpcr_history
                          # as a parameter and had no source to draw from.

# v-G57: rolling buffer of total OI-delta activity (|PE|+|CE| per candle),
# used ONLY to compute magnitude_dpcr's stable denominator above -- a
# separate accumulator from _BOTG_DPCR_HISTORY, which stays signed_dpcr-
# only. Capped generously; only the last BOTG_MAGNITUDE_DPCR_BASELINE_
# CANDLES entries are ever read. Kept identical to the Fyers file.
_BOTG_TOTAL_OI_ACTIVITY_HISTORY = []

# v-G58: EMA-based activity baseline for the fourth DPCR research variant
# below (activity_weighted_dpcr) -- a separate state variable from the
# v-G57 rolling-average buffer above, since this one uses an EMA (0.80/
# 0.20) rather than a simple mean over a fixed window. Kept identical to
# the Fyers file.
_BOTG_DPCR_EMA_ACTIVITY_BASELINE = None

# v-G12: BOT_G shares _bot_g_try_entry() with BOT_G (same function, two
# different bot dicts). is_new_3m_candle(bot_name) tracks state PER bot
# name, so both bots independently see True at the same candle boundary --
# fine for their own per-bot rejection scans, but WRONG for the shared
# DPCR fetch below: gating that on the per-bot flag would fetch and append
# to _BOTG_DPCR_HISTORY twice per real candle (once per bot), corrupting
# the smoothing average (which counts appended entries, not distinct
# candles) and doubling the Fyers option-chain call. This is a SEPARATE,
# bot-agnostic gate -- only the first of the two bots to check in a given
# cycle triggers the real fetch; the second sees the candle already
# updated and just re-reads the (now-fresh) shared history.
_LAST_SHARED_DPCR_CANDLE_KEY = None

# v-G75: DPCR FLOW history -- (epoch, net_pe_doi, net_ce_doi, anchor) per
# real DPCR snapshot, oldest first. Cleared whenever the DPCR module
# re-baselines (re-anchor or restart), because the intraday nets restart
# from 0 there and a difference across that boundary would be a fake flow.
# LOG/CSV ONLY -- never read by any entry/exit decision.
_BOTG_FLOW_HISTORY = []


def _reset_flow_history(reason):
    """v-G75: drop flow history across a DPCR baseline reset."""
    if _BOTG_FLOW_HISTORY:
        _BOTG_FLOW_HISTORY.clear()
        log(f"BOT_G DPCR FLOW | RunID:{RUN_ID} history reset ({reason}) -- "
            f"no flow reading until {BOTG_FLOW_WINDOW_MIN} min of new snapshots (v-G75)")


def compute_bot_g_flow():
    """
    v-G75: change in the window's intraday net PE/CE OI over the last
    ~BOTG_FLOW_WINDOW_MIN minutes, from _BOTG_FLOW_HISTORY. Uses the
    snapshot whose age is closest to the window, accepted only if it is
    within +/-2 min of it (so a missed snapshot doesn't silently turn a
    9-min flow into a 15-min one). Returns dict(dpe, dce, minutes) or None.
    """
    if len(_BOTG_FLOW_HISTORY) < 2:
        return None
    now_t, pe_now, ce_now, _ = _BOTG_FLOW_HISTORY[-1]
    best = None
    for t, pe, ce, _a in _BOTG_FLOW_HISTORY[:-1]:
        age = (now_t - t) / 60.0
        if abs(age - BOTG_FLOW_WINDOW_MIN) <= 2.0:
            if best is None or abs(age - BOTG_FLOW_WINDOW_MIN) < abs(best[0] - BOTG_FLOW_WINDOW_MIN):
                best = (age, pe, ce)
    if best is None:
        return None
    return {"dpe": pe_now - best[1], "dce": ce_now - best[2], "minutes": round(best[0], 1)}


def classify_bot_g_flow(side, flow):
    """
    v-G75: tier of the recent flow FOR THE GIVEN TRADE SIDE (bot convention:
    DPCR = PE/CE, high -> CE lock).
      CE buy: PE OI up = support, CE OI down = support
      PE buy: PE OI down = support, CE OI up = support
    MOST  = both sides supportive
    HALF  = one side supportive, other flat
    MIXED = one supportive, one against
    NOT   = nothing supportive (flat and/or against)
    Returns (tier, net_supportive) or ("NA", None). LOG/CSV ONLY.
    """
    if flow is None or side not in ("CE", "PE"):
        return "NA", None
    s_pe = 1 if side == "CE" else -1
    s_ce = -1 if side == "CE" else 1
    pe_s = s_pe * flow["dpe"]
    ce_s = s_ce * flow["dce"]
    eps = BOTG_FLOW_FLAT_EPS
    good = (pe_s > eps) + (ce_s > eps)
    bad = (pe_s < -eps) + (ce_s < -eps)
    if good == 2:
        tier = "MOST"
    elif good == 1 and bad == 0:
        tier = "HALF"
    elif good == 1 and bad == 1:
        tier = "MIXED"
    else:
        tier = "NOT"
    return tier, pe_s + ce_s


_BOTG_LAST_DATA_TIME = [None]   # v-G85


def _snap_is_stale(snap):
    """v-G85: True if the module marked the snapshot stale, OR its option-
    chain fetch time is identical to the previous snapshot's (a cached
    chain served again). Diagnostics/flow only."""
    if snap.get("stale"):
        return True
    dt = snap.get("data_time")
    if dt is not None and dt == _BOTG_LAST_DATA_TIME[0]:
        log("BOT_G DPCR FLOW | snapshot reuses the previous option-chain fetch "
            "(data_time unchanged) -- not recorded for flow/diagnostics (v-G85)")
        return True
    _BOTG_LAST_DATA_TIME[0] = dt
    return False


# v-G81: OI / ATM diagnostics -- LOG/CSV ONLY, never read by any decision.
_BOTG_STRIKE_PREV = {}      # "ATM"/"ANCHOR" -> previous fresh reading
_BOTG_LAST_OI_DIAG = {}     # latest diagnostic, copied into the trade at entry


def _side_driver(prefix, d, eps):
    """v-G81: PUT_ADD / PUT_UNWIND / PUT_FLAT (or CALL_...)."""
    if d is None:
        return f"{prefix}_NA"
    return f"{prefix}_ADD" if d > eps else (f"{prefix}_UNWIND" if d < -eps else f"{prefix}_FLAT")


def _oi_premium_reading(d_oi, resid):
    """v-G81: OI change + spot-adjusted premium change -> likely reading.
    'Likely', not proof: every contract has a buyer and a seller."""
    if d_oi is None or resid is None:
        return "NA"
    e_oi, e_r = BOTG_ATM_OI_FLAT_EPS, BOTG_ATM_RESID_FLAT_PTS
    if d_oi > e_oi:
        return "WRITING" if resid < -e_r else ("BUYING" if resid > e_r else "OI_UP_UNCLEAR")
    if d_oi < -e_oi:
        return "SHORT_COVERING" if resid > e_r else ("LONG_UNWINDING" if resid < -e_r else "OI_DOWN_UNCLEAR")
    return "FLAT"


def _get_strike_quotes(snap, strikes):
    """v-G81 (RMoney): OI from the DPCR snapshot (window strikes); for a
    strike outside the window one extra batched OI call via the v3
    module. LTP for all requested contracts + Nifty spot in ONE batched
    get_multi_ltp() call (same 1502 quote path the bot already uses).
    Contract = the DPCR chain's expiry (nearest weekly).
    Returns (spot_or_None, {strike: {"CE": {oi, ltp}, "PE": {...}}})."""
    oi_map = {int(round(float(k))): v for k, v in (snap.get("oi_by_strike") or {}).items()}
    code = _bot_g_symbol_expiry_code(_nearest_nifty_weekly_expiry_date())
    ks = sorted({int(k) for k in strikes if k is not None})
    need = [k for k in ks if k not in oi_map]
    extra = _oc_filter.fetch_oi_for_strikes(_md_headers(), code, need) if need else {}
    syms = {(k, s): f"NIFTY{code}{k}{s}" for k in ks for s in ("CE", "PE")}
    ltp = get_multi_ltp(["NIFTY_SPOT"] + list(syms.values()))
    out = {}
    for (k, s), sym in syms.items():
        oi = (oi_map.get(k) or {}).get(s)
        if oi is None:
            oi = extra.get((k, s))
        out.setdefault(k, {})[s] = {"oi": oi, "ltp": ltp.get(sym)}
    return ltp.get("NIFTY_SPOT"), out


def _strike_block(kind, strike, q, spot_q, now_t, with_resid):
    """v-G81: one strike's reading + change vs the previous FRESH reading
    of the same kind. Change fields only when the strike is unchanged
    (status SAME) -- an ATM roll never produces a fake delta."""
    q = q or {}
    ce, pe = q.get("CE") or {}, q.get("PE") or {}
    cur = {"strike": strike, "ce_oi": ce.get("oi"), "pe_oi": pe.get("oi"),
           "ce_ltp": ce.get("ltp"), "pe_ltp": pe.get("ltp"), "spot": spot_q, "t": now_t}
    prev = _BOTG_STRIKE_PREV.get(kind)
    status = "NEW" if prev is None else ("SAME" if prev["strike"] == strike else "CHANGED")
    out = dict(cur, status=status, d_ce_oi=None, d_pe_oi=None, d_ce_ltp=None, d_pe_ltp=None,
               d_spot=None, dt_min=None, ce_resid=None, pe_resid=None,
               ce_reading="NA", pe_reading="NA")
    if status == "SAME":
        def _d(a, b):
            return (a - b) if (a is not None and b is not None) else None
        out.update(d_ce_oi=_d(cur["ce_oi"], prev["ce_oi"]), d_pe_oi=_d(cur["pe_oi"], prev["pe_oi"]),
                   d_ce_ltp=_d(cur["ce_ltp"], prev["ce_ltp"]), d_pe_ltp=_d(cur["pe_ltp"], prev["pe_ltp"]),
                   d_spot=_d(cur["spot"], prev["spot"]), dt_min=round((now_t - prev["t"]) / 60.0, 2))
        if with_resid and out["d_spot"] is not None:
            if out["d_ce_ltp"] is not None:
                out["ce_resid"] = round(out["d_ce_ltp"] - BOTG_ATM_DELTA_APPROX * out["d_spot"], 2)
            if out["d_pe_ltp"] is not None:
                out["pe_resid"] = round(out["d_pe_ltp"] + BOTG_ATM_DELTA_APPROX * out["d_spot"], 2)
            out["ce_reading"] = _oi_premium_reading(out["d_ce_oi"], out["ce_resid"])
            out["pe_reading"] = _oi_premium_reading(out["d_pe_oi"], out["pe_resid"])
    _BOTG_STRIKE_PREV[kind] = cur
    return out


def _fmt(v, nd=0):
    if v is None:
        return "NA"
    return f"{v:+.{nd}f}" if isinstance(v, (int, float)) else str(v)


def _log_oi_diag(snap, spot, signed_dpcr, raw_ratio):
    """v-G81: writes the two diagnostic lines and refreshes _BOTG_LAST_OI_DIAG."""
    global _BOTG_LAST_OI_DIAG
    if not BOTG_OI_DIAG_ENABLED:
        return
    now_t = time.time()
    abs_ce = snap.get("abs_ce_oi_window")
    abs_pe = snap.get("abs_pe_oi_window")
    abs_pcr = round(abs_pe / abs_ce, 3) if (abs_ce and abs_pe is not None) else None
    flow = compute_bot_g_flow()
    dpe_pm = dce_pm = dpe_pct = dce_pct = None
    driver = "NA"
    ce_tier = pe_tier = "NA"
    if flow and flow.get("minutes"):
        m = flow["minutes"]
        dpe_pm, dce_pm = flow["dpe"] / m, flow["dce"] / m
        dpe_pct = (100.0 * dpe_pm / abs_pe) if abs_pe else None
        dce_pct = (100.0 * dce_pm / abs_ce) if abs_ce else None
        driver = (_side_driver("PUT", flow["dpe"], BOTG_FLOW_FLAT_EPS) + "+" +
                  _side_driver("CALL", flow["dce"], BOTG_FLOW_FLAT_EPS))
        ce_tier, _ = classify_bot_g_flow("CE", flow)
        pe_tier, _ = classify_bot_g_flow("PE", flow)
    atm = int(round(spot / 50.0)) * 50 if spot else None
    anchor = snap.get("anchor", snap.get("anchor_strike"))
    anchor = int(round(float(anchor))) if anchor is not None else None
    spot_q, quotes = _get_strike_quotes(snap, [atm, anchor])
    spot_q = spot_q if spot_q else spot
    a = _strike_block("ATM", atm, quotes.get(atm), spot_q, now_t, with_resid=True)
    n = _strike_block("ANCHOR", anchor, quotes.get(anchor), spot_q, now_t, with_resid=False)
    log(f"BOT_G OI DIAG | RunID:{RUN_ID} Spot:{spot} Anchor:{anchor} "
        f"Window:{len(snap.get('window_strikes') or [])}strikes AbsCE:{_fmt(abs_ce)} AbsPE:{_fmt(abs_pe)} "
        f"AbsPCR:{abs_pcr} DPCRraw:{raw_ratio} DPCRsigned:{_fmt(signed_dpcr, 3)} | "
        f"dPE/min:{_fmt(dpe_pm)} dCE/min:{_fmt(dce_pm)} dPE%/min:{_fmt(dpe_pct, 3)} dCE%/min:{_fmt(dce_pct, 3)} "
        f"over {flow['minutes'] if flow else 'NA'}m | Driver:{driver} TierForCE:{ce_tier} TierForPE:{pe_tier} "
        f"(v-G81, log-only)")
    log(f"BOT_G ATM DIAG | RunID:{RUN_ID} SpotQ:{spot_q} ATM:{atm}({a['status']}) "
        f"CE oi:{_fmt(a['ce_oi'])} ltp:{a['ce_ltp']} dOI:{_fmt(a['d_ce_oi'])} dLTP:{_fmt(a['d_ce_ltp'], 2)} "
        f"resid:{_fmt(a['ce_resid'], 2)} {a['ce_reading']} | "
        f"PE oi:{_fmt(a['pe_oi'])} ltp:{a['pe_ltp']} dOI:{_fmt(a['d_pe_oi'])} dLTP:{_fmt(a['d_pe_ltp'], 2)} "
        f"resid:{_fmt(a['pe_resid'], 2)} {a['pe_reading']} | dSpot:{_fmt(a['d_spot'], 2)} dt:{a['dt_min'] if a['dt_min'] is not None else 'NA'}m | "
        f"ANCHOR:{anchor}({n['status']}) CE oi:{_fmt(n['ce_oi'])} ltp:{n['ce_ltp']} dOI:{_fmt(n['d_ce_oi'])} "
        f"PE oi:{_fmt(n['pe_oi'])} ltp:{n['pe_ltp']} dOI:{_fmt(n['d_pe_oi'])} "
        f"(delta~{BOTG_ATM_DELTA_APPROX}, v-G81, log-only)")
    def _r(v, nd=0):
        return round(v, nd) if isinstance(v, (int, float)) else ""
    _BOTG_LAST_OI_DIAG = {
        "t": now_t, "diag_spot": spot_q, "abs_ce_oi": _r(abs_ce), "abs_pe_oi": _r(abs_pe),
        "abs_pcr": abs_pcr if abs_pcr is not None else "",
        "flow_dpe_per_min": _r(dpe_pm), "flow_dce_per_min": _r(dce_pm),
        "flow_dpe_pct_per_min": _r(dpe_pct, 4), "flow_dce_pct_per_min": _r(dce_pct, 4),
        "driver": driver, "atm_strike": atm if atm else "", "atm_status": a["status"],
        "atm_ce_oi": _r(a["ce_oi"]), "atm_pe_oi": _r(a["pe_oi"]),
        "atm_ce_ltp": a["ce_ltp"] if a["ce_ltp"] is not None else "",
        "atm_pe_ltp": a["pe_ltp"] if a["pe_ltp"] is not None else "",
        "atm_d_ce_oi": _r(a["d_ce_oi"]), "atm_d_pe_oi": _r(a["d_pe_oi"]),
        "atm_ce_resid": _r(a["ce_resid"], 2), "atm_pe_resid": _r(a["pe_resid"], 2),
        "atm_ce_reading": a["ce_reading"], "atm_pe_reading": a["pe_reading"],
        "anchor_strike": anchor if anchor else "", "anchor_ce_oi": _r(n["ce_oi"]),
        "anchor_pe_oi": _r(n["pe_oi"]),
        "anchor_ce_ltp": n["ce_ltp"] if n["ce_ltp"] is not None else "",
        "anchor_pe_ltp": n["pe_ltp"] if n["pe_ltp"] is not None else "",
    }


def _record_flow_snapshot(pe_delta, ce_delta, anchor):
    """v-G75: append one DPCR snapshot to flow history and log the flow."""
    if (_BOTG_FLOW_HISTORY and anchor is not None
            and _BOTG_FLOW_HISTORY[-1][3] is not None and anchor != _BOTG_FLOW_HISTORY[-1][3]):
        _reset_flow_history(f"anchor {_BOTG_FLOW_HISTORY[-1][3]}->{anchor}")
    _BOTG_FLOW_HISTORY.append((time.time(), pe_delta, ce_delta, anchor))
    if len(_BOTG_FLOW_HISTORY) > 20:
        del _BOTG_FLOW_HISTORY[0]
    flow = compute_bot_g_flow()
    if flow is None:
        log(f"BOT_G DPCR FLOW | RunID:{RUN_ID} PE:{pe_delta:+.0f} CE:{ce_delta:+.0f} "
            f"Flow{BOTG_FLOW_WINDOW_MIN}m:NA (v-G75)")
        return
    ce_tier, _ = classify_bot_g_flow("CE", flow)
    pe_tier, _ = classify_bot_g_flow("PE", flow)
    log(f"BOT_G DPCR FLOW | RunID:{RUN_ID} PE:{pe_delta:+.0f} CE:{ce_delta:+.0f} "
        f"dPE{flow['minutes']}m:{flow['dpe']:+.0f} dCE{flow['minutes']}m:{flow['dce']:+.0f} "
        f"TierForCE:{ce_tier} TierForPE:{pe_tier} (v-G75, log-only)")


def _is_new_shared_dpcr_candle():
    """
    v-G48 (bug fix): removed the narrow 0<=now.second<=10 wall-clock
    window that gated this -- same fragile pattern already found and
    fixed once in is_new_bot_g_candle() (the old rejection/arm-state
    gate), but this DPCR-specific function was never touched by that
    fix. Any tick that missed the narrow window meant DPCR simply
    didn't refresh for that whole 3-minute cycle -- confirmed via
    independent review, this session. Now detects a boundary crossing
    by comparing which 3-min bucket "now" falls into against the last-
    seen bucket, which works no matter which second within that bucket
    the tick actually lands on.
    """
    global _LAST_SHARED_DPCR_CANDLE_KEY
    now = datetime.now()
    bucket = (now.hour * 60 + now.minute) // 3
    key = f"{bucket}"
    if _LAST_SHARED_DPCR_CANDLE_KEY != key:
        _LAST_SHARED_DPCR_CANDLE_KEY = key
        return True
    return False


def compute_signed_dpcr(pe_delta, ce_delta):
    """
    v-G31 (23-Aug-2026): explicit instruction, root-caused a real defect
    in the raw ratio (PE_delta/CE_delta): the same ratio value can arise
    from opposite underlying scenarios (confirmed against real Nifty/
    Sensex log data -- ~25-28% of real readings fall in a "mixed sign"
    quadrant where this matters), and the raw ratio is numerically
    unstable whenever either delta is small (confirmed: real Nifty DPCR
    swung to -554/+269 on 20-Aug-2026 from exactly this).

    Verified against 10 worked examples, all directions: "trade the
    lighter side" -- whichever of PE_delta/CE_delta is algebraically
    SMALLER is the side to trade. This signed, bounded formula reproduces
    the identical direction as today's existing CE/PE convention (no
    reversal) while fixing both defects above:

        signed_dpcr = (pe_delta - ce_delta) / (|pe_delta| + |ce_delta|)

    Naturally bounded [-1, +1] regardless of how large or small either
    delta is -- can never spike the way the raw ratio did. Positive =
    PE side heavier (CE is lighter -> CE trade, matches today's "high
    DPCR -> lock CE"). Negative = CE side heavier (PE trade). Zero when
    perfectly balanced.

    Returns None if both deltas are zero (no signal at all, not even a
    balanced reading -- caller must NOT treat this as 0.0/no-trade-zone).
    """
    denom = abs(pe_delta) + abs(ce_delta)
    if denom == 0:
        return None
    return (pe_delta - ce_delta) / denom


# v-E9 (B'): carry-forward of the DPCR score across re-anchors. LOG + decision.
_BOTG_DPCR_CARRY = {"date": None, "anchor": None, "last_pe": None, "last_ce": None,
                    "carry_pe": 0.0, "carry_ce": 0.0, "events": 0}


def _dpcr_carry_update(snap, pe_delta, ce_delta, fresh):
    """v-E9: returns (carry_pe, carry_ce) to add to the current window's
    intraday deltas. On the first fresh reading with a NEW anchor, the old
    window's last totals are added to the carry. Resets each day."""
    st = _BOTG_DPCR_CARRY
    today = date.today()
    if st["date"] != today:
        st.update(date=today, anchor=None, last_pe=None, last_ce=None,
                  carry_pe=0.0, carry_ce=0.0, events=0)
    if not BOTG_DPCR_CARRY_ENABLED:
        return 0.0, 0.0
    anchor = snap.get("anchor", snap.get("anchor_strike"))
    if fresh:   # v-E11 (was a second _snap_is_stale() call -- always True)
        if (st["anchor"] is not None and anchor is not None and anchor != st["anchor"]
                and st["last_pe"] is not None):
            st["carry_pe"] += st["last_pe"]
            st["carry_ce"] += st["last_ce"]
            st["events"] += 1
            log(f"BOT_G DPCR CARRY | RE-ANCHOR {st['anchor']} -> {anchor} | carried "
                f"PE:{st['carry_pe']:+.0f} CE:{st['carry_ce']:+.0f} (old window last "
                f"PE:{st['last_pe']:+.0f} CE:{st['last_ce']:+.0f}) (v-E9)")
        st["anchor"] = anchor
        st["last_pe"] = pe_delta
        st["last_ce"] = ce_delta
    return st["carry_pe"], st["carry_ce"]


# v-E14 (vE6): CARRIED FLOW. Flow measured on carried totals (window deltas
# + B' carry) so a re-anchor never breaks it. SEPARATE from
# _BOTG_FLOW_HISTORY (resets per anchor, still drives BOT_GE's tiers --
# unchanged). Resets daily; entries older than BOTG_CARRIED_FLOW_KEEP_MIN
# are dropped.
_BOTG_FLOW_CARRIED = {"date": None, "hist": []}


def _record_carried_flow(pe_tot, ce_tot, anchor):
    st = _BOTG_FLOW_CARRIED
    if st["date"] != date.today():
        st["date"] = date.today()
        st["hist"] = []
    now = time.time()
    st["hist"].append((now, float(pe_tot), float(ce_tot), anchor))
    cutoff = now - BOTG_CARRIED_FLOW_KEEP_MIN * 60
    st["hist"] = [x for x in st["hist"] if x[0] >= cutoff]


def _record_carried_baseline(anchor):
    """v-E14: a re-anchor's baseline reading (window nets restart at 0) is
    recorded at the old window's last carried total, so the carried series
    has no gap across the re-anchor (same assumption as B' carry). Skipped
    at the day's first baseline / after a restart (nothing to carry)."""
    c = _BOTG_DPCR_CARRY
    if not BOTG_DPCR_CARRY_ENABLED or c["date"] != date.today() or c["last_pe"] is None:
        return
    _record_carried_flow(c["carry_pe"] + c["last_pe"], c["carry_ce"] + c["last_ce"], anchor)


def compute_carried_flow(minutes):
    """v-E14: change in carried PE/CE totals over ~`minutes` (latest reading
    vs the reading whose age is nearest `minutes`, within +/-2 min -- same
    method as compute_bot_g_flow()). None (= NA) if no such reading, if the
    latest reading is older than BOTG_CARRIED_FLOW_MAX_AGE_SEC, or if carry
    is OFF and the two readings belong to different anchors."""
    st = _BOTG_FLOW_CARRIED
    h = st["hist"]
    if st["date"] != date.today() or len(h) < 2:
        return None
    now_t, pe_now, ce_now, a_now = h[-1]
    if time.time() - now_t > BOTG_CARRIED_FLOW_MAX_AGE_SEC:
        return None
    best = None
    for t, pe, ce, a in h[:-1]:
        age = (now_t - t) / 60.0
        if abs(age - minutes) <= 2.0 and (best is None or abs(age - minutes) < abs(best[0] - minutes)):
            best = (age, pe, ce, a)
    if best is None:
        return None
    if not BOTG_DPCR_CARRY_ENABLED and best[3] != a_now:
        return None
    return {"dpe": pe_now - best[1], "dce": ce_now - best[2], "minutes": round(best[0], 1)}


def _botg_entry_carried_flows():
    """v-E14: carried flow for every logged window plus the skip window."""
    out = {}
    for m in sorted(set(BOTG_CARRIED_FLOW_LOG_WINDOWS) | {BOTG_CE_CALLADD_SKIP_MIN}):
        try:
            out[m] = compute_carried_flow(m)
        except Exception as _e:
            log(f"BOT_G CARRIED FLOW | error (ignored): {_e}")
            out[m] = None
    return out


def _botg_cflow_text(flows):
    return " | ".join(
        f"{m}m " + ("NA" if f is None else f"dPE:{f['dpe']:+,.0f} dCE:{f['dce']:+,.0f}")
        for m, f in sorted(flows.items()))


def _botg_ce_calladd_check(bot, side, flows):
    """v-E15: returns (skip: bool, status: str). Main slot (BOT_G) CE only.
    Does NOT touch BOT_GE's flow-tier rule (early slot -> 'n/a early')."""
    if bot.get("early_slot"):
        return False, "n/a early"
    if side != "CE":
        return False, "n/a PE"
    if not BOTG_CE_CALLADD_SKIP_ENABLED:
        return False, "OFF"
    f = flows.get(BOTG_CE_CALLADD_SKIP_MIN)
    if f is None:
        return False, "flow NA"
    if f["dce"] > BOTG_CE_CALLADD_SKIP_THRESHOLD:
        return True, "SKIP"
    return False, "PASS"


def get_current_dpcr(spot=None, gap_day=False, dpcr_window=None):
    """
    v-G8: WIRED to option_chain_filter_nifty.compute_dpcr() -- no longer a
    stub. Uses that module's fixed-anchor DPCR (v-G-DPCR3): anchor set at
    09:16 normal day / 10:00 gap day, re-anchors on 0.75% drift from the
    most recent anchor, smoothing history resets on each re-anchor. See
    that module's FIXED-ANCHOR WINDOW block for the full spec -- nothing
    about the anchor/re-anchor logic lives here, this function only calls
    it and tracks the returned scalar for BOT_G's own history buffer.

    `gap_day` MUST be supplied by the caller once this is actually wired
    into main()'s dispatch loop -- pass the same is_gap_day value returned
    by detect_bot_g_gap_day(df3), don't recompute it here.

    v-G31 (23-Aug-2026): now computes TWO values from the same snapshot --
    the NEW signed, bounded formula (compute_signed_dpcr(), using the raw
    snap["net_pe_doi"]/snap["net_ce_doi"] deltas) is what gets appended to
    _BOTG_DPCR_HISTORY and drives every real decision (lock/veto/flip/
    falling-block). The OLD raw ratio (snap["dpcr"]) is kept SEPARATELY,
    for the dashboard chart only -- explicit instruction: the dashboard is
    a glance-value display, not a decision input, and its existing
    centered-near-1 look should not change just because the internal
    metric did. Nothing about send_botg_reading()/backend.py/dashboard_
    live.html needed to change as a result.

    Returns (signed_dpcr, raw_ratio_for_dashboard) -- both None if
    unavailable. Callers MUST treat signed_dpcr=None as "gate fails
    closed", never as "skip the check" or "treat as 0".

    v-G37 (05-Sep-2026): `dpcr_window` param added -- passed straight
    through to compute_dpcr(). Caller (_update_bot_g_dpcr_state()) supplies
    get_bot_g_dpcr_window_today()'s result; None here just falls back to
    that module's own fixed DPCR_WINDOW default.

    v-RG-FIX1 (bug fix, this session): the expiry code passed to
    compute_dpcr() now comes from _nearest_nifty_weekly_expiry_date(), NOT
    getNiftyWeeklyExpiry() -- the latter is BOT_G's own next-week traded
    contract, a different chain entirely from the front-week chain DPCR's
    OI data is supposed to read. Confirmed as a real, live discrepancy
    from the Fyers version (which gets this right for free, since Fyers'
    own option-chain fetch takes no expiry param and defaults to nearest).
    """
    if spot is None:
        log("BOT_G DPCR   | get_current_dpcr() called without spot -- cannot compute, returning None")
        return None, None

    snap = _oc_filter.compute_dpcr(_md_headers(), spot, _bot_g_symbol_expiry_code(_nearest_nifty_weekly_expiry_date()), bot_name="BOT_G", gap_day=gap_day, dpcr_window=dpcr_window,
                                   anchor_ref=_v39_anchor_ref(gap_day))   # v-E39
    # v-G75: a snapshot that came back but with dpcr=None is the DPCR
    # module's baseline reading (restart or re-anchor) -- nets restart
    # from 0, so flow history must not bridge it. snap=None (fetch failed)
    # is NOT a reset.
    if snap is not None and snap.get("dpcr") is None and not snap.get("stale"):   # v-G80
        _reset_flow_history("DPCR baseline reading")
        try:
            _record_carried_baseline(snap.get("anchor", snap.get("anchor_strike")))   # v-E14
        except Exception as _cf_err:
            log(f"BOT_G CARRIED FLOW | error (ignored): {_cf_err}")
    if snap is None or snap.get("dpcr") is None:
        return None, None

    raw_ratio = snap["dpcr"]
    pe_delta = snap.get("net_pe_doi")
    ce_delta = snap.get("net_ce_doi")
    if pe_delta is None or ce_delta is None:
        log("BOT_G DPCR   | snap missing net_pe_doi/net_ce_doi -- cannot compute signed_dpcr, returning None")
        return None, raw_ratio
    _fresh = not _snap_is_stale(snap)   # v-E11: checked ONCE per reading (has a side effect)
    if _fresh:   # v-G80/v-G85: never record a re-served snapshot
        try:
            _record_flow_snapshot(pe_delta, ce_delta,
                                  snap.get("anchor", snap.get("anchor_strike")))   # v-G75/v-G80, log-only
        except Exception as _flow_err:
            log(f"BOT_G DPCR FLOW | error (ignored, log-only): {_flow_err}")
        try:
            _log_oi_diag(snap, spot, compute_signed_dpcr(pe_delta, ce_delta), raw_ratio)   # v-G81, log-only
        except Exception as _diag_err:
            log(f"BOT_G OI DIAG | error (ignored, log-only): {_diag_err}")

    # v-E9 (B'): decision DPCR = window deltas + carry from earlier windows.
    _carry_pe, _carry_ce = _dpcr_carry_update(snap, pe_delta, ce_delta, _fresh)
    signed_dpcr = compute_signed_dpcr(pe_delta + _carry_pe, ce_delta + _carry_ce)
    if _fresh:   # v-E14: carried-flow history (never reset at a re-anchor)
        try:
            _record_carried_flow(pe_delta + _carry_pe, ce_delta + _carry_ce,
                                 snap.get("anchor", snap.get("anchor_strike")))
        except Exception as _cf_err:
            log(f"BOT_G CARRIED FLOW | error (ignored): {_cf_err}")
    if _BOTG_DPCR_CARRY["events"] > 0 and _fresh:
        _reset_val = compute_signed_dpcr(pe_delta, ce_delta)
        log(f"BOT_G DPCR CARRY | reset={'NA' if _reset_val is None else round(_reset_val, 3)} "
            f"carried={'NA' if signed_dpcr is None else round(signed_dpcr, 3)} "
            f"window PE:{pe_delta:+.0f} CE:{ce_delta:+.0f} carry PE:{_carry_pe:+.0f} CE:{_carry_ce:+.0f} "
            f"anchor:{snap.get('anchor', snap.get('anchor_strike'))} (v-E9)")
    if signed_dpcr is None:
        return None, raw_ratio

    # v-G57 (this session): third DPCR variant -- signed like signed_dpcr
    # (0=neutral, sign=CE/PE) but magnitude-preserving beyond +/-1, unlike
    # signed_dpcr's bounded formula. Deliberately NOT built the way an
    # uploaded alternative attempted this (dividing by ce_delta alone,
    # i.e. raw_ratio's own PE/CE formula) -- that's mathematically the
    # SAME instability already proven unreliable: verified directly
    # against real 17-Sep data, raw_ratio disagreed with signed_dpcr's
    # DIRECTION at 10:15 (signed said CE, raw_ratio's PE/CE ratio said
    # -1.421, i.e. not-CE) at the exact moment that decided a real trade.
    # Dividing by CE_delta alone is unstable whenever CE_delta is small,
    # which is exactly the opposite-sign scenario causing trouble.
    #
    # This version instead divides by a ROLLING AVERAGE of total OI-delta
    # activity (|PE|+|CE|) over the last N readings -- a slowly-changing
    # reference that doesn't collapse near zero on any single tick's own
    # fluke reading, so it stays both signed AND stable AND genuinely
    # unbounded (real magnitude beyond +/-1, not a saturation artifact).
    #
    # LOGGING/RESEARCH ONLY. signed_dpcr remains the sole value in
    # _BOTG_DPCR_HISTORY and the sole value any lock/veto/flip/falling-
    # block decision reads -- explicit agreement: this needs a full
    # historical replay (16-Sep, 17-Sep, and future days) before it could
    # ever be considered as a decision input, not a same-day swap. Kept
    # identical to the Fyers file.
    total_activity = abs(pe_delta) + abs(ce_delta)
    _prior_activity = list(_BOTG_TOTAL_OI_ACTIVITY_HISTORY[-BOTG_MAGNITUDE_DPCR_BASELINE_CANDLES:])
    rolling_avg_activity = (sum(_prior_activity) / len(_prior_activity)) if _prior_activity else None
    magnitude_dpcr = ((pe_delta - ce_delta) / rolling_avg_activity) if rolling_avg_activity else None
    _BOTG_TOTAL_OI_ACTIVITY_HISTORY.append(total_activity)
    if len(_BOTG_TOTAL_OI_ACTIVITY_HISTORY) > BOTG_MAGNITUDE_DPCR_BASELINE_CANDLES * 3:
        del _BOTG_TOTAL_OI_ACTIVITY_HISTORY[0]

    # v-G58: fourth DPCR research variant -- an independently-proposed EMA
    # + log-scaled alternative, found in an uploaded file that had
    # (incorrectly) made it the PRIMARY decision metric while only
    # PARTIALLY updating the codebase for its 1.0-centred convention (the
    # zone/no-trade-zone config constants were correctly co-updated, but
    # there was no historical replay validating it before deployment, and
    # no evidence the flat-band/falling-block thresholds -- delta-based,
    # so insensitive to the constant shift, but NOT necessarily to the
    # new formula's different typical change-magnitudes -- still fit).
    # Restored here as a fourth research-only candidate instead of
    # discarding the idea, alongside v-G57's own magnitude_dpcr, so both
    # can be compared against real outcomes via replay before either is
    # ever trusted with a real decision. signed_dpcr remains untouched
    # and is still the only value in _BOTG_DPCR_HISTORY. Kept identical
    # to the Fyers file.
    global _BOTG_DPCR_EMA_ACTIVITY_BASELINE
    if pe_delta - ce_delta == 0:
        activity_weighted_dpcr = 1.0
    else:
        _net = pe_delta - ce_delta
        _imbalance = abs(_net) / total_activity if total_activity > 0 else 0.0
        if _BOTG_DPCR_EMA_ACTIVITY_BASELINE is None or _BOTG_DPCR_EMA_ACTIVITY_BASELINE <= 0:
            _BOTG_DPCR_EMA_ACTIVITY_BASELINE = total_activity
        else:
            _BOTG_DPCR_EMA_ACTIVITY_BASELINE = 0.80 * _BOTG_DPCR_EMA_ACTIVITY_BASELINE + 0.20 * total_activity
        _activity_factor = math.log1p(total_activity / max(_BOTG_DPCR_EMA_ACTIVITY_BASELINE, 1.0))
        _magnitude = _imbalance * _activity_factor
        activity_weighted_dpcr = 1.0 + (_magnitude if _net > 0 else -_magnitude)

    log(f"BOT_G DPCR   | PRIMARY={signed_dpcr:+.3f}(0=neutral) RAW_RATIO={raw_ratio:+.3f}(1.0=neutral) "
        f"MagnitudeDPCR={f'{magnitude_dpcr:+.3f}' if magnitude_dpcr is not None else 'NA'}(0=neutral,v-G57) "
        f"ActivityWeightedDPCR={activity_weighted_dpcr:+.3f}(1.0=neutral,v-G58) | "
        f"PE:{pe_delta:+.0f} CE:{ce_delta:+.0f}")

    # v-G33 (23-Aug-2026): SATURATION DIAGNOSTIC. Confirmed via real paper-
    # trade log comparison (25-Aug-2026, Fyers vs RMoney Nifty side by
    # side): whenever pe_delta and ce_delta have OPPOSITE signs,
    # compute_signed_dpcr() always returns exactly +-1.0 regardless of
    # magnitude -- this is the deliberately-specified behavior (mixed-sign
    # direction is "the sign of the numerator, full stop"), not a bug, but
    # it means the zone/flat-band/falling-block apparatus built on top
    # goes completely dormant for as long as the mismatch persists (a
    # value pinned at exactly 1.0 can never show slope or cross a
    # boundary). Fyers' real Nifty session today pinned at +1.000 for
    # 45+ minutes straight with zero visibility into it from the log
    # alone. Purely diagnostic -- does not change signed_dpcr, does not
    # touch _BOTG_DPCR_HISTORY, does not affect any decision.
    if (pe_delta > 0) != (ce_delta > 0) and pe_delta != 0 and ce_delta != 0:
        log(f"BOT_G DPCR   | SATURATED at {signed_dpcr:+.1f} -- opposite-sign "
            f"deltas (PE:{pe_delta:+.0f} CE:{ce_delta:+.0f}) -- magnitude info "
            f"lost until signs realign (v-G33) | "
            f"MagnitudeDPCR:{f'{magnitude_dpcr:+.3f}' if magnitude_dpcr is not None else 'NA'} "
            f"(0=neutral, unbounded, research-only, v-G57) | "
            f"ActivityWeightedDPCR:{activity_weighted_dpcr:+.3f} "
            f"(1.0=neutral, unbounded, research-only, v-G58)")

    _BOTG_DPCR_HISTORY.append(signed_dpcr)
    if len(_BOTG_DPCR_HISTORY) > BOTG_DPCR_HISTORY_MAX:
        _BOTG_DPCR_HISTORY.pop(0)
    return signed_dpcr, raw_ratio


def get_bot_g_dpcr_history():
    """v-G8: returns the accumulated DPCR history (oldest first) built up by
    get_current_dpcr() -- this is what should be passed as the dpcr_history
    argument to check_bot_g_dpcr_gate(), lock_bot_g_daily_bias(),
    check_bot_g_locked_side_veto(), and log_bot_g_open_position_dpcr()."""
    return list(_BOTG_DPCR_HISTORY)




# =============================================================================
#  SECTION 5 — DPCR DAILY DIRECTION BIAS  (v-G7)
#     LOG-ONLY. Supersedes check_bot_g_dpcr_gate()'s role (that function is
#     left in place, unused by the flow below, same rollback convention) --
#     the earlier version re-decided CE-vs-PE on every check; this version
#     locks ONE side, once, for the whole day, then only ever vetoes or
#     permits entries on that locked side. Also logs DPCR/slope continuously
#     for any OPEN BOT_G position, per explicit instruction -- NO exit
#     action taken on a DPCR reversal; that mechanism is deliberately not
#     built yet ("we will see later").
# =============================================================================

def detect_bot_g_gap_day(df3, bot_name="BOT_G"):
    """
    v-G7: REAL (explicit instruction) -- gap defined on NIFTY SPOT itself,
    reusing the SAME df3 already fetched by fetch_data() for BOT_A-F (2
    days of history, per _get_historical_nifty_safe()) -- no new data
    source or API call needed.

    Gap % = today's first candle's open vs yesterday's last candle's
    close, abs value, >= BOTG_GAP_THRESHOLD_PCT (1.0%) either direction.

    Returns (is_gap_day: bool, gap_pct: float or None). None only if df3
    doesn't yet span two distinct trading dates (e.g. very first session
    ever run, or a data gap) -- caller should treat that as "cannot
    determine gap status" and fail toward the NORMAL-day window rather
    than silently guessing.
    """
    if df3 is None or len(df3) == 0:
        return False, None
    dates = df3.index.normalize().unique()
    if len(dates) < 2:
        log(f"{bot_name} GAP CHECK | Insufficient history (<2 sessions in df3) — "
            "cannot determine gap status, defaulting to NORMAL-day window (v-G9)")
        return False, None

    today = dates[-1]
    yesterday = dates[-2]
    today_open = df3[df3.index.normalize() == today]["open"].iloc[0]
    yesterday_close = df3[df3.index.normalize() == yesterday]["close"].iloc[-1]
    if yesterday_close == 0 or pd.isna(yesterday_close) or pd.isna(today_open):
        return False, None

    gap_pct = (today_open - yesterday_close) / yesterday_close * 100.0
    is_gap = abs(gap_pct) >= BOTG_GAP_THRESHOLD_PCT
    log(f"{bot_name} GAP CHECK | YesterdayClose:{round(yesterday_close,2)} "
        f"TodayOpen:{round(today_open,2)} Gap:{round(gap_pct,2)}% "
        f"Threshold:{BOTG_GAP_THRESHOLD_PCT}% -> "
        f"{'GAP DAY' if is_gap else 'NORMAL DAY'} (v-G9)")
    # v-G9-FIX6: today_open/yesterday_close come from .iloc[] on a pandas
    # Series, so they're numpy scalars -- gap_pct ends up numpy.float64
    # (harmless, it subclasses Python's float) but is_gap ends up
    # numpy.bool_ (NOT a subclass of Python's bool). That crashed
    # save_state()'s json.dump() the first time it ran after bot["gap_day"]
    # was set, since gap_day was added to PERSIST_KEYS this same session.
    # Cast both explicitly to native types before they ever reach a bot
    # dict field.
    return bool(is_gap), float(round(gap_pct, 2))


def get_bot_g_windows(is_gap_day, trade_start_override_normal=None, trade_start_override_gap=None):
    """v-G7: REAL. Returns (watch_start_hhmm, trade_start_hhmm) — the
    watch window exists purely to build enough DPCR history for the slope
    check by the time trade_start arrives; no lock/trade decision is made
    before trade_start regardless of what DPCR has already done.

    v-G15: trade_start_override_normal/gap added -- BOT_G starts trading
    later than BOT_G (11:00 normal / 13:00 gap vs BOT_G's 10:30/12:30),
    explicit instruction. watch_start stays the SAME for both bots
    regardless of override -- the watch window only builds DPCR history,
    which is shared between both bots anyway (single anchor), so there's
    no reason to delay watching just because a bot trades later."""
    if is_gap_day:
        trade_start = trade_start_override_gap if trade_start_override_gap is not None else BOTG_TRADE_START_GAP_HHMM
        return BOTG_WATCH_START_GAP_HHMM, trade_start
    trade_start = trade_start_override_normal if trade_start_override_normal is not None else BOTG_TRADE_START_NORMAL_HHMM
    return BOTG_WATCH_START_NORMAL_HHMM, trade_start


def lock_bot_g_strike_pool(bot_name, profile):
    """
    v-G37 (05-Sep-2026): REPLACES lock_bot_g_vix_regime(). Explicit
    instruction (04/05-Sep-2026 session) -- BOT_G now watches a POOL of 3
    strikes per VIX band instead of locking onto one single OTM depth
    (motivation: real paper-trade setups were being missed when the one
    locked strike's own VWAP-distance check failed even though DPCR/slope
    were favorable). Also folds in the new 2-slab VIX-linked quantity
    table, which REPLACES the old VIX>=18 half-qty rule entirely.

    profile shape: {"vix_thresholds": [t1, t2], "pools": [[...],[...],[...]],
    "qty_vix_threshold": X, "qty_low_vix": Y, "qty_high_vix": Z}.
    len(pools) must be len(vix_thresholds)+1. Bands (confirmed explicitly,
    not a placeholder convention this time -- both cutoffs are upper-bound
    inclusive):
      VIX <= vix_thresholds[0]                     -> pools[0]
      vix_thresholds[0] < VIX <= vix_thresholds[1]  -> pools[1]
      VIX >  vix_thresholds[-1]                     -> pools[-1]
      VIX <= qty_vix_threshold -> qty_low_vix, else qty_high_vix

    Deliberately does its OWN fetch_india_vix() call rather than reusing
    the shared _VIX_VALUE/_VIX_FETCH_HHMM cache -- same reasoning as the
    function this replaces: that cache's first fetch is scheduled at
    09:20, later than BOT_G's own 09:16 anchor/10:15 trade-start, so
    waiting for it would either run this lock stale-or-empty or force an
    awkward deferral for no principled reason.

    Returns (pool, qty_base, vix_value) -- pool is a LIST of otm_steps
    values (0=ATM), not a single int. On fetch failure, falls back to the
    DEEPEST pool tier and the smaller (high-VIX) qty -- fails toward the
    more conservative regime rather than guessing, same principle as the
    function it replaces.
    """
    vix_value = fetch_india_vix()
    if vix_value is None:
        fallback_pool = profile["pools"][-1]
        log(f"{bot_name} VIX LOCK | fetch_india_vix() failed -- falling back to "
            f"pool {fallback_pool} / high-VIX qty (v-G37)")
        return fallback_pool, profile["qty_high_vix"], None

    pool = profile["pools"][-1]
    for i, threshold in enumerate(profile["vix_thresholds"]):
        if vix_value <= threshold:
            pool = profile["pools"][i]
            break

    qty_base = (profile["qty_low_vix"] if vix_value <= profile["qty_vix_threshold"]
                else profile["qty_high_vix"])

    log(f"{bot_name} VIX LOCK | VIX:{vix_value} -> pool:{pool}, "
        f"qty_base:{qty_base} ({qty_base // LOT_SIZE} lots) (v-G37)")
    return pool, qty_base, vix_value

def _fresh_pool_strike_state():
    """
    v-G37: blank per-strike rejection-arm/confirm state -- one instance of
    this lives in bot["pool_state"] for every strike currently in the
    VIX-selected pool. Same fields the old single-strike scalar version
    had (rejection_armed/low/vwap/close/vwap_touched/symbol/candle_key),
    plus the two confirm-diagnostics fields, now duplicated per strike
    instead of living directly on the bot dict.

    v-G49 (superseded by v-G50's redesign -- see _BOTG_LAST_SCANNED_
    CANDLE_BY_SYMBOL below): originally added a preserve_scan_key param
    here to survive a reset. That fixed the entry-confirmed/entry-abort
    case but not strike-shift -- confirmed live, 11-Sep: OTM2 flickered
    23450CE -> 23400CE -> 23450CE within two minutes (ATM computation
    landing differently tick to tick), and the strike-shift reset (which
    the v-G49 preserve didn't cover, reasoning a symbol change always
    means fresh history) wiped the scan memory anyway when it flickered
    BACK to a symbol it had just held. Scan memory now lives keyed by
    SYMBOL, in a module-level dict, completely decoupled from this
    per-OTM-slot state -- so it's naturally immune to every reset here,
    caused by anything, while still correctly starting fresh for any
    symbol genuinely never seen before. No parameter needed anymore.
    Kept identical to the Fyers file.
    """
    return {
        "rejection_armed":       False,
        "rejection_low":         None,
        "rejection_vwap":        None,
        "rejection_close":       None,
        "rejection_vwap_touched": False,
        "rejection_symbol":      None,
        "rejection_candle_key":  None,
        "_botg_last_confirm_fail_reason": None,
        "_botg_last_confirm_dist":        None,
        "confirm_window_running_low": None,   # v-G50: reset fresh for every new arm
    }

_BOTG_LAST_SCANNED_CANDLE_BY_SYMBOL = {}   # symbol -> candle key of its last-scanned rejection candle

def _sync_bot_g_pool_state(bot, pool):
    """
    v-G37: called every time bot["otm_pool"] is (re)locked -- both the
    bot's own trade_start lock and the 14:00 relock. Creates a fresh state
    slot for any pool member that's new this lock, and DROPS (fully
    resets/removes) any existing slot for a strike that just fell out of
    the pool -- same principle as the pre-existing single-strike "ARM
    DROPPED | ATM shifted" behavior, just applied per pool member instead
    of to one shared scalar. Explicit instruction (05-Sep-2026 session):
    an armed-but-unconfirmed strike that drops out of the pool at relock
    gets its arm dropped, not carried through.

    Keys are strings (str(otm_val)), not the raw int -- JSON round-trips
    dict keys through strings on save/load, so keying this way from the
    start avoids an int/str mismatch after a same-day restart (nothing
    else in PERSIST_KEYS/save_state()/load_state() does type coercion on
    restore, so matching that existing plain-copy convention here too).
    """
    if bot.get("pool_state") is None:
        bot["pool_state"] = {}
    for otm_val in pool:
        key = str(otm_val)
        if key not in bot["pool_state"]:
            bot["pool_state"][key] = _fresh_pool_strike_state()
    pool_keys = {str(v) for v in pool}
    for key in list(bot["pool_state"].keys()):
        if key not in pool_keys:
            dropped = bot["pool_state"][key]
            if dropped.get("rejection_armed"):
                log(f"{bot['name']} ARM DROPPED | OTM{key} left the VIX pool at relock (v-G37)")
            del bot["pool_state"][key]

def get_bot_g_dpcr_window_today():
    """
    v-G37 (05-Sep-2026): plain calendar-weekday lookup into
    BOTG_DPCR_WINDOW_BY_WEEKDAY, computed fresh each call (cheap -- one
    dict lookup, no API call) rather than locked/cached, since weekday
    can't change mid-session anyway.

    Deliberately independent of _next_nifty_weekly_expiry_date() / BOT_G's
    own contract-roll logic -- that function always skips to NEXT week's
    contract (avoids trading the expiring week's own elevated theta/gamma
    risk), which is a completely different concept from this. This window
    is about DPCR's OI data, which comes from whatever chain Fyers returns
    by default for a bare optionchain() call with no expiry param -- the
    NEAREST/front-week chain, confirmed via fetch_option_chain() in
    option_chain_filter_nifty.py. So "days to expiry" here means days to
    the imminent Tuesday, not days to whatever BOT_G itself is holding.
    """
    weekday = date.today().weekday()   # Mon=0 ... Sun=6
    return BOTG_DPCR_WINDOW_BY_WEEKDAY.get(weekday, BOTG_DPCR_WINDOW_DEFAULT)


def compute_dpcr_no_trade_zone(vix_value):
    """
    v-G28 (20-Aug-2026): 4-tier VIX-scaled DPCR no-trade zone (supersedes
    the v-G24 3-tier version). Reasoning unchanged: in calm markets (low
    VIX), OI repositioning is naturally smaller, so even a modest DPCR
    deviation from 1.0 is more likely a genuine signal relative to that
    day's quiet baseline -- tighter zone. In volatile markets (high VIX),
    OI shifts are naturally larger/noisier, so the same small deviation
    is more likely noise -- wider zone, requiring a more decisive reading
    before trusting it.

    All thresholds and bands come from config (BOTG_DPCR_ZONE_VIX_*_MAX,
    BOTG_DPCR_ZONE_TIGHT/MID/WIDE/XWIDE) -- nothing hardcoded here.

    vix_value=None (fetch failed) falls back to the original fixed
    BOTG_DPCR_NO_TRADE_LOW/HIGH constants -- same fail-toward-the-known-
    default philosophy as lock_bot_g_vix_regime()'s own fallback.

    UNVALIDATED against real trade outcomes -- this is a plausible
    hypothesis given VIX's relationship to OI-shift magnitude, not
    something backtested the way BOTG_CONSISTENCY_MIN_PCT or the SL cap
    were. Worth watching real days under this rule before trusting it as
    strongly as those.
    """
    if vix_value is None:
        return BOTG_DPCR_NO_TRADE_LOW, BOTG_DPCR_NO_TRADE_HIGH
    if vix_value < BOTG_DPCR_ZONE_VIX_LOW_MAX:
        return BOTG_DPCR_ZONE_TIGHT
    elif vix_value < BOTG_DPCR_ZONE_VIX_MID_MAX:
        return BOTG_DPCR_ZONE_MID
    elif vix_value < BOTG_DPCR_ZONE_VIX_HIGH_MAX:
        return BOTG_DPCR_ZONE_WIDE
    else:
        return BOTG_DPCR_ZONE_XWIDE


def compute_dpcr_raw_ratio_no_trade_zone(vix_value):
    """
    v-G47 (this session): explicit instruction -- parallel VIX-scaled
    no-trade zone for raw_ratio (the OLD, centered-at-1.0 DPCR metric).
    DISPLAY/LOG ONLY -- mirrors compute_dpcr_no_trade_zone() exactly
    (same VIX tiers, same half-widths), just re-centered on 1.0. Does
    NOT drive any decision; nothing calls this for gating, only for the
    log line alongside the real signed_dpcr zone.
    """
    if vix_value is None:
        return BOTG_DPCR_RAW_NO_TRADE_LOW, BOTG_DPCR_RAW_NO_TRADE_HIGH
    if vix_value < BOTG_DPCR_ZONE_VIX_LOW_MAX:
        return BOTG_DPCR_RAW_ZONE_TIGHT
    elif vix_value < BOTG_DPCR_ZONE_VIX_MID_MAX:
        return BOTG_DPCR_RAW_ZONE_MID
    elif vix_value < BOTG_DPCR_ZONE_VIX_HIGH_MAX:
        return BOTG_DPCR_RAW_ZONE_WIDE
    else:
        return BOTG_DPCR_RAW_ZONE_XWIDE


def compute_bot_g_dpcr_falling_block(dpcr_history, vix_value, locked_side=None):
    """
    v-G28 (20-Aug-2026): early-warning gate for NEW entries only. Compares
    the latest DPCR reading to BOTG_DPCR_LOOKBACK_CANDLES back (same
    lookback as compute_bot_g_dpcr_slope()), but against a tighter,
    VIX-scaled threshold (BOTG_DPCR_FALLING_THRESH_*) rather than the
    coarser BOTG_DPCR_FLAT_BAND used for the lock/flip decision. This is
    deliberately more sensitive: a move too small to justify flipping the
    daily lock can still be a real early signal worth pausing fresh
    entries over.

    Direction-agnostic on purpose -- a "falling" DPCR move is treated as
    an early warning regardless of which side is currently locked, since
    it's an early signal of a POSSIBLE direction change either way (CE->PE
    or PE->CE), not specific to the current lock.

    Does NOT affect any already-open position -- callers must only use
    this to gate NEW entries (arming a rejection candle or confirming an
    already-armed one). An open position keeps running via its own
    SL/BE/TSL/partial-booking machinery regardless of this signal; see
    log_bot_g_open_position_dpcr() for the log-only in-trade watch.

    Returns (blocked: bool, change: float or None). change is the same
    signed delta compute_bot_g_dpcr_slope() would report (negative =
    falling); None only when there isn't enough history yet.
    """
    if not dpcr_history or len(dpcr_history) < BOTG_DPCR_LOOKBACK_CANDLES + 1:
        return False, None
    current  = dpcr_history[-1]
    lookback = dpcr_history[-(BOTG_DPCR_LOOKBACK_CANDLES + 1)]
    change = current - lookback

    if vix_value is None:
        threshold = BOTG_DPCR_FALLING_THRESH_WIDE   # mid-of-the-road fallback
    elif vix_value < BOTG_DPCR_ZONE_VIX_LOW_MAX:
        threshold = BOTG_DPCR_FALLING_THRESH_TIGHT
    elif vix_value < BOTG_DPCR_ZONE_VIX_MID_MAX:
        threshold = BOTG_DPCR_FALLING_THRESH_MID
    elif vix_value < BOTG_DPCR_ZONE_VIX_HIGH_MAX:
        threshold = BOTG_DPCR_FALLING_THRESH_WIDE
    else:
        threshold = BOTG_DPCR_FALLING_THRESH_XWIDE

    # v-G72: side-aware -- block on a move AGAINST the locked side only.
    # Signed DPCR: + = CE side, - = PE side. With no lock yet (None) or
    # the flag off, behaves exactly as v1 (falling-only).
    if BOTG_DPCR_FALLING_BLOCK_SIDE_AWARE and locked_side == "PE":
        return (change >= threshold), round(change, 3)
    return (change <= -threshold), round(change, 3)


def compute_bot_g_flat_band(vix_value):
    """
    v-G27 (21-Aug-2026): VIX-scaled flat-band for compute_bot_g_dpcr_slope().
    See the config comment on BOTG_DPCR_FLAT_BAND_TIGHT/MID/WIDE/XWIDE for
    the reasoning (must stay below each tier's own zone half-width or the
    veto's early-warning becomes dead weight). Same tier structure as
    compute_dpcr_no_trade_zone() / compute_bot_g_dpcr_falling_block().

    vix_value=None falls back to BOTG_DPCR_FLAT_BAND (the mid-of-the-road
    default), same fail-toward-known-default philosophy used elsewhere.
    """
    if vix_value is None:
        return BOTG_DPCR_FLAT_BAND
    if vix_value < BOTG_DPCR_ZONE_VIX_LOW_MAX:
        return BOTG_DPCR_FLAT_BAND_TIGHT
    elif vix_value < BOTG_DPCR_ZONE_VIX_MID_MAX:
        return BOTG_DPCR_FLAT_BAND_MID
    elif vix_value < BOTG_DPCR_ZONE_VIX_HIGH_MAX:
        return BOTG_DPCR_FLAT_BAND_WIDE
    else:
        return BOTG_DPCR_FLAT_BAND_XWIDE


def compute_bot_g_dpcr_slope(dpcr_history, vix_value=None):
    """
    v-G7: Shared slope calc — used both by the daily-lock decision and the
    per-entry veto below, and also by the in-trade reversal LOGGING.
    Compares the latest reading to BOTG_DPCR_LOOKBACK_CANDLES back.

    v-G27 (21-Aug-2026): flat-band is now VIX-scaled via
    compute_bot_g_flat_band(vix_value) instead of a single fixed constant
    -- callers should pass the bot's current vix_value where they have
    one; omitting it falls back to the old fixed BOTG_DPCR_FLAT_BAND.

    Returns (slope: 'rising'/'falling'/'flat'/None, current, change).
    None only when there isn't yet enough history — caller must treat
    that as "cannot judge direction yet," not as flat.
    """
    if not dpcr_history or len(dpcr_history) < BOTG_DPCR_LOOKBACK_CANDLES + 1:
        return None, None, None
    current  = dpcr_history[-1]
    lookback = dpcr_history[-(BOTG_DPCR_LOOKBACK_CANDLES + 1)]
    change = current - lookback
    flat_band = compute_bot_g_flat_band(vix_value)
    if abs(change) <= flat_band:
        slope = "flat"
    elif change > 0:
        slope = "rising"
    else:
        slope = "falling"
    return slope, current, round(change, 3)


def lock_bot_g_daily_bias(dpcr_history, now_hhmm, trade_start_hhmm, already_locked=None,
                           bot_name="BOT_G", no_trade_low=None, no_trade_high=None,
                           vix_value=None, raw_ratio=None):
    """
    v-G7: REAL. Called once per DPCR update from trade_start_hhmm onward
    (never before — the watch window before that exists only to seed
    dpcr_history for the slope calc, see get_bot_g_windows()).

    v-G25 (18-Aug-2026): REVISED from a PERMANENT once-per-day lock to a
    continuously re-evaluated one, explicit instruction -- direction can
    now flip CE->PE->CE etc. as many times as DPCR genuinely re-qualifies
    a NEW side, not just decide once and hold all day. A flip requires a
    genuine fresh crossing in the OPPOSITE direction (same threshold+slope
    condition as the original lock, just re-checked every cycle instead
    of only when nothing was locked yet) -- since the CE-qualifying and
    PE-qualifying zones sit on opposite sides of the no-trade band with
    no overlap, DPCR's own continuous value cannot jump from one to the
    other without genuinely passing through the no-trade zone first, so
    the "must traverse the zone" sequence happens naturally, not from any
    extra state tracked here.

    STICKY in between crossings, not reset to None: while DPCR sits in
    the no-trade zone (or is outside it but with the "wrong" slope for a
    fresh cross), the existing already_locked label is preserved as-is
    rather than dropped -- check_bot_g_locked_side_veto() already
    correctly PAUSES new entries during this window regardless of what
    the label says, so there's no safety reason to blank it, and keeping
    the old label makes the dashboard/log read as "CE, paused" rather
    than confusingly flipping to "no side" and back.

    An open trade is COMPLETELY UNAFFECTED by any flip that happens while
    it's running -- locked_side is only ever read inside THIS function's
    own call chain (_bot_g_try_entry(), which only runs while the bot is
    FLAT); _bot_g_manage() never references it. So a position always
    still runs its own SL/BE/partial/TSL to natural completion regardless
    of what DPCR does in the background; the flip only affects what gets
    considered once the bot is flat again.

    v-G12: bot_name added purely for log labeling -- BOT_G and BOT_G each
    call this independently against the SAME shared dpcr_history, so they
    will always reach the identical decision; bot_name just makes clear
    whose cycle produced this particular log line.

    v-G24: no_trade_low/high passed in explicitly (defaulting to the fixed
    BOTG_DPCR_NO_TRADE_LOW/HIGH if omitted) -- caller passes the bot's own
    current VIX-scaled zone (bot["dpcr_no_trade_low"/"high"]).

    Returns the (possibly unchanged, possibly flipped) lock state:
    'CE' / 'PE' / None.
    """
    if no_trade_low is None:
        no_trade_low = BOTG_DPCR_NO_TRADE_LOW
    if no_trade_high is None:
        no_trade_high = BOTG_DPCR_NO_TRADE_HIGH

    # v-G47 (this session): raw_ratio (the OLD, centered-at-1.0 DPCR
    # metric) + its own parallel VIX-scaled zone, added to every log line
    # below purely for readability. DISPLAY ONLY -- raw_ratio plays no
    # part in any comparison or decision in this function; every actual
    # lock/flip check below still runs entirely on signed_dpcr (`current`)
    # against no_trade_low/no_trade_high, unchanged.
    if raw_ratio is not None:
        _raw_low, _raw_high = compute_dpcr_raw_ratio_no_trade_zone(vix_value)
        _raw_suffix = f" | raw_ratio={round(raw_ratio,3)} raw_zone=[{_raw_low},{_raw_high}]"
    else:
        _raw_suffix = ""

    if now_hhmm < trade_start_hhmm:
        return None

    slope, current, change = compute_bot_g_dpcr_slope(dpcr_history, vix_value=vix_value)
    if slope is None:
        log(f"{bot_name} DAILY BIAS | now={now_hhmm} insufficient DPCR history yet — "
            f"cannot lock (v-G9){_raw_suffix}")
        return already_locked

    if current >= no_trade_high and slope in ("rising", "flat"):
        if already_locked != "CE":
            _flip_note = f" <-- FLIP from {already_locked}" if already_locked else ""
            log(f"{bot_name} DAILY BIAS | LOCKED CE | DPCR={round(current,3)} "
                f"slope={slope} (change={change} over "
                f"{BOTG_DPCR_LOOKBACK_CANDLES} candles) zone=[{no_trade_low},{no_trade_high}] "
                f"at now={now_hhmm}{_flip_note}{_raw_suffix} (v-G25)")
        return "CE"
    if current <= no_trade_low and slope in ("falling", "flat"):
        if already_locked != "PE":
            _flip_note = f" <-- FLIP from {already_locked}" if already_locked else ""
            log(f"{bot_name} DAILY BIAS | LOCKED PE | DPCR={round(current,3)} "
                f"slope={slope} (change={change} over "
                f"{BOTG_DPCR_LOOKBACK_CANDLES} candles) zone=[{no_trade_low},{no_trade_high}] "
                f"at now={now_hhmm}{_flip_note}{_raw_suffix} (v-G25)")
        return "PE"

    # v-G25: no fresh crossing -- preserve the existing label (sticky), not
    # reset to None. check_bot_g_locked_side_veto() still correctly pauses
    # new entries whenever DPCR is genuinely back in the no-trade zone,
    # independent of what this label says.
    if already_locked in ("CE", "PE"):
        return already_locked

    log(f"{bot_name} DAILY BIAS | not yet locked | DPCR={round(current,3)} "
        f"slope={slope} now={now_hhmm} zone=[{no_trade_low},{no_trade_high}] — "
        f"waiting for a valid zone-clearing crossing{_raw_suffix} (v-G25)")
    return None


def check_bot_g_locked_side_veto(locked_side, dpcr_history, bot_name="BOT_G",
                                  no_trade_low=None, no_trade_high=None,
                                  vix_value=None):
    """
    v-G7: REAL. This is the ONLY thing that can PAUSE new entries on the
    currently-locked side -- direction pointing back toward the no-trade
    zone. Deliberately narrower than lock_bot_g_daily_bias(): this
    function never decides or flips the side itself (never re-evaluates
    CE-vs-PE), it only says whether the CURRENT side is safe to act on
    right now.

    v-G12: bot_name added purely for log labeling (see lock_bot_g_daily_bias).

    v-G24 (18-Aug-2026): no_trade_low/high now passed in explicitly
    (defaulting to the fixed BOTG_DPCR_NO_TRADE_LOW/HIGH if omitted) -- a
    2pm VIX-driven zone change takes effect here immediately, every
    cycle, e.g. if VIX rose enough to widen the zone at 14:00, a DPCR
    reading that would have paused entries under the old tighter zone
    might now pass under the new wider one, or vice versa.

    v-G25: since lock_bot_g_daily_bias() can now flip the locked side
    itself (CE<->PE), this function's own pause logic is what runs
    DURING the transition -- while DPCR sits in the no-trade zone between
    an old crossing and a fresh opposite one, this correctly returns
    False regardless of which side's label is still showing.

    Returns (allowed: bool, reason: str).
    """
    if no_trade_low is None:
        no_trade_low = BOTG_DPCR_NO_TRADE_LOW
    if no_trade_high is None:
        no_trade_high = BOTG_DPCR_NO_TRADE_HIGH
    if locked_side not in ("CE", "PE"):
        return False, "NO_SIDE_LOCKED"

    slope, current, change = compute_bot_g_dpcr_slope(dpcr_history, vix_value=vix_value)
    if slope is None:
        return False, "DPCR_UNAVAILABLE"

    if no_trade_low <= current <= no_trade_high:
        log(f"{bot_name} ENTRY VETO | side={locked_side} DPCR={round(current,3)} "
            f"back in no-trade zone [{no_trade_low},{no_trade_high}] -> "
            f"PAUSED, not un-locked (v-G24)")
        return False, "DPCR_IN_NO_TRADE_ZONE"

    if locked_side == "CE":
        allowed = slope in ("rising", "flat")
        reason = "" if allowed else "DPCR_REVERSING_TOWARD_ZONE"
        _dist_past_boundary = current - no_trade_high
    else:
        allowed = slope in ("falling", "flat")
        reason = "" if allowed else "DPCR_REVERSING_TOWARD_ZONE"
        _dist_past_boundary = no_trade_low - current

    # v-G54: explicit instruction, from reviewing 16-Sep Trade 3 (DPCR
    # 0.183, just 0.003 past the +0.18 boundary -- technically ALLOW, but
    # about as marginal as a crossing can be). Scaled to the zone's own
    # half-width (not an absolute points value) so this stays meaningful
    # across VIX regimes, since the zone itself widens with VIX. LOGGING
    # ONLY -- no gate, no extra confirmation requirement yet; needs a
    # real multi-day sample the same way every other metric here did.
    # Kept identical to the Fyers file.
    _half_width = (no_trade_high - no_trade_low) / 2.0
    _boundary_strength_pct = (_dist_past_boundary / _half_width) if _half_width > 0 else None
    if _boundary_strength_pct is None:
        dpcr_boundary_strength = "UNKNOWN"
    elif _boundary_strength_pct < 0.10:
        dpcr_boundary_strength = "EDGE"
    elif _boundary_strength_pct < 0.50:
        dpcr_boundary_strength = "MODERATE"
    else:
        dpcr_boundary_strength = "STRONG"

    log(f"{bot_name} ENTRY VETO | side={locked_side} DPCR={round(current,3)} "
        f"slope={slope} (change={change}) -> "
        f"{'ALLOW' if allowed else 'VETO'} {reason} "
        f"BoundaryStrength:{dpcr_boundary_strength}({round(_boundary_strength_pct*100,1) if _boundary_strength_pct is not None else 'NA'}%) "
        f"(v-G9/v-G54)")
    return allowed, reason


def log_bot_g_open_position_dpcr(position_side, dpcr_history, bot_name="BOT_G", vix_value=None):
    """
    v-G7: LOG-ONLY, per explicit instruction — "DPCR reversal we will see
    later, I want the log file to log/display information." NO exit or
    tightening action is taken here, on purpose — this is observation
    only, to build a real record of how reversal signals relate to actual
    price turns before any exit mechanism gets designed.

    Call this on every DPCR update while a BOT_G position is open.
    """
    slope, current, change = compute_bot_g_dpcr_slope(dpcr_history, vix_value=vix_value)
    if slope is None:
        log(f"{bot_name} DPCR IN-TRADE | position={position_side} "
            f"insufficient DPCR history to judge slope yet")
        return

    against_position = (
        (position_side == "CE" and slope == "falling") or
        (position_side == "PE" and slope == "rising")
    )
    log(f"{bot_name} DPCR IN-TRADE | position={position_side} DPCR={round(current,3)} "
        f"slope={slope} (change={change} over "
        f"{BOTG_DPCR_LOOKBACK_CANDLES} candles)"
        + (f"  *** REVERSAL WATCH: slope against open {position_side} "
           f"position — NO ACTION TAKEN, log-only ***" if against_position else ""))


def compute_bot_g_initial_sl(entry, rejection_candle_low, rejection_vwap=None):
    """
    v-G6: REAL. Initial SL = the rejection candle's own Low -- a real
    defended support level, not a further-back close (that approach broke
    down: for a declining-into-VWAP setup it can sit ABOVE entry, unusable
    for a long). No cap applied -- see config comment, flagged not approved.

    v-G39 (this session): explicit instruction -- if the rejection candle's
    own low sits ABOVE its VWAP (meaning the candle never actually reached
    VWAP before "rejecting"), the SL is widened to rejection_vwap -
    BOTG_SL_VWAP_BUFFER instead of using that low directly. This only ever
    widens the stop (never tightens it) and only in the specific case where
    the raw SL wouldn't have let the trade test its own support thesis.
    `rejection_vwap=None` (the historical default, e.g. any other caller)
    skips this clamp entirely and behaves exactly as before. Kept identical
    to the Fyers file's copy of this function.

    v-G41 (this session): DISABLED by default (BOTG_SL_VWAP_CLAMP_ENABLED
    =False) -- see config comment for the full evidence history (net
    negative across the 3 days of data now available, including one live
    day). Mechanism left fully in place, just gated off, so it can be
    re-enabled cleanly once there's a larger sample to trust.
    """
    # v-G71: continuous version -- SL = min(rej_low, VWAP - buffer). The v1
    # rule (clamp only when rej_low > VWAP) gave a TIGHTER stop to a low
    # just below VWAP than to a low just above it; see config comment.
    if BOTG_SL_VWAP_CLAMP_ENABLED and rejection_vwap is not None:
        if BOTG_SL_VWAP_CLAMP_CONTINUOUS:
            return min(rejection_candle_low, rejection_vwap - BOTG_SL_VWAP_BUFFER)
        if rejection_candle_low > rejection_vwap:
            return rejection_vwap - BOTG_SL_VWAP_BUFFER
    return rejection_candle_low


def _botg_targets(bot, entry, risk_pts):
    """v-E4: (P1, P2) target prices for this bot -- per-bot override if the
    bot dict has one (BOT_GE), else the config default (BOT_G = v3.2)."""
    b = bot or {}
    p1 = entry + max(b.get("p1_r_mult", BOTG_PARTIAL_R1_MULT) * risk_pts,
                     b.get("p1_pct_floor", BOTG_PARTIAL_R1_PCT_FLOOR) * entry)
    p2 = entry + max(b.get("p2_r_mult", BOTG_PARTIAL_R15_MULT) * risk_pts,
                     b.get("p2_pct_floor", BOTG_PARTIAL_R15_PCT_FLOOR) * entry)
    return p1, p2


def _botg_tsl_buffer(bot):
    """v-E4: trailing buffer in points. BOT_G: BOTG_TSL_BUFFER_PTS (8).
    BOT_GE: max(min_pts, min(max_pts, k x risk_pts))."""
    if bot.get("tsl_buffer_mode") == "R":
        r = bot.get("risk_pts") or 0.0
        return max(bot["tsl_buffer_min_pts"], min(bot["tsl_buffer_max_pts"], bot["tsl_buffer_r"] * r))
    return BOTG_TSL_BUFFER_PTS


def _botg_flip_against(bot):
    """v-E2: DPCR-flip condition (checked only while below BE).
    BOT_G: daily lock now points the other way (unchanged v3.2 rule).
    BOT_GE (no lock): latest signed DPCR has the opposite sign to the trade."""
    if bot.get("early_slot"):
        h = get_bot_g_dpcr_history()
        if not h:
            return False
        sd = h[-1]
        return (bot["side"] == "CE" and sd < 0) or (bot["side"] == "PE" and sd > 0)
    return bot["locked_side"] is not None and bot["locked_side"] != bot["side"]


def _botge_entry_side(bot, now_hhmm, trade_start_hhmm):
    """v-E1: early-slot direction for THIS tick, or None (no early trade).
    Called on every tick while flat, so it gates both arming and
    confirmation. Resets the strike pool if the side changes."""
    if bot.get("gap_day"):
        if not bot.get("_ge_gap_logged"):
            log(f"{bot['name']} EARLY SLOT | gap day -- early slot inactive today (vE4)")
            bot["_ge_gap_logged"] = True
        return None
    if now_hhmm < trade_start_hhmm or now_hhmm >= BOTGE_ENTRY_END_HHMM:
        return None
    h = get_bot_g_dpcr_history()
    if not h:
        return None
    sd = h[-1]
    side = "CE" if sd > 0 else ("PE" if sd < 0 else None)
    flow = compute_bot_g_flow()
    tier = classify_bot_g_flow(side, flow)[0] if side else "NA"
    ok = side is not None and tier in BOTGE_ALLOWED_TIERS
    key = (round(sd, 3), side, tier, ok)
    if key != bot.get("_ge_last_dir_key"):
        log(f"{bot['name']} DIRECTION | DPCRsigned:{sd:+.3f} -> side:{side} flowTier:{tier} "
            f"-> {'ALLOW ' + side if ok else 'NO EARLY TRADE'} (vE4)")
        bot["_ge_last_dir_key"] = key
    if not ok:
        return None
    if bot.get("_ge_side") != side:
        if bot.get("_ge_side") is not None and bot.get("pool_state"):
            for ov in (bot.get("otm_pool") or []):
                bot["pool_state"][str(ov)] = _fresh_pool_strike_state()
            log(f"{bot['name']} DIRECTION | side changed {bot.get('_ge_side')} -> {side}: pool arms reset (vE4)")
        bot["_ge_side"] = side
    return side


def _tick_ceil(x):
    t = BOTG_STOP_TICK
    return round(math.ceil(round(x / t, 6)) * t, 2)


def _tick_floor(x):
    t = BOTG_STOP_TICK
    return round(math.floor(round(x / t, 6)) * t, 2)


def apply_bot_g_stop_band(entry, chart_sl):
    """v-E16 (vE6): BOT_G AND BOT_GE, CE and PE. Defined order:
      1. chart stop (compute_bot_g_initial_sl) -> distance = entry - chart_sl
      2. distance held to [BOTG_STOP_MIN_PCT, BOTG_STOP_MAX_PCT] x entry
      3. separate hard limit BOTG_STOP_HARD_MAX_PTS (always applied, wins
         over the 3% floor too)
      4. SL rounded to BOTG_STOP_TICK -- up when capping, down when widening,
         so the rounding never breaks the band
      5. caller computes R, BE, TSL arm, P1/P2 from the returned SL.
    Returns (sl, reason) with reason "STOP CAPPED", "STOP CAPPED (hard
    limit)", "STOP WIDENED" or "" (unchanged)."""
    hard = BOTG_STOP_HARD_MAX_PTS
    hi = BOTG_STOP_MAX_PCT * entry if BOTG_STOP_BAND_ENABLED else float("inf")
    lo = BOTG_STOP_MIN_PCT * entry if BOTG_STOP_BAND_ENABLED else 0.0
    cap = min(hi, hard)
    lo = min(lo, cap)
    dist = entry - chart_sl
    if dist > cap:
        sl = _tick_ceil(entry - cap)
        reason = "STOP CAPPED (hard limit)" if hard < hi else "STOP CAPPED"
    elif dist < lo:
        sl = _tick_floor(entry - lo)
        if entry - sl > cap + 1e-9:          # floor rounding never beyond cap/hard
            sl = _tick_ceil(entry - cap)
        reason = "STOP WIDENED"
    else:
        sl, reason = chart_sl, ""
    if entry - sl > hard + 1e-9:             # final hard-limit guarantee
        sl, reason = _tick_ceil(entry - hard), "STOP CAPPED (hard limit)"
    if sl >= entry:                          # pathological tiny premium
        sl = round(entry - BOTG_STOP_TICK, 2)
    return sl, reason


def compute_bot_g_levels(entry, initial_sl, bot=None):
    """v-G6: REAL. Returns (risk_pts, breakeven_level, tsl_arm_level) from
    entry and the initial SL computed above. Risk is in POINTS, not %,
    consistent with BOTG_NEAR_VWAP_PTS/BOTG_TSL_BUFFER_PTS."""
    risk_pts = entry - initial_sl
    b = bot or {}   # v-E4: per-bot override, else config default
    be_level  = entry + b.get("be_r_mult", BOTG_BE_R_MULT) * risk_pts
    arm_level = entry + b.get("tsl_arm_r_mult", BOTG_TSL_ARM_R_MULT) * risk_pts
    return risk_pts, be_level, arm_level


def manage_bot_g_exit(bot_g_state, ltp, high_since_last_check=None):
    """
    v-G6: LOG-ONLY exit state machine -- mirrors the shape of manage() /
    apply_breakeven() / apply_trailing_sl() used by BOT_A-F, but kept fully
    separate (does not call or alter those functions) since BOT_G is not
    wired into BOTS[] or main()'s dispatch.

    bot_g_state: dict with keys entry, initial_sl, risk_pts, be_level,
    arm_level, active_sl, stage ("INITIAL"/"BREAKEVEN"/"TRAILING"),
    highest_close_since_arm, armed (bool). Caller owns this dict (mirrors
    the live `bot` dicts in BOTS[] for A-F, but a parallel, independent one).

    high_since_last_check: optional -- if driving this off ticks, pass the
    highest ltp seen since the last call so TSL arming isn't missed between
    checks (same intent as manage()'s per-tick high tracking).

    Returns (exit_now: bool, reason: str) -- caller is responsible for
    actually logging/recording the exit; this function only decides.
    """
    s = bot_g_state
    check_high = high_since_last_check if high_since_last_check is not None else ltp

    if ltp <= s["active_sl"]:
        reason = ("TSL_EXIT" if s["stage"] == "TRAILING" else
                   "BREAKEVEN_EXIT" if s["stage"] == "BREAKEVEN" else "SL_EXIT")
        return True, reason

    if s["stage"] != "TRAILING" and check_high >= s["be_level"] and s["active_sl"] < s["entry"]:
        s["active_sl"] = s["entry"]
        s["stage"] = "BREAKEVEN"

    # v-E17 (vE6): optional CE profit lock -- OFF by default (config).
    if (BOTG_CE_PROFIT_LOCK_ENABLED and s.get("side") == "CE" and s["stage"] != "TRAILING"
            and s.get("risk_pts") and not (BOTG_CE_PROFIT_LOCK_MAIN_ONLY and s.get("early_slot"))):
        _lock = _tick_floor(s["entry"] + BOTG_CE_LOCK_LEVEL_R * s["risk_pts"])
        if check_high >= s["entry"] + BOTG_CE_LOCK_TRIGGER_R * s["risk_pts"] and s["active_sl"] < _lock:
            s["active_sl"] = _lock
            s["stage"] = "BREAKEVEN"
            log(f"{s.get('name', 'BOT_G')} CE PROFIT LOCK | high {check_high} >= +{BOTG_CE_LOCK_TRIGGER_R}R -> "
                f"SL {_lock} (entry+{BOTG_CE_LOCK_LEVEL_R}R) (v-E17)")

    if check_high >= s["arm_level"]:
        s["armed"] = True

    if s["armed"]:
        if ltp > s["highest_close_since_arm"]:
            s["highest_close_since_arm"] = ltp
        new_sl = s["highest_close_since_arm"] - _botg_tsl_buffer(s)   # v-E4
        if new_sl > s["active_sl"]:
            s["active_sl"] = new_sl
            s["stage"] = "TRAILING"
            if ltp <= s["active_sl"]:
                return True, "TSL_EXIT"

    return False, ""


def check_bot_g_partial_booking(bot, ltp, check_high):
    """
    G6/G7: Two-stage hybrid profit booking. Targets use the larger of the
    R-based target and the premium-percentage floor, while SL/BE/TSL remain
    fully R-based.

      Stage 1 @ max(entry + 1R, entry + 5%) -> book 50% of qty_base
      Stage 2 @ max(entry + 1.5R, entry + 7.5%) -> book 25% of qty_base

    Both fractions are of the ORIGINAL qty_base (not whatever qty remains
    at each stage), so together they book 75% of the position, leaving
    25% to trail via the EXISTING BE(0.75R)/TSL(1.5R-arm, 8pt buffer)
    machinery in manage_bot_g_exit() -- unchanged, still runs on whatever
    qty remains after this function does its own booking.

    v-G16 (13-Aug-2026): qty_base is NOT guaranteed a clean multiple of 4
    anymore now that the base lot count can go as low as 1 (explicit
    instruction: "minimum lot size should be 1 lot in any case"). Both
    stages now round to the NEAREST lot, floor at 1 lot minimum whenever
    qty still remains, and cap at whatever's actually left -- e.g. at a
    2-lot base, Stage 1 books 1 lot, Stage 2 also floors up to 1 lot, and
    together that's the ENTIRE position: nothing left to trail. That's a
    real, expected consequence of the 1-lot floor at small base sizes, not
    a bug -- flagged here so it isn't mistaken for one later.

    Mutates `bot` in place (qty, partial1_done/partial2_done,
    partial1_booked_qty/partial2_booked_qty). Reuses log_partial_trade()
    for the trade-CSV row and running PnL, same as A-F's own partial
    booking, for consistency -- note its own log line hardcodes "Locked
    50%" regardless of actual fraction; the BOT_G-specific log line right
    after states the real fraction/stage correctly.

    Called from _bot_g_manage() BEFORE manage_bot_g_exit() each cycle, so
    a full-exit decision in the same cycle sees the already-reduced qty.

    Returns True if the position was FULLY closed by partial booking
    alone (qty hit zero) -- caller MUST skip manage_bot_g_exit() and the
    rest of its own exit handling in that case; the trade is already
    closed and trade_open is already False by the time this returns.
    """
    if bot["risk_pts"] <= 0:
        return False  # degenerate/inverted-risk entry -- shouldn't reach here
                       # post-v-G9-FIX7 (that fix aborts the entry itself),
                       # this is a defensive no-op only

    def _lot_safe_qty(target_qty, remaining_qty):
        """v-G16: round to nearest lot, floor at 1 lot if anything remains,
        never book more than what's actually left."""
        if remaining_qty <= 0:
            return 0
        lots = max(round(target_qty / LOT_SIZE), 1)
        return min(lots * LOT_SIZE, remaining_qty)

    def _close_fully_via_partial(reason_suffix):
        """v-G16: partial booking consumed the ENTIRE position -- close the
        trade properly here rather than letting manage_bot_g_exit() run on
        a phantom zero-qty position afterward (which would silently block
        any new entry for the rest of the day, since trade_open would
        never flip back to False)."""
        cancel_broker_sl_order(bot)
        log(f"{bot['name']} PARTIAL | Position fully closed via partial booking "
            f"alone ({reason_suffix}) -- nothing left to trail (v-G16)")
        tg(f"{bot['name']} FULLY CLOSED via partial booking ({reason_suffix})\n"
           f"No remainder left to trail.")
        _close_bot(bot, cooldown=0)
        bot["stage"] = "INITIAL"
        bot["armed"] = False
        bot["_botg_last_broker_sl"] = None
        bot["partial1_done"] = False
        bot["partial2_done"] = False

    # v-RG-FIX3: profit targets are independent of R so a very small
    # rejection-candle risk does not create unrealistically tiny profit
    # targets. Risk-based BE/TSL remain unchanged in compute_bot_g_levels()/
    # manage_bot_g_exit(). Now pulls BOTG_PARTIAL_R1_PCT_FLOOR/BOTG_PARTIAL_
    # R15_PCT_FLOOR straight from config (already a plain fraction of entry,
    # e.g. 0.05 = 5%) instead of the bot-file-local G4_PARTIAL_1_PCT/
    # G4_PARTIAL_2_PCT (which needed a /100 conversion) -- matches the
    # Fyers file's formula exactly, same numeric result, one shared source.
    r1_level, r15_level = _botg_targets(bot, bot["entry"], bot["risk_pts"])   # v-E4

    if not bot["partial1_done"] and check_high >= r1_level:
        book_qty = _lot_safe_qty(bot["qty_base"] * BOTG_PARTIAL_R1_FRACTION, bot["qty"])
        fill_price, filled_qty = _execute_partial_sell(bot, book_qty)
        if filled_qty <= 0:
            raise RuntimeError("Stage 1 partial exit returned zero verified fill")
        book_qty = min(book_qty, int(filled_qty))
        bot["partial1_done"]       = True
        bot["partial1_booked_qty"] = book_qty
        bot["qty"] -= book_qty
        log_partial_trade(bot, bot["side"], bot["entry"], fill_price if fill_price is not None else r1_level, book_qty, "BOTG_PARTIAL_R1")
        _r1_via = "%floor" if bot.get("p1_pct_floor", BOTG_PARTIAL_R1_PCT_FLOOR) * bot["entry"] > bot.get("p1_r_mult", BOTG_PARTIAL_R1_MULT) * bot["risk_pts"] else "1R"
        log(f"{bot['name']} PARTIAL | Stage 1 ({_r1_via}={round(r1_level,2)}): booked "
            f"{book_qty} qty ({book_qty // LOT_SIZE} lots) -- "
            f"Remaining:{bot['qty']} ({bot['qty'] // LOT_SIZE} lots) (v-G16)")
        tg(f"{bot['name']} PARTIAL BOOK ({_r1_via})\nBooked {book_qty // LOT_SIZE} lot(s) "
           f"@ {round(r1_level,1)}\nRemaining {bot['qty'] // LOT_SIZE} lot(s) running")
        if bot["qty"] <= 0:
            _close_fully_via_partial("Stage 1")
            return True
        update_broker_sl_order(bot, bot["active_sl"])

    if not bot["partial2_done"] and check_high >= r15_level:
        book_qty = _lot_safe_qty(bot["qty_base"] * BOTG_PARTIAL_R15_FRACTION, bot["qty"])
        fill_price, filled_qty = _execute_partial_sell(bot, book_qty)
        if filled_qty <= 0:
            raise RuntimeError("Stage 2 partial exit returned zero verified fill")
        book_qty = min(book_qty, int(filled_qty))
        bot["partial2_done"]       = True
        bot["partial2_booked_qty"] = book_qty
        bot["qty"] -= book_qty
        log_partial_trade(bot, bot["side"], bot["entry"], fill_price if fill_price is not None else r15_level, book_qty, "BOTG_PARTIAL_R15")
        _r15_via = "%floor" if bot.get("p2_pct_floor", BOTG_PARTIAL_R15_PCT_FLOOR) * bot["entry"] > bot.get("p2_r_mult", BOTG_PARTIAL_R15_MULT) * bot["risk_pts"] else "1.5R"
        log(f"{bot['name']} PARTIAL | Stage 2 ({_r15_via}={round(r15_level,2)}): booked "
            f"{book_qty} qty ({book_qty // LOT_SIZE} lots) -- "
            f"Remaining:{bot['qty']} ({bot['qty'] // LOT_SIZE} lots) (v-G16)")
        tg(f"{bot['name']} PARTIAL BOOK ({_r15_via})\nBooked {book_qty // LOT_SIZE} lot(s) "
           f"@ {round(r15_level,1)}\nRemaining {bot['qty'] // LOT_SIZE} lot(s) running")
        if bot["qty"] <= 0:
            _close_fully_via_partial("Stage 2")
            return True
        update_broker_sl_order(bot, bot["active_sl"])

    return False


# =============================================================================
#  SECTION 6 — MAIN-LOOP DISPATCH  (v-G9)
#     FULL PAPER-TRADE WIRING -- no longer log-only. Called directly from
#     main()'s per-bot loop (bypasses signal()/manage()/get_option_symbol()
#     entirely -- see the BOTS[] comment on BOT_G's own dict for why).
#     Reuses execute_entry()/log_trade()/register_entry()/register_exit()/
#     _close_bot()/allow_trade()/force_exit() -- all already generic across
#     bot dicts -- so state persistence, the trade CSV, dashboard, circuit
#     breaker, profit-lock, and force-exit-at-1510 all apply to BOT_G
#     automatically. Deliberately does NOT use can_enter() -- see the
#     v-G9-FIX5 comment in _bot_g_try_entry() for why.
# =============================================================================

def bot_g_tick(bot, df3, spot, ltp_map, stale, now):
    """v-G9: single entry point called once per main-loop cycle for BOT_G."""
    if bot["trade_open"]:
        _bot_g_manage(bot, spot, ltp_map, stale, now)
    else:
        _bot_g_try_entry(bot, df3, spot, stale, now)


def _bot_g_manage(bot, spot, ltp_map, stale, now):
    """
    v-G9: manages an open BOT_G position using manage_bot_g_exit(). `bot`
    itself is passed AS the state dict (bot_g_state) -- it already carries
    every key that function expects (entry, initial_sl, risk_pts, be_level,
    arm_level, active_sl, stage, highest_close_since_arm, armed), added to
    BOT_DEFAULTS specifically so no separate parallel dict is needed here.

    v-G28 (20-Aug-2026): now also calls _update_bot_g_dpcr_state() so the
    daily lock keeps evolving during an open trade (previously frozen
    while in a position, by the original v-G7 design). This lets a DPCR
    flip against the open position force an early exit -- but ONLY while
    still below breakeven (stage == "INITIAL"); a position already at/
    above breakeven keeps running via its own BE/TSL/partial booking
    exactly as before, untouched by the flip.
    """
    if stale:
        return

    ltp = ltp_map.get(bot.get("entry_symbol"), 0)

    now_hhmm = hhmm()
    _update_bot_g_dpcr_state(bot, spot, now_hhmm)

    # v-G7: log-only in-trade DPCR reversal watch -- still no exit action
    # taken here directly; the actual (limited) flip-driven exit is the
    # explicit BOTG_FLIP_FORCE_EXIT_BELOW_BE check below, not this log line.
    log_bot_g_open_position_dpcr(bot["side"], get_bot_g_dpcr_history(),
                                  bot_name=bot["name"], vix_value=bot.get("vix_value"))

    if ltp <= 0:
        return   # no fresh quote this cycle -- wait for the next one, same
                 # fail-soft behavior as the generic manage() path for A-F
    _v36_safe(lambda: _v36_tick(bot, ltp))   # v-E36 exit what-if, log-only

    bot["highest"] = max(bot["highest"], ltp)
    bot["_last_ltp"] = ltp; bot["_last_ltp_hhmm"] = hhmm()   # v-E21
    # v-G59: per-trade peak-unrealized tracker (LOGGING ONLY). Uses current
    # remaining qty at each tick, matching how SESSION_PEAK_PNL computes
    # unrealized elsewhere -- so a trade that has already taken a partial
    # reports peak unrealized on its remaining size, not the original.
    # Kept identical to the Fyers file.
    _current_unrealized = (ltp - bot["entry"]) * bot["qty"]
    bot["peak_unrealized_pnl"] = max(bot.get("peak_unrealized_pnl", 0.0), _current_unrealized)
    try:
        _track_post_entry(bot, ltp)   # v-G83, log/CSV only
        _path_record(bot, ltp)        # v-G84, log only
    except Exception:
        pass

    # v-G28: DPCR flip force-exit -- checked BEFORE partial booking / the
    # normal SL-BE-TSL machinery, since it's a higher-priority override.
    # Only fires while still below breakeven (stage == "INITIAL"); at/
    # above breakeven, this condition is simply never checked again for
    # the rest of the trade -- BE/TSL/partial booking alone govern it,
    # exactly as before v-G28.
    if (BOTG_FLIP_FORCE_EXIT_BELOW_BE and bot["stage"] == "INITIAL"
            and _botg_flip_against(bot)):   # v-E2 (BOT_G: same lock rule as v3.2)
        exit_now, reason = True, "DPCR_FLIP_EXIT"
    # v-G30: theta-decay time cap -- an option-BUYING position that's
    # still below breakeven after this many minutes hasn't shown real
    # progress, and every extra minute is theta working against it for no
    # compensating gain. Only applies while stage == "INITIAL" (matches
    # "no SL or target hit yet" exactly) -- once BE arms or a partial
    # books, this check is never evaluated again for the rest of the
    # trade; BE/TSL/partial booking alone govern it from there.
    elif (bot["stage"] == "INITIAL" and bot.get("entry_epoch")
            and (time.time() - bot["entry_epoch"]) >= bot.get("max_hold_min", BOTG_MAX_HOLD_MINUTES_INITIAL) * 60):   # v-E4
        exit_now, reason = True, "THETA_DECAY_EXIT"
    # v-G11: partial booking runs BEFORE the full-exit decision each cycle,
    # so if it reduces bot["qty"] this same cycle, manage_bot_g_exit() (and
    # the final log_trade() below, if it also exits this cycle) both see
    # the already-reduced qty -- the remaining 25% tranche, not the
    # original position.
    # v-G16: check_bot_g_partial_booking() can now fully close the trade by
    # itself (small base sizes + the 1-lot floor can consume 100% across
    # both stages) -- if it returns True, the trade is ALREADY closed and
    # trade_open is already False, so nothing below should run this cycle.
    elif check_bot_g_partial_booking(bot, ltp, bot["highest"]):
        return
    else:
        exit_now, reason = manage_bot_g_exit(bot, ltp, high_since_last_check=bot["highest"])

    if bot["active_sl"] and bot["active_sl"] != bot.get("_botg_last_broker_sl"):
        update_broker_sl_order(bot, bot["active_sl"])
        bot["_botg_last_broker_sl"] = bot["active_sl"]

    if exit_now:
        cancel_broker_sl_order(bot)
        # G4.1: in PAPER mode, a stop-triggered exit is assumed filled at the
        # actual stop level. This avoids artificial gap-through losses caused
        # by recording a later polling LTP (e.g. BE 111.95 -> observed 111.15).
        exit_price = ltp
        if PAPER_TRADE and G4_PAPER_STOP_AT_TRIGGER and reason in ("SL_EXIT", "BREAKEVEN_EXIT", "TSL_EXIT"):
            stop_level = bot.get("active_sl")
            if stop_level is not None and stop_level > 0:
                exit_price = float(stop_level)
                log(f"PAPER STOP FILL | {bot['name']} {reason} TriggerLTP:{round(ltp,2)} "
                    f"Stop:{round(exit_price,2)} -> using stop level for paper fill (G4.1)")
        pnl_preview = round((exit_price - bot["entry"]) * bot["qty"], 0)
        tg(f"EXIT {bot['name']} {bot['side']}\n"
           f"Entry: {bot['entry']}  Exit: {round(exit_price,1)}\n"
           f"PnL: Rs{pnl_preview}\nReason: {reason}")
        if log_trade(bot, bot["side"], bot["entry"], exit_price, reason, bot["qty"]):
            _close_bot(bot, cooldown=0)
            bot["stage"] = "INITIAL"
            bot["armed"] = False
            bot["_botg_last_broker_sl"] = None
            # v-G11: reset partial-booking state so the next trade starts clean
            bot["partial1_done"]       = False
            bot["partial2_done"]       = False
            bot["partial1_booked_qty"] = 0
            bot["partial2_booked_qty"] = 0
        return

    if now - bot.get("last_main_print", 0) >= 60:
        pnl_pts = ltp - bot["entry"]
        log(f"LIVE         | {bot['name']} {bot['side']} Qty:{bot['qty']} Symbol:{bot.get('entry_symbol','?')} "
            f"Entry:{bot['entry']} LTP:{round(ltp,2)} Stage:{bot['stage']} "
            f"ActiveSL:{round(bot['active_sl'],2)} "
            f"OpenPnL:Rs{round(pnl_pts * bot['qty'],2)}")
        bot["last_main_print"] = now


def _update_bot_g_dpcr_state(bot, spot, now_hhmm):
    """
    v-G28 (20-Aug-2026): shared DPCR/VIX-lock updater, called from BOTH
    _bot_g_try_entry() (while flat) and _bot_g_manage() (while a position
    is open) so the daily direction lock keeps evolving even during a
    trade -- needed so _bot_g_manage() can detect a DPCR flip against an
    open position (see BOTG_FLIP_FORCE_EXIT_BELOW_BE). Before v-G28, this
    logic only ran while flat, by design (v-G7: "position always runs to
    natural completion") -- that design is now conditional on the
    flip/still-below-breakeven rule, not absolute.

    Mutates bot["otm_pool"/"pool_state"/"qty_base"/"vix_value"/
    "dpcr_no_trade_low"/"dpcr_no_trade_high"/"vix_locked_open"/
    "vix_locked_2pm"/"locked_side"/"_botg_veto_ok"/"_botg_falling_blocked"/
    "_botg_dpcr_change"] in place.

    Returns (watch_start_hhmm, trade_start_hhmm) so callers that need
    them (currently just _bot_g_try_entry()) don't have to recompute
    get_bot_g_windows() a second time.
    """
    gap_day = bot.get("gap_day") or False
    watch_start_hhmm, trade_start_hhmm = get_bot_g_windows(
        gap_day,
        trade_start_override_normal=bot.get("trade_start_override_normal"),
        trade_start_override_gap=bot.get("trade_start_override_gap"),
    )

    # v-G24 (18-Aug-2026): VIX-based strike-pool/qty AND the DPCR no-trade
    # zone width lock TWICE per day, not once -- first at the bot's own
    # trade_start, again at 14:00, so both can react to a real intraday
    # VIX move rather than being stuck on whatever VIX read at market
    # open all day. v-G37: "New trade should have new strikes" now means
    # the 2pm relock can swap in a genuinely different 3-strike pool, not
    # just one depth -- _sync_bot_g_pool_state() drops any arm on a strike
    # that falls out of the new pool, same principle as the old single-
    # strike "ARM DROPPED | ATM shifted" behavior.
    if not bot["vix_locked_open"] and now_hhmm >= trade_start_hhmm:
        pool, qty_base, vix_value = lock_bot_g_strike_pool(bot["name"], bot["vix_profile"])
        bot["otm_pool"]   = pool
        _sync_bot_g_pool_state(bot, pool)
        bot["qty_base"]   = qty_base
        bot["vix_value"]  = vix_value
        bot["dpcr_no_trade_low"], bot["dpcr_no_trade_high"] = compute_dpcr_no_trade_zone(vix_value)
        bot["vix_locked_open"] = True
        log(f"{bot['name']} VIX LOCK (OPEN) | zone now "
            f"[{bot['dpcr_no_trade_low']},{bot['dpcr_no_trade_high']}] (v-G24)")
        # v-E53 (vE6.13): VIX gate, decided once per day at the OPEN lock
        bot["v53_gate_vix"] = vix_value
        bot["v53_gate_block"] = bool(BOTG_VIX_GATE_ENABLED and not bot.get("early_slot")
                                     and vix_value is not None and float(vix_value) <= BOTG_VIX_GATE_MAX)
        if BOTG_VIX_GATE_ENABLED and not bot.get("early_slot"):
            if vix_value is None:
                log(f"{bot['name']} VIX GATE | VIX unavailable at the open lock -> gate OPEN (v-E53)")
            else:
                log(f"{bot['name']} VIX GATE | VIX {float(vix_value):.2f} "
                    f"{'<=' if bot['v53_gate_block'] else '>'} {BOTG_VIX_GATE_MAX} -> "
                    f"{'NO new entries today' if bot['v53_gate_block'] else 'trading allowed'} (v-E53)")

    if not bot["vix_locked_2pm"] and now_hhmm >= 1400:
        pool, qty_base, vix_value = lock_bot_g_strike_pool(bot["name"], bot["vix_profile"])
        bot["otm_pool"]   = pool
        _sync_bot_g_pool_state(bot, pool)
        bot["qty_base"]   = qty_base
        bot["vix_value"]  = vix_value
        bot["dpcr_no_trade_low"], bot["dpcr_no_trade_high"] = compute_dpcr_no_trade_zone(vix_value)
        bot["vix_locked_2pm"] = True
        log(f"{bot['name']} VIX LOCK (2PM RELOCK) | zone now "
            f"[{bot['dpcr_no_trade_low']},{bot['dpcr_no_trade_high']}] (v-G24)")

    if now_hhmm < watch_start_hhmm:
        return watch_start_hhmm, trade_start_hhmm
    if _v39_anchor_wait(bot, gap_day, now_hhmm):   # v-E39: wait for the 09:15 reference, no bucket used
        _v42_pre_snapshot(spot)   # v-E42 (vE6.6): 09:18 OI reading kept as the first baseline
        return watch_start_hhmm, trade_start_hhmm

    # ── DPCR update + daily direction lock + locked-side veto ──
    # v-G9-FIX3: all three of get_current_dpcr()/lock_bot_g_daily_bias()/
    # check_bot_g_locked_side_veto() log on every call, and DPCR itself only
    # actually changes once per 3m candle -- calling the latter two every
    # ~1-3s tick (the main loop's real cadence) produced a duplicate log
    # line every tick with no new information between candles. Now gated to
    # _new_candle, same as the DPCR fetch itself; the veto result is cached
    # on the bot dict and reused for ticks in between (still functionally
    # correct -- nothing about the veto changes between candles anyway).
    if is_new_3m_candle(bot["name"]):
        # v-G12 (historical): the fetch+append is bot-AGNOSTIC (shared
        # history, one real DPCR per candle) -- gated on
        # _is_new_shared_dpcr_candle(), not on is_new_3m_candle() (kept
        # this way even after BOT_G's removal since it's still correct
        # and harmless for a single bot). dpcr_history is still re-read
        # fresh every time regardless -- cheap, no API call, just a list copy.
        # v-G47: defensive init -- _raw_ratio_for_dashboard is only assigned
        # inside the _is_new_shared_dpcr_candle() branch below, but is now
        # also read further down (at the lock_bot_g_daily_bias() call) on
        # every is_new_3m_candle() tick, not just ticks where the shared
        # candle also just rolled. Without this default it would raise
        # NameError on any tick where the two conditions diverge -- caught
        # before shipping, not from a live crash.
        _raw_ratio_for_dashboard = None
        if _is_new_shared_dpcr_candle():
            # v-G31: get_current_dpcr() now returns (signed_dpcr, raw_ratio)
            # -- signed_dpcr already appended to _BOTG_DPCR_HISTORY inside
            # that function (drives all real decisions below); raw_ratio is
            # ONLY for the dashboard chart, kept on the old centered-near-1
            # scale on purpose, explicit instruction.
            # v-G37: dpcr_window now DTE-scaled (weekday lookup), not the
            # fixed module default -- see get_bot_g_dpcr_window_today().
            _signed_dpcr, _raw_ratio_for_dashboard = get_current_dpcr(
                spot=spot, gap_day=gap_day, dpcr_window=get_bot_g_dpcr_window_today())
            if _signed_dpcr is not None:
                # v-G9-FIX4: this call existed in heartbeat_snippet.py but was
                # never actually wired anywhere -- without it, /botg_series stays
                # empty and the dashboard's DPCR/Nifty charts have nothing to
                # plot, even with BOT_G fully live.
                # v-E10: signed DPCR (+ raw ratio, broker, zone) -- was raw only.
                send_botg_reading(_signed_dpcr, _raw_ratio_for_dashboard, spot,
                                  bot.get("dpcr_no_trade_high"))
        if bot.get("early_slot"):
            # v-E1: early slot -- DPCR fetched above (shared), but no daily
            # lock / veto / pause; direction is checked per tick instead.
            return watch_start_hhmm, trade_start_hhmm
        dpcr_history = get_bot_g_dpcr_history()
        bot["locked_side"] = lock_bot_g_daily_bias(
            dpcr_history, now_hhmm, trade_start_hhmm, already_locked=bot["locked_side"],
            bot_name=bot["name"], no_trade_low=bot["dpcr_no_trade_low"],
            no_trade_high=bot["dpcr_no_trade_high"], vix_value=bot.get("vix_value"),
            raw_ratio=_raw_ratio_for_dashboard)
        _v46_shadow(bot, dpcr_history, spot, now_hhmm, trade_start_hhmm)   # v-E46/v-E47 (vE6.9), log-only
        if bot["locked_side"] is not None:
            allowed, _veto_reason = check_bot_g_locked_side_veto(
                bot["locked_side"], dpcr_history, bot_name=bot["name"],
                no_trade_low=bot["dpcr_no_trade_low"], no_trade_high=bot["dpcr_no_trade_high"],
                vix_value=bot.get("vix_value"))
            bot["_botg_veto_ok"] = allowed
        else:
            bot["_botg_veto_ok"] = False
        # v-G28: falling-DPCR early-warning gate, direction-agnostic, blocks
        # NEW entries only -- see compute_bot_g_dpcr_falling_block() docstring.
        bot["_botg_falling_blocked"], bot["_botg_dpcr_change"] = \
            compute_bot_g_dpcr_falling_block(dpcr_history, bot.get("vix_value"),
                                             locked_side=bot.get("locked_side"))   # v-G72

    return watch_start_hhmm, trade_start_hhmm


def _bot_g_try_entry(bot, df3, spot, stale, now):
    """
    v-G9: flat-side handler. Sequence per cycle:
      1. Determine gap-day status (once per day) and the resulting watch/
         trade windows.
      2. Update DPCR (once per 3m candle) and the daily direction lock,
         via the shared _update_bot_g_dpcr_state() (v-G28).
      3. If a side is locked, run the per-entry reversal veto.
      4. Generic safety gates (allow_trade only -- deliberately not
         can_enter(), see v-G9-FIX5 note below).
      5. v-G37: rejection-candle scan (3m-candle cadence) across EVERY
         strike in bot["otm_pool"] -> arms the next candle per strike.
      6. Live/intrabar confirmation check (EVERY tick, per strike, while
         armed) -> the first strike to fully confirm takes the trade;
         deepest-OTM wins any same-tick tie; every other pool strike
         resets at that point (see the pool-scan block below).
    """
    if stale:
        return

    # ── Day-level state: gap-day + watch/trade windows, computed ONCE ──
    # v-E30 (vE6.2.2): an undetermined gap check (gap_pct None) is re-tried
    # every 3 min until BOTG_GAP_RECHECK_UNTIL_HHMM instead of staying
    # NORMAL for the whole day.
    if bot["gap_day"] is None or (bot.get("gap_pct") is None and hhmm() < BOTG_GAP_RECHECK_UNTIL_HHMM
                                   and time.time() - bot.get("_gap_recheck_t", 0) >= 180):
        bot["_gap_recheck_t"] = time.time()
        is_gap, gap_pct = detect_bot_g_gap_day(df3)
        bot["gap_day"], bot["gap_pct"] = is_gap, gap_pct

    now_hhmm = hhmm()
    watch_start_hhmm, trade_start_hhmm = _update_bot_g_dpcr_state(bot, spot, now_hhmm)

    if now_hhmm < watch_start_hhmm or now_hhmm >= FORCE_EXIT_G:
        return

    if bot.get("early_slot"):
        # v-E1: BOT_GE -- per-tick direction (DPCR sign + flow tier), no lock.
        side = _botge_entry_side(bot, now_hhmm, trade_start_hhmm)
        if side is None:
            return
    else:
        # v-E3 (option B): BOT_G opens nothing while an early trade is open.
        # Everything above (DPCR fetch, 10:15 lock, VIX lock) already ran.
        if BOTG_WAIT_FOR_EARLY_TRADE and any(b.get("early_slot") and b.get("trade_open") for b in BOTS):
            if now - bot.get("_ge_wait_log", 0) >= 60:
                log(f"{bot['name']} WAITING | early-slot trade still open -- no new {bot['name']} entry yet (vE4 option B)")
                bot["_ge_wait_log"] = now
            return

        if bot.get("v53_gate_block"):   # v-E53 (vE6.13): low-VIX day, no new entries
            if now - bot.get("_v53_log", 0) >= 900:
                log(f"{bot['name']} VIX GATE | VIX {bot.get('v53_gate_vix')} <= {BOTG_VIX_GATE_MAX} -- no new entries today (v-E53)")
                bot["_v53_log"] = now
            return

        if bot["locked_side"] is None:
            return
        side = bot["locked_side"]

        if not bot.get("_botg_veto_ok", False):
            return

    # v-G15: no NEW entries after BOTG_ENTRY_CUTOFF_HHMM (14:30) -- placed
    # here deliberately, AFTER the DPCR/lock/veto block above so that
    # tracking keeps running and logging normally right through the rest
    # of the session (useful for observation, and it's shared with the
    # other bot anyway), but BEFORE the rejection scan/live-trigger below
    # so no new position can actually open past this point. Blocks
    # unconditionally, including any arm already in progress from just
    # before cutoff -- the concern (afternoon premium/theta behavior)
    # applies to the moment of entry itself, not when the arm started.
    if now_hhmm >= BOTG_ENTRY_CUTOFF_HHMM:
        return

    # v-G36 (29-Aug-2026): per-bot daily profit cap, explicit instruction.
    # HARD stop, not a trailing lock -- once this bot's own realized P/L
    # for the day reaches the cap, no new entries for the rest of the
    # session, full stop, even if PnL later dips back below it (that
    # trailing-resume alternative was explicitly considered and rejected).
    # BOT_G and BOT_G are capped INDEPENDENTLY of each other -- this
    # check only ever looks at `bot["cum_realized_pnl"]`, never the other
    # bot's or the combined TOTAL_REALIZED_PNL. Placed here (after the
    # entry-cutoff check, before the generic safety gates) so it blocks
    # NEW entries only -- an already-open position at the moment this
    # bot's cap is crossed is NOT force-closed; it continues to be
    # managed normally by the existing SL/BE/TSL/partial-booking
    # machinery to its own natural exit. This only ever fires once per
    # day per bot in practice (cum_realized_pnl only grows monotonically
    # more slowly than it could cross back below the cap), but the check
    # itself is a plain >= comparison, not a one-time latch, so it stays
    # correctly blocking on every subsequent tick without needing its
    # own separate "already capped" flag.
    if BOTG_DAILY_PROFIT_CAP_ENABLED and bot["cum_realized_pnl"] >= BOTG_DAILY_PROFIT_CAP_PER_BOT:
        return

    # ── Generic safety gates (circuit breaker, losing streak, profit lock,
    #    data health, duplicate position, paper/live position checks) ──
    # v-G9-FIX5: deliberately does NOT call can_enter() here. That function
    # enforces BASE_REENTRY_COOLDOWN_SEC (300s) via bot["last_exit_time"] --
    # a generic same-bot cooldown meant for A-F, which don't have their own
    # setup-based re-arm mechanism. BOT_G already has one: a fresh
    # rejection candle + live trigger has to independently re-form after
    # every exit before it can enter again (see the rejection scan below).
    # That's the intended reentry gate for BOT_G, not a fixed timer on top
    # of it -- confirmed and corrected after replaying real trade data
    # showed can_enter() silently blocking legitimate back-to-back setups.
    ok, _reason = allow_trade(bot, side)
    if not ok:
        return

    # ── v-G37: multi-strike pool scan. Each strike in bot["otm_pool"] runs
    # its OWN independent rejection-arm/confirm state machine (bot["pool_
    # state"][str(otm_val)]) off its own premium series -- the same
    # sequence a single strike used to run, just repeated per pool member.
    # Every strike that fully qualifies THIS tick is collected before
    # anything fires, so a same-tick tie is resolved deliberately (deepest
    # OTM wins) rather than by scan order. While a trade is open this
    # whole function isn't even called (see bot_g_tick()'s dispatch), so
    # the other pool strikes are naturally untouched -- no extra gating
    # needed for "only check other strikes once this trade ends".
    # v-G40: BOT_G candle state is driven by actual native 5m candle timestamps,
    # not a fragile 0-10 second wall-clock boundary.
    pool = bot.get("otm_pool") or []

    # v-G28: falling-DPCR early-warning gate -- blocks arming any FRESH
    # rejection candle across the whole pool (an already-armed strike is
    # left alone; it still confirms or expires on its own below).
    # Checked/logged ONCE per tick here, not per pool strike, so a
    # 3-strike pool doesn't produce 3 duplicate lines for one bot-level gate.
    falling_blocked = bool(bot.get("_botg_falling_blocked"))

    # Batch-fetch LTP for every currently-armed pool strike in ONE call --
    # the old single-strike version called get_multi_ltp([one_symbol]) per
    # tick; get_multi_ltp() already accepts a list, so up to 3 armed
    # strikes still cost exactly one quote call, not three.
    armed_symbols = [
        bot["pool_state"][str(ov)]["rejection_symbol"]
        for ov in pool
        if bot["pool_state"].get(str(ov), {}).get("rejection_armed")
        and bot["pool_state"][str(ov)].get("rejection_symbol")
    ]
    pool_ltp_map = get_multi_ltp(armed_symbols) if armed_symbols else {}

    qualifying = []   # (otm_val, candidate_symbol, candidate_ltp, live_vwap, rejection_low)

    for otm_val in pool:
        key = str(otm_val)
        st = bot["pool_state"].setdefault(key, _fresh_pool_strike_state())

        if not st["rejection_armed"]:
            candidate_symbol = get_option_symbol_bot_g(spot, side, otm_steps=otm_val, bot_name=bot["name"])
            df_setup = fetch_option_history_5m(
                candidate_symbol, force_refresh=_bot_g_should_force_5m_refresh(candidate_symbol, _v49_opt_tf(bot)),
                tf=_v49_opt_tf(bot))   # v-E49
            if df_setup is None or len(df_setup) < 2:
                continue

            # v-G40: row -2 is the latest CLOSED 5m candle. Scan each
            # closed candle exactly once per pool strike, independent of
            # main-loop/API timing.
            # v-G50: dedup now keyed by SYMBOL (module-level dict), not
            # per-OTM-slot state -- see _fresh_pool_strike_state()
            # docstring for why (flickering strikes need this).
            closed_row = df_setup.iloc[-2]
            closed_key = closed_row.name.strftime("%Y-%m-%d %H:%M")
            if _BOTG_LAST_SCANNED_CANDLE_BY_SYMBOL.get(f"{bot['name']}|{candidate_symbol}") == closed_key:   # v-E5
                continue
            _BOTG_LAST_SCANNED_CANDLE_BY_SYMBOL[f"{bot['name']}|{candidate_symbol}"] = closed_key   # v-E5

            if falling_blocked:
                log(f"{bot['name']} ENTRY PAUSED | OTM{otm_val} closed candle {closed_key} | "
                    f"DPCR moving against locked {bot.get('locked_side')} "
                    f"(change={bot.get('_botg_dpcr_change')}, v-G28/v-G72)")
                continue

            rej = find_bot_g_rejection_5m(df_setup, bot_name=f"{bot['name']}:OTM{otm_val}")
            if rej and rej["rejection"]:
                st["rejection_armed"] = True
                st["rejection_low"] = rej["low"]
                st["rejection_vwap"] = rej["vwap"]
                st["rejection_close"] = rej["close"]
                st["rejection_vwap_touched"] = False
                st["rejection_symbol"] = candidate_symbol
                st["rejection_candle_key"] = closed_key
                # v-G66 (this session): capture setup-quality metrics at arm
                # time, purely for post-trade research logging -- does NOT
                # feed into any entry/exit decision. Carried through to the
                # bot's own state at entry (see below) and written to the
                # trades CSV when the trade closes, so hypothesis testing
                # (e.g. "does Close Location predict outcome for
                # RED_PULLBACK setups") no longer requires manually cross-
                # referencing ARMED log lines against TRADE EXIT rows by
                # timestamp -- exactly the error-prone process this session
                # already had to untangle once (RMoney T2, 25-Sep).
                st["rejection_setup_type"] = rej.get("setup_type")
                st["rejection_close_location"] = rej.get("close_location")
                st["rejection_rel_vol_5"] = rej.get("rel_volume_5")
                st["rejection_vwap_penetration"] = rej.get("vwap_penetration")
                log(f"{bot['name']} ARMED | OTM{otm_val} TF:{_v49_opt_tf(bot)}m side={side} Symbol:{candidate_symbol} "
                    f"Type:{rej.get('setup_type')} O:{rej.get('open')} H:{rej.get('high')} "
                    f"L:{rej['low']} C:{rej['close']} VWAP:{rej['vwap']} "
                    f"Dist:{rej['close']-rej['vwap']:+.2f} Body:{rej.get('body',0):.2f} "
                    f"Range:{rej.get('range',0):.2f} UpperW:{rej.get('upper_shadow',0):.2f} "
                    f"LowerW:{rej.get('lower_shadow',0):.2f} CloseLoc:{rej.get('close_location',0):.0%} "
                    f"-- next candle only: {closed_key} -> confirmation window (v-G41)")
                _v35_safe(lambda: _v35_tag("ARM", bot, candidate_symbol, side, otm_val, spot, detail=f"{rej.get('setup_type')} close {rej['close']} low {rej['low']} vwap {rej['vwap']}"))   # v-E35
            continue

        candidate_symbol = st["rejection_symbol"]
        df_setup = fetch_option_history_5m(
            candidate_symbol, force_refresh=_bot_g_should_force_5m_refresh(candidate_symbol, _v49_opt_tf(bot)),
            tf=_v49_opt_tf(bot))   # v-E49
        if df_setup is None or len(df_setup) == 0:
            continue
        # v-G45 (reinstated -- this session's v-G41 upload had regressed to
        # the pre-fix version): rejection_ts must be the FIXED candle stored
        # at arm time (st["rejection_candle_key"]), NOT recomputed from
        # df_setup.index[-2] each tick. Recomputing it fresh means "the
        # candle just before whatever's forming right now" is ALWAYS exactly
        # 5 minutes before the forming one in a contiguous series, so the
        # comparison can never actually fail and this never expires
        # (verified directly: simulated tick by tick, EXPIRES=False every
        # time, no matter how far time drifted). Live evidence: 10-Sep
        # RMoney, an arm from 10:40 persisted unexpired until it finally
        # confirmed at 10:57 -- 17 minutes and 7+ points from where it
        # armed, that day's single biggest loss. Anchoring the comparison
        # to the value fixed at arm time restores the intended behavior:
        # confirm within the ONE immediately-following candle, or expire.
        rejection_ts = datetime.strptime(st["rejection_candle_key"], "%Y-%m-%d %H:%M")
        current_forming_ts = df_setup.index[-1]
        current_forming_key = current_forming_ts.strftime("%Y-%m-%d %H:%M")
        next_candle_key = (rejection_ts + pd.Timedelta(minutes=_v49_opt_tf(bot))).strftime("%Y-%m-%d %H:%M")

        if current_forming_key != next_candle_key:
            _reason = st.get("_botg_last_confirm_fail_reason", "NOT_TOUCHED")
            _dist = st.get("_botg_last_confirm_dist")
            log(f"{bot['name']} ARM EXPIRED | OTM{otm_val} Symbol:{candidate_symbol} "
                f"rejection candle {st['rejection_candle_key']} "
                f"closed without confirmation -- current candle {current_forming_key}; "
                f"last reason: {_reason}"
                + (f" (dist to VWAP: {_dist:+.2f})" if _dist is not None else "") + " (v-G45)")
            _v35_safe(lambda: _v35_tag("ARM_EXPIRED", bot, candidate_symbol, side, otm_val, spot, detail=f"{_reason} dist {_dist}"))   # v-E35
            bot["pool_state"][key] = _fresh_pool_strike_state()
            continue

        fresh_candidate = get_option_symbol_bot_g(spot, side, otm_steps=otm_val, bot_name=bot["name"])
        if fresh_candidate != candidate_symbol:
            log(f"{bot['name']} ARM DROPPED | OTM{otm_val} strike shifted "
                f"{candidate_symbol} -> {fresh_candidate} (v-G40)")
            _v35_safe(lambda: _v35_tag("ARM_DROPPED", bot, candidate_symbol, side, otm_val, spot, detail=f"shifted_to {fresh_candidate}"))   # v-E35
            bot["pool_state"][key] = _fresh_pool_strike_state()
            continue

        live_vwap = df_setup["vwap"].iloc[-1]
        candidate_ltp = pool_ltp_map.get(candidate_symbol)

        # v-G50: update the tick-by-tick running low for this confirm
        # window BEFORE checking confirmation this tick -- must happen
        # every tick regardless of whether confirmation ends up true,
        # so the running low genuinely reflects everything seen so far.
        if candidate_ltp is not None:
            if st.get("confirm_window_running_low") is None or candidate_ltp < st["confirm_window_running_low"]:
                st["confirm_window_running_low"] = candidate_ltp

        touched, confirmed, fail_reason = check_bot_g_5m_confirmation(
            candidate_ltp, live_vwap, st.get("rejection_close"), st.get("rejection_vwap_touched", False),
            vix_value=bot.get("vix_value"))
        st["rejection_vwap_touched"] = touched
        # v-G30: remember the last check's outcome so ARM EXPIRED above can
        # report WHY, rather than just "no confirmation".
        if candidate_ltp is not None and live_vwap is not None:
            st["_botg_last_confirm_dist"] = candidate_ltp - live_vwap
        st["_botg_last_confirm_fail_reason"] = fail_reason

        # v-G50: confirmation-window integrity check -- only once the
        # ordinary confirmation criteria are otherwise satisfied. Uses
        # the genuine running low tracked above (this window's own LTP
        # stream), NOT any closed candle. See config comment for the
        # full evidence and why this is scoped narrower than the
        # proposal it replaces.
        if confirmed and BOTG_CONFIRM_INTEGRITY_ENABLED:
            _proposed_sl = compute_bot_g_initial_sl(candidate_ltp, st["rejection_low"], st.get("rejection_vwap"))
            _run_low = st.get("confirm_window_running_low")
            if _run_low is not None and _run_low <= _proposed_sl:
                log(f"{bot['name']} ENTRY ABORT | OTM{otm_val} Symbol:{candidate_symbol} "
                    f"reason=CONFIRM_WINDOW_BREACHED_PROPOSED_SL "
                    f"running_low={round(_run_low,2)} proposed_sl={round(_proposed_sl,2)} (v-G50)")
                _v35_safe(lambda: _v35_tag("ENTRY_ABORT", bot, candidate_symbol, side, otm_val, spot, entry=candidate_ltp, sl=_proposed_sl, detail=f"CONFIRM_WINDOW_BREACHED running_low {_run_low}"))   # v-E35
                # immediate reset (not a fall-through failed-confirm), same
                # reason as the existing entry-abort path just below: without
                # this, the SAME breach would keep re-triggering on every
                # tick for the rest of the window (the running low can only
                # stay breached, never recover) -- pure log spam. Scan
                # memory is symbol-keyed now (v-G50), so this plain reset
                # can't cause a same-candle re-arm the way it used to.
                bot["pool_state"][key] = _fresh_pool_strike_state()
                continue

        if not confirmed:
            continue

        if candidate_ltp is None or candidate_ltp <= st["rejection_low"]:
            log(f"{bot['name']} ENTRY ABORT | OTM{otm_val} Symbol:{candidate_symbol} price={candidate_ltp} "
                f"at/below rejection low={st['rejection_low']}")
            _v35_safe(lambda: _v35_tag("ENTRY_ABORT", bot, candidate_symbol, side, otm_val, spot, detail=f"price {candidate_ltp} at/below rejection low {st['rejection_low']}"))   # v-E35
            bot["pool_state"][key] = _fresh_pool_strike_state()
            continue

        # v-G67 (this session): diagnostic-only flag distinguishing a
        # genuine VWAP reclaim (candidate_ltp >= live_vwap) from an entry
        # that only cleared BOTG_CONFIRM_VWAP_LOWER_TOL's allowance (up to
        # 1 point below VWAP) -- confirmed by name, but not actually back
        # above the pivot. Originally motivated by a mechanical replay
        # (23000 CE, 11-25 Sep) that appeared to show a large improvement
        # from tightening this boundary -- CORRECTED afterward: most of
        # that improvement came from including rejection candidates whose
        # confirmation window started before BOTG_TRADE_START_NORMAL_HHMM
        # (1015), which the real bot can never trade (locked_side is None
        # until then). Once restricted to genuinely tradable entry times,
        # the tightened-boundary version produced IDENTICAL results to the
        # current bot on that dataset -- zero backtest evidence either way.
        # This flag (and v-G68's raw distance below) stays in as pure
        # logging precisely because the backtest can no longer settle this;
        # only real live trade data can now, same discipline as v-G64/v-G66.
        vwap_reclaim_type = "GENUINE" if candidate_ltp >= live_vwap else "LOWER_TOLERANCE"
        # v-G68 (this session): the exact signed distance, not just which
        # side of zero it landed on -- lets research look for a threshold
        # anywhere in the range, not only at zero. GENUINE/LOWER_TOLERANCE
        # above is fully derivable from this value's sign; kept as its own
        # column too since it's already computed and some queries are
        # simpler against a categorical label than a raw float.
        vwap_reclaim_distance = round(candidate_ltp - live_vwap, 4)

        qualifying.append((otm_val, candidate_symbol, candidate_ltp, live_vwap, st["rejection_low"], st["rejection_vwap"],
                            st.get("rejection_setup_type"), st.get("rejection_close_location"),
                            st.get("rejection_rel_vol_5"), st.get("rejection_vwap_penetration"),
                            vwap_reclaim_type, vwap_reclaim_distance))

    if not qualifying:
        return

    # v-G37: tie-break, explicit instruction -- if more than one pool
    # strike qualifies on the same scan, the deepest-OTM (cheapest
    # premium) strike wins. Pool lists are ordered ascending by OTM depth,
    # so this is just "max otm_val among this tick's qualifiers".
    qualifying.sort(key=lambda q: q[0])
    winner_otm, candidate_symbol, candidate_ltp, live_vwap, rejection_low, rejection_vwap, \
        rej_setup_type, rej_close_location, rej_rel_vol_5, rej_vwap_penetration, \
        rej_vwap_reclaim_type, rej_vwap_reclaim_distance = qualifying[-1]
    if len(qualifying) > 1:
        log(f"{bot['name']} TIE-BREAK | strikes {[(q[0], q[1]) for q in qualifying]} all qualified "
            f"this scan -> OTM{winner_otm} Symbol:{candidate_symbol} (deepest) selected, others reset (v-G37)")

    # Winner takes the trade -- EVERY pool strike's state resets here
    # (the winning values are already captured into locals above), so
    # when this trade eventually closes, the pool scan resumes completely
    # fresh rather than carrying any stale arm through.
    #
    # v-G49 (bug fix, superseded by v-G50's redesign): originally
    # preserved each strike's scan-key across this reset. Confirmed live
    # (11-Sep): a fast-closing trade (16 seconds) left the SAME 5-min
    # candle as the latest closed one when scanning resumed; wiping the
    # scan memory made that candle look "never scanned" again, so it
    # re-armed and re-entered on the IDENTICAL setup 90 seconds later --
    # combined loss -Rs5,616 on the exact same rejection candle, twice.
    # That fix worked for this exact path, but not for strike-shift
    # resets (see _fresh_pool_strike_state() docstring) -- scan memory
    # is now symbol-keyed and lives outside this per-OTM-slot state
    # entirely, so a plain reset here is correct and sufficient; every
    # field still resets to fully fresh/unarmed, exactly as before.
    for ov in pool:
        bot["pool_state"][str(ov)] = _fresh_pool_strike_state()

    # v-E14/v-E15 (vE6): carried flow at the moment of entry; main-slot CE
    # skip when calls are being added. Pool already reset above, so a
    # skipped setup is not re-armed; scanning resumes fresh.
    _cflows = _botg_entry_carried_flows()
    try:
        _dtd = _day_type_diag(spot)   # v-E20, log/CSV only
    except Exception:
        _dtd = {k: "" for k in _DAY_KEYS}
    _skip, _skip_status = _botg_ce_calladd_check(bot, side, _cflows)
    if _skip and BOTG_CE_CALLADD_SKIP_LOGONLY:   # v-E48 (vE6.10): log the would-have skip, take the entry
        _f = _cflows[BOTG_CE_CALLADD_SKIP_MIN]
        log(f"{bot['name']} CE SKIP WOULD-HAVE (log-only) | OTM{winner_otm} Symbol:{candidate_symbol} "
            f"LTP:{candidate_ltp} | {BOTG_CE_CALLADD_SKIP_MIN}m carried flow dCE:{_f['dce']:+,.0f} "
            f"(> {BOTG_CE_CALLADD_SKIP_THRESHOLD:,}) dPE:{_f['dpe']:+,.0f} over {_f['minutes']}m -- entry TAKEN (v-E48)")
        _v35_safe(lambda: _v35_tag("CE_SKIP_WOULD", bot, candidate_symbol, side, winner_otm, spot, entry=candidate_ltp, rej_low=rejection_low, rej_vwap=rejection_vwap, detail="calls being added, log-only (v-E48)"))
        _skip, _skip_status = False, "WOULD_SKIP"
    if BOTG_ST_FILTER_ENABLED and bot["name"] == "BOT_G":   # v-E50 (vE6.11)
        _std = _v50_st_dir(df3)
        if _std is not None and ((side == "CE" and _std < 0) or (side == "PE" and _std > 0)):
            log(f"{bot['name']} ST SKIP | {side} against 3m spot Supertrend({BOTG_ST_FILTER_N},{BOTG_ST_FILTER_MULT}) "
                f"= {'UP' if _std > 0 else 'DOWN'} | OTM{winner_otm} Symbol:{candidate_symbol} LTP:{candidate_ltp} (v-E50)")
            _v35_safe(lambda: _v35_tag("ST_SKIP", bot, candidate_symbol, side, winner_otm, spot, entry=candidate_ltp,
                                       rej_low=rejection_low, rej_vwap=rejection_vwap, detail=f"3m ST {_std} (v-E50)"))
            return
        if _std is None:
            log(f"{bot['name']} ST CHECK | 3m Supertrend NA -- entry allowed (v-E50)")
    if _skip:
        _f = _cflows[BOTG_CE_CALLADD_SKIP_MIN]
        log(f"{bot['name']} CE SKIPPED: calls being added | OTM{winner_otm} Symbol:{candidate_symbol} "
            f"LTP:{candidate_ltp} | {BOTG_CE_CALLADD_SKIP_MIN}m carried flow dCE:{_f['dce']:+,.0f} "
            f"(> {BOTG_CE_CALLADD_SKIP_THRESHOLD:,}) dPE:{_f['dpe']:+,.0f} over {_f['minutes']}m | "
            f"all: {_botg_cflow_text(_cflows)} (v-E15)")
        try:   # v-E19/v-E20: follow the skipped option; would-have stop/P1 as vE6 would set them
            _sk_e = candidate_ltp
            _sk_sl, _ = apply_bot_g_stop_band(_sk_e, compute_bot_g_initial_sl(_sk_e, rejection_low, rejection_vwap))
            _sk_p1, _sk_p2 = _botg_targets(bot, _sk_e, _sk_e - _sk_sl)
            log(f"{bot['name']} CE SKIP DAY | {_dtd.get('day_type', 'NA')} {_dtd.get('pct_from_open', 'NA')}% from open "
                f"pos {_dtd.get('pos_in_range', 'NA')} 30m {_dtd.get('spot_30m_chg', 'NA')} (v-E20, log-only)")
            _track_start("SKIP", bot["name"], f"{bot['name']}-SKIP-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                         candidate_symbol, side, _sk_e, entry=_sk_e, sl=_sk_sl, p1=round(_sk_p1, 2), p2=round(_sk_p2, 2),
                         extra=dict(_dtd, cflow9_dce=round(_f["dce"])))
        except Exception as _sk_err:
            log(f"vE6.2 TRACK | skip audit failed (ignored): {_sk_err}")
        _v35_safe(lambda: _v35_tag("CE_SKIP", bot, candidate_symbol, side, winner_otm, spot, entry=candidate_ltp, rej_low=rejection_low, rej_vwap=rejection_vwap, detail="calls being added (v-E15)"))   # v-E35
        return
    if _skip_status == "flow NA":
        log(f"{bot['name']} CE SKIP CHECK | flow NA ({BOTG_CE_CALLADD_SKIP_MIN}m carried flow unavailable) "
            f"-- entry allowed (v-E15)")
    _f9 = _cflows.get(9)
    bot["_e6_diag"] = {"ce_skip_check": _skip_status,
                       "quiet_flow": "" if _f9 is None else (
                           "Y" if abs(_f9["dpe"]) <= BOTG_FLOW_FLAT_EPS and abs(_f9["dce"]) <= BOTG_FLOW_FLAT_EPS else "N")}
    for _m in (3, 6, 9, 12, 15):
        _fm = _cflows.get(_m)
        bot["_e6_diag"][f"cflow{_m}_dpe"] = "" if _fm is None else round(_fm["dpe"])
        bot["_e6_diag"][f"cflow{_m}_dce"] = "" if _fm is None else round(_fm["dce"])
    bot["_e6_diag"].update(_dtd)   # v-E20

    _lc_t0 = time.time()   # v-E22: signal moment
    try:
        _lc_ask, _lc_bid = _get_ask_bid_rmoney(candidate_symbol)
    except Exception:
        _lc_ask, _lc_bid = None, None
    bot["entry_symbol"]=candidate_symbol; bot["qty"]=bot["qty_base"]
    order_id,fill_price,filled_qty=execute_entry(bot,side)
    if order_id is None and not PAPER_TRADE: return
    if filled_qty is not None and filled_qty != bot["qty"] and not PAPER_TRADE: bot["qty"]=filled_qty
    fetched_premium=fill_price if fill_price is not None and fill_price>0 and not PAPER_TRADE else (candidate_ltp or get_multi_ltp([candidate_symbol]).get(candidate_symbol,0))
    if not fetched_premium or fetched_premium<=0: return
    bot["_lc"] = dict(sig=candidate_ltp or fetched_premium, ask=_lc_ask, bid=_lc_bid, fill=fetched_premium,
                      ms=round(1000 * (time.time() - _lc_t0)), qty0=bot["qty"])   # v-E22
    log(f"{bot['name']} ENTRY FILL | signal {bot['_lc']['sig']} ask {_lc_ask} bid {_lc_bid} -> fill {fetched_premium} "
        f"slip {round(fetched_premium - bot['_lc']['sig'], 2)} pts in {bot['_lc']['ms']} ms (v-E22, log-only)")
    _chart_sl=compute_bot_g_initial_sl(fetched_premium,rejection_low,rejection_vwap)
    initial_sl,_stop_reason=apply_bot_g_stop_band(fetched_premium,_chart_sl)   # v-E16: band + hard limit, then levels
    risk_pts,be_level,arm_level=compute_bot_g_levels(fetched_premium,initial_sl,bot)   # v-E4
    bot["trade_open"]=True; bot["entry"]=fetched_premium; bot["entry_spot"]=spot; bot["highest"]=fetched_premium
    bot["best_idx_move"]=0.0; bot["side"]=side; bot["initial_sl"]=initial_sl; bot["active_sl"]=initial_sl
    bot["risk_pts"]=risk_pts; bot["be_level"]=be_level; bot["arm_level"]=arm_level; bot["stage"]="INITIAL"; bot["armed"]=False
    bot["highest_close_since_arm"]=fetched_premium; bot["entry_hhmm"]=now_hhmm
    bot["entry_epoch"]=time.time()   # v-G30: real timestamp, for the theta-decay time cap
    # v-G76: trade identity for the CSV (groups partial legs + final exit)
    _entry_dt = datetime.now()
    bot["entry_time"] = _entry_dt.strftime("%Y-%m-%d %H:%M:%S")
    bot["trade_id"] = f"{bot['name']}-{_entry_dt.strftime('%Y%m%d-%H%M%S')}"
    bot["trade_pnl_acc"] = 0.0
    bot["post_entry"] = {}   # v-G83: fresh post-entry tracker for this trade
    # v-G66: carry the setup-quality metrics captured at arm time through
    # to the trade's own state, purely for research logging at exit --
    # never read by any decision path.
    bot["entry_setup_type"] = rej_setup_type
    bot["entry_close_location"] = rej_close_location
    bot["entry_rel_vol_5"] = rej_rel_vol_5
    bot["entry_vwap_penetration"] = rej_vwap_penetration
    bot["entry_vwap_reclaim_type"] = rej_vwap_reclaim_type   # v-G67, diagnostic only
    bot["entry_vwap_reclaim_distance"] = rej_vwap_reclaim_distance   # v-G68, diagnostic only
    bot["_botg_last_broker_sl"]=None
    bot["partial1_done"]=False; bot["partial2_done"]=False; bot["partial1_booked_qty"]=0; bot["partial2_booked_qty"]=0
    # v-G59: per-trade peak-unrealized tracker, explicit instruction after
    # 21-Sep Trade 1 (peak +Rs3,068, ~1.4pts short of P1, gave it all back
    # to a near-breakeven exit) -- reusing bot["highest"] for peak LTP
    # (already tracked per-trade), plus storing p1_target here so exit can
    # report the peak's distance short of P1 without re-deriving it.
    # LOGGING ONLY -- does not touch SL/BE/TSL/P1/P2 decision logic at all.
    # Kept identical to the Fyers file.
    bot["peak_unrealized_pnl"] = 0.0
    bot["p1_target"] = _botg_targets(bot, fetched_premium, risk_pts)[0]   # v-E4
    register_entry(bot, side)
    _sl_ok = update_broker_sl_order(bot, initial_sl)
    if not _sl_ok and not PAPER_TRADE and LIVE_REQUIRE_BROKER_SL:
        log(f"{bot['name']} LIVE SAFETY | Entry has no confirmed broker SL; attempting immediate emergency flatten.")
        if _emergency_flatten(bot, "initial broker SL unavailable"):
            _close_bot(bot, cooldown=0)
            bot["stage"] = "INITIAL"; bot["armed"] = False; bot["_botg_last_broker_sl"] = None
        return
    _dist_at_entry = candidate_ltp - live_vwap if (candidate_ltp is not None and live_vwap is not None) else None
    _sl_clamped = (rejection_vwap is not None and _chart_sl < rejection_low)   # v-E16: judged on the chart stop   # v-G71: true whenever the clamp moved the SL
    # v-G54: explicit instruction, from reviewing 16-Sep's three real trades
    # -- risk in points AND rupees, plus the actual P1/P2 target PRICES (not
    # just multipliers), logged once at entry so every trade's economics are
    # visible without cross-referencing config constants by hand. Reuses the
    # exact same formula the partial-booking logic itself uses later
    # (BOTG_PARTIAL_R1_MULT/R15_MULT with the %-floor), so this is guaranteed
    # consistent with what actually triggers a partial, not a separate
    # approximation. LOGGING ONLY -- no gate, no MAX_INITIAL_RISK_PTS yet;
    # that needs the same multi-day validation every other gate here got.
    # Kept identical to the Fyers file.
    _risk_rupees = risk_pts * bot["qty"]
    _p1_target = bot["p1_target"]
    _p2_target = _botg_targets(bot, fetched_premium, risk_pts)[1]   # v-E4
    log(f"{bot['name']} ENTRY RISK | Entry:{fetched_premium} SL:{initial_sl} "
        f"RiskPts:{round(risk_pts,2)} RiskRupees:{round(_risk_rupees,2)} "
        f"P1Target:{round(_p1_target,2)} P2Target:{round(_p2_target,2)} "
        f"BE:{round(be_level,2)} TSLArm:{round(arm_level,2)} (v-G54)")
    # v-E16: stop-band audit line (every entry)
    _chart_pts = fetched_premium - _chart_sl
    _stop_pts = fetched_premium - initial_sl
    log(f"{bot['name']} {_stop_reason or 'STOP OK'} | Side:{side} Entry:{fetched_premium} "
        f"ChartSL:{round(_chart_sl,2)} ({_chart_pts:.2f} pts, {100*_chart_pts/fetched_premium:.1f}%) -> "
        f"SL:{initial_sl} ({_stop_pts:.2f} pts, {100*_stop_pts/fetched_premium:.1f}%) | band "
        f"{100*BOTG_STOP_MIN_PCT:.0f}-{100*BOTG_STOP_MAX_PCT:.0f}% hard {BOTG_STOP_HARD_MAX_PTS} pts (v-E16)")
    log(f"{bot['name']} ENTRY CFLOW | {_botg_cflow_text(_cflows)} | quiet:{bot['_e6_diag']['quiet_flow'] or 'NA'} "
        f"CEskip:{_skip_status} (v-E14, log-only)")
    bot["_e6_diag"].update(chart_sl=round(_chart_sl, 2), adj_sl=initial_sl, stop_pts=round(_stop_pts, 2),
                           stop_pct=round(100 * _stop_pts / fetched_premium, 2),
                           stop_adj_reason=_stop_reason or "OK")
    log(f"{bot['name']} ENTRY CONFIRMED | OTM{winner_otm} TF:{_v49_opt_tf(bot)}m Symbol:{candidate_symbol} Entry:{fetched_premium} "
        f"VWAP touch + confirmation above rejection close"
        + (f" (dist to VWAP: {_dist_at_entry:+.2f}, v-G30)" if _dist_at_entry is not None else "")
        + (f" [SL CLAMPED: rej_low {rejection_low} rej_vwap {round(rejection_vwap,2)} -> "
           f"chart SL {round(_chart_sl,2)} (vwap-{BOTG_SL_VWAP_BUFFER}), v-G39/v-G71]" if _sl_clamped else ""))
    _v43_txt = _v43_zlm_tag(bot, side, spot)   # v-E43 (vE6.6), log-only
    _v35_safe(lambda: _v35_tag("ENTRY", bot, candidate_symbol, side, winner_otm, spot, entry=fetched_premium, sl=initial_sl, trade_id=bot.get("trade_id"), detail=f"qty {bot.get('qty')} chartSL {round(_chart_sl, 2)} clamped {bool(_sl_clamped)}" + _v43_txt))   # v-E35/v-E43
    # v-G75/v-G76: per-trade identity + DPCR flow at entry, LOG/CSV ONLY.
    bot["sl_clamped"] = bool(_sl_clamped)
    try:
        _flow = compute_bot_g_flow()
        _tier, _net = classify_bot_g_flow(side, _flow)
        bot["entry_flow_dpe"] = round(_flow["dpe"]) if _flow else ""
        bot["entry_flow_dce"] = round(_flow["dce"]) if _flow else ""
        bot["entry_flow_minutes"] = _flow["minutes"] if _flow else ""
        bot["entry_flow_tier"] = _tier
        bot["entry_flow_net"] = round(_net) if _net is not None else ""
        _hist = get_bot_g_dpcr_history()
        bot["entry_dpcr_signed"] = round(_hist[-1], 3) if _hist else ""
        log(f"{bot['name']} ENTRY FLOW | TradeID:{bot['trade_id']} Side:{side} "
            f"dPE:{bot['entry_flow_dpe']} dCE:{bot['entry_flow_dce']} over {bot['entry_flow_minutes']}m "
            f"Tier:{_tier} NetSupportive:{bot['entry_flow_net']} DPCR:{bot['entry_dpcr_signed']} (v-G75, log-only)")
    except Exception as _flow_err:
        log(f"{bot['name']} ENTRY FLOW | error (ignored, log-only): {_flow_err}")
    # v-G82: latest OI/ATM diagnostic at entry -> trade CSV. LOG/CSV ONLY.
    try:
        _dg = dict(_BOTG_LAST_OI_DIAG)
        _dg["diag_age_sec"] = round(time.time() - _dg["t"]) if _dg.get("t") else ""
        bot["entry_diag"] = {k: _dg.get(k, "") for k in _ENTRY_DIAG_KEYS}
    except Exception as _dg_err:
        bot["entry_diag"] = {}
        log(f"{bot['name']} ENTRY DIAG | error (ignored, log-only): {_dg_err}")
    bot["entry_diag"].update(bot.get("_e6_diag") or {})   # v-E14/v-E16 -> trade CSV
    _v45_entry_context(bot, side, spot)   # v-E45 (vE6.8), log-only


# v-G22 (18-Aug-2026): BOT_DEFAULTS was found to be ENTIRELY MISSING from
# this file -- caused a NameError crash at startup (line 'BOTS = [' below,
# right at the first '**BOT_DEFAULTS,' usage). Almost certainly lost
# accidentally during the manual rewrite/compression that built the new
# 5-min confirmation logic -- restored here verbatim from the last known-
# good baseline. Verified every field the rewrite's own new logic reads
# (rejection_close, rejection_vwap_touched, etc.) is accessed via .get()
# with a safe default everywhere in the file, not direct bot["..."]
# indexing -- so this restore alone is sufficient, no new fields needed
# adding on top of the original set.
BOT_DEFAULTS = dict(
    trade_open     = False,
    entry          = 0.0,
    entry_spot     = 0.0,
    entry_symbol   = None,
    highest        = 0.0,
    active_sl      = 0.0,
    side           = "",
    last_print     = 0,
    last_exit_time = 0,
    sl_lock_until  = 0,
    partial_done   = False,
    sl_order_id    = None,
    last_main_print= 0,
    entry_hhmm     = 0,
    # v-G34 (25-Aug-2026): ROOT-CAUSE FIX. Confirmed live crash on the
    # RMoney side of this build, 25-Aug-2026: entry_epoch (added in v-G30
    # for the theta-decay cap) was only ever set at actual entry time,
    # never given a default here -- PERSIST_KEYS includes it
    # unconditionally, so save_state() crashed with KeyError('entry_epoch')
    # the moment ANY bot's exit called save_state() while ANOTHER bot in
    # BOTS[] hadn't entered a trade yet that session (its dict genuinely
    # never had the key). This exact same latent bug is present here too
    # (same v-G30 origin) -- it simply hasn't triggered yet in any Fyers
    # session, since both bots happened to enter trades before any exit
    # fired save_state(). Fixed at the root (a real default here) rather
    # than patching the specific trigger condition, since any future
    # PERSIST_KEYS entry set only at a specific event (not present from
    # bot-dict creation) is vulnerable to the same failure mode.
    entry_epoch    = None,
    peak_open_pnl  = 0.0,   # v2.6-N2: peak open PnL tracker for profit floor
    reentry_block_side  = None,   # v3.1-R3: side that's on a same-dir SL cooldown
    reentry_block_until = 0,      # v3.1-R3: epoch time that cooldown expires
    # v-G9: BOT_G-only state, added here (not only on its own BOTS[] dict) so
    # PERSIST_KEYS/save_state()/load_state() -- shared, generic infra across
    # every bot -- don't need special-casing. Harmless no-ops for BOT_A-F,
    # never read or written by their code paths.
    locked_side    = None,    # 'CE'/'PE'/None -- BOT_G's daily direction lock
    gap_day        = None,    # bool -- determined once per trading day
    gap_pct        = None,
    # v-G37 (05-Sep-2026): REPLACES the old single-strike scalar rejection_*
    # fields. otm_pool is the current VIX-selected list of otm_steps values
    # (e.g. [0,1,2]); pool_state holds one independent rejection-arm/
    # confirm state dict per pool member, keyed by str(otm_steps) -- see
    # _fresh_pool_strike_state()/_sync_bot_g_pool_state(). Both harmless
    # no-ops for BOT_A-F.
    otm_pool       = None,
    pool_state     = None,
    initial_sl               = 0.0,
    risk_pts                 = 0.0,
    be_level                 = 0.0,
    arm_level                = 0.0,
    stage                    = "INITIAL",   # INITIAL / BREAKEVEN / TRAILING
    armed                    = False,
    highest_close_since_arm  = 0.0,
    # v-G11: VIX-based strike-pool/qty lock. Harmless no-ops for BOT_A-F.
    # v-G24 (18-Aug-2026): was locked ONCE per day (vix_locked); now locks
    # TWICE -- once at the bot's own trade_start, again at 14:00 -- so both
    # the pool AND the DPCR no-trade zone (below) can react to a real
    # intraday VIX move, not just whatever VIX read at market open. Two
    # independent flags since the two checkpoints fire at different times.
    vix_locked_open   = False,   # first lock, at bot's own trade_start
    vix_locked_2pm     = False,   # second lock/relock, at 14:00
    vix_value          = None,
    qty_base           = None,   # 4 or 8 lots -- the per-trade qty before
                                  # any partial booking; re-set at each lock
    # v-G24: per-bot DPCR no-trade zone, set alongside otm_pool/qty_base
    # at each VIX lock (see compute_dpcr_no_trade_zone()). Defaults to the
    # original fixed BOTG_DPCR_NO_TRADE_LOW/HIGH until the first lock
    # happens, so behavior before that first lock matches the pre-v-G24
    # design exactly -- no change in behavior for anyone not yet reading
    # this new logic.
    dpcr_no_trade_low  = BOTG_DPCR_NO_TRADE_LOW,
    dpcr_no_trade_high = BOTG_DPCR_NO_TRADE_HIGH,
    partial1_done         = False,
    partial2_done         = False,
    partial1_booked_qty   = 0,
    partial2_booked_qty   = 0,
    # v-G12: which VIX/pool profile dict this bot's lock_bot_g_strike_pool()
    # call uses -- None here (harmless for A-F), set explicitly on BOT_G's
    # own BOTS[] dict below.
    vix_profile           = None,
    # v-G14: per-bot cumulative realized P/L, separate from the process-wide
    # TOTAL_REALIZED_PNL -- kept even with a single bot now, so the
    # per-bot daily profit cap (BOTG_DAILY_PROFIT_CAP_PER_BOT) still has
    # its own dedicated counter to check.
    cum_realized_pnl      = 0.0,
    # v-G15: per-bot trade-start override -- None means "use the shared
    # BOTG_TRADE_START_NORMAL/GAP_HHMM constants" (BOT_G's own behavior).
    # No longer used by anything now that BOT_G is gone, kept only so
    # PERSIST_KEYS/get_bot_g_windows() don't need a special case.
    trade_start_override_normal = None,
    trade_start_override_gap    = None,
    # v-G75/v-G76: per-trade CSV identity + flow-at-entry fields. Defaults
    # here (v-G34 lesson) because PERSIST_KEYS includes them.
    trade_id          = "",
    entry_time        = "",
    trade_pnl_acc     = 0.0,
    sl_clamped        = False,
    entry_dpcr_signed = "",
    entry_flow_dpe    = "",
    entry_flow_dce    = "",
    entry_flow_minutes= "",
    entry_flow_tier   = "",
    entry_flow_net    = "",
    entry_diag        = None,   # v-G82: dict copied from _BOTG_LAST_OI_DIAG at entry
    post_entry        = None,   # v-G83: post-entry low/high/marks tracker
)


BOTS = [
    # v-G37 (05-Sep-2026): BOT_G entry REMOVED ENTIRELY -- explicit
    # instruction. Only BOT_G runs now, and only one trade can be open at
    # a time (enforced by the existing trade_open dispatch in bot_g_tick()
    # -- see _bot_g_try_entry()'s docstring). In exchange, BOT_G no longer
    # trades one fixed strike -- it watches a small VIX-selected POOL of
    # 3 strikes at once (see BOTG_STRIKE_POOL_PROFILE in config).
    # ── BOT_G : DPCR daily-bias + option-own-VWAP rejection/live-trigger,
    #    multi-strike pool (v-G9, 10-Aug-2026: full paper-trade wiring;
    #    v-G37, 05-Sep-2026: single-strike -> pool). Does NOT go through
    #    signal()/manage()/get_option_symbol() -- routed straight to
    #    bot_g_tick() in main()'s per-bot loop instead, since its entry/
    #    exit mechanics (points-based SL, rejection-candle arm, DPCR daily
    #    lock) don't fit the generic BOT_A-F shape. Reuses execute_entry(),
    #    log_trade(), register_entry()/register_exit(), _close_bot(),
    #    allow_trade(), force_exit() -- all already generic across bot
    #    dicts -- so state persistence, trade CSV, dashboard, circuit
    #    breaker, profit-lock, and force-exit-at-1510 all apply to BOT_G
    #    automatically with no separate code path needed for those.
    #    Deliberately skips can_enter() (BASE_REENTRY_COOLDOWN_SEC) --
    #    BOT_G's own rejection-candle re-arm is its reentry gate, not a
    #    fixed timer (v-G9-FIX5).
    {
        **BOT_DEFAULTS,
        "name"             : "BOT_G",
        "qty"              : QTY_BOT_G,
        "force_exit"       : FORCE_EXIT_G,
        "mode"             : "DPCR_VWAP",
        "duplicate_exempt" : True,   # different instrument selection (weekly
                                     # multi-strike pool, own DPCR/VWAP entry)
                                     # from BOT_A-F -- same exemption pattern
                                     # as BOT_BB.
        "reentry_lock_exempt": True,   # v-G9-FIX8: no reentry cooldown of any
                                     # kind for BOT_G -- neither the flat timer
                                     # (already removed, v-G9-FIX5) nor the
                                     # v-CD2 tiered lock. Its own rejection-
                                     # candle re-arm is the intended gate.
        "losing_streak_exempt": False,   # v-G56 (bug fix, explicit
                                     # instruction): was True from v-G28
                                     # (20-Aug-2026) onward -- confirmed via
                                     # full trace this made allow_trade()'s
                                     # losing-streak check structurally
                                     # unable to ever return
                                     # LOSING_STREAK_LOCKED for BOT_G, while
                                     # the counter/cooldown-timer logging ran
                                     # unconditionally and looked like real
                                     # enforcement. On 16-Sep (Fyers), DPCR
                                     # happened to sit in the no-trade zone
                                     # for the whole 30-min window, which is
                                     # very possibly why this went unnoticed
                                     # -- if DPCR had cleared mid-window, a
                                     # 4th trade could have fired with zero
                                     # streak protection. Now False: 3
                                     # consecutive SL/TSL exits genuinely
                                     # halt new BOT_G entries for
                                     # LOSING_STREAK_COOLDOWN_SEC, independent
                                     # of DPCR or any other gate. The
                                     # counter/timer code itself was already
                                     # correct and is unchanged -- only this
                                     # exemption flag flips. Kept identical
                                     # to the Fyers file.
        "vix_profile"      : BOTG_STRIKE_POOL_PROFILE,   # v-G37
    },
]

# v-E1/v-E2 (vE4): early-entry slot. Same machinery as BOT_G; only the
# keys below differ. BOT_G above has none of these keys, so it keeps the
# v3.2 config values for every exit parameter.
if BOTGE_ENABLED:
    BOTS.append({
        **BOT_DEFAULTS,
        "name"               : "BOT_GE",
        "qty"                : QTY_BOT_G,
        "force_exit"         : FORCE_EXIT_G,
        "mode"               : "DPCR_VWAP_EARLY",
        "duplicate_exempt"   : True,
        "reentry_lock_exempt": True,
        "losing_streak_exempt": False,
        "vix_profile"        : BOTG_STRIKE_POOL_PROFILE,
        "early_slot"         : True,
        "trade_start_override_normal": BOTGE_TRADE_START_HHMM,
        "be_r_mult"          : BOTGE_BE_R_MULT,
        "tsl_arm_r_mult"     : BOTGE_TSL_ARM_R_MULT,
        "p1_r_mult"          : BOTGE_P1_R_MULT,
        "p1_pct_floor"       : BOTGE_P1_PCT_FLOOR,
        "p2_r_mult"          : BOTGE_P2_R_MULT,
        "p2_pct_floor"       : BOTGE_P2_PCT_FLOOR,
        "tsl_buffer_mode"    : "R",
        "tsl_buffer_r"       : BOTGE_TSL_BUFFER_R,
        "tsl_buffer_min_pts" : BOTGE_TSL_BUFFER_MIN_PTS,
        "tsl_buffer_max_pts" : BOTGE_TSL_BUFFER_MAX_PTS,
        "max_hold_min"       : BOTGE_MAX_HOLD_MINUTES_INITIAL,
    })


# =============================================================================
#  SECTION 7 — FILE PATHS
# =============================================================================

# v-WEEKLY1: switched from getNiftyMonthlyExpiry() to getNiftyWeeklyExpiry()
# -- the comment below's own invariant ("always agrees with what the bot is
# actually trading") would otherwise become false the moment
# get_option_symbol() switched to weekly, since file naming would silently
# stay on the old monthly cadence while actual trades moved to weekly.
# Bonus effect: log/trade/summary/state files now roll over weekly instead
# of monthly, which matches the new weekly trading cadence.
_SERIES_CODE = getNiftyWeeklyExpiry()[0]
# v-G70: one naming pattern for every file either broker's v2 bot writes:
#   <kind>_<_FILE_STEM>_<series>_<_BROKER_TAG>.<ext>
# RMoney v2 uses the identical stem, only _BROKER_TAG differs.
_FILE_STEM   = "nifty_g_pool_vE6"   # vE6 (was nifty_g_pool_vE5)
_BROKER_TAG  = "rmoney"
LOG_FILE       = f"bot_log_{_FILE_STEM}_{_SERIES_CODE}_{_BROKER_TAG}.txt"
TRADE_FILE     = f"trades_{_FILE_STEM}_{_SERIES_CODE}_{_BROKER_TAG}.csv"
SUMMARY_FILE   = f"summary_{_FILE_STEM}_{_SERIES_CODE}_{_BROKER_TAG}.csv"
STATE_FILE     = f"bot_state_{_FILE_STEM}_{_SERIES_CODE}_{_BROKER_TAG}.json"
HEARTBEAT_FILE = f"heartbeat_{_FILE_STEM}_{_BROKER_TAG}.txt"   # was heartbeat_nifty_g_pool_<series>_G4_ALLFIX_5M_VWAP.txt (set inside main())

# v-G75: identifies this process in every DPCR FLOW line and every trade
# row, so restarts / two instances writing the same day can be separated.
RUN_ID = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{os.getpid()}"


# =============================================================================
#  SECTION 8 — RUNTIME STATE  (do not edit — managed by code)
# =============================================================================

# ── Dashboard heartbeat (control-room web dashboard) ────────────────────────
# Reports this bot's live P/L to the local dashboard backend once per main
# loop cycle, and receives back "run" or "halt". Fully isolated from trading
# logic: if the dashboard is offline, send_dashboard_heartbeat() just returns
# "run" and the bot keeps trading exactly as before this was added.
import requests as _dash_requests
DASHBOARD_URL = "http://localhost:8000"
BOT_ID = "NIFTY_RMONEY_G"   # v-G13: own dashboard cell, separate from "NIFTY_FYERS"
_LIVE_UNREALISED_PNL = 0.0  # kept fresh inside check_profit_lock() each cycle

def send_dashboard_heartbeat(pnl, status="running", bot_id=None):
    """
    v-G14: bot_id param added -- BOT_G and BOT_G now each post their own
    heartbeat under their own dashboard identity (see the call site in
    main()) instead of one combined process-wide number, which merged
    their P/L and defeated the point of running them side by side for
    comparison. Defaults to the process-wide BOT_ID if not passed, so
    nothing else in the file needs to change.
    """
    try:
        r = _dash_requests.post(
            f"{DASHBOARD_URL}/status/{bot_id or BOT_ID}",
            json={"pnl": pnl, "status": status},
            timeout=2,
        )
        return r.json().get("command", "run")
    except Exception:
        return "run"


# v-G9-FIX4: this was written in heartbeat_snippet.py with an explicit note
# that it was "not wired into any bot file yet -- BOT_G isn't in BOTS[]/
# main() dispatch, still log-only." That's no longer true as of v-G9 (BOT_G
# is fully wired and paper-trading), but the actual call to this function
# was never added anywhere -- so /botg_series stayed empty even after BOT_G
# went live, and the dashboard's DPCR/Nifty charts had nothing to plot.
# Called from _bot_g_try_entry() every time get_current_dpcr() returns a
# real value (i.e. every 3m candle once past the anchor time) -- same
# fail-soft pattern as send_dashboard_heartbeat() above, never blocks
# trading if the dashboard is offline.
DASH_BROKER = "RMONEY"   # v-E10: tags this bot's dashboard series


def send_botg_reading(dpcr, raw, nifty_spot, zone=None):
    """v-E10: dpcr = SIGNED DPCR (-1..+1, the decision value); raw = PE/CE
    ratio (display only); zone = upper edge of today's no-trade zone."""
    try:
        _dash_requests.post(
            f"{DASHBOARD_URL}/botg_reading",
            json={"dpcr": dpcr, "raw": raw, "nifty_spot": nifty_spot,
                  "broker": DASH_BROKER, "zone": zone},
            timeout=2,
        )
    except Exception:
        pass

TOTAL_REALIZED_PNL     = 0.0
CIRCUIT_BREAKER_LOCKED = False

# FIX-6: profit-lock runtime state
SESSION_PEAK_PNL    = 0.0    # highest TOTAL_REALIZED_PNL reached today
PROFIT_LOCK_ACTIVE  = False  # True once PnL >= MAX_DAILY_PROFIT
PROFIT_LOCK_SEALED  = False  # True once trail fires — no more entries, exit all

PORTFOLIO = {
    "max_open_trades": MAX_OPEN_TRADES,
    "max_total_qty"  : MAX_PORTFOLIO_QTY,
    "current_qty"    : 0,
    "open_trades"    : 0,
    "direction"      : None,
    "blocked_until"  : 0,
}

SYSTEM_EXIT = False

# v2.9-S7: India VIX runtime state
_VIX_VALUE       = None
_VIX_FETCH_HHMM  = 0
_VIX_FETCH_TIMES = [920, 1230]

# v2.9-O10: Losing streak tracker (global, legacy — used when LOSING_STREAK_PER_BOT=False)
_CONSECUTIVE_SL_COUNT = 0

# v3.0: Per-bot losing-streak tracker with cooldown, used when
# LOSING_STREAK_PER_BOT=True (the new default). Keyed by bot name.
_BOT_SL_STREAK   = {}
_BOT_LOCK_UNTIL  = {}


def _bot_streak_locked(bot_name):
    """
    v3.0: Returns True if this bot is currently halted by the per-bot
    losing-streak cooldown. Auto re-arms (clears the lock and resets the
    streak) once LOSING_STREAK_COOLDOWN_SEC has elapsed, unless COOLDOWN_SEC
    is 0 (permanent lock for the day, matching the old v2.9 behaviour).
    """
    until = _BOT_LOCK_UNTIL.get(bot_name, 0)
    if until <= 0:
        return False
    if until == float("inf"):
        return True
    if time.time() >= until:
        _BOT_LOCK_UNTIL[bot_name] = 0
        _BOT_SL_STREAK[bot_name]  = 0
        log(f"STREAK       | {bot_name} cooldown expired — re-armed for new entries.")
        return False
    return True

# FIX-3: consecutive fetch failure tracking
_FETCH_FAIL_COUNT = 0
_FETCH_FAIL_LIMIT = 5      # lenient — only suppresses after 5 straight failures
_DATA_HEALTHY     = True

# v3.19-STALEFIX1: how old the last fetched 3m candle is allowed to be
# before fetch_data() treats it as a fetch failure (not just an empty
# response). v-RG3 (23-Aug-2026): 360 -> 420 -- real paper-trade log
# (25-Aug-2026) showed recurring 366-419s readings, self-correcting
# within a cycle or two, consistent with RMoney/XTS's OHLC feed having a
# modest lag (30-60s) before a just-closed candle appears -- not a
# genuinely stalled feed. 420s = 2 candle-widths + ~1min slack for that
# lag, while still catching a real multi-minute stall (like the
# 91-minute one on 2026-08-03 that motivated this check originally).
STALE_CANDLE_SEC = 420


# =============================================================================
#  SECTION 9 — STATE PERSISTENCE
# =============================================================================

PERSIST_KEYS = [
    "name", "trade_open", "entry", "entry_spot", "entry_symbol",
    "highest", "active_sl", "side", "sl_lock_until", "partial_done",
    "qty", "sl_order_id", "entry_hhmm", "entry_epoch",
    "reentry_block_side", "reentry_block_until",   # v3.1-R3
    # v-G9: BOT_G daily-lock + rejection-arm + points-based SL state --
    # harmless no-ops for BOT_A-F (their code never reads these). Needed so
    # a same-day restart doesn't lose the current direction lock (v-G25:
    # no longer permanent, but still needs to survive a restart -- losing
    # it would mean re-deciding from scratch, not resuming) or an
    # in-progress trade's BE/TSL stage.
    "locked_side", "gap_day", "gap_pct",
    # v-G37: otm_pool/pool_state REPLACE the old scalar rejection_armed/
    # rejection_low/rejection_vwap/rejection_symbol/rejection_candle_key/
    # otm_steps keys -- pool_state is a nested dict (str(otm_steps) ->
    # per-strike state), plain JSON-serializable, no special handling
    # needed in save_state()/load_state()'s existing generic copy loop.
    "otm_pool", "pool_state",
    "initial_sl", "risk_pts", "be_level", "arm_level", "stage", "armed",
    "highest_close_since_arm",
    "vix_locked_open", "vix_locked_2pm", "vix_value", "qty_base",
    "v53_gate_vix", "v53_gate_block",   # v-E53 (vE6.13): survives a mid-day restart
    "dpcr_no_trade_low", "dpcr_no_trade_high",
    "partial1_done", "partial2_done", "partial1_booked_qty", "partial2_booked_qty",
    "cum_realized_pnl",   # v-G14: per-bot dashboard P/L
    # v-G75/v-G76: so a mid-trade restart still writes a complete CSV row
    "trade_id", "entry_time", "trade_pnl_acc", "sl_clamped", "entry_dpcr_signed",
    "entry_flow_dpe", "entry_flow_dce", "entry_flow_minutes", "entry_flow_tier", "entry_flow_net",
    "entry_diag",   # v-G82
    "post_entry",   # v-G83
]


def save_state():
    payload = {
        "date"                  : str(date.today()),
        "TOTAL_REALIZED_PNL"    : TOTAL_REALIZED_PNL,
        "SESSION_PEAK_PNL"      : SESSION_PEAK_PNL,
        "PROFIT_LOCK_ACTIVE"    : PROFIT_LOCK_ACTIVE,
        "PROFIT_LOCK_SEALED"    : PROFIT_LOCK_SEALED,
        "CIRCUIT_BREAKER_LOCKED": CIRCUIT_BREAKER_LOCKED,
        "BOT_SL_STREAK"         : _BOT_SL_STREAK,
        "BOT_LOCK_UNTIL"        : _BOT_LOCK_UNTIL,
        "PORTFOLIO"             : PORTFOLIO,
        "bots"                  : [{k: b[k] for k in PERSIST_KEYS} for b in BOTS],
    }
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp, STATE_FILE)


def _broker_reconcile():
    """
    v-RG2: fail-closed startup reconciliation against RMoney/XTS.
    We never silently trust JSON state in LIVE mode.
    """
    if PAPER_TRADE:
        return True
    positions = _get_positions_rmoney()
    if positions is None:
        raise RuntimeError("RMoney positions query failed; LIVE startup blocked")

    broker_positions = _find_nonzero_nifty_fo_positions()
    if broker_positions is None:
        raise RuntimeError("RMoney positions query failed; LIVE startup blocked")

    open_bots = [b for b in BOTS if b.get("trade_open")]
    if not open_bots:
        if broker_positions:
            raise RuntimeError(f"Unexpected NIFTY F&O broker positions at startup: {broker_positions}. "
                               "Refusing LIVE start to prevent unmanaged positions.")
        log("RECONCILE    | PASS — broker NIFTY F&O position is flat and local state is flat")
        return True

    if len(open_bots) != 1:
        raise RuntimeError(f"Unexpected local BOT_G state: {len(open_bots)} open bots")

    bot = open_bots[0]
    broker_qty = _check_existing_position(bot["entry_symbol"])
    if broker_qty is None:
        raise RuntimeError("Could not query broker position for restored BOT_G trade")
    expected = int(bot.get("qty", 0))
    if broker_qty != expected:
        raise RuntimeError(f"POSITION MISMATCH for {bot['entry_symbol']}: local={expected}, broker={broker_qty}")

    extras = [(sym, q) for sym, q in broker_positions if str(sym) != str(bot["entry_symbol"]) and q]
    if extras:
        raise RuntimeError(f"Unexpected additional NIFTY F&O broker positions: {extras}")

    if not bot.get("initial_sl") or bot.get("active_sl") is None:
        raise RuntimeError("Restored BOT_G position has no valid SL state; LIVE start blocked")

    existing_sl = _find_open_sl_order_rmoney(bot["entry_symbol"])
    if existing_sl:
        bot["sl_order_id"] = existing_sl
        log(f"RECONCILE    | PASS — broker protective SL found OrderID:{existing_sl}")
    else:
        # Restore protection immediately from persisted active SL; do not run live
        # with an unmanaged option position.
        log(f"RECONCILE    | No open broker SL found for {bot['entry_symbol']} — placing protection now")
        bot["sl_order_id"] = None
        update_broker_sl_order(bot, bot["active_sl"])
        if not bot.get("sl_order_id"):
            raise RuntimeError("Could not restore broker-side SL for restored BOT_G position")
        verified = _find_open_sl_order_rmoney(bot["entry_symbol"])
        if not verified:
            raise RuntimeError("Broker-side SL could not be verified after placement")
        bot["sl_order_id"] = verified
    return True


def load_state():
    global TOTAL_REALIZED_PNL, CIRCUIT_BREAKER_LOCKED
    global SESSION_PEAK_PNL, PROFIT_LOCK_ACTIVE, PROFIT_LOCK_SEALED

    if not os.path.exists(STATE_FILE):
        log("STATE | No state file found — fresh start.")
        return
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        log(f"STATE | Could not read state file: {e} — fresh start.")
        return

    saved_date = data.get("date", "")
    today      = str(date.today())
    if saved_date != today:
        log(f"STATE | Saved date {saved_date} != today {today}. "
            f"Daily counters reset. No positions restored.")
        TOTAL_REALIZED_PNL     = 0.0
        SESSION_PEAK_PNL       = 0.0
        PROFIT_LOCK_ACTIVE     = False
        PROFIT_LOCK_SEALED     = False
        CIRCUIT_BREAKER_LOCKED = False
        _BOT_SL_STREAK.clear()
        _BOT_LOCK_UNTIL.clear()
        return

    TOTAL_REALIZED_PNL     = data.get("TOTAL_REALIZED_PNL", 0.0)
    SESSION_PEAK_PNL       = data.get("SESSION_PEAK_PNL", 0.0)
    PROFIT_LOCK_ACTIVE     = data.get("PROFIT_LOCK_ACTIVE", False)
    PROFIT_LOCK_SEALED     = data.get("PROFIT_LOCK_SEALED", False)
    CIRCUIT_BREAKER_LOCKED = data.get("CIRCUIT_BREAKER_LOCKED", False)
    _BOT_SL_STREAK.update(data.get("BOT_SL_STREAK", {}))
    _BOT_LOCK_UNTIL.update(data.get("BOT_LOCK_UNTIL", {}))
    PORTFOLIO.update(data.get("PORTFOLIO", {}))

    restored = 0
    for saved_bot in data.get("bots", []):
        for bot in BOTS:
            if bot["name"] == saved_bot["name"]:
                for k in PERSIST_KEYS:
                    if k in saved_bot:
                        bot[k] = saved_bot[k]
                if bot["trade_open"]:
                    restored += 1
                break

    log(f"STATE | Restored from {saved_date}. Open positions: {restored}. "
        f"PnL: Rs{round(TOTAL_REALIZED_PNL,2)}. "
        f"PeakPnL: Rs{round(SESSION_PEAK_PNL,2)}. "
        f"ProfitLock: {PROFIT_LOCK_ACTIVE}. "
        f"Sealed: {PROFIT_LOCK_SEALED}. "
        f"CB: {CIRCUIT_BREAKER_LOCKED}.")
    if CIRCUIT_BREAKER_LOCKED:
        log("STATE | Circuit breaker was LOCKED — no new entries today.")
    if PROFIT_LOCK_SEALED:
        log("STATE | Profit lock was SEALED — no new entries today.")


# =============================================================================
#  SECTION 10 — LOGGING UTILITIES  (RotatingFileHandler)
# =============================================================================

_log_handler  = RotatingFileHandler(
    LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=30, encoding="utf-8"
)
_log_handler.setFormatter(logging.Formatter("%(message)s"))
_logger = logging.getLogger("bot_rmoney")
_logger.setLevel(logging.DEBUG)
_logger.addHandler(_log_handler)


def log(msg):
    t    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{t} | {msg}"
    print(line)
    _logger.info(line)


# =============================================================================
#  TELEGRAM ALERTS  (v2.8-L6)
#  Fill in your token and chat ID below to enable. Leave blank to disable.
# =============================================================================

def tg(msg):
    """
    v2.9-D6: Send Telegram message via daemon thread.
    Async — Telegram latency never blocks trading loop.
    """
    token  = ""   # paste your bot token here e.g. "7412563890:AAFxxx..."
    chatid = ""   # paste your chat ID here  e.g. "912345678"
    if not token or not chatid:
        return
    def _send():
        try:
            import requests as _req
            _req.get(
                f"https://api.telegram.org/bot{token}/sendMessage",
                params={"chat_id": chatid, "text": f"[NF-RMoney]\n{msg}"},
                timeout=5
            )
        except Exception:
            pass
    threading.Thread(target=_send, daemon=True).start()


_last_heartbeat = 0.0   # v2.8-L7: heartbeat tracker
_LAST_DASHBOARD_SIG = None   # v3.19-LOGFIX1: last-printed dashboard signature


# v-G76: v2 schema. One row per LEG (partial booking or final exit),
# grouped by trade_id; leg_type = PARTIAL / FINAL; trade_pnl filled on the
# FINAL row only (whole-trade P&L incl. partials). Legacy BOT_A-F columns
# (adx/rsi/orb/tsi/entry_reason...) dropped -- always blank for BOT_G.
# v-G82: diagnostic columns appended to every trade row (values = the
# latest OI/ATM diagnostic at entry; diag_age_sec = how old it was).
# v-G83: post-entry response columns (FINAL row only).
_POST_ENTRY_KEYS = (["pe_low", "pe_low_sec", "mae_pts", "mae_r",
                     "pe_high", "pe_high_sec", "mfe_pts", "mfe_r"]
                    + [f"ltp_{m}m" for m in BOTG_POST_ENTRY_MARKS_MIN]
                    + [f"ret_{m}m_r" for m in BOTG_POST_ENTRY_MARKS_MIN])


# v-G84: per-trade price path (LOG ONLY). See header.
PATH_FILE = f"trade_paths_{_FILE_STEM}_{_SERIES_CODE}_{_BROKER_TAG}.csv"
_PATH_HEADER = ("ts,trade_id,run_id,bot,symbol,side,entry,risk_pts,elapsed_sec,ltp,"
                "r_now,mfe_r_sofar,mae_r_sofar,qty_open,stage,active_sl")
_PATH_BUF = []
_PATH_LAST = {}   # trade_id -> (ltp, epoch) of the last row written


def _path_flush():
    """v-G84: append buffered path rows. Fail-soft; never raises."""
    if not _PATH_BUF:
        return
    rows = _PATH_BUF[:]
    del _PATH_BUF[:]
    try:
        new = not os.path.exists(PATH_FILE)
        with open(PATH_FILE, "a", encoding="utf-8") as f:
            if new:
                f.write(_PATH_HEADER + "\n")
            f.write("".join(rows))
    except Exception as e:
        log(f"PATH LOG | write failed (ignored, log-only): {e}")


def _path_record(bot, ltp):
    """v-G84: one path row for this tick if LTP changed, or every
    BOTG_PATH_HEARTBEAT_SEC. Called before the tick's exit decision."""
    if not BOTG_PATH_LOG_ENABLED or not ltp or ltp <= 0 or not bot.get("entry_epoch"):
        return
    tid = bot.get("trade_id") or ""
    now = time.time()
    last = _PATH_LAST.get(tid)
    if last is not None and ltp == last[0] and (now - last[1]) < BOTG_PATH_HEARTBEAT_SEC:
        return
    _PATH_LAST[tid] = (ltp, now)
    entry = bot.get("entry") or 0.0
    risk = bot.get("risk_pts") or 0.0
    pe = bot.get("post_entry") or {}
    def _r(v):
        return round(v / risk, 3) if (v is not None and risk > 0) else ""
    mfe = (pe["high"] - entry) if pe.get("high") is not None else None
    mae = (entry - pe["low"]) if pe.get("low") is not None else None
    vals = [datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3], tid, RUN_ID, bot["name"],
            bot.get("entry_symbol", ""), bot.get("side", ""), entry, round(risk, 2),
            round(now - bot["entry_epoch"], 1), ltp, _r(ltp - entry), _r(mfe), _r(mae),
            bot.get("qty", ""), bot.get("stage", ""), bot.get("active_sl", "")]
    _PATH_BUF.append(",".join(str(v) for v in vals) + "\n")
    if len(_PATH_BUF) >= BOTG_PATH_FLUSH_ROWS:
        _path_flush()


# =============================================================================
# vE6.2 v-E19/v-E20/v-E21 -- trackers, day type, data-lost handling (log-only
# except DATA_LOST closing a PAPER trade so it appears in the trade CSV).
# =============================================================================
TRACK_FILE = f"post_exit_paths_{_FILE_STEM}_{_SERIES_CODE}_{_BROKER_TAG}.csv"
TRACK_SUM_FILE = f"post_exit_summary_{_FILE_STEM}_{_SERIES_CODE}_{_BROKER_TAG}.csv"
LIVECMP_FILE = f"livecmp_{_FILE_STEM}_{_SERIES_CODE}_{_BROKER_TAG}.csv"
_TRACK_HDR = "ts,kind,ref_id,bot,symbol,side,ref_price,elapsed_sec,ltp"
_TRACK_SUM_HDR = ("ts,kind,ref_id,bot,symbol,side,ref_price,entry,sl,p1,p2,max_ltp,max_sec,"
                  "min_ltp,min_sec,ltp_5m,ltp_15m,ltp_30m,outcome,outcome_sec,polls,day_type,"
                  "pct_from_open,cflow9_dce,status")
_BOTG_TRACK = []
_TRACK_STATE = {"last": 0.0}
_BOTG_DAY = {"date": None, "open": None, "high": None, "low": None, "hist": []}
_DATA_STALE = {"t": None, "alerted": set()}


def _append_csv(path, header, rows):
    if not rows:
        return
    try:
        new = not os.path.exists(path)
        with open(path, "a", encoding="utf-8") as f:
            if new:
                f.write(header + "\n")
            f.write("".join(rows))
    except Exception as e:
        log(f"vE6.2 TRACK | write failed (ignored, log-only): {e}")


def _day_track(spot, df3=None):
    """v-E20: day open (first reading at/after 09:15 -- approximate after a
    mid-day restart), running high/low and a 40-min spot history."""
    if not spot or spot <= 0:
        return
    st = _BOTG_DAY
    if st["date"] != date.today():
        st.update(date=date.today(), open=None, high=None, low=None, hist=[], open_915=False,
                  ext1015=None, ext_src="", ref915=None)   # v-E35, v-E39
    if hhmm() < 915:
        return
    now = time.time()
    if st["open"] is None:
        st["open"] = spot
        log(f"vE6.2 DAY OPEN | first spot reading {spot} used as day open (v-E20)")
    if not st.get("open_915") and df3 is not None:   # v-E32 (vE6.2.3)
        _c915 = _zlm.candle_915(df3)
        if _c915 and _c915.get("open"):
            log(f"vE6.2.3 DAY OPEN | 09:15 3m candle open {_c915['open']} used as day open "
                f"(first reading was {st['open']}) (v-E32, log-only)")
            st["open"], st["open_915"] = _c915["open"], True
    if st.get("ext1015") is None and st["open"] and hhmm() >= 1015:   # v-E35 (vE6.2.4), log-only
        st["ext1015"] = round(100.0 * (spot - st["open"]) / st["open"], 3)
        st["ext_src"] = "ok" if hhmm() <= 1018 else "late"
        log(f"vE6.2.4 EXT1015 | spot {spot} vs day open {st['open']} -> {st['ext1015']}% "
            f"({st['ext_src']}) (v-E35, log-only)")
    if st.get("ref915") is None and df3 is not None and V39_COMMON_ANCHOR and hhmm() >= 918:   # v-E39
        _r915 = _v39_ref915_from(df3)
        if _r915:
            st["ref915"] = _r915
            log(f"vE6.4 COMMON ANCHOR | reference = closed 09:15 3m candle close {_r915} "
                f"(live spot {spot}) (v-E39)")
    st["high"] = spot if st["high"] is None else max(st["high"], spot)
    st["low"] = spot if st["low"] is None else min(st["low"], spot)
    if not st["hist"] or now - st["hist"][-1][0] >= 15:
        st["hist"].append((now, spot))
    st["hist"] = [x for x in st["hist"] if x[0] >= now - 40 * 60]


_DAY_KEYS = ["day_open", "day_high", "day_low", "pct_from_open", "pos_in_range", "spot_30m_chg", "day_type"]


# =============================================================================
# vE6.2.4 v-E35 -- SETUP TAGS (log-only). Row arithmetic lives in the shared
# setup_tags_nifty_vE6.py; this wrapper only gathers context. Never changes any
# bot state, never calls the broker.
# =============================================================================
# =============================================================================
# vE6.4 v-E39 -- common first DPCR anchor (closed 09:15 3-min candle close).
# =============================================================================
_V39_LOG = {"date": None, "wait": False, "giveup": False}


def _v39_ref915_from(df3):
    """v-E39: today's 09:15 3-min candle close, only once that candle is CLOSED
    (df3 already has a row at or after 09:18 today). None otherwise."""
    try:
        if df3 is None or len(df3) == 0:
            return None
        today = date.today()
        idx = df3.index
        closed = any(ts.date() == today and (ts.hour, ts.minute) >= (9, 18) for ts in idx)
        if not closed:
            return None
        c = _zlm.candle_915(df3, today)
        return round(float(c["close"]), 2) if c and c.get("close") else None
    except Exception:
        return None


def _v39_anchor_wait(bot, gap_day, now_hhmm):
    """v-E39: True = do not run the DPCR fetch yet (no 3-min bucket used):
    normal day, 09:18-09:20, no anchor yet today and the 09:15 reference
    not captured yet. Gives up at V39_ANCHOR_WAIT_UNTIL_HHMM (live spot)."""
    if not V39_COMMON_ANCHOR or gap_day or now_hhmm < 918:
        return False
    if _v39_anchor_set_today():
        return False
    if _BOTG_DAY.get("date") == date.today() and _BOTG_DAY.get("ref915"):
        return False
    if _V39_LOG["date"] != date.today():
        _V39_LOG.update(date=date.today(), wait=False, giveup=False)
    if now_hhmm < V39_ANCHOR_WAIT_UNTIL_HHMM:
        if not _V39_LOG["wait"]:
            _V39_LOG["wait"] = True
            log("vE6.4 COMMON ANCHOR | waiting for the closed 09:15 3m candle before the first DPCR anchor (v-E39)")
        return True
    if not _V39_LOG["giveup"]:
        _V39_LOG["giveup"] = True
        log(f"vE6.4 COMMON ANCHOR | no closed 09:15 candle by {V39_ANCHOR_WAIT_UNTIL_HHMM} -> first anchor on the live spot (v-E39)")
    return False


# =============================================================================
# vE6.6 v-E43 -- ZLM check at entry (log-only): does the ZLM state agree?
# =============================================================================
def _v43_zlm_tag(bot, side, spot):
    """v-E43: log the ZLM state at entry; returns ' | zlm <state> <verdict>' for the setup tag."""
    if not V43_ZLM_TAG:
        return ""
    try:
        z = _zlm.state_now()
        if z is None:
            z, verdict = "NA", "NA"
        else:
            verdict = "AGREE" if z == side else ("NEUTRAL" if z == "-" else "AGAINST")
        ref = _zlm._ST.get("ref") if _zlm._ST else None
        dist = round(spot - ref, 1) if (ref and spot) else "NA"
        log(f"{bot['name']} ZLM CHECK | entry {side} | ZLM state {z} (spot-ref {dist}) -> {verdict} | "
            f"a 'ZLM must agree' rule would {'ALLOW' if verdict == 'AGREE' else 'SKIP'} this entry (v-E43, log-only)")
        return f" | zlm {z} {verdict}"
    except Exception as e:
        log(f"vE6.6 ZLM CHECK | error (ignored, log-only): {e}")
        return ""


# =============================================================================
# vE6.8 v-E45 -- ENTRY CONTEXT line (log-only): the candidate filters in one place.
# =============================================================================
def _v45_spot_chg(spot, sec):
    """Nifty spot change over the last `sec` seconds from the 15-s day history (None if not enough)."""
    h = _BOTG_DAY.get("hist") or []
    now = time.time()
    old = [x for x in h if x[0] <= now - sec]
    return round(spot - old[-1][1], 1) if (old and spot) else None


def _v45_entry_context(bot, side, spot):
    """v-E45: log DPCR / ZLM / spot direction / flow tier at entry with a warning count."""
    if not V45_ENTRY_CONTEXT:
        return
    try:
        c15, c30 = _v45_spot_chg(spot, 900), _v45_spot_chg(spot, 1800)
        sgn = 1 if side == "CE" else -1
        w15 = None if c15 is None else round(sgn * c15, 1)
        sp = ("NA" if w15 is None else "AGAINST" if w15 <= -V45_SPOT_AGAINST_PTS
              else "WITH" if w15 >= V45_SPOT_AGAINST_PTS else "FLAT")
        z = _zlm.state_now()
        zv = "NA" if z is None else ("AGREE" if z == side else ("NEUTRAL" if z == "-" else "AGAINST"))
        tier = bot.get("entry_flow_tier") or "NA"
        warn = [n for n, bad in (("ZLM", zv != "AGREE"), ("SPOT", sp == "AGAINST"), ("FLOW", tier != "MOST")) if bad]
        w30 = None if c30 is None else round(sgn * c30, 1)   # v-E46
        gate = "SKIP" if (w15 is not None and w30 is not None and w15 <= -V45_SPOT_AGAINST_PTS and w30 < 0) else "ALLOW"
        log(f"{bot['name']} ENTRY CONTEXT | TradeID:{bot.get('trade_id')} Side:{side} | DPCR {bot.get('entry_dpcr_signed', 'NA')} | "
            f"ZLM {z if z is not None else 'NA'} {zv} | spot 15m {c15 if c15 is not None else 'NA'} 30m "
            f"{c30 if c30 is not None else 'NA'} -> {sp} for {side} (+/-{V45_SPOT_AGAINST_PTS:g}) | flow tier {tier} | "
            f"warnings {len(warn)}/3 {','.join(warn) if warn else '-'} | gate15+30 {gate} | "
            f"shadow lock {(_V46['side'] or '-') if _V46.get('date') == date.today() else '-'} (v-E45/v-E46, log-only)")
    except Exception as e:
        log(f"vE6.8 ENTRY CONTEXT | error (ignored, log-only): {e}")


# =============================================================================
# vE6.9 v-E46 -- SHADOW LOCK (log-only): zone +/-V46_ZONE + spot 30-min sync.
# =============================================================================
_V46 = {"date": None, "side": None}
_V47 = {"date": None, "keys": set()}


def _v46_shadow(bot, hist, spot, now_hhmm, trade_start_hhmm):
    """v-E46: log the shadow lock for this 3-min candle (never touches bot state)."""
    if not (V46_SHADOW_LOCK or V47_OPTION_TAPE) or not hist:
        return
    try:
        if V47_OPTION_TAPE and spot and now_hhmm >= 915:
            _v47_note_strikes(spot)
        if not V46_SHADOW_LOCK:
            return
        if _V46["date"] != date.today():
            _V46.update(date=date.today(), side=None)
        v = float(hist[-1])
        c30 = _v45_spot_chg(spot, 1800)
        want = "CE" if v >= V46_ZONE else ("PE" if v <= -V46_ZONE else None)
        note = ""
        if now_hhmm >= trade_start_hhmm and want and want != _V46["side"]:
            if c30 is not None and ((want == "CE" and c30 >= V46_SYNC_PTS) or (want == "PE" and c30 <= -V46_SYNC_PTS)):
                _V46["side"] = want
                note = f"shadow lock -> {want}"
            else:
                note = f"{want} wanted but spot 30m {c30 if c30 is not None else 'NA'} not in sync"
        real = bot.get("locked_side")
        log(f"{bot['name']} SHADOW LOCK | DPCR {v:+.3f} spot30 {c30 if c30 is not None else 'NA'} | real {real or '-'} | "
            f"Z{V46_ZONE:g}+sync {_V46['side'] or '-'}" + (" | DIFFERS" if (real or None) != _V46["side"] else "")
            + (f" | {note}" if note else "") + " (v-E46, log-only)")
    except Exception as e:
        log(f"vE6.9 SHADOW LOCK | error (ignored, log-only): {e}")


def _v47_note_strikes(spot):
    """v-E47: remember today's ATM +/-V47_STEPS strikes (CE and PE) for the end-of-day tape."""
    if _V47["date"] != date.today():
        _V47.update(date=date.today(), keys=set())
    atm = round50(spot)
    for k in range(-V47_STEPS, V47_STEPS + 1):
        for sd in ("CE", "PE"):
            _V47["keys"].add((atm + k * STRIKE_ROUND_UNIT, sd))


def _v47_write_tape():
    """v-E47: at shutdown, fetch today's 1-min OHLCV for the noted strikes -> option_tape CSV."""
    if not V47_OPTION_TAPE or _V47["date"] != date.today() or not _V47["keys"]:
        return
    try:
        _code, _exp = getNiftyWeeklyExpiry()
        _sx = _bot_g_symbol_expiry_code(_exp)
        keys = sorted(_V47["keys"])[:V47_MAX_SYMBOLS]
        out = f"option_tape_{date.today():%Y%m%d}_{_BROKER_TAG}.csv"
        n_ok = n_rows = 0
        with open(out, "w", encoding="utf-8") as f:
            f.write("date,time,symbol,expiry,strike,side,open,high,low,close,volume\n")
            for strike, sd in keys:
                sym = _v47_symbol(_sx, strike, sd)
                try:
                    rows = _v47_fetch_1m(sym)
                except Exception as e:
                    log(f"vE6.9 OPTION TAPE | {sym} fetch error (ignored): {e}")
                    rows = []
                if rows:
                    n_ok += 1
                for t, o, h, l, c, v in rows:
                    if t.date() != date.today():
                        continue
                    f.write(f"{t:%Y-%m-%d},{t:%H:%M},{sym},{_exp.isoformat()},{strike},{sd},{o},{h},{l},{c},{v}\n")
                    n_rows += 1
                time.sleep(V47_SLEEP_SEC)
        log(f"vE6.9 OPTION TAPE | {out}: {n_ok}/{len(keys)} symbols, {n_rows} 1-min rows, expiry {_exp.isoformat()} (v-E47, log-only)")
    except Exception as e:
        log(f"vE6.9 OPTION TAPE | failed (ignored): {e}")


def _v47_symbol(sx, strike, sd):
    return f"NIFTY{sx}{strike}{sd}"


def _v47_fetch_1m(sym):
    """v-E47 (RMoney/XTS): today's native 1-min candles -> [(IST datetime, o, h, l, c, v)]."""
    eid = _resolve_option_eid(sym)
    if eid is None:
        return []
    start_dt = datetime.combine(date.today(), datetime.min.time()).replace(hour=9, minute=15)
    fmt = "%b %d %Y %H%M%S"
    resp = _HTTP.get(f"{MARKETDATA_URL}/instruments/ohlc", headers=_md_headers(),
                     params={"exchangeSegment": NIFTY_FO_SEGMENT, "exchangeInstrumentID": eid,
                             "startTime": start_dt.strftime(fmt), "endTime": datetime.now().strftime(fmt),
                             "compressionValue": 1}, timeout=10)
    if resp.status_code != 200:
        return []
    data = resp.json()
    raw = (data.get("result") or {}).get("dataReponse", "") if data.get("type") == "success" else ""
    out = []
    for r in _parse_ticks(raw) if raw else []:
        t = datetime(1970, 1, 1) + timedelta(seconds=int(r["ts"]))   # XTS ts is IST-encoded (same as the 5m path)
        out.append((t, r["open"], r["high"], r["low"], r["close"], r["volume"]))
    return out


def _v39_anchor_ref(gap_day):
    """v-E39: the reference passed to compute_dpcr() (None = live spot)."""
    if not V39_COMMON_ANCHOR or gap_day or hhmm() >= V39_ANCHOR_REF_UNTIL_HHMM:
        return None
    if _BOTG_DAY.get("date") != date.today():
        return None
    return _BOTG_DAY.get("ref915")


def _v39_anchor_set_today():
    """v-E39: has the DPCR module already set today's first anchor?"""
    st = _oc_filter._STATE
    return st.get("date") == date.today() and st.get("anchor") is not None


def _v42_pre_snapshot(spot):
    """v-E42 (vE6.6, RMoney): while waiting for the 09:15 reference, read the
    OI around the live spot at the 09:18 boundary (kept as the first baseline)."""
    if not V42_RMONEY_PRE_SNAPSHOT:
        return
    try:
        msg = _oc_filter.pre_snapshot(_md_headers(), spot,
                                      _bot_g_symbol_expiry_code(_nearest_nifty_weekly_expiry_date()),
                                      dpcr_window=get_bot_g_dpcr_window_today())
        if msg:
            log(f"vE6.6 {msg}")
    except Exception as e:
        log(f"vE6.6 PRE-SNAPSHOT | error (ignored, old rule applies): {e}")


# =============================================================================
# vE6.3 v-E36 -- EXIT WHAT-IF shadow (log-only). The plans are simulated in the
# shared exit_whatif_nifty_vE6.py; this wrapper only passes the trade's own
# levels and LTPs. Never changes any bot state, never calls the broker.
# =============================================================================
WHATIF_FILE = f"exit_whatif_{_FILE_STEM}_{_BROKER_TAG}.csv"
_V36_ERR = {"n": 0}


def _v36_safe(fn):
    """v-E36: run a what-if call; any error -> at most 5 log lines, trading untouched."""
    if not WHATIF_ENABLED:
        return
    try:
        fn()
    except Exception as e:
        _V36_ERR["n"] += 1
        if _V36_ERR["n"] <= 5:
            log(f"vE6.3 WHATIF | error (ignored, log-only): {e}")


def _v36_tick(bot, ltp):
    """v-E36: feed one live LTP of the open trade (registers the trade on first sight)."""
    if not _wi.CTX:
        _wi.configure(log, {k: v for k, v in globals().items() if k.startswith("WHATIF_")}, WHATIF_FILE)
    tid = bot.get("trade_id")
    if not tid:
        return
    if tid not in _wi._T:
        p1, p2 = _botg_targets(bot, bot["entry"], bot["risk_pts"])
        try:
            t0 = datetime.strptime(bot.get("entry_time") or "", "%Y-%m-%d %H:%M:%S")
        except Exception:
            t0 = datetime.now()
        qty0 = (bot.get("_lc") or {}).get("qty0") or bot.get("qty_base") or bot["qty"]
        late = bool(bot.get("partial1_done") or bot.get("partial2_done") or (datetime.now() - t0).total_seconds() > 120)
        _wi.start(tid, bot["name"], bot.get("entry_symbol"), bot["side"], bot["entry"], bot["initial_sl"], qty0,
                  bot["be_level"], p1, p2, bot["arm_level"], _botg_tsl_buffer(bot),
                  BOTG_PARTIAL_R1_FRACTION, BOTG_PARTIAL_R15_FRACTION, t0, late)
        log(f"{bot['name']} WHATIF START | {tid} entry {bot['entry']} SL {bot['initial_sl']} R {round(bot['risk_pts'], 2)} "
            f"qty {qty0} | early bank {WHATIF_EB_LOTS} lot @ {round(bot['entry'] + WHATIF_EB_R * bot['risk_pts'], 2)} "
            f"| time stop {WHATIF_TS_MIN:g} min unless {round(bot['entry'] + WHATIF_TS_R * bot['risk_pts'], 2)}"
            + (f" | LOW STOP: R {round(bot['risk_pts'], 2)} < {WHATIF_LOW_STOP_PTS:g} pts, min-stop plans "
               f"{list(WHATIF_MS_PTS)} (v-E40)" if bot['risk_pts'] < WHATIF_LOW_STOP_PTS else "")
            + (" | LATE (restart/partial already booked)" if late else "") + " (v-E36, log-only)")
    _wi.tick(tid, ltp)


SETUP_TAGS_FILE = f"setup_tags_{_FILE_STEM}_{_BROKER_TAG}.csv"
_V35_ERR = {"n": 0}


def _v35_safe(fn):
    """v-E35: run a tag call; any error (even in argument building) -> at most 5 log lines."""
    if not TAG_SETUP_ENABLED:
        return
    try:
        fn()
    except Exception as e:
        _V35_ERR["n"] += 1
        if _V35_ERR["n"] <= 5:
            log(f"vE6.2.4 SETUP TAG | error (ignored, log-only): {e}")


def _v35_tag(event, bot, symbol, side, otm, spot, entry=None, sl=None, trade_id="", detail="",
             rej_low=None, rej_vwap=None):
    """v-E35: one setup_tags row. For CE_SKIP the would-be stop is rebuilt from the rejection candle."""
    if entry is not None and sl is None and rej_low is not None:
        sl, _ = apply_bot_g_stop_band(entry, compute_bot_g_initial_sl(entry, rej_low, rej_vwap))
    st = _BOTG_DAY
    try:
        _dt = _day_type_diag(spot)
    except Exception:
        _dt = {}
    cfg = dict(wide_pct=TAG_WIDE_PCT, max_lots=TAG_MAX_LOTS, lot_qty=TAG_LOT_QTY, budgets=TAG_LOT_BUDGETS,
               big1=TAG_BIG_PCT_1, big2=TAG_BIG_PCT_2)
    row = _v35.build_row(datetime.now(), event, trade_id, bot.get("name"), symbol, side, otm,
                         bot.get("locked_side"), spot, st.get("open"), bot.get("gap_pct"), st.get("ext1015"),
                         st.get("ext_src"), _dt.get("pct_from_open"), _dt.get("day_type"), entry, sl, detail, cfg)
    _v35.write(SETUP_TAGS_FILE, row)


# =============================================================================
# vE6.2.3 v-E31 -- ZLM (Zero-Line Momentum) SHADOW. LOG-ONLY: no orders, reads
# BOT_G's locked side but never changes any bot state. Logic lives in the
# shared zlm_shadow_nifty_vE6.py (identical for both brokers).
# =============================================================================
def _zlm_symbol(spot, side):
    """v-E31: ATM 100-multiple strike on the current weekly expiry."""
    strike = int(round(float(spot) / 100.0)) * 100
    _code, _exp = getNiftyWeeklyExpiry()
    return f"{_ZLM_SYM_PREFIX}{_bot_g_symbol_expiry_code(_exp)}{strike}{side}", strike


def _zlm_tick(spot, df3):
    """v-E31: called once per loop (fresh data only)."""
    if not ZLM_SHADOW_ENABLED:
        return
    if not _zlm.CTX:
        _zlm.configure(log=log, ltp=get_multi_ltp, symbol=_zlm_symbol, broker=_BROKER_TAG,
                       cfg={k: v for k, v in globals().items() if k.startswith("ZLM_")})
    _g = next((b for b in BOTS if b.get("name") == "BOT_G"), None)
    _zlm.on_tick(spot, _g.get("locked_side") if _g else None, df3)


def _day_type_diag(spot):
    """v-E20: LOG/CSV ONLY. TREND_UP / TREND_DOWN / RANGE from % move vs the
    day open and position inside the day's range."""
    st = _BOTG_DAY
    if st["date"] != date.today() or st["open"] is None or not spot:
        return {k: "" for k in _DAY_KEYS}
    o, h, l = st["open"], st["high"], st["low"]
    pct = 100.0 * (spot - o) / o
    rng = (h - l) if (h is not None and l is not None) else 0.0
    pos = (spot - l) / rng if rng > 0 else 0.5
    old = [x for x in st["hist"] if x[0] <= time.time() - 30 * 60]
    chg30 = round(spot - old[-1][1], 2) if old else ""
    if pct >= BOTG_DAYTYPE_TREND_PCT and pos >= BOTG_DAYTYPE_RANGE_POS:
        lab = "TREND_UP"
    elif pct <= -BOTG_DAYTYPE_TREND_PCT and pos <= 1 - BOTG_DAYTYPE_RANGE_POS:
        lab = "TREND_DOWN"
    else:
        lab = "RANGE"
    return {"day_open": round(o, 2), "day_high": round(h, 2), "day_low": round(l, 2),
            "pct_from_open": round(pct, 3), "pos_in_range": round(pos, 2),
            "spot_30m_chg": chg30, "day_type": lab}


def _track_start(kind, bot_name, ref_id, symbol, side, ref_price, entry="", sl="", p1="", p2="", extra=None):
    """v-E19: start following `symbol` for BOTG_TRACK_MIN minutes. LOG ONLY."""
    if not BOTG_TRACK_ENABLED or not symbol or not ref_price or ref_price <= 0:
        return
    while len(_BOTG_TRACK) >= BOTG_TRACK_MAX:
        _track_finish(_BOTG_TRACK.pop(0), "DROPPED_MAX")
    _BOTG_TRACK.append(dict(kind=kind, bot=bot_name, ref_id=ref_id, symbol=symbol, side=side,
                            ref=ref_price, entry=entry, sl=sl, p1=p1, p2=p2, t0=time.time(),
                            hi=ref_price, hi_t=0, lo=ref_price, lo_t=0, marks={}, outcome="",
                            outcome_t="", polls=0, extra=extra or {}))
    log(f"{bot_name} TRACK START | {kind} {symbol} ref {ref_price} for {BOTG_TRACK_MIN} min"
        + (f" | would-have SL {sl} P1 {p1}" if kind == "SKIP" else "") + " (v-E19, log-only)")


def _track_finish(x, status="DONE"):
    e = x["extra"]
    if x["kind"] == "EXIT":   # v-E40: tracker over -> close what the min-stop plans still hold
        _v36_safe(lambda: _wi.tail_end(x["ref_id"], why="TRACK_" + status))
    row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), x["kind"], x["ref_id"], x["bot"], x["symbol"],
           x["side"], x["ref"], x["entry"], x["sl"], x["p1"], x["p2"], x["hi"], x["hi_t"], x["lo"], x["lo_t"],
           x["marks"].get(5, ""), x["marks"].get(15, ""), x["marks"].get(30, ""),
           x["outcome"] or ("NEITHER" if x["kind"] == "SKIP" else ""), x["outcome_t"], x["polls"],
           e.get("day_type", ""), e.get("pct_from_open", ""), e.get("cflow9_dce", ""), status]
    _append_csv(TRACK_SUM_FILE, _TRACK_SUM_HDR, [",".join(str(v).replace(",", ";") for v in row) + "\n"])
    log(f"{x['bot']} TRACK DONE | {x['kind']} {x['symbol']} ref {x['ref']} -> max {x['hi']} @{x['hi_t']}s "
        f"min {x['lo']} @{x['lo_t']}s | 5m {x['marks'].get(5, 'NA')} 15m {x['marks'].get(15, 'NA')} "
        f"30m {x['marks'].get(30, 'NA')}"
        + (f" | would-have: {x['outcome'] or 'NEITHER'}" if x["kind"] == "SKIP" else "")
        + f" [{status}] (v-E19, log-only)")


def _trackers_tick():
    """v-E19: one batched LTP call for all tracked symbols every
    BOTG_TRACK_POLL_SEC. Skip outcome: first of SL / P1 touched (poll prices)."""
    if not _BOTG_TRACK or time.time() - _TRACK_STATE["last"] < BOTG_TRACK_POLL_SEC:
        return
    _TRACK_STATE["last"] = time.time()
    m = get_multi_ltp(sorted({x["symbol"] for x in _BOTG_TRACK})) or {}
    now = time.time()
    rows, done = [], []
    for x in _BOTG_TRACK:
        el = round(now - x["t0"], 1)
        ltp = m.get(x["symbol"])
        if ltp and ltp > 0:
            x["polls"] += 1
            if x["kind"] == "EXIT":   # v-E40: min-stop what-if plans still running after a stop-out
                _v36_safe(lambda: _wi.tail_tick(x["ref_id"], ltp))
            rows.append(",".join(str(v) for v in [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), x["kind"],
                        x["ref_id"], x["bot"], x["symbol"], x["side"], x["ref"], el, ltp]) + "\n")
            if ltp > x["hi"]:
                x["hi"], x["hi_t"] = ltp, round(el)
            if ltp < x["lo"]:
                x["lo"], x["lo_t"] = ltp, round(el)
            for mk in (5, 15, 30):
                if mk not in x["marks"] and el >= mk * 60:
                    x["marks"][mk] = ltp
            if x["kind"] == "SKIP" and not x["outcome"] and x["sl"] != "" and x["p1"] != "":
                if ltp <= x["sl"]:
                    x["outcome"], x["outcome_t"] = "SL_FIRST", round(el)
                elif ltp >= x["p1"]:
                    x["outcome"], x["outcome_t"] = "P1_FIRST", round(el)
        if el >= BOTG_TRACK_MIN * 60:
            done.append(x)
    if V40_WRITE_POST_EXIT_PATHS:   # v-E41 (vE6.5): off by default, post_exit_summary is kept
        _append_csv(TRACK_FILE, _TRACK_HDR, rows)
    for x in done:
        _BOTG_TRACK.remove(x)
        _track_finish(x)


def _track_flush_all():
    """v-E19: at shutdown, write whatever unfinished trackers have so far."""
    while _BOTG_TRACK:
        _track_finish(_BOTG_TRACK.pop(0), "INCOMPLETE_SHUTDOWN")
    _v36_safe(_wi.flush_tails)   # v-E40


# =============================================================================
# vE6.5 v-E41 -- one daily upload zip per broker (files Anu uploads for review).
# =============================================================================
def _v51_quote(sym):
    """v-E51: (ltp, bid, ask) from one XTS 1502 quote (Touchline); None where missing."""
    eid = _resolve_option_eid(sym)
    if eid is None:
        return None, None, None
    resp = _HTTP.post(f"{MARKETDATA_URL}/instruments/quotes", headers=_md_headers(),
                      json={"instruments": [{"exchangeSegment": NIFTY_FO_SEGMENT, "exchangeInstrumentID": eid}],
                            "xtsMessageCode": 1502, "publishFormat": "JSON"}, timeout=5)
    if resp.status_code != 200:
        return None, None, None
    data = resp.json()
    if data.get("type") != "success":
        return None, None, None
    for item in data["result"].get("listQuotes", []):
        q = json.loads(item) if isinstance(item, str) else item
        tl = q.get("Touchline", {}) or {}
        g = lambda x: (float(x) if x not in (None, "") and float(x) > 0 else None)
        return g(tl.get("LastTradedPrice")), g((tl.get("BidInfo") or {}).get("Price")), g((tl.get("AskInfo") or {}).get("Price"))
    return None, None, None


def _v51_exit_quote(bot, leg, reason, qty, exit_price):
    """v-E51 (vE6.12, log-only): bid/ask at this exit leg vs the paper exit price.
    One quote call per exit leg; any error is logged and ignored."""
    if not V51_EXIT_QUOTES:
        return
    try:
        sym = bot.get("entry_symbol") or bot.get("symbol") or ""
        ltp, bid, ask = _v51_quote(sym)
        spread = round(ask - bid, 2) if (ask and bid) else ""
        gap = round(float(exit_price) - bid, 2) if bid else ""
        cost = round(gap * qty, 2) if gap != "" else ""
        log(f"{bot['name']} EXIT QUOTE | {leg} {reason} | {sym} qty {qty} | paper exit {exit_price} | ltp {ltp} "
            f"bid {bid} ask {ask} spread {spread} | exit-bid {gap} pts = Rs{cost} (v-E51, log-only)")
        new = not os.path.exists(V51_EXIT_QUOTES_FILE)
        with open(V51_EXIT_QUOTES_FILE, "a", encoding="utf-8") as f:
            if new:
                f.write("ts,trade_id,bot,leg,reason,symbol,qty,entry,paper_exit,ltp,bid,ask,spread,exit_minus_bid,cost_inr\n")
            f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S},{bot.get('trade_id','')},{bot['name']},{leg},{reason},{sym},{qty},"
                    f"{bot.get('entry','')},{exit_price},{ltp if ltp is not None else ''},{bid or ''},{ask or ''},{spread},{gap},{cost}\n")
    except Exception as e:
        log(f"EXIT QUOTE | error (ignored): {e}")


def _v41_daily_zip():
    """v-E41: at shutdown, zip the review files into upload_YYYYMMDD_<broker>.zip.
    Never touches the originals; any error is logged and ignored."""
    if not V40_DAILY_ZIP:
        return
    try:
        import zipfile
        import glob as _glob
        names = sorted(set(_glob.glob(LOG_FILE + "*")))
        names += [TRADE_FILE, LIVECMP_FILE, PATH_FILE, WHATIF_FILE, SETUP_TAGS_FILE,
                  getattr(_oc_filter, "DPCR_SHIFT_LOG_FILE", ""), TRACK_SUM_FILE,
                  f"option_tape_{datetime.now():%Y%m%d}_{_BROKER_TAG}.csv",   # v-E47
                  V51_EXIT_QUOTES_FILE]   # v-E51
        names = [n for i, n in enumerate(names) if n and os.path.exists(n) and n not in names[:i]]
        out = f"upload_{datetime.now():%Y%m%d}_{_BROKER_TAG}.zip"
        log(f"vE6.5 UPLOAD ZIP | writing {out} with {len(names)} files: {', '.join(names)} (v-E41)")
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for n in names:
                z.write(n, os.path.basename(n))
        return out, names   # v-E54 (vE6.14): for the end-of-day cleanup check
    except Exception as e:
        log(f"vE6.5 UPLOAD ZIP | failed (ignored, originals untouched): {e}")
    return None


def _v54_eod_cleanup(zip_result):
    """v-E54 (vE6.14): end-of-day cleanup, NORMAL 15:10 shutdown only.
    Verifies the upload zip first; deletes nothing if the check fails. Never deletes
    .py files, configs, token files or upload_*.zip."""
    import glob as _glob, zipfile as _zf
    if not V54_EOD_CLEANUP:
        return
    if not SYSTEM_EXIT:
        log("vE6.14 EOD CLEANUP | not a normal 15:10 shutdown -> nothing deleted (restart-safe) (v-E54)")
        return
    if not zip_result:
        log("vE6.14 EOD CLEANUP | no upload zip was written -> nothing deleted (v-E54)")
        return
    out, zipped = zip_result
    try:
        with _zf.ZipFile(out) as z:
            bad = z.testzip()
            inside = set(z.namelist())
        missing = [n for n in zipped if os.path.basename(n) not in inside]
        if bad or missing:
            log(f"vE6.14 EOD CLEANUP | zip check FAILED (bad {bad}, missing {missing}) -> nothing deleted (v-E54)")
            return
    except Exception as e:
        log(f"vE6.14 EOD CLEANUP | zip check error {e} -> nothing deleted (v-E54)")
        return
    st, tg_ = _FILE_STEM, _BROKER_TAG
    pats = [f"bot_log_{st}_*_{tg_}.txt*", f"trades_{st}_*_{tg_}.csv", f"summary_{st}_*_{tg_}.csv",
            f"bot_state_{st}_*_{tg_}.json*", f"trade_paths_{st}_*_{tg_}.csv",
            f"post_exit_paths_{st}_*_{tg_}.csv", f"post_exit_summary_{st}_*_{tg_}.csv",
            f"livecmp_{st}_*_{tg_}.csv", f"option_tape_*_{tg_}.csv", f"zlm_shadow_*_{tg_}.csv"]
    files = set(zipped) | {HEARTBEAT_FILE, WHATIF_FILE, SETUP_TAGS_FILE, V51_EXIT_QUOTES_FILE}
    files |= {getattr(_oc_filter, a, "") for a in ("OC_LOG_FILE", "DPCR_LOG_FILE", "DPCR_SHIFT_LOG_FILE")}
    for p in pats:
        files |= set(_glob.glob(p))
    files = sorted(f for f in files if f and os.path.isfile(f) and os.path.dirname(f) == ""
                   and not f.lower().endswith((".py", ".zip")) and "token" not in f.lower()
                   and "client_id" not in f.lower())
    log(f"vE6.14 EOD CLEANUP | {out} verified ({len(inside)} files) -> deleting {len(files)} daily files: "
        f"{', '.join(files)} (v-E54)")
    try:   # release the log file (Windows cannot delete an open file)
        _logger.removeHandler(_log_handler)
        _log_handler.close()
    except Exception:
        pass
    gone, kept = 0, []
    for f in files:
        try:
            os.remove(f); gone += 1
        except Exception as e:
            kept.append(f"{f} ({e})")
    print(f"vE6.14 EOD CLEANUP | deleted {gone}/{len(files)} files; kept upload zip {out}"
          + (f" | could not delete: {kept}" if kept else "") + " (v-E54)")


def _data_lost_check(stale):
    """v-E21: data stale for >= BOTG_DATA_LOST_SEC with an open BOT_G/BOT_GE
    trade. PAPER: close it at the last known LTP (reason DATA_LOST) so it is
    recorded. LIVE: send NO exit (the broker SL order protects the position);
    log + Telegram alert once."""
    st = _DATA_STALE
    if not stale:
        st["t"] = None
        st["alerted"] = set()
        return
    if st["t"] is None:
        st["t"] = time.time()
        return
    gone = time.time() - st["t"]
    if gone < BOTG_DATA_LOST_SEC:
        return
    for b in BOTS:
        if b["name"] not in ("BOT_G", "BOT_GE") or not b.get("trade_open"):
            continue
        if PAPER_TRADE:
            px = b.get("_last_ltp") or b["entry"]
            log(f"{b['name']} DATA_LOST | data stale {round(gone)}s with an open PAPER trade -> closed at "
                f"last known LTP {px} (set {b.get('_last_ltp_hhmm', 'NA')}) (v-E21)")
            tg(f"{b['name']} DATA LOST\nPaper trade closed at last known LTP {px}")
            if log_trade(b, b["side"], b["entry"], px, "DATA_LOST", b["qty"]):
                _close_bot(b, cooldown=0)
                b["stage"] = "INITIAL"; b["armed"] = False; b["_botg_last_broker_sl"] = None
        elif b["name"] not in st["alerted"]:
            st["alerted"].add(b["name"])
            log(f"{b['name']} DATA_LOST | data stale {round(gone)}s with an open LIVE trade -- no exit sent; "
                f"broker SL order {b.get('sl_order_id')} is the protection. CHECK THE BROKER APP. (v-E21)")
            tg(f"{b['name']} DATA LOST (LIVE)\nNo market data for {round(gone)}s. Broker SL "
               f"{b.get('sl_order_id')} protects the position. CHECK BROKER APP.")


def _track_post_entry(bot, ltp):
    """v-G83: called every manage tick with the traded option's LTP.
    Keeps the lowest/highest price since entry (+ seconds from entry) and
    the first price seen at/after each +N-minute mark. LOG/CSV ONLY."""
    if not ltp or ltp <= 0 or not bot.get("entry_epoch"):
        return
    pe = bot.get("post_entry")
    if pe is None:
        pe = bot["post_entry"] = {}
    el = time.time() - bot["entry_epoch"]
    if pe.get("low") is None or ltp < pe["low"]:
        pe["low"], pe["low_sec"] = ltp, round(el)
    if pe.get("high") is None or ltp > pe["high"]:
        pe["high"], pe["high_sec"] = ltp, round(el)
    for m in BOTG_POST_ENTRY_MARKS_MIN:
        k = f"ltp_{m}m"
        if pe.get(k) is None and el >= m * 60:
            pe[k] = ltp


def _post_entry_cols(bot, entry):
    """v-G83: CSV values for _POST_ENTRY_KEYS. Blank where unknown (e.g.
    the trade closed before the +9 min mark)."""
    pe = bot.get("post_entry") or {}
    risk = bot.get("risk_pts") or 0.0
    def _r(pts):
        return round(pts / risk, 3) if (pts is not None and risk > 0) else ""
    lo, hi = pe.get("low"), pe.get("high")
    mae = round(entry - lo, 2) if lo is not None else None
    mfe = round(hi - entry, 2) if hi is not None else None
    vals = {"pe_low": lo if lo is not None else "", "pe_low_sec": pe.get("low_sec", ""),
            "mae_pts": mae if mae is not None else "", "mae_r": _r(mae),
            "pe_high": hi if hi is not None else "", "pe_high_sec": pe.get("high_sec", ""),
            "mfe_pts": mfe if mfe is not None else "", "mfe_r": _r(mfe)}
    for m in BOTG_POST_ENTRY_MARKS_MIN:
        v = pe.get(f"ltp_{m}m")
        vals[f"ltp_{m}m"] = v if v is not None else ""
        vals[f"ret_{m}m_r"] = _r(v - entry) if v is not None else ""
    return [vals[k] for k in _POST_ENTRY_KEYS]


_ENTRY_DIAG_KEYS = [
    "diag_age_sec", "diag_spot", "abs_ce_oi", "abs_pe_oi", "abs_pcr",
    "flow_dpe_per_min", "flow_dce_per_min", "flow_dpe_pct_per_min", "flow_dce_pct_per_min",
    "driver", "atm_strike", "atm_status", "atm_ce_oi", "atm_pe_oi", "atm_ce_ltp", "atm_pe_ltp",
    "atm_d_ce_oi", "atm_d_pe_oi", "atm_ce_resid", "atm_pe_resid", "atm_ce_reading", "atm_pe_reading",
    "anchor_strike", "anchor_ce_oi", "anchor_pe_oi", "anchor_ce_ltp", "anchor_pe_ltp",
    "chart_sl", "adj_sl", "stop_pts", "stop_pct", "stop_adj_reason",
    "cflow3_dpe", "cflow3_dce", "cflow6_dpe", "cflow6_dce", "cflow9_dpe", "cflow9_dce",
    "cflow12_dpe", "cflow12_dce", "cflow15_dpe", "cflow15_dce", "quiet_flow", "ce_skip_check",
    "day_open", "day_high", "day_low", "pct_from_open", "pos_in_range", "spot_30m_chg", "day_type",   # v-E20
]
# v-E22 (vE6.2): LIVE vs PAPER comparison columns (Option A) -- log-only.
_LC_KEYS = ["entry_signal_price", "entry_ask", "entry_bid", "entry_spread", "entry_slip_pts",
            "entry_slip_inr", "entry_latency_ms", "leg_signal_price", "leg_slip_pts",
            "charges_inr", "net_pnl_inr", "paper_pnl_inr"]


def _leg_charges(qty, buy_px, sell_px, qty0):
    """v-E22: estimated charges for one exit leg of an option BUY trade:
    brokerage (this exit order + this leg's share of the entry order), STT on
    the sell premium, exchange transaction charges, SEBI fee, stamp duty on
    the buy, GST on brokerage+exchange+SEBI. Rates: config CHG_* (VERIFY)."""
    buy, sell = buy_px * qty, sell_px * qty
    share = (qty / qty0) if qty0 else 1.0
    brok = CHG_BROKERAGE_PER_ORDER * (1.0 + share)
    stt = sell * CHG_STT_SELL_PCT / 100.0
    txn = (buy + sell) * CHG_TXN_PCT / 100.0
    sebi = (buy + sell) * CHG_SEBI_PER_CRORE / 1e7
    stamp = buy * CHG_STAMP_BUY_PCT / 100.0
    gst = (brok + txn + sebi) * CHG_GST_PCT / 100.0
    return round(brok + stt + txn + sebi + stamp + gst, 2)


def _lc_cols(bot, qty, entry, exit_price, signal_price, pnl):
    try:
        lc = bot.get("_lc") or {}
        sig = lc.get("sig") or entry
        ask, bid = lc.get("ask"), lc.get("bid")
        spread = round(ask - bid, 2) if (ask and bid) else ""
        eslip = round(entry - sig, 4)
        leg_sig = signal_price if signal_price not in ("", None) else exit_price
        ch = _leg_charges(qty, entry, exit_price, lc.get("qty0") or qty)
        pnl_v = float(pnl) if pnl not in ("", None) else (exit_price - entry) * qty
        return [sig, ask or "", bid or "", spread, eslip, round(eslip * qty, 2), lc.get("ms", ""),
                leg_sig, round(exit_price - leg_sig, 4), ch, round(pnl_v - ch, 2),
                round((leg_sig - sig) * qty, 2)]
    except Exception:
        return [""] * len(_LC_KEYS)


def _write_livecmp():
    """v-E22: today's LIVE vs PAPER block from the trade CSV (all legs)."""
    import csv as _csv
    if not os.path.exists(TRADE_FILE):
        return
    today = date.today().isoformat()
    tot = dict(legs=0, trades=set(), pnl=0.0, paper=0.0, charges=0.0, net=0.0, eslip=0.0, xslip=0.0)
    with open(TRADE_FILE, encoding="utf-8") as f:
        for r in _csv.DictReader(f):
            if not str(r.get("timestamp", "")).startswith(today) or r.get("bot") not in ("BOT_G", "BOT_GE"):
                continue
            def g(k):
                try:
                    return float(r.get(k) or 0)
                except (TypeError, ValueError):
                    return 0.0
            tot["legs"] += 1; tot["trades"].add(r.get("trade_id"))
            tot["pnl"] += g("pnl_inr"); tot["paper"] += g("paper_pnl_inr"); tot["charges"] += g("charges_inr")
            tot["net"] += g("net_pnl_inr"); tot["eslip"] += g("entry_slip_inr"); tot["xslip"] += g("exit_slippage_inr")
    n = len(tot["trades"])
    log("=" * 70)
    log(f"LIVE vs PAPER  [{'PAPER' if PAPER_TRADE else 'LIVE'}]  {today}  trades {n} legs {tot['legs']} (v-E22)")
    log(f"  P&L at fills (gross)   : Rs{tot['pnl']:.0f}")
    log(f"  P&L at signal prices   : Rs{tot['paper']:.0f}   (difference = slippage)")
    log(f"  Entry slippage         : Rs{tot['eslip']:.0f}   Exit slippage: Rs{tot['xslip']:.0f}")
    log(f"  Charges (estimated)    : Rs{tot['charges']:.0f}")
    log(f"  NET P&L after charges  : Rs{tot['net']:.0f}")
    log("=" * 70)
    _append_csv(LIVECMP_FILE, "date,mode,run_id,trades,legs,gross_pnl,signal_pnl,entry_slip,exit_slip,charges,net_pnl",
                [",".join(str(v) for v in [today, "PAPER" if PAPER_TRADE else "LIVE", RUN_ID, n, tot["legs"],
                 round(tot["pnl"], 2), round(tot["paper"], 2), round(tot["eslip"], 2), round(tot["xslip"], 2),
                 round(tot["charges"], 2), round(tot["net"], 2)]) + "\n"])


_TRADE_HEADER = ("timestamp,trade_id,run_id,bot,side,symbol,leg_type,qty,"
                  "entry_time,entry_premium,exit_premium,initial_sl,risk_pts,"
                  "pnl_pts,r_multiple,pnl_inr,trade_pnl,reason,"
                  "exit_signal_price,exit_slippage_pts,exit_slippage_inr,"
                  "setup_type,close_location,rel_vol_5,vwap_penetration,"
                  "vwap_reclaim_type,confirmation_vwap_distance,sl_clamped,"
                  "peak_ltp,reached_p1,pct_of_p1_reached,short_of_p1_pts,"
                  "dpcr_signed_at_entry,flow_dpe,flow_dce,flow_minutes,"
                  "flow_tier,flow_net_supportive,"
                  + ",".join(_ENTRY_DIAG_KEYS)   # v-G82
                  + "," + ",".join(_POST_ENTRY_KEYS)   # v-G83
                  + "," + ",".join(_LC_KEYS))   # v-E22


def _v2_trade_row(bot, side, qty, entry, exit_price, pnl, reason, leg_type,
                  signal_price="", slip_pts="", slip_inr="", trade_pnl="",
                  peak_ltp="", reached_p1="", pct_of_p1="", short_of_p1=""):
    """v-G76: builds one CSV row matching _TRADE_HEADER exactly."""
    risk = bot.get("risk_pts") or 0.0
    pnl_pts = round(exit_price - entry, 4)
    r_mult = round(pnl_pts / risk, 3) if risk > 0 else ""
    vals = [datetime.now(), bot.get("trade_id", ""), RUN_ID, bot["name"], side,
            bot.get("entry_symbol", ""), leg_type, qty,
            bot.get("entry_time", ""), entry, exit_price,
            round(bot.get("initial_sl", 0.0) or 0.0, 2), round(risk, 2),
            pnl_pts, r_mult, pnl, trade_pnl, reason,
            signal_price, slip_pts, slip_inr,
            bot.get("entry_setup_type", ""), bot.get("entry_close_location", ""),
            bot.get("entry_rel_vol_5", ""), bot.get("entry_vwap_penetration", ""),
            bot.get("entry_vwap_reclaim_type", ""), bot.get("entry_vwap_reclaim_distance", ""),
            bot.get("sl_clamped", ""),
            peak_ltp, reached_p1, pct_of_p1, short_of_p1,
            bot.get("entry_dpcr_signed", ""), bot.get("entry_flow_dpe", ""),
            bot.get("entry_flow_dce", ""), bot.get("entry_flow_minutes", ""),
            bot.get("entry_flow_tier", ""), bot.get("entry_flow_net", "")] + \
           [(bot.get("entry_diag") or {}).get(k, "") for k in _ENTRY_DIAG_KEYS] + \
           (_post_entry_cols(bot, entry) if leg_type == "FINAL"
            else [""] * len(_POST_ENTRY_KEYS)) + \
           _lc_cols(bot, qty, entry, exit_price, signal_price, pnl)   # v-E22
    return ",".join(str(v).replace(",", ";") for v in vals) + "\n"


def _ensure_trade_header():
    if not os.path.exists(TRADE_FILE):
        with open(TRADE_FILE, "w", encoding="utf-8") as f:
            # v2.4-L1: extended with market context columns captured at entry
            # v3.4-ORB4: +entry_type,orb_high,orb_low. NOTE: TRADE_FILE is not
            # date-stamped — archive/rename any existing trades_nifty_g_pool_*_
            # rmoney.csv before running this version, or the new columns will
            # misalign on appended rows.
            f.write(_TRADE_HEADER + "\n")
    else:
        # v3.7-E-F3: File already existed with a stale header (e.g. from
        # before entry_reason was added). v3.4-E-F2 only *warned* about this
        # and kept appending new-schema rows under the old header — which is
        # exactly what caused write_summary() to silently drop every trade
        # from today (total_trades: 0 on 2026-07-17 despite real SL hits).
        # Self-heal instead: archive the mismatched file with a timestamp
        # and start a fresh one on the current schema, so write_summary()
        # always parses a single consistent column count.
        try:
            with open(TRADE_FILE, "r", encoding="utf-8") as f:
                existing_header = f.readline().strip()
            if existing_header != _TRADE_HEADER:
                archive_name = (f"{TRADE_FILE}.schema_mismatch_"
                                 f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak")
                shutil.move(TRADE_FILE, archive_name)
                log(f"TRADE FILE WARN | {TRADE_FILE} header did not match "
                    f"current schema. Existing: '{existing_header}' Expected: "
                    f"'{_TRADE_HEADER}'. Archived mismatched file to "
                    f"'{archive_name}' and started a fresh {TRADE_FILE} on "
                    "the current schema (v3.7-E-F3 auto-migration). Trades "
                    "logged under the old header are preserved in the "
                    "archive but will NOT appear in today's write_summary() "
                    "unless manually merged.")
                with open(TRADE_FILE, "w", encoding="utf-8") as f:
                    f.write(_TRADE_HEADER + "\n")
        except Exception as e:
            log(f"TRADE FILE WARN | Could not verify header: {e}")


def _check_botg_profit_cap_crossing(bot, pnl_before, pnl_after):
    """
    v-G36: announces the moment a bot's daily profit cap is actually
    crossed -- fires exactly once per crossing (compares before/after this
    specific trade's pnl, not a persisted flag, so it naturally can't
    double-fire or need special handling across a restart). The actual
    ENFORCEMENT (blocking new entries) lives in _bot_g_try_entry()'s own
    plain >= check on bot["cum_realized_pnl"] -- this function only logs,
    it does not gate anything itself.
    """
    if BOTG_DAILY_PROFIT_CAP_ENABLED and pnl_before < BOTG_DAILY_PROFIT_CAP_PER_BOT <= pnl_after:
        log(f"{bot['name']} PROFIT CAP  | Daily profit cap reached: "
            f"Rs{pnl_after} >= Rs{BOTG_DAILY_PROFIT_CAP_PER_BOT}. "
            f"No further NEW entries for {bot['name']} today (v-G36). "
            f"Any position still open continues to be managed normally.")
        tg(f"{bot['name']} DAILY PROFIT CAP REACHED\nRs{pnl_after} >= Rs{BOTG_DAILY_PROFIT_CAP_PER_BOT}\n"
           f"No further new entries for {bot['name']} today.")

def log_trade(bot, side, entry, exit_price, reason, qty):
    """
    v-EXITFIX1: now places the REAL closing order in LIVE mode before doing
    anything else. Every exit path already funnels through this one
    function before _close_bot() runs. Previously no exit path sent a real
    order in LIVE mode -- exits only updated bookkeeping while the actual
    broker position stayed open.

    Returns True if the trade was actually closed (safe for the caller to
    proceed to _close_bot()), False if a LIVE closing order failed --
    callers MUST check this and skip _close_bot() on False.

    `exit_price` as passed in is the SIGNAL price (the ltp that triggered
    the exit decision); in LIVE mode it's replaced by the real fill price
    for PnL purposes, and the gap is logged as slippage (v-SLIP1).
    """
    global TOTAL_REALIZED_PNL

    signal_price = exit_price
    # v-E23 (vE6.2.1): for a stop-type exit the planned price is the stop
    # level itself, so slippage = fill - stop (was fill - fill = 0).
    _v23_stop = bot.get("active_sl")
    if reason in ("SL_EXIT", "BREAKEVEN_EXIT", "TSL_EXIT", "BROKER_SL_FILLED") and _v23_stop:
        signal_price = round(float(_v23_stop), 2)
    if not PAPER_TRADE:
        order_id, real_fill, _filled_qty = place_exit_order(bot)
        if order_id is None:
            log(f"EXIT ABORTED | {bot['name']} closing order failed — "
                f"position REMAINS OPEN at broker. NOT marking trade closed.")
            tg(f"EXIT ORDER FAILED {bot['name']}\n"
               f"Reason: {reason}\nPosition is STILL OPEN at broker.\n"
               "Bot will retry on the next signal — check manually if this repeats.")
            return False
        if real_fill is not None:
            exit_price = real_fill
        bot["sl_order_id"] = None

    _ensure_trade_header()
    # OPTION BUYING PnL — same formula for BOTH CE and PE:
    #   We always BUY the option. Profit = (current premium - entry premium).
    #   CE bought: premium rises when Nifty rises  → (exit - entry) positive = profit
    #   PE bought: premium rises when Nifty falls  → (exit - entry) positive = profit
    #   In both cases the formula is identical: pnl = (exit - entry) x qty
    #   The old code used (entry - exit) for PE which was WRONG — it flipped the sign,
    #   showing profits as losses and losses as profits.
    pnl_pts = exit_price - entry   # correct for both CE and PE (option buying)
    pnl     = round(pnl_pts * qty, 2)
    TOTAL_REALIZED_PNL += pnl
    _pnl_before_this_trade = bot.get("cum_realized_pnl", 0.0)
    bot["cum_realized_pnl"] = round(_pnl_before_this_trade + pnl, 2)   # v-G14
    _check_botg_profit_cap_crossing(bot, _pnl_before_this_trade, bot["cum_realized_pnl"])
    # v2.4-L1: write market context captured at entry alongside trade result
    adx_at_entry       = bot.get("entry_adx", "")
    rsi_at_entry       = bot.get("entry_rsi", "")
    vwap_dist_at_entry = bot.get("entry_vwap_dist", "")
    orb_entry_type     = bot.get("orb_entry_type", "")  # v3.4-ORB
    orb_high_at_entry  = bot.get("orb_high", "")
    orb_low_at_entry   = bot.get("orb_low", "")
    tsi_at_entry        = bot.get("entry_tsi", "")         # v-F1: BOT_F only, blank elsewhere
    tsi_signal_at_entry = bot.get("entry_tsi_signal", "")  # v-F1: BOT_F only, blank elsewhere
    # v3.6-L1: entry_reason — plain-English record of which conditions fired
    # at entry (set by _log_rationale / signal_bot_d / signal_bot_e), quoted
    # and with internal commas stripped so it can't break CSV parsing.
    entry_reason_at_entry = str(bot.get("entry_reason", "")).replace(",", ";")
    slip_pts = round(exit_price - signal_price, 4)   # v-SLIP1
    slip_inr = round(slip_pts * qty, 2)              # v-SLIP1
    # v-G66: research-only fields captured at arm/entry time, never read
    # back by any decision path -- purely so post-trade hypothesis testing
    # (e.g. does Close Location predict outcome for RED_PULLBACK setups)
    # can filter/sort this CSV directly instead of cross-referencing ARMED
    # log lines against exit rows by timestamp.
    setup_type_val    = bot.get("entry_setup_type", "")
    close_loc_val     = bot.get("entry_close_location", "")
    rel_vol_5_val     = bot.get("entry_rel_vol_5", "")
    vwap_penet_val    = bot.get("entry_vwap_penetration", "")
    vwap_reclaim_val  = bot.get("entry_vwap_reclaim_type", "")   # v-G67
    vwap_reclaim_dist_val = bot.get("entry_vwap_reclaim_distance", "")   # v-G68
    # v-G69 (this session): surface the EXISTING peak-vs-P1 diagnostic
    # (v-G59/v-G61, computed again below for the log() line -- kept
    # separate here rather than restructured, so this addition can't
    # disturb that already-working code path) into the CSV itself.
    # Motivated directly by the "21-Sep Trade 1" profit-protection
    # discussion: the sharper follow-up question agreed on was "how many
    # actual trades have meaningful MFE but still fail to reach P1" --
    # this is exactly that population, filterable directly from the CSV
    # from here on, rather than reconstructed by hand per trade as we did
    # for the 24-Sep 8-trade study. Only meaningful for a genuine final
    # exit, not a partial booking -- blank on partial rows (log_partial_trade
    # never had a p1_target-relative question to answer in the first place).
    _v69_peak_ltp = bot.get("highest", entry)
    _v69_p1_tgt = bot.get("p1_target")
    if _v69_p1_tgt is not None and _v69_p1_tgt > entry:
        _v69_pct_of_p1 = round(100.0 * (_v69_peak_ltp - entry) / (_v69_p1_tgt - entry), 1)
        _v69_short_by_pts = round(max(0.0, _v69_p1_tgt - _v69_peak_ltp), 2)
    else:
        _v69_pct_of_p1 = ""
        _v69_short_by_pts = ""
    _v69_reached_p1 = bot.get("partial1_done", False)
    # v-G73/v-G76: whole-trade P&L = partial legs already booked + this leg
    _trade_total_pnl = round(bot.get("trade_pnl_acc", 0.0) + pnl, 2)
    _v36_safe(lambda: _wi.close(bot.get("trade_id"), exit_price, _trade_total_pnl, reason=reason))   # v-E36/v-E40, log-only
    try:
        _path_flush()   # v-G84: path rows for this trade on disk before its exit row
    except Exception:
        pass
    _v51_exit_quote(bot, "FINAL", reason, qty, exit_price)   # v-E51 (vE6.12, log-only)
    with open(TRADE_FILE, "a", encoding="utf-8") as f:
        f.write(_v2_trade_row(bot, side, qty, entry, exit_price, pnl, reason, "FINAL",
                              signal_price=signal_price, slip_pts=slip_pts, slip_inr=slip_inr,
                              trade_pnl=_trade_total_pnl,
                              peak_ltp=_v69_peak_ltp, reached_p1=_v69_reached_p1,
                              pct_of_p1=_v69_pct_of_p1, short_of_p1=_v69_short_by_pts))
    # v-G59: per-trade peak-vs-P1 report, explicit instruction after 21-Sep
    # Trade 1 (peak +Rs3,068, ~1.4pts short of P1, gave it all back to a
    # near-breakeven exit) -- printed once per trade, on the FINAL exit
    # only (not on partial bookings, where "peak vs P1" isn't the relevant
    # question since P1 already fired). LOGGING ONLY -- does not touch
    # SL/BE/TSL/P1/P2 decision logic; BOTG_PARTIAL_R1/R15 reasons are
    # skipped here since those are partial bookings, not the trade's end.
    # Kept identical to the Fyers file.
    if "PARTIAL" not in reason:   # v-E19: follow the option for 30 min after the final exit
        try:
            _track_start("EXIT", bot["name"], bot.get("trade_id", ""), bot.get("entry_symbol", ""),
                         bot.get("side", ""), exit_price, entry=entry, sl=round(bot.get("initial_sl") or 0, 2),
                         p1=round(bot.get("p1_target") or 0, 2),
                         p2=round(_botg_targets(bot, entry, bot.get("risk_pts") or 0)[1], 2) if bot.get("risk_pts") else "",
                         extra=dict(bot.get("entry_diag") or {}))
        except Exception as _tr_err:
            log(f"vE6.2 TRACK | start failed (ignored): {_tr_err}")
    if "PARTIAL" not in reason:
        _peak_ltp = bot.get("highest", entry)
        _peak_pnl = bot.get("peak_unrealized_pnl", 0.0)
        _p1_tgt = bot.get("p1_target")
        if _p1_tgt is not None and _p1_tgt > entry:
            _pct_of_p1 = round(100.0 * (_peak_ltp - entry) / (_p1_tgt - entry), 1)
            _short_by_pts = round(max(0.0, _p1_tgt - _peak_ltp), 2)
        else:
            _pct_of_p1 = None
            _short_by_pts = None
        # v-G61: TSL-arm-gap report, explicit instruction after checking the
        # 21-Sep Trade 1 claim precisely against the actual code -- TSL's
        # "armed" flag does fire correctly once peak crosses arm_level, but
        # the stage/active_sl only update if the buffer-adjusted trailing
        # level (peak - BOTG_TSL_BUFFER_PTS) actually exceeds what's already
        # protecting the trade (typically the BE level) -- a fixed 8pt
        # buffer next to a tight-risk trade's tightly-bunched BE/arm levels
        # can mean this never happens even once armed. Confirmed by hand for
        # Trade 1 (peak 151.70, buffer-adjusted 143.70, BE 148.65 -- short
        # by 4.95pts) -- this is NOT a bug, the max()-style guard against
        # ever downgrading protection is working as intended; it's a
        # parameter-fit question. LOGGING ONLY -- does not change whether
        # TSL arms or where active_sl ends up; reports the same numbers the
        # existing decision logic already computed, so a pattern across
        # multiple trades can be seen before any buffer design changes.
        # Kept identical to the Fyers file.
        _arm_lvl = bot.get("arm_level")
        _be_lvl = bot.get("be_level")
        if bot.get("stage") == "TRAILING":
            _tsl_note = "TSL engaged"
        elif _arm_lvl is not None and _peak_ltp >= _arm_lvl:
            _implied_tsl = round(_peak_ltp - _botg_tsl_buffer(bot), 2)   # v-E4
            _reference = _be_lvl if _be_lvl is not None else entry
            _gap = round(max(0.0, _reference - _implied_tsl), 2)
            _tsl_note = (f"ArmedButNoTrail(peak{_peak_ltp}-buffer{round(_botg_tsl_buffer(bot), 2)}"
                         f"={_implied_tsl}, short of existing protection {_reference} by {_gap}pts)")
        elif _arm_lvl is not None:
            _tsl_note = f"NeverArmed(peak{_peak_ltp}<arm{_arm_lvl})"
        else:
            _tsl_note = "NA"
        log(f"{bot['name']} TRADE PEAK  | PeakLTP:{_peak_ltp} PeakUnrealized:Rs{round(_peak_pnl,2)} "
            f"P1Target:{_p1_tgt} "
            f"{'ReachedP1' if bot.get('partial1_done') else f'ShortOfP1By:{_short_by_pts}pts({_pct_of_p1}pctOfP1)'} "
            f"TSL:{_tsl_note} "
            f"FinalPnL:Rs{pnl} (v-G59/v-G61)")
    log(f"TRADE EXIT  | Bot:{bot['name']} Side:{side} Qty:{qty} Symbol:{bot.get('entry_symbol','?')} "
        f"Entry:{entry} Exit:{round(exit_price,2)} "
        f"PnL:Rs{pnl}  Session:Rs{round(TOTAL_REALIZED_PNL,2)} | {reason}"
        + (f"  Slippage:{slip_pts}pts/Rs{slip_inr}" if slip_pts != 0 else ""))

    # v3.1-R3: Same-direction re-entry cooldown. Root-caused against the
    # 2026-07-01 BOT_B losing streak — trade #3 re-entered CE just 29s after
    # the existing flat 600s cooldown expired, same direction as the trade
    # that had just been stopped out. A SL/TSL (losing) exit now arms an
    # EXTRA, longer, direction-aware lock on top of the normal exit cooldown.
    # A winning exit (profit-protect/partial/breakeven) clears it.
    # v-G9-FIX8: BOT_G is fully exempt from this lock (reentry_lock_exempt=True
    # on its own bot dict) -- per explicit instruction, no reentry cooldown of
    # any kind for BOT_G, not the flat one removed in v-G9-FIX5 nor this
    # tiered one. Its own rejection-candle re-arm requirement is the intended
    # gate, full stop.
    if REENTRY_COOLDOWN_FILTER and not bot.get("reentry_lock_exempt"):
        # v-CD2: exit-reason-tiered same-direction lock.
        #   SL_EXIT                     -> full lock (unchanged, original case)
        #   TSL_EXIT / PROFIT_PROTECT /
        #   EARLY_GIVEBACK              -> 0 for trend/momentum/breakout/confluence
        #                                  bots (validated win, don't block
        #                                  continuation); FULL lock for BOT_C
        #                                  ("mean_reversion" flag) — a completed
        #                                  bounce doesn't license chasing a second
        #                                  one in the same range
        #   BREAKEVEN_EXIT / EMA_REVERSAL_EXIT -> HALF lock (ambiguous: not
        #                                  wrong, but not confirmed either)
        _full_lock = bot.get("sl_same_dir_cooldown_sec", SL_SAME_DIR_COOLDOWN_SEC)
        _mean_rev  = bot.get("mean_reversion", False)
        if reason == "SL_EXIT":
            _lock_sec, _tier = _full_lock, "SL_FULL"
        elif reason in ("TSL_EXIT", "PROFIT_PROTECT", "EARLY_GIVEBACK", "FIXED_TARGET_EXIT"):
            _lock_sec, _tier = (_full_lock, "WIN_MEANREV_FULL") if _mean_rev else (0, "WIN_NONE")
        elif reason in ("BREAKEVEN_EXIT", "EMA_REVERSAL_EXIT", "TSI_REVERSAL_EXIT"):
            _lock_sec, _tier = round(_full_lock / 2), "AMBIG_HALF"
        else:
            _lock_sec, _tier = 0, "UNKNOWN_NONE"
        if _lock_sec > 0:
            bot["reentry_block_side"]  = side
            bot["reentry_block_until"] = time.time() + _lock_sec
            log(f"REENTRY LOCK | {bot['name']} {side} re-entry blocked for "
                f"{_lock_sec}s after {reason} (v-CD2 tier={_tier}; "
                f"old flat scheme would have used "
                f"{SL_SAME_DIR_COOLDOWN_SEC if reason in ('SL_EXIT','TSL_EXIT') else 0}s)")
        else:
            bot["reentry_block_side"]  = None
            bot["reentry_block_until"] = 0
            if reason in ("TSL_EXIT", "PROFIT_PROTECT", "EARLY_GIVEBACK", "FIXED_TARGET_EXIT"):
                log(f"REENTRY LOCK | {bot['name']} {side} NOT locked "
                    f"(v-CD2 tier={_tier} — validated win, old flat scheme "
                    f"would have used {SL_SAME_DIR_COOLDOWN_SEC if reason=='TSL_EXIT' else 0}s)")

    # v2.9-O10 / v3.0: Update consecutive SL counter (per-bot or global)
    global _CONSECUTIVE_SL_COUNT, CIRCUIT_BREAKER_LOCKED
    # v-G73: with BOTG_STREAK_COUNT_LOSSES_ONLY, judge by the WHOLE trade
    # (partials + this leg) -- a profitable trade whose runner ended on a
    # TSL is a win, not a streak hit. Flag off = exact v1 behaviour.
    _counts_as_loss = reason in ("SL_EXIT", "TSL_EXIT") and (
        not BOTG_STREAK_COUNT_LOSSES_ONLY or _trade_total_pnl <= 0)
    _counts_as_win = (_trade_total_pnl > 0) if BOTG_STREAK_COUNT_LOSSES_ONLY else (pnl > 0)
    if _counts_as_loss:
        if LOSING_STREAK_PER_BOT:
            bname = bot["name"]
            _BOT_SL_STREAK[bname] = _BOT_SL_STREAK.get(bname, 0) + 1
            streak = _BOT_SL_STREAK[bname]
            log(f"STREAK       | {bname} consecutive SL count: {streak}/{LOSING_STREAK_LIMIT}")
            if (LOSING_STREAK_LIMIT > 0
                    and streak >= LOSING_STREAK_LIMIT
                    and not _bot_streak_locked(bname)):
                if LOSING_STREAK_COOLDOWN_SEC > 0:
                    _BOT_LOCK_UNTIL[bname] = time.time() + LOSING_STREAK_COOLDOWN_SEC
                    unlock_str = f"cooldown {LOSING_STREAK_COOLDOWN_SEC}s"
                else:
                    _BOT_LOCK_UNTIL[bname] = float("inf")
                    unlock_str = "rest of day"
                log(f"LOSING STREAK| {bname}: {streak} consecutive SL hits — "
                    f"new entries HALTED ({unlock_str}). Other bots unaffected. (v3.0)")
                tg(f"LOSING STREAK HALT — {bname}\n"
                   f"{streak} consecutive SL exits.\n"
                   f"Halted: {unlock_str}. Other bots continue.")
        else:
            _CONSECUTIVE_SL_COUNT += 1
            log(f"STREAK       | Consecutive SL count: {_CONSECUTIVE_SL_COUNT}/{LOSING_STREAK_LIMIT}")
            if (LOSING_STREAK_LIMIT > 0
                    and _CONSECUTIVE_SL_COUNT >= LOSING_STREAK_LIMIT
                    and not CIRCUIT_BREAKER_LOCKED):
                CIRCUIT_BREAKER_LOCKED = True
                log(f"LOSING STREAK| {_CONSECUTIVE_SL_COUNT} consecutive SL hits — "
                    "new entries HALTED for today. (v2.9-O10)")
                tg(f"LOSING STREAK HALT\n"
                   f"{_CONSECUTIVE_SL_COUNT} consecutive SL exits.\n"
                   f"No new entries today. Existing trades continue.")
    elif _counts_as_win:   # v-G73 (v1: pnl > 0)
        if LOSING_STREAK_PER_BOT:
            bname = bot["name"]
            if _BOT_SL_STREAK.get(bname, 0) > 0:
                log(f"STREAK RESET | {bname} profitable exit resets SL streak "
                    f"(was {_BOT_SL_STREAK[bname]})")
            _BOT_SL_STREAK[bname] = 0
        else:
            if _CONSECUTIVE_SL_COUNT > 0:
                log(f"STREAK RESET | Profitable exit resets SL streak "
                    f"(was {_CONSECUTIVE_SL_COUNT})")
            _CONSECUTIVE_SL_COUNT = 0

    save_state()
    return True


def _execute_partial_sell(bot, requested_qty):
    """LIVE-only partial exit. Never updates local qty until broker fill is verified."""
    if PAPER_TRADE:
        return float(bot.get("_paper_partial_fill_price", 0) or 0) or None, int(requested_qty)
    broker_qty = _check_existing_position(bot["entry_symbol"])
    if broker_qty is None:
        raise RuntimeError("RMoney position query failed before partial exit")
    if broker_qty <= 0:
        raise RuntimeError("Broker position is already flat before partial exit")
    qty = min(int(requested_qty), int(broker_qty))
    response = placeOrder(bot["entry_symbol"], "SELL", qty, "MARKET", 0, "MIS", papertrading=1)
    if not response or response.get("type") != "success":
        raise RuntimeError(f"Partial exit order rejected: {(response or {}).get('description', response)}")
    oid = response.get("result", {}).get("AppOrderID")
    if not oid:
        raise RuntimeError("Partial exit accepted without AppOrderID")
    fp, fq, _ = _wait_live_order_fill(oid, bot["entry_symbol"], qty)
    if fp is None or not fq:
        raise RuntimeError(f"Partial exit {oid} has no verified fill")
    if fq < qty:
        log(f"PARTIAL EXIT | requested={qty} verified_fill={fq} @ {fp}; remainder stays broker-open")
    return fp, int(fq)


def log_partial_trade(bot, side, entry, exit_price, qty, reason):
    _ps = None   # v-E22: partial leg's signal price = its target level
    try:
        if str(reason).startswith("BOTG_PARTIAL"):
            _tg = _botg_targets(bot, bot["entry"], bot["risk_pts"])
            _ps = round(_tg[1] if "R15" in str(reason) else _tg[0], 2)
    except Exception:
        _ps = None
    global TOTAL_REALIZED_PNL
    _ensure_trade_header()
    pnl_pts = exit_price - entry   # correct for both CE and PE (option buying)
    pnl     = round(pnl_pts * qty, 2)
    TOTAL_REALIZED_PNL += pnl
    _pnl_before_this_trade = bot.get("cum_realized_pnl", 0.0)
    bot["cum_realized_pnl"] = round(_pnl_before_this_trade + pnl, 2)   # v-G14
    _check_botg_profit_cap_crossing(bot, _pnl_before_this_trade, bot["cum_realized_pnl"])
    # v2.4-L1: include entry context in partial booking rows too
    adx_at_entry       = bot.get("entry_adx", "")
    rsi_at_entry       = bot.get("entry_rsi", "")
    vwap_dist_at_entry = bot.get("entry_vwap_dist", "")
    orb_entry_type     = bot.get("orb_entry_type", "")  # v3.4-ORB
    orb_high_at_entry  = bot.get("orb_high", "")
    orb_low_at_entry   = bot.get("orb_low", "")
    tsi_at_entry        = bot.get("entry_tsi", "")         # v-F1: BOT_F only, blank elsewhere
    tsi_signal_at_entry = bot.get("entry_tsi_signal", "")  # v-F1: BOT_F only, blank elsewhere
    entry_reason_at_entry = str(bot.get("entry_reason", "")).replace(",", ";")  # v3.6-L1
    # v-G66: same research-only fields as log_trade(). Also fixes a
    # pre-existing column misalignment here -- this row was missing the
    # exit_signal_price/exit_slippage_pts/exit_slippage_inr columns
    # entirely (not applicable to a partial leg), leaving them blank so
    # every column lines up with the header instead of shifting the new
    # v-G66 fields into the wrong positions.
    setup_type_val    = bot.get("entry_setup_type", "")
    close_loc_val     = bot.get("entry_close_location", "")
    rel_vol_5_val     = bot.get("entry_rel_vol_5", "")
    vwap_penet_val    = bot.get("entry_vwap_penetration", "")
    vwap_reclaim_val  = bot.get("entry_vwap_reclaim_type", "")   # v-G67
    vwap_reclaim_dist_val = bot.get("entry_vwap_reclaim_distance", "")   # v-G68
    bot["trade_pnl_acc"] = round(bot.get("trade_pnl_acc", 0.0) + pnl, 2)   # v-G73/v-G76
    try:
        _path_flush()   # v-G84
    except Exception:
        pass
    _v51_exit_quote(bot, "PARTIAL", reason, qty, exit_price)   # v-E51 (vE6.12, log-only)
    with open(TRADE_FILE, "a", encoding="utf-8") as f:
        f.write(_v2_trade_row(bot, side, qty, entry, exit_price, pnl, reason, "PARTIAL",
                              signal_price=_ps, slip_pts=(round(exit_price - _ps, 4) if _ps else ""),
                              slip_inr=(round((exit_price - _ps) * qty, 2) if _ps else "")))   # v-G76/v-E22
    log(f"PARTIAL BOOK| Bot:{bot['name']} qty:{qty} "
        f"PnL:Rs{pnl}  Remaining qty:{bot['qty']}  "
        f"Session:Rs{round(TOTAL_REALIZED_PNL,2)}")
    save_state()
    return True


def _bot_stats(df_bot, bot_name):
    d = df_bot[df_bot["bot"] == bot_name]
    if d.empty:
        return {"trades":0,"wins":0,"losses":0,"win_pct":0,
                "net_pnl":0,"avg_pnl":0,"best":0,"worst":0}
    total = len(d)
    wins  = int((d["pnl_inr"] > 0).sum())
    return {
        "trades" : total,
        "wins"   : wins,
        "losses" : total - wins,
        "win_pct": round(wins / total * 100, 1),
        "net_pnl": round(d["pnl_inr"].sum(), 2),
        "avg_pnl": round(d["pnl_inr"].mean(), 2),
        "best"   : round(d["pnl_inr"].max(), 2),
        "worst"  : round(d["pnl_inr"].min(), 2),
    }


def write_summary():
    if not os.path.exists(TRADE_FILE):
        return
    try:
        # v3.4-E-F1: engine="python" + on_bad_lines="warn" tolerates ragged
        # rows (e.g. a future schema change that adds columns without a
        # matching header migration). Instead of the whole summary silently
        # failing via SUMMARY ERROR, malformed rows are skipped and logged,
        # and the summary still runs on the rest.
        try:
            df = pd.read_csv(TRADE_FILE)
        except Exception as parse_err:
            log(f"SUMMARY WARN  | Strict CSV parse failed ({parse_err}) — "
                "schema drift in TRADE_FILE (old rows have fewer columns "
                "than the current header). The lenient parser below would "
                "silently DROP every mismatched row — including today's "
                "real trades if they're the ones that don't match — which "
                "is exactly what caused total_trades:0 despite real SL "
                "hits. Self-healing instead: archiving the drifted file "
                "now so tomorrow starts clean. Today's summary below is "
                "still read leniently as a best-effort, but check it "
                "against SessionPnL in the console output, not just this "
                "table, since some of today's own rows may be the ones "
                "that don't match and get skipped.")
            # v-SUMFIX2: the old code reset TRADE_FILE down to just its
            # header, then re-read TRADE_FILE itself for the lenient
            # summary — so it always saw 0 data rows and silently hit the
            # `if df.empty: return` below, printing no summary at all
            # despite real trades existing. Now we read from the archived
            # copy (which still holds every row) instead of TRADE_FILE.
            archive_name = None
            try:
                archive_name = (f"{TRADE_FILE}.schema_mismatch_"
                                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak")
                shutil.copy(TRADE_FILE, archive_name)
                with open(TRADE_FILE, "r", encoding="utf-8") as f_in:
                    lines = f_in.readlines()
                if lines:
                    with open(TRADE_FILE, "w", encoding="utf-8") as f_out:
                        f_out.write(_TRADE_HEADER + "\n")
                log(f"TRADE FILE WARN | Archived drifted {TRADE_FILE} to "
                    f"'{archive_name}' (full copy preserved) and reset "
                    f"{TRADE_FILE} to a fresh, consistent header for "
                    "tomorrow onward (v-SUMFIX1).")
            except Exception as heal_err:
                log(f"TRADE FILE WARN | Auto-heal attempt failed: {heal_err}")
            lenient_source = archive_name if archive_name and os.path.exists(archive_name) else TRADE_FILE
            # v-SUMFIX2: pd.read_csv(..., on_bad_lines="warn") DROPS every
            # row whose column count doesn't match the file's own (possibly
            # stale) header — which is exactly what silently zeroed out
            # today's real BOT_F trades before (they're 17-wide; the header
            # on disk was still the old 15-wide one). Instead, parse with
            # csv.reader (handles the quoted entry_reason field correctly)
            # and pad/truncate every row to the known-correct column count
            # from _TRADE_HEADER, so mismatched rows are RECOVERED, not
            # dropped. The first line of the file is treated as a header
            # and skipped regardless of what it says, since it may be stale.
            correct_cols = _TRADE_HEADER.split(",")
            ncols = len(correct_cols)
            recovered_rows = []
            truncated_count = 0
            with open(lenient_source, "r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                for i, row in enumerate(reader):
                    if i == 0:
                        continue  # skip whatever header is on disk (may be stale)
                    if not row:
                        continue
                    if len(row) < ncols:
                        row = row + [""] * (ncols - len(row))
                    elif len(row) > ncols:
                        row = row[:ncols]
                        truncated_count += 1
                    recovered_rows.append(row)
            if truncated_count:
                log(f"SUMMARY WARN  | {truncated_count} row(s) had MORE columns "
                    f"than the expected {ncols} (possibly an unescaped comma in "
                    "entry_reason, or a schema wider than current _TRADE_HEADER) "
                    "— truncated to fit rather than dropped; worth a manual check.")
            df = pd.DataFrame(recovered_rows, columns=correct_cols)
            # numeric columns come back as strings from csv.reader; restore
            # them so downstream .sum()/.cumsum()/comparisons work correctly
            for numcol in ("qty", "entry_premium", "exit_premium", "pnl_inr",
                           "entry_adx", "entry_rsi", "entry_vwap_dist",
                           "orb_high", "orb_low", "tsi_at_entry", "tsi_signal_at_entry"):
                if numcol in df.columns:
                    df[numcol] = pd.to_numeric(df[numcol], errors="coerce")
            log(f"SUMMARY RECOVERY | Lenient-parsed {len(df)} row(s) from "
                f"{lenient_source} by padding/truncating to the {ncols}-column "
                "schema instead of dropping mismatched rows (v-SUMFIX2).")
        if df.empty:
            return
        today_df = (df[df["timestamp"].astype(str).str.startswith(str(date.today()))]
                    if "timestamp" in df.columns else df)
        today_df = today_df.copy()
        today_df["pnl_inr"] = pd.to_numeric(today_df["pnl_inr"], errors="coerce").fillna(0.0)
        legs = len(today_df)
        # v-G74: stats per WHOLE TRADE (legs grouped by trade_id), not per
        # leg -- 28-Sep showed "6 trades, 66.7% win" for what was really 3
        # trades (+597, -26, +2,980), with a -19.5 BE remainder after P1
        # counted as a "loss". Rows without a trade_id each count alone.
        if "trade_id" in today_df.columns:
            _tid = today_df["trade_id"].astype(str)
            _tid = _tid.where((_tid != "") & (_tid != "nan"), "row" + today_df.index.astype(str))
            trades_df = (today_df.assign(_tid=_tid)
                         .groupby("_tid", sort=False)
                         .agg(bot=("bot", "first"), pnl_inr=("pnl_inr", "sum")))
        else:
            trades_df = today_df[["bot", "pnl_inr"]]
        tp = trades_df["pnl_inr"]
        total      = len(tp)
        wins       = (tp > 0).sum()
        cumulative = tp.cumsum()
        # v-G74: running peak starts at 0 (flat), so a losing FIRST trade is
        # a drawdown -- 28-Sep RMoney reported 0.0 after opening with -780.
        max_dd     = round(min(0.0, (cumulative - cumulative.cummax().clip(lower=0.0)).min()), 2) if total else 0.0
        summary = {
            "date"         : str(date.today()),
            "mode"         : "PAPER" if PAPER_TRADE else "LIVE",
            "total_trades" : total,
            "legs"         : legs,   # v-G74
            "wins"         : int(wins),
            "losses"       : int((tp <= 0).sum()),
            "win_pct"      : round(wins / total * 100, 1) if total else 0,
            "gross_profit" : round(tp[tp > 0].sum(), 2),
            "gross_loss"   : round(tp[tp <= 0].sum(), 2),
            "net_pnl"      : round(tp.sum(), 2),
            "avg_pnl"      : round(tp.mean(), 2) if total else 0,
            "best_trade"   : round(tp.max(), 2) if total else 0,
            "worst_trade"  : round(tp.min(), 2) if total else 0,
            "max_drawdown" : max_dd,
            "peak_pnl"     : round(SESSION_PEAK_PNL, 2),
        }
        if V40_WRITE_SUMMARY_CSV:   # v-E41 (vE6.5): off by default, same numbers are in livecmp + the log
            header = not os.path.exists(SUMMARY_FILE)
            with open(SUMMARY_FILE, "a", encoding="utf-8") as f:
                if header:
                    f.write(",".join(summary.keys()) + "\n")
                f.write(",".join(str(v) for v in summary.values()) + "\n")

        log("=" * 70)
        log(f"SESSION SUMMARY  [{summary['mode']}]  {str(date.today())}")
        log("-" * 70)
        for k, v in summary.items():
            log(f"  {k:<20} {v}")

        if PAPER_TRADE and "bot" in today_df.columns:
            log("-" * 70)
            log("PER-BOT COMPARISON")
            log(f"  {'Bot':<8} {'Trades':>7} {'Wins':>5} {'Win%':>6} "
                f"{'Net PnL':>10} {'Avg':>8} {'Best':>8} {'Worst':>8}")
            log(f"  {'-'*8} {'-'*7} {'-'*5} {'-'*6} {'-'*10} {'-'*8} {'-'*8} {'-'*8}")
            for bname in ["BOT_G", "BOT_GE"]:   # v-E6;   # v-G13: A-F removed, standalone G/GG process
                s = _bot_stats(trades_df.reset_index(), bname)   # v-G74: per trade
                if s["trades"] > 0:
                    log(f"  {bname:<8} {s['trades']:>7} {s['wins']:>5} "
                        f"{s['win_pct']:>5}% {s['net_pnl']:>10} "
                        f"{s['avg_pnl']:>8} {s['best']:>8} {s['worst']:>8}")
        log("=" * 70)
    except Exception as e:
        log(f"SUMMARY ERROR | {e}")


# =============================================================================
#  SECTION 11 — TIME UTILITIES
# =============================================================================

def hhmm():
    n = datetime.now()
    return n.hour * 100 + n.minute


def force_exit(bot):
    return hhmm() >= bot["force_exit"]


# =============================================================================
#  SECTION 12 — DATA FETCH & CACHE
#  FIX-2: sleep between historical calls raised 0.3 -> 0.5s (minimal change)
#  FIX-3: suppress entries after 5 consecutive failures (lenient)
# =============================================================================

# v3.12-API2: CACHE_SEC moved to config (Section L, DATA/API TIMING) — was
# hardcoded here. HIST_CACHE_SEC was already in config; this makes both
# timing knobs live in one place, editable without touching the bot script.
STALE_SEC = 90     # v2.9-D5: raised from 30s to 90s — also blocks new entries
CACHE     = {"spot": None, "df3": None,
             "time": 0, "hist_time": 0}


def _get_historical_nifty_safe(retries=2, retry_delay=1.5):
    """
    v-RG1 (23-Aug-2026): rebuilt on RMoney's verified /instruments/ohlc
    pattern (same call the A-F suite's own _fetch_raw_1min() uses for the
    Nifty index, proven working), resampled to 3-min here. Retries on
    failure -- same defensive pattern as the Fyers original, adapted to
    RMoney's own response shape (dataReponse pipe-delimited string, not a
    DataFrame-returning SDK call).
    """
    for attempt in range(1, retries + 2):
        try:
            start_dt = datetime.combine(_prev_trading_day(), datetime.min.time()).replace(hour=9, minute=15)
            end_dt = datetime.now()
            fmt = "%b %d %Y %H%M%S"
            resp = _HTTP.get(
                f"{MARKETDATA_URL}/instruments/ohlc",
                headers=_md_headers(),
                params={"exchangeSegment": NIFTY_EXCHANGE_SEGMENT, "exchangeInstrumentID": NIFTY_INSTRUMENT_ID,
                        "startTime": start_dt.strftime(fmt), "endTime": end_dt.strftime(fmt),
                        "compressionValue": 3},
                timeout=10)
            if resp.status_code != 200:
                raise RuntimeError(f"HTTP {resp.status_code}")
            data = resp.json()
            if data.get("type") != "success":
                raise RuntimeError(data.get("description"))
            raw_str = data.get("result", {}).get("dataReponse", "")
            if not raw_str:
                raise RuntimeError("empty dataReponse")
            rows = _parse_ticks(raw_str)
            if len(rows) < 10:
                raise RuntimeError(f"only {len(rows)} ticks")

            df_raw = pd.DataFrame(rows)
            df_raw["datetime"] = pd.to_datetime(df_raw["ts"], unit="s")   # tz-NAIVE, confirmed IST already
            df_raw = df_raw.set_index("datetime").sort_index().drop(columns=["ts"])
            df_raw = df_raw[~df_raw.index.duplicated(keep="last")]

            today_open = pd.Timestamp(datetime.now().date()) + pd.Timedelta(hours=9, minutes=15)
            df3 = df_raw.resample("3min", origin=today_open).agg({
                "open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum",
            }).dropna(subset=["close"])
            # G4.4: keep the first/current forming bar in df3. Signal functions
            # already use closed-bar indexing (typically iloc[-2]), while gap/
            # anchor readiness can use the live session-open bar before 09:18.
            return df3
        except Exception as e:
            log(f"[HISTORICAL PIPELINE ERROR] attempt {attempt}/{retries + 1}: {e}")
            if attempt <= retries:
                time.sleep(retry_delay)
    return None


def fetch_data(force_refresh=False):
    """
    v3.0: Two-tier fetch.
    - Spot price: fetched every CACHE_SEC (3s) — lightweight.
    - Historical candles: fetched only every HIST_CACHE_SEC (45s) — heavy.
    Reused from cache between refreshes so the bot still evaluates every
    tick using the last known candles.

    v3.14-STALE1: force_refresh bypasses both cache gates during the
    candle-boundary window, guaranteeing df3 is pulled fresh right after a
    candle closes. Same reasoning as the Fyers version.
    """
    global _FETCH_FAIL_COUNT, _DATA_HEALTHY
    now = time.time()
    if not force_refresh and now - CACHE["time"] < CACHE_SEC:
        return CACHE

    try:
        instruments = [{"exchangeSegment": NIFTY_EXCHANGE_SEGMENT, "exchangeInstrumentID": NIFTY_INSTRUMENT_ID}]
        resp = _HTTP.post(f"{MARKETDATA_URL}/instruments/quotes", headers=_md_headers(),
                           json={"instruments": instruments, "xtsMessageCode": 1502, "publishFormat": "JSON"},
                           timeout=5)
        if resp.status_code != 200:
            log(f"[API ERROR FETCHING SPOT] HTTP {resp.status_code}")
            _on_fetch_fail()
            return CACHE
        data = resp.json()
        if data.get("type") != "success":
            log(f"[API ERROR FETCHING SPOT] {data.get('description')}")
            _on_fetch_fail()
            return CACHE
        quotes = data["result"].get("listQuotes", [])
        if not quotes:
            log("[API ERROR FETCHING SPOT] empty listQuotes")
            _on_fetch_fail()
            return CACHE
        q = json.loads(quotes[0]) if isinstance(quotes[0], str) else quotes[0]
        ltp = q.get("Touchline", {}).get("LastTradedPrice")
        if ltp is None:
            log("[API ERROR FETCHING SPOT] no LastTradedPrice in response")
            _on_fetch_fail()
            return CACHE

        spot = float(ltp)
        CACHE["spot"] = spot
        CACHE["time"] = now

        need_hist = force_refresh or (now - CACHE["hist_time"]) >= HIST_CACHE_SEC
        if need_hist or CACHE["df3"] is None:
            df3 = _get_historical_nifty_safe()

            if df3 is None or not hasattr(df3, "columns"):
                log("[DATA FETCH ERROR] 3m timeframe returned invalid data.")
                _on_fetch_fail()
                return CACHE

            # v-RG1: tz-NAIVE comparison -- RMoney's own ticks are already
            # naive IST timestamps (confirmed, same as fetch_option_history_5m's
            # comment above), unlike Fyers' tz-aware feed. Using
            # pd.Timestamp.now(tz="Asia/Kolkata") here would raise the exact
            # tz-mismatch error already found and fixed on the Sensex side
            # (v-SG8) -- same root cause, different symptom location.
            _last_bar_age = (pd.Timestamp.now() - df3.index[-1]).total_seconds()
            if _last_bar_age > STALE_CANDLE_SEC:
                # v-RG3 (23-Aug-2026): pre-market suppression -- before 09:15
                # there simply IS no fresh candle yet (market hasn't opened),
                # so this isn't a real feed failure; the old behavior spammed
                # [DATA FETCH ERROR] every ~3-5s for the whole pre-market
                # window (real paper-trade log, 25-Aug-2026: 13 minutes of
                # repeated identical lines) and counted toward the 5-failure
                # SUPPRESSED-entries trip for no reason, since entries are
                # gated off anyway before watch_start_hhmm. Logs ONE line per
                # day instead, and does NOT call _on_fetch_fail() during this
                # window -- after 09:15, behavior is completely unchanged
                # (every case below this still applies exactly as before).
                if datetime.now().time() < datetime.strptime("09:15", "%H:%M").time():
                    if CACHE.get("_premarket_logged_date") != date.today():
                        log("[WAITING] Pre-market — no fresh candle yet, market opens 09:15. "
                            "(Further pre-market staleness checks suppressed until then.)")
                        CACHE["_premarket_logged_date"] = date.today()
                    return CACHE
                log(f"[DATA FETCH ERROR] Last 3m candle is {int(_last_bar_age)}s old "
                    f"(>{STALE_CANDLE_SEC}s) — feed not advancing, reusing cached candles")
                _on_fetch_fail()
                return CACHE

            CACHE["df3"]       = df3
            CACHE["hist_time"] = now

            _bars_now = len(df3)
            _is_new_bar = (_bars_now != CACHE.get("_last_logged_bars"))
            if _is_new_bar:
                CACHE["_last_logged_bars"] = _bars_now

            # v3.2-R6: VWAP visibility check (diagnostic only — no behavior change).
            if _is_new_bar:
                try:
                    _vwap_chk  = CACHE["df3"]["vwap"].iloc[-2]
                    _close_chk = CACHE["df3"]["close"].iloc[-2]
                    _mode = ("weighted" if ("volume" in df3.columns and df3["volume"].sum() > 0)
                             else "equal-weight")
                    if not pd.isna(_vwap_chk):
                        log(f"VWAP CHECK   | Spot:{round(spot,2)}  BotVWAP:{round(float(_vwap_chk),2)}  "
                            f"Gap:{round(float(_close_chk - _vwap_chk),2)}  Mode:{_mode}")
                except Exception:
                    pass

        _FETCH_FAIL_COUNT = 0
        if not _DATA_HEALTHY:
            _DATA_HEALTHY = True
            log("DATA HEALTH   | Feed recovered — entry signals re-enabled.")

        return CACHE

    except Exception as e:
        log(f"[HISTORICAL PIPELINE ERROR] {e}")
        _on_fetch_fail()
        time.sleep(2)
        return CACHE


def _on_fetch_fail():
    """FIX-3: increment fail counter; suppress entries at limit."""
    global _FETCH_FAIL_COUNT, _DATA_HEALTHY
    _FETCH_FAIL_COUNT += 1
    if _FETCH_FAIL_COUNT >= _FETCH_FAIL_LIMIT and _DATA_HEALTHY:
        _DATA_HEALTHY = False
        log(f"DATA HEALTH   | {_FETCH_FAIL_COUNT} consecutive fetch failures. "
            f"Entry signals SUPPRESSED until feed recovers.")
        tg(f"API DEGRADED\n{_FETCH_FAIL_COUNT} consecutive fetch failures.\nEntries blocked.")


def data_is_stale():
    return (time.time() - CACHE["time"]) > STALE_SEC


# =============================================================================
#  SECTION 13 — STRIKE ROUNDING + VIX
# =============================================================================


def round50(x):
    return int(x / STRIKE_ROUND_UNIT + 0.5) * STRIKE_ROUND_UNIT


def fetch_india_vix():
    """
    Group 1 / VIX-VALIDATED: fetch India VIX from RMoney/XTS NSE EID 26002.

    Broker-specific endpoint remains unchanged, but the returned payload is
    now validated strictly before the value enters the VIX regime/strike logic.
    Missing, non-numeric, non-positive, or implausible values fail closed.
    The configured VIX thresholds themselves are untouched.
    """
    vix_eid = 26002
    try:
        instruments = [{
            "exchangeSegment": NIFTY_EXCHANGE_SEGMENT,
            "exchangeInstrumentID": vix_eid,
        }]
        resp = _HTTP.post(
            f"{MARKETDATA_URL}/instruments/quotes",
            headers=_md_headers(),
            json={
                "instruments": instruments,
                "xtsMessageCode": 1502,
                "publishFormat": "JSON",
            },
            timeout=5,
        )
        if resp.status_code != 200:
            log(f"[VIX FETCH ERROR] HTTP {resp.status_code} for EID {vix_eid}")
            return None

        data = resp.json()
        if data.get("type") != "success":
            log(f"[VIX FETCH ERROR] XTS returned {data.get('description', data)}")
            return None

        quotes = data.get("result", {}).get("listQuotes", [])
        if not quotes:
            log(f"[VIX FETCH ERROR] no quote returned for India VIX EID {vix_eid}")
            return None

        q = json.loads(quotes[0]) if isinstance(quotes[0], str) else quotes[0]
        touchline = q.get("Touchline", {}) if isinstance(q, dict) else {}
        ltp = touchline.get("LastTradedPrice")
        if ltp is None:
            log(f"[VIX FETCH ERROR] LastTradedPrice missing for India VIX EID {vix_eid}")
            return None

        value = float(ltp)
        if not (0.0 < value < 100.0):
            log(f"[VIX FETCH ERROR] implausible India VIX value {value} from EID {vix_eid}")
            return None

        log(f"VIX SOURCE    | RMoney/XTS EID:{vix_eid} India VIX:{value:.2f}")
        return value

    except (TypeError, ValueError) as e:
        log(f"[VIX FETCH ERROR] invalid numeric value from EID {vix_eid}: {e}")
        return None
    except Exception as e:
        log(f"[VIX FETCH ERROR] EID {vix_eid}: {e}")
        return None

def get_vix_regime():
    """
    Reports a plain VIX-tier label for the periodic 09:20/12:30 log+Telegram
    update in main(). Purely informational for BOT_G -- its own strike-pool
    ladder (lock_bot_g_strike_pool(), BOTG_STRIKE_POOL_PROFILE) does its
    own independent VIX fetch and is not driven by this function.
    """
    if _VIX_VALUE is None:
        return {"label": "UNKNOWN(no VIX)"}
    v = _VIX_VALUE
    if v < VIX_LOW_MAX:
        return {"label": f"LOW({v:.1f})"}
    elif v <= VIX_NORMAL_MAX:
        return {"label": f"NORMAL({v:.1f})"}
    elif v <= VIX_ELEVATED_MAX:
        return {"label": f"ELEVATED({v:.1f})"}
    else:
        return {"label": f"HIGH({v:.1f})"}


# =============================================================================
#  SECTION 14 — PORTFOLIO GATE
# =============================================================================



def allow_trade(bot, side):
    if CIRCUIT_BREAKER_LOCKED:
        return False, "CIRCUIT_BREAKER_LOCKED"
    # v-G28 (20-Aug-2026): losing_streak_exempt -- BOT_G no longer
    # halt on consecutive SL/TSL exits, explicit instruction. Mirrors the
    # existing reentry_lock_exempt pattern.
    if (LOSING_STREAK_PER_BOT and not bot.get("losing_streak_exempt")
            and _bot_streak_locked(bot["name"])):
        return False, "LOSING_STREAK_LOCKED"
    if PROFIT_LOCK_SEALED:
        return False, "PROFIT_LOCK_SEALED"
    if not _DATA_HEALTHY:
        return False, "DATA_FEED_UNHEALTHY"

    # v3.1-R3: same-direction re-entry cooldown after a SL/TSL exit.
    if (REENTRY_COOLDOWN_FILTER
            and bot.get("reentry_block_side") == side
            and time.time() < bot.get("reentry_block_until", 0)):
        return False, "REENTRY_SAME_DIR_COOLDOWN"

    # FIX-4: duplicate position guard
    if not ALLOW_DUPLICATE_POSITIONS:
        # Check all open positions for same symbol+side
        for other_bot in BOTS:
            if (other_bot["name"] != bot["name"]
                    and other_bot["trade_open"]
                    and other_bot.get("entry_symbol")
                    and other_bot["side"] == side
                    # v3.3-BB: BOT_BB is a parallel comparison bot (replica of
                    # BOT_B + extra range filter) — exempted from cross-bot
                    # duplicate blocking in both directions, so its own P&L
                    # can be compared against BOT_B independent of which one
                    # happens to enter first. BOT_A/B/C/D's mutual duplicate
                    # blocking is unaffected — this only skips when either
                    # side of the check is the comparison bot.
                    and not bot.get("duplicate_exempt", False)
                    and not other_bot.get("duplicate_exempt", False)):
                # Same side already open — skip (symbol will likely be same
                # since both bots use ATM strike from same spot price)
                return False, "DUPLICATE_POSITION_BLOCKED"

    if PAPER_TRADE:
        if bot["trade_open"]:
            return False, "BOT_ALREADY_IN_TRADE"
        return True, "OK"

    if time.time() < PORTFOLIO["blocked_until"]:
        return False, "PORTFOLIO_COOLDOWN"
    if PORTFOLIO["open_trades"] >= PORTFOLIO["max_open_trades"]:
        return False, "MAX_OPEN_TRADES_REACHED"
    if PORTFOLIO["direction"] is not None and PORTFOLIO["direction"] != side:
        return False, "OPPOSITE_DIRECTION_BLOCKED"
    if PORTFOLIO["current_qty"] + bot["qty"] > PORTFOLIO["max_total_qty"]:
        return False, "MAX_QTY_EXCEEDED"
    return True, "OK"


def register_entry(bot, side):
    PORTFOLIO["open_trades"] += 1
    PORTFOLIO["current_qty"] += bot["qty"]
    PORTFOLIO["direction"]    = side


def register_exit(bot):
    PORTFOLIO["open_trades"] = max(0, PORTFOLIO["open_trades"] - 1)
    PORTFOLIO["current_qty"] = max(0, PORTFOLIO["current_qty"] - bot["qty"])
    if PORTFOLIO["open_trades"] == 0:
        PORTFOLIO["direction"] = None
    if not PAPER_TRADE:
        PORTFOLIO["blocked_until"] = time.time() + PORTFOLIO_COOLDOWN


# =============================================================================
#  SECTION 15 — ORDER EXECUTION (SIMULATED/LIVE BROKER INTERFACE)
# =============================================================================



def _norm_key(d, *names):
    """Return the first non-None value from a dict using case-insensitive keys."""
    if not isinstance(d, dict):
        return None
    low = {str(k).lower(): v for k, v in d.items()}
    for name in names:
        if str(name).lower() in low:
            return low[str(name).lower()]
    return None


def _result_list(data):
    if not isinstance(data, dict):
        return []
    r = data.get("result", [])
    if isinstance(r, list):
        return r
    if isinstance(r, dict):
        for k in ("result", "data", "positions", "orders", "trades", "listPositions"):
            v = r.get(k)
            if isinstance(v, list):
                return v
    return []


def _get_order_book_rmoney():
    try:
        resp = _HTTP.get(f"{INTERACTIVE_URL}/orders", headers=_int_headers(), timeout=5)
        if resp.status_code != 200:
            log(f"ORDER BOOK ERROR | HTTP {resp.status_code}")
            return []
        data = resp.json()
        if data.get("type") != "success":
            log(f"ORDER BOOK ERROR | {data.get('description')}")
            return []
        return _result_list(data)
    except Exception as e:
        log(f"ORDER BOOK ERROR | {e}")
        return []


def _get_trade_book_rmoney():
    try:
        resp = _HTTP.get(f"{INTERACTIVE_URL}/orders/trades", headers=_int_headers(), timeout=5)
        if resp.status_code != 200:
            log(f"TRADE BOOK ERROR | HTTP {resp.status_code}")
            return []
        data = resp.json()
        if data.get("type") != "success":
            log(f"TRADE BOOK ERROR | {data.get('description')}")
            return []
        return _result_list(data)
    except Exception as e:
        log(f"TRADE BOOK ERROR | {e}")
        return []


def _get_order_fill(order_id):
    """v-RG2: verified XTS TradeBook reconciliation for real fills."""
    if not order_id or str(order_id).startswith("SIM_"):
        return None, None
    try:
        trades = _get_trade_book_rmoney()
        oid = str(order_id)
        qty = 0
        value = 0.0
        for t in trades:
            tid = _norm_key(t, "AppOrderID", "AppOrderId", "OrderID", "OrderId")
            if tid is None or str(tid) != oid:
                continue
            q = float(_norm_key(t, "OrderGeneratedQuantity", "OrderQuantity", "TradedQuantity", "FilledQuantity", "Quantity") or 0)
            px = float(_norm_key(t, "ExecutionPrice", "TradedPrice", "AverageTradedPrice", "Price") or 0)
            if q > 0 and px > 0:
                qty += int(q)
                value += q * px
        if qty > 0:
            return round(value / qty, 4), qty
        return None, 0
    except Exception as e:
        log(f"FILL QUERY ERROR | {order_id}: {e}")
        return None, None


def _get_order_status_rmoney(order_id):
    """Return (status, average/fill price, filled quantity) from XTS order book."""
    if not order_id or str(order_id).startswith("SIM_"):
        return "UNKNOWN", None, None
    for o in _get_order_book_rmoney():
        oid = _norm_key(o, "AppOrderID", "AppOrderId", "OrderID", "OrderId")
        if oid is not None and str(oid) == str(order_id):
            status = str(_norm_key(o, "OrderStatus", "Status") or "UNKNOWN").upper()
            fp, fq = _get_order_fill(order_id)
            if fp is None:
                fp = _norm_key(o, "AverageTradedPrice", "TradedPrice", "Price")
            fq = fq or int(float(_norm_key(o, "FilledQuantity", "TradedQuantity", "CumulativeQuantity") or 0))
            return status, fp, fq
    return "UNKNOWN", None, None


def _position_symbol(p):
    return _norm_key(p, "TradingSymbol", "Symbol", "tradingSymbol", "Description")


def _position_eid(p):
    return _norm_key(p, "ExchangeInstrumentId", "ExchangeInstrumentID", "exchangeInstrumentID")


def _position_net_qty(p):
    v = _norm_key(p, "NetQty", "NetQuantity", "Quantity", "OpenNetQuantity")
    if v is not None:
        try: return int(float(v))
        except Exception: pass
    buy = _norm_key(p, "BuyQuantity", "OpenBuyQuantity") or 0
    sell = _norm_key(p, "SellQuantity", "OpenSellQuantity") or 0
    try: return int(float(buy)) - int(float(sell))
    except Exception: return 0


def _get_positions_rmoney():
    """v-RG2: verified XTS positions endpoint; returns current day positions."""
    try:
        resp = _HTTP.get(f"{INTERACTIVE_URL}/portfolio/positions?dayOrNet=DayWise",
                         headers=_int_headers(), timeout=5)
        if resp.status_code != 200:
            log(f"POSITIONS ERROR | HTTP {resp.status_code}")
            return None
        data = resp.json()
        if data.get("type") != "success":
            log(f"POSITIONS ERROR | {data.get('description')}")
            return None
        return _result_list(data)
    except Exception as e:
        log(f"POSITIONS ERROR | {e}")
        return None


def _check_existing_position(symbol):
    """Return signed net quantity for one exact option symbol; None means query failed."""
    positions = _get_positions_rmoney()
    if positions is None:
        return None
    target_eid = _resolve_option_eid(symbol)
    net = 0
    for p in positions:
        ps = _position_symbol(p)
        pe = _position_eid(p)
        if (ps and str(ps) == str(symbol)) or (target_eid is not None and pe is not None and str(pe) == str(target_eid)):
            net += _position_net_qty(p)
    return net


LIVE_EXECUTION_HALT = False   # v-RG3: fail-closed live execution latch, mirrors Fyers' vRG2

def _halt_live_execution(reason):
    """
    v-RG3 (bug fix): this entire function was missing from the RMoney
    build -- confirmed via independent review. Fyers' vRG2 build has had
    it since that version; RMoney had none of the halt/emergency-flatten
    infrastructure at all, not just a missing call site. Mirrors Fyers'
    _halt_live_execution() exactly.
    """
    global LIVE_EXECUTION_HALT
    LIVE_EXECUTION_HALT = True
    log(f"LIVE SAFETY HALT | {reason}")
    tg(f"LIVE SAFETY HALT\n{reason}\nNo further live orders will be submitted until the process is restarted and reconciled.")


def _emergency_flatten(bot, reason):
    """
    v-RG3 (bug fix): also missing entirely from the RMoney build.
    Built on RMoney's own already-verified place_exit_order() (broker-
    quantity-capped market sell, fill verification, already-flat-via-
    broker-SL detection) rather than reimplementing position-check/
    order-place/fill-verify from scratch -- lower risk than writing new
    order-placement logic for a function whose whole purpose is safety.
    place_exit_order() raises on failure (RMoney's own error-handling
    style); this wrapper catches that and converts it into the same
    True/False-plus-halt contract Fyers' _emergency_flatten() uses, so
    the caller can act on it the same way in both bots.
    """
    if PAPER_TRADE or not bot.get("entry_symbol"):
        return False
    symbol = bot["entry_symbol"]
    qty = _check_existing_position(symbol)
    if qty is None:
        _halt_live_execution(f"Emergency flatten position query failed for {symbol}")
        return False
    if qty <= 0:
        return True   # already flat -- nothing to do
    log(f"EMERGENCY FLATTEN | {bot['name']} {symbol} qty={qty} reason={reason}")
    try:
        order_id, fill_price, filled_qty = place_exit_order(bot)
    except Exception as e:
        _halt_live_execution(f"Emergency flatten exception for {symbol}: {e}")
        return False
    if order_id is None:
        _halt_live_execution(f"Emergency flatten order rejected for {symbol}")
        return False
    log(f"EMERGENCY FLATTEN CONFIRMED | {symbol} qty={filled_qty} fill={fill_price}")
    return True


def _find_nonzero_nifty_fo_positions():
    positions = _get_positions_rmoney()
    if positions is None:
        return None
    out = []
    for p in positions:
        q = _position_net_qty(p)
        seg = str(_norm_key(p, "ExchangeSegment", "exchangeSegment") or "").upper()
        if q and ("NSEFO" in seg or "NSE_FO" in seg or "NSE" in seg):
            out.append((str(_position_symbol(p) or _position_eid(p) or "UNKNOWN"), q))
    return out




# =============================================================================
#  EXECUTION ENGINE v1.0 — Fyers (v1.0-EE)
#  USE_LIMIT_ORDERS=False → delegates to place_market_order() unchanged.
#  USE_LIMIT_ORDERS=True  → aggressive limit, 2 attempts, market fallback.
# =============================================================================

# =============================================================================
#  EXECUTION ENGINE v1.0 — RMoney/XTS
#  USE_LIMIT_ORDERS=False → delegates to place_market_order() unchanged.
#  USE_LIMIT_ORDERS=True  → NOT YET PORTED for RMoney, see note below.
# =============================================================================
# v-RG1 (23-Aug-2026): the limit-order attempt/retry/fallback engine below
# (_get_ask_bid_rmoney/_place_limit_rmoney/_get_order_status_rmoney) is
# NOT built out -- USE_LIMIT_ORDERS=False in config (confirmed), so
# execute_entry() never reaches this path in practice; building a full
# speculative limit-order engine on unverified XTS order-status/ask-bid
# endpoints wasn't worth the risk for a path that isn't currently used.
# If USE_LIMIT_ORDERS is ever flipped to True for RMoney, these stubs
# will make execute_entry() fall back to a plain market order rather than
# silently fail or call something broken -- but the limit-order attempt
# itself won't actually happen until this is built and verified.


def _get_ask_bid_rmoney(symbol):
    """v-RG1: NOT YET PORTED -- returns (None, None) unconditionally, which
    makes execute_entry()'s limit-order path fall back to market."""
    return None, None


def _place_limit_rmoney(bot, side, limit_price):
    """v-RG1: NOT YET PORTED -- returns (None, 'NOT_IMPLEMENTED')."""
    return None, "NOT_IMPLEMENTED"


# v-RG2: _get_order_status_rmoney is implemented above using the verified XTS order/trade books.


def _find_open_sl_order_rmoney(symbol):
    for o in _get_order_book_rmoney():
        osym = _norm_key(o, "TradingSymbol", "Symbol")
        typ = str(_norm_key(o, "OrderType", "orderType") or "").upper()
        status = str(_norm_key(o, "OrderStatus", "Status") or "").upper()
        if osym == symbol and typ == "SL-M" and any(x in status for x in ("PENDING", "OPEN", "NEW", "TRIGGER PENDING")):
            return str(_norm_key(o, "AppOrderID", "AppOrderId", "OrderID", "OrderId"))
    return None


def _check_open_orders_rmoney(symbol):
    """
    v-RG1: ported from the A-F suite's own _check_open_orders_rmoney()
    unchanged -- this one IS verified (GET /order/order-book).
    """
    try:
        resp = _HTTP.get(f"{INTERACTIVE_URL}/order/order-book", headers=_int_headers(), timeout=5)
        if resp.status_code != 200:
            return False
        data = resp.json()
        orders = data.get("result", []) if data.get("type") == "success" else []
        for o in orders:
            if (o.get("TradingSymbol") == symbol and "PENDING" in str(o.get("OrderStatus", "")).upper()):
                return True
        return False
    except Exception:
        return False


def execute_entry(bot, side):
    """
    Execution Engine v1.0 — RMoney/XTS.
    USE_LIMIT_ORDERS=False → place_market_order() directly (no change).
    USE_LIMIT_ORDERS=True  → aggressive limit with 2 attempts then market.
    Returns (order_id, fill_price, filled_qty).
    """
    if not USE_LIMIT_ORDERS or PAPER_TRADE:
        return place_market_order(bot, side)

    symbol     = bot["entry_symbol"]
    qty        = bot["qty"]
    bot_name   = bot["name"]

    ask0, bid0 = _get_ask_bid_rmoney(symbol)
    if ask0 is None:
        log(f"EXEC ENGINE  | {bot_name} ask fetch failed — market fallback")
        return place_market_order(bot, side)

    signal_ask = ask0

    def _buf(ask, bid):
        spread = (ask - bid) if bid and bid > 0 else ask * EXEC_SPREAD_FALLBACK_PCT
        return min(max(EXEC_MIN_BUFFER, spread * EXEC_SPREAD_BUFFER_FRACTION), EXEC_MAX_BUFFER)

    def _ok(current_ask):
        pct = (current_ask - signal_ask) / signal_ask * 100
        if pct > EXEC_MAX_SLIPPAGE_PCT:
            log(f"EXEC ENGINE  | {bot_name} slippage {pct:.1f}% > {EXEC_MAX_SLIPPAGE_PCT}% — abort")
            return False
        return True

    # Attempt 1
    if _check_existing_position(symbol) > 0 or _check_open_orders_rmoney(symbol):
        log(f"EXEC ENGINE  | {bot_name} position/order exists — aborting")
        return None, None, None

    lim1 = round(ask0 + _buf(ask0, bid0), 1)
    log(f"EXEC ENGINE  | {bot_name} Att1 LIMIT={lim1} Ask={ask0} Bid={bid0}")
    oid1, s1 = _place_limit_rmoney(bot, side, lim1)
    if oid1 is None:
        log(f"EXEC ENGINE  | {bot_name} Att1 failed ({s1}) — market fallback")
        return place_market_order(bot, side)

    time.sleep(EXEC_WAIT_SEC)
    st1, fp1, fq1 = _get_order_status_rmoney(oid1)
    if st1 == "FILLED":
        log(f"EXEC ENGINE  | {bot_name} Att1 FILLED at {fp1}")
        return oid1, fp1, fq1 or qty
    if st1 in ("PENDING", "UNKNOWN", "PENDING_CANCEL"):
        _cancel_order_rmoney(oid1)
        time.sleep(EXEC_CANCEL_WAIT_SEC)

    # Attempt 2
    ask2, bid2 = _get_ask_bid_rmoney(symbol)
    if ask2 is None or not _ok(ask2):
        return None, None, None
    if _check_existing_position(symbol) > 0 or _check_open_orders_rmoney(symbol):
        log(f"EXEC ENGINE  | {bot_name} position/order appeared — aborting")
        return None, None, None

    lim2 = round(ask2 + _buf(ask2, bid2), 1)
    log(f"EXEC ENGINE  | {bot_name} Att2 LIMIT={lim2} Ask={ask2} Bid={bid2}")
    oid2, s2 = _place_limit_rmoney(bot, side, lim2)
    if oid2 is None:
        log(f"EXEC ENGINE  | {bot_name} Att2 failed ({s2}) — market fallback")
        return place_market_order(bot, side)

    time.sleep(EXEC_WAIT_SEC)
    st2, fp2, fq2 = _get_order_status_rmoney(oid2)
    if st2 == "FILLED":
        log(f"EXEC ENGINE  | {bot_name} Att2 FILLED at {fp2}")
        return oid2, fp2, fq2 or qty
    if st2 in ("PENDING", "UNKNOWN", "PENDING_CANCEL"):
        _cancel_order_rmoney(oid2)
        time.sleep(EXEC_CANCEL_WAIT_SEC)

    # Market fallback
    askf, _ = _get_ask_bid_rmoney(symbol)
    if askf is None or not _ok(askf):
        return None, None, None
    log(f"EXEC ENGINE  | {bot_name} market fallback after 2 limit attempts")
    return place_market_order(bot, side)


def placeOrder(symbol, action, quantity, order_type, price, product_type, papertrading=0, product="intraday_fno"):
    """
    v-RG1: ported from the A-F suite's own placeOrder() unchanged --
    verified working pattern (POST /interactive/orders via XTS).
    papertrading=0 -> paper (print only); papertrading=1 -> live order.
    """
    if papertrading == 0:
        log(f"  [PAPER ORDER] {action} {symbol}  Qty:{quantity}  Type:{order_type}  Price:{price}")
        return {"type": "success", "result": {"AppOrderID": "PAPER_ORDER"}}
    try:
        is_sl_order = (order_type == "SL-M")
        payload = {
            "exchangeSegment":      NIFTY_FO_SEGMENT,
            "exchangeInstrumentID": _resolve_option_eid(symbol) or 0,
            "productType":          "MIS",
            "orderType":            order_type,
            "orderSide":            action,
            "timeInForce":          "DAY",
            "disclosedQuantity":    0,
            "orderQuantity":        quantity,
            "limitPrice":           0 if is_sl_order else price,
            "stopPrice":            price if is_sl_order else 0,
            "orderUniqueIdentifier": str(int(time.time())),
        }
        resp = _HTTP.post(f"{INTERACTIVE_URL}/orders", headers=_int_headers(), json=payload, timeout=5)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        log(f"  [ORDER ERROR] {e}")
        return None


def _modify_order_rmoney(order_id, new_stop_price, qty):
    """v-RG1: ported from the A-F suite's own _modify_order_rmoney() unchanged."""
    try:
        payload = {
            "appOrderID": int(order_id), "modifiedProductType": "MIS", "modifiedOrderType": "SL-M",
            "modifiedOrderQuantity": qty, "modifiedDisclosedQuantity": 0, "modifiedLimitPrice": 0,
            "modifiedStopPrice": round(new_stop_price, 1), "modifiedTimeInForce": "DAY",
            "orderUniqueIdentifier": str(int(time.time())),
        }
        resp = _HTTP.put(f"{INTERACTIVE_URL}/orders", headers=_int_headers(), json=payload, timeout=5)
        if resp.status_code != 200:
            return False
        return resp.json().get("type") == "success"
    except Exception as e:
        log(f"[SL MODIFY ERROR] {e}")
        return False


def _cancel_order_rmoney(order_id):
    """v-RG1: ported from the A-F suite's own _cancel_order_rmoney() unchanged."""
    try:
        resp = requests.delete(f"{INTERACTIVE_URL}/order/cancel-order", headers=_int_headers(),
                                json={"appOrderID": int(order_id)}, timeout=5)
        if resp.status_code != 200:
            return False
        return resp.json().get("type") == "success"
    except Exception:
        return False


def _wait_live_order_fill(order_id, symbol, requested_qty):
    deadline = time.time() + float(LIVE_FILL_TIMEOUT_SEC)
    last_status = "UNKNOWN"
    while time.time() < deadline:
        st, fp, fq = _get_order_status_rmoney(order_id)
        last_status = st
        if st in ("FILLED", "COMPLETE", "EXECUTED") and fq:
            return fp, fq, st
        if fq and fp:
            return fp, fq, st
        time.sleep(float(LIVE_FILL_POLL_SEC))
    # Reconcile the actual broker position before declaring the order lost.
    pos = _check_existing_position(symbol)
    if pos is None:
        raise RuntimeError(f"Cannot reconcile live order {order_id}; broker position query failed")
    if pos > 0:
        fp, fq = _get_order_fill(order_id)
        if fp is None:
            raise RuntimeError(f"Order {order_id} created a broker position but fill price is unavailable")
        return fp, pos, "RECONCILED_POSITION"
    # Try to cancel only after proving no position exists.
    _cancel_order_rmoney(order_id)
    time.sleep(float(EXEC_CANCEL_WAIT_SEC))
    pos2 = _check_existing_position(symbol)
    if pos2 is None or pos2 > 0:
        raise RuntimeError(f"Order {order_id} became uncertain after cancel/recheck")
    raise RuntimeError(f"Order {order_id} not filled within {LIVE_FILL_TIMEOUT_SEC}s; no broker position")


def place_market_order(bot, side):
    """v-RG2: live market entry with mandatory broker fill/position reconciliation."""
    log(f"ORDER ENTRY  | {bot['name']} BUY {side} QTY:{bot['qty']} "
        f"{'[PAPER]' if PAPER_TRADE else '[LIVE]'}")
    if PAPER_TRADE:
        return "SIM_ENTRY_ORDER_ID", None, None

    existing_qty = _check_existing_position(bot['entry_symbol'])
    if existing_qty is None:
        raise RuntimeError("RMoney position query failed before entry; LIVE entry blocked")
    if existing_qty != 0:
        log(f"PRE-ENTRY GUARD | {bot['name']} broker position already exists qty={existing_qty}")
        tg(f"LIVE ENTRY BLOCKED {bot['name']}\nExisting broker position: {existing_qty}")
        return None, None, None
    if _find_open_sl_order_rmoney(bot['entry_symbol']):
        log(f"PRE-ENTRY GUARD | {bot['name']} broker SL order already exists")
        tg(f"LIVE ENTRY BLOCKED {bot['name']}\nExisting broker SL order found.")
        return None, None, None

    response = placeOrder(bot['entry_symbol'], "BUY", bot['qty'], "MARKET", 0, "MIS", papertrading=1)
    if not response or response.get("type") != "success":
        msg = (response or {}).get("description", str(response))
        log(f"ORDER REJECTED | {bot['name']} {side} — {msg}")
        tg(f"ORDER REJECTED {bot['name']} {side}\nSymbol: {bot['entry_symbol']}\nReason: {msg}")
        return None, None, None

    order_id = response.get("result", {}).get("AppOrderID")
    if not order_id:
        raise RuntimeError("RMoney accepted entry request without AppOrderID")
    log(f"ORDER PLACED | {bot['name']} OrderID:{order_id}")
    try:
        fill_price, filled_qty, status = _wait_live_order_fill(order_id, bot['entry_symbol'], bot['qty'])
    except Exception as e:
        tg(f"LIVE ENTRY UNCERTAIN {bot['name']}\nOrder: {order_id}\n{e}\nSTOP NEW ENTRIES / RECONCILE BROKER.")
        raise
    if filled_qty <= 0 or fill_price is None:
        raise RuntimeError(f"Entry {order_id} has no verified fill")
    if filled_qty != bot['qty']:
        log(f"PARTIAL FILL | {bot['name']} ordered={bot['qty']} filled={filled_qty} fill_price={fill_price}")
        tg(f"PARTIAL FILL {bot['name']}\nOrdered: {bot['qty']} Filled: {filled_qty}\nFill price: {fill_price}")
    return order_id, fill_price, filled_qty


def place_exit_order(bot):
    """v-RG2: live exit uses actual broker position and verified fill only."""
    symbol = bot["entry_symbol"]
    broker_qty = _check_existing_position(symbol)
    if broker_qty is None:
        raise RuntimeError(f"RMoney position query failed before EXIT for {symbol}")
    if broker_qty <= 0:
        # Most likely the broker-side SL already filled. Recover its fill if possible.
        fp, fq = _get_order_fill(bot.get("sl_order_id"))
        if fp is not None and fq:
            log(f"EXIT RECONCILE | {bot['name']} broker already flat; recovered SL fill {fp} qty={fq}")
            return "BROKER_SL_ALREADY_FILLED", fp, fq
        raise RuntimeError(f"Broker position already flat for {symbol} but exit fill cannot be identified")

    qty = min(int(bot["qty"]), int(broker_qty))
    log(f"ORDER EXIT   | {bot['name']} SELL {bot['side']} QTY:{qty} {'[PAPER]' if PAPER_TRADE else '[LIVE]'}")
    if PAPER_TRADE:
        return "RMONEY_EXIT_ORDER_PAPER", None, qty

    response = placeOrder(symbol, "SELL", qty, "MARKET", 0, "MIS", papertrading=1)
    if not response or response.get("type") != "success":
        msg = (response or {}).get("description", str(response))
        log(f"EXIT ORDER REJECTED | {bot['name']} — {msg}")
        tg(f"EXIT ORDER REJECTED {bot['name']}\nSymbol: {symbol}\nReason: {msg}\nPOSITION REMAINS OPEN.")
        return None, None, None
    order_id = response.get("result", {}).get("AppOrderID")
    if not order_id:
        raise RuntimeError("RMoney accepted exit request without AppOrderID")
    log(f"ORDER PLACED | {bot['name']} EXIT OrderID:{order_id}")
    try:
        fill_price, filled_qty, status = _wait_live_order_fill(order_id, symbol, qty)
    except Exception as e:
        tg(f"LIVE EXIT UNCERTAIN {bot['name']}\nOrder: {order_id}\n{e}\nCHECK BROKER IMMEDIATELY.")
        raise
    if filled_qty <= 0 or fill_price is None:
        raise RuntimeError(f"Exit {order_id} has no verified fill")
    if filled_qty != qty:
        log(f"PARTIAL EXIT | {bot['name']} requested={qty} filled={filled_qty} fill_price={fill_price}")
        tg(f"PARTIAL EXIT {bot['name']}\nRequested: {qty} Filled: {filled_qty}\nFill price: {fill_price}")
    return order_id, fill_price, filled_qty


def update_broker_sl_order(bot, new_sl):
    """
    v-RG1: rebuilt on RMoney's verified placeOrder()/_modify_order_rmoney()
    -- places a real resting SL-M order in LIVE mode, trails it in place
    on subsequent calls (modify, not cancel+replace, so there's no window
    with no resting protection). Paper mode behavior unchanged.

    v-RG3 (bug fix): this function previously never returned a proper
    True/False signal on any path -- every success path fell through
    with an implicit `return None`, and some failure paths `raise`d a
    RuntimeError instead of returning False, while other failure paths
    just logged and also fell through to an implicit `return None`. The
    caller (right after a live entry) was also never checking any
    return value at all -- confirmed via independent review. Together,
    this meant a genuinely failed broker SL placement after a live
    entry could leave a real, unprotected options position with no
    safety net and no halt. Now returns True/False explicitly on every
    path and calls _halt_live_execution() at the same failure points
    Fyers' version does, so the caller's emergency-flatten check (added
    below, mirroring Fyers exactly) can actually see failures and act
    on them.
    """
    trigger = round(new_sl, 1)
    if PAPER_TRADE:
        if bot["sl_order_id"] is None:
            log(f"SL SET       | {bot['name']} Virtual SL registered at premium {trigger}")
            bot["sl_order_id"] = "SIM_SL_ORDER_ID"
        else:
            log(f"SL UPDATE    | {bot['name']} SL moved to premium {trigger}")
        return True

    if bot["sl_order_id"] is None:
        try:
            response = placeOrder(bot["entry_symbol"], "SELL", bot["qty"], "SL-M", trigger, "MIS", papertrading=1)
        except Exception as e:
            log(f"SL SET ERROR | {bot['name']} {e}")
            tg(f"SL PLACEMENT ERROR {bot['name']}\n{e}\nPosition currently has NO broker-side stop.")
            _halt_live_execution(f"Broker SL placement exception for {bot['name']}: {e}")
            return False
        if response and response.get("type") == "success":
            order_id = response.get("result", {}).get("AppOrderID", "RMONEY_SL_ORDER")
            bot["sl_order_id"] = order_id
            time.sleep(0.2)
            verified = _find_open_sl_order_rmoney(bot["entry_symbol"])
            if not verified:
                bot["sl_order_id"] = None
                log(f"SL SET FAILED | {bot['name']} broker accepted SL request but open-order verification failed")
                tg(f"SL VERIFICATION FAILED {bot['name']}\nNo verified broker-side stop exists. LIVE management blocked until checked.")
                _halt_live_execution(f"Broker SL placement could not be verified for {bot['name']}")
                return False
            bot["sl_order_id"] = verified
            log(f"SL SET       | {bot['name']} broker SL-M verified OrderID:{verified} @ {trigger}")
        else:
            msg = (response or {}).get("description", str(response))
            log(f"SL SET FAILED | {bot['name']} could not place broker SL-M @ {trigger} — {msg}")
            tg(f"SL PLACEMENT FAILED {bot['name']}\nPosition currently has NO broker-side stop.\nCheck manually.")
            _halt_live_execution(f"Broker SL placement failed for {bot['name']}")
            return False
    else:
        ok = _modify_order_rmoney(bot["sl_order_id"], trigger, bot["qty"])
        if ok:
            verified = _find_open_sl_order_rmoney(bot["entry_symbol"])
            if not verified:
                log(f"SL UPDATE FAILED | {bot['name']} modify acknowledged but no open SL could be verified")
                tg(f"SL VERIFICATION FAILED {bot['name']}\nBroker SL status could not be verified after modification.")
                _halt_live_execution(f"Broker SL modification could not be verified for {bot['name']}")
                return False
            bot["sl_order_id"] = verified
            log(f"SL UPDATE    | {bot['name']} broker SL verified at premium {trigger}")
        else:
            log(f"SL UPDATE FAILED | {bot['name']} could not move broker SL to {trigger} "
                f"— still resting at previous trigger")
            tg(f"SL MODIFY FAILED {bot['name']}\nCould not trail SL to {trigger} — still at old level.\nCheck manually.")
            if LIVE_REQUIRE_BROKER_SL:
                _halt_live_execution(f"Broker SL modify failed for {bot['name']} at {trigger}")
                return False
    return True


def cancel_broker_sl_order(bot):
    if not bot["sl_order_id"]:
        return
    if not PAPER_TRADE:
        broker_qty = _check_existing_position(bot["entry_symbol"])
        if broker_qty == 0:
            # Broker-side SL may already have executed. Preserve the order id
            # long enough for place_exit_order()/tradebook reconciliation to
            # recover its fill instead of issuing a second SELL.
            log(f"SL CANCEL    | {bot['name']} broker position already flat; preserving SL order id for fill reconciliation")
            return
        if broker_qty is None:
            raise RuntimeError("Cannot verify broker position before cancelling SL")
    if PAPER_TRADE:
        log(f"SL CANCEL    | {bot['name']} SL order cleared")
        bot["sl_order_id"] = None
        return
    ok = _cancel_order_rmoney(bot["sl_order_id"])
    if ok:
        time.sleep(0.2)
        still_open = _find_open_sl_order_rmoney(bot["entry_symbol"])
        if still_open:
            log(f"SL CANCEL FAILED | {bot['name']} cancel acknowledged but SL remains open OrderID:{still_open}")
            tg(f"SL CANCEL VERIFICATION FAILED {bot['name']}\nOrder {still_open} still appears open.")
            raise RuntimeError("Broker SL cancellation could not be verified")
        log(f"SL CANCEL    | {bot['name']} broker SL cancellation verified")
    else:
        log(f"SL CANCEL FAILED | {bot['name']} could not cancel broker SL order "
            f"{bot['sl_order_id']} — check manually before re-entering")
        tg(f"SL CANCEL FAILED {bot['name']}\nOrder {bot['sl_order_id']} may still be resting at broker.\nCheck manually.")
    bot["sl_order_id"] = None



# =============================================================================
#  SECTION 16 — POSITION MANAGER
#
#  SL LOGIC CONFIRMATION (both CE and PE):
#  ----------------------------------------
#  We always BUY options. SL fires when the OPTION PREMIUM falls below
#  active_sl -- regardless of CE or PE:
#    CE bought: premium falls when Nifty falls  -> ltp <= active_sl -> exit
#    PE bought: premium falls when Nifty rises  -> ltp <= active_sl -> exit
#  The condition  ltp <= active_sl  is correct for BOTH sides.
#
#  PnL:  CE = (exit - entry) x qty   (positive when premium rises)
#        PE = (entry - exit) x qty   (positive when premium rises)
#  Both formulae are correct for option buying.
# =============================================================================


def _close_bot(bot, cooldown=0):
    register_exit(bot)
    bot["trade_open"]     = False
    bot["last_exit_time"] = time.time()
    bot["sl_lock_until"]  = time.time() + cooldown
    save_state()


# =============================================================================
#  SECTION 17 — BATCH LTP FETCHER
# =============================================================================

def get_multi_ltp(symbols):
    """
    v-RG1: rebuilt for RMoney/XTS -- unlike Fyers' single quotes() call by
    symbol string, XTS needs each option resolved to its EID first, then
    a SINGLE batched quotes POST for all of them together (still one API
    call per cycle, same load profile as the Fyers version). "NIFTY_SPOT"
    is a sentinel string (not a real broker symbol) meaning "the Nifty 50
    index itself" -- resolved directly via NIFTY_INSTRUMENT_ID, no EID
    search needed, same special-case the A-F suite's own getQuotes() uses
    for "Nifty 50".
    """
    if not symbols:
        return {}
    try:
        instruments = []
        eid_to_symbol = {}
        for sym in symbols:
            if sym == "NIFTY_SPOT":
                eid = NIFTY_INSTRUMENT_ID
                seg = NIFTY_EXCHANGE_SEGMENT
            else:
                eid = _resolve_option_eid(sym)
                seg = NIFTY_FO_SEGMENT
            if eid is None:
                # v-G60 (this session): _resolve_option_eid() already logs
                # WHY a lookup failed ([EID SEARCH ERROR/EMPTY/AMBIGUOUS]),
                # but nothing previously logged the CONSEQUENCE -- that this
                # symbol is dropped from this tick's LTP batch entirely,
                # which downstream shows up as a confirmation that can
                # never succeed with no visible cause. Not confirmed as
                # today's specific gap (checked: no EID SEARCH lines fired
                # in the affected window, so those symbols were already
                # cached) -- but the same silent-drop shape, so worth the
                # same visibility for a day where fresh resolution is what
                # fails (e.g. a new week's first-ever lookup on a symbol).
                # LOGGING ONLY.
                log(f"MULTI-LTP GAP | EID resolution failed for {sym}, dropped from batch (v-G60)")
                continue
            instruments.append({"exchangeSegment": seg, "exchangeInstrumentID": eid})
            eid_to_symbol[eid] = sym
        if not instruments:
            return {}

        resp = _HTTP.post(f"{MARKETDATA_URL}/instruments/quotes", headers=_md_headers(),
                           json={"instruments": instruments, "xtsMessageCode": 1502, "publishFormat": "JSON"},
                           timeout=5)
        if resp.status_code != 200:
            log(f"MULTI-LTP ERROR | HTTP {resp.status_code}")
            return {}
        data = resp.json()
        if data.get("type") != "success":
            log(f"MULTI-LTP ERROR | {data.get('description')}")
            return {}

        result = {}
        _dropped_no_quote = []
        for item in data["result"].get("listQuotes", []):
            q = json.loads(item) if isinstance(item, str) else item
            eid = q.get("ExchangeInstrumentID")
            sym = eid_to_symbol.get(eid)
            if sym is None:
                continue
            tl = q.get("Touchline", {})
            ltp = tl.get("LastTradedPrice")
            ask = float(tl.get("AskInfo", {}).get("Price", 0) or 0)
            bid = float(tl.get("BidInfo", {}).get("Price", 0) or 0)
            if ask > 0 and bid > 0:
                result[sym] = round((ask + bid) / 2, 2)
            elif ltp is not None:
                result[sym] = float(ltp)
            else:
                # v-G60 (this session): traced live -- 21-Sep RMoney, every
                # single confirmation attempt from 11:15 to 11:50 expired
                # with "last reason: None", which by check_bot_g_5m_
                # confirmation()'s own docstring should be structurally
                # impossible for a non-confirmed arm (None means confirmed,
                # NO_DATA means ltp was None). Traced back through
                # pool_ltp_map -> here: the symbol appeared in the API's
                # own response (request succeeded, symbol resolved) but had
                # neither a valid bid/ask nor a last-traded-price -- so it
                # silently never made it into result at all, with nothing
                # logged. get_multi_ltp() returned "success" while quietly
                # missing exactly the symbol this tick's confirmation check
                # needed. Checked directly: no [EID SEARCH...] or MULTI-LTP
                # ERROR lines appear anywhere in that window, confirming
                # this exact gap, not a resolution or request failure.
                # LOGGING ONLY -- does not change what result contains,
                # only makes a previously silent gap visible.
                _dropped_no_quote.append(sym)
        if _dropped_no_quote:
            log(f"MULTI-LTP GAP | no bid/ask or LTP in response for: {_dropped_no_quote} "
                f"(v-G60)")
        return result
    except Exception as e:
        log(f"MULTI-LTP ERROR | {e}")
        return {}


# =============================================================================
#  SECTION 18 — CANDLE GATE
# =============================================================================

LAST_CANDLE_KEYS: dict = {}


def is_new_3m_candle(bot_name):
    """
    v-G48 (bug fix): same fix as _is_new_shared_dpcr_candle() above --
    removed the narrow 0<=now.second<=10 wall-clock window, now bucket-
    compared instead. See that function's docstring for the full
    rationale.
    """
    global LAST_CANDLE_KEYS
    now = datetime.now()
    bucket = (now.hour * 60 + now.minute) // 3
    key = f"{bucket}"
    if LAST_CANDLE_KEYS.get(bot_name) != key:
        LAST_CANDLE_KEYS[bot_name] = key
        if len(LAST_CANDLE_KEYS) > 100:
            live_names       = {b["name"] for b in BOTS}
            LAST_CANDLE_KEYS = {k: v for k, v in LAST_CANDLE_KEYS.items()
                                if k in live_names}
        return True
    return False


def is_new_bot_g_candle(bot_name, minutes):
    """Legacy wall-clock helper retained for compatibility; BOT_G v-G40
    no longer uses it for rejection/arm state."""
    if minutes not in (5,10): return False
    now=datetime.now(); elapsed=(now.hour*60+now.minute)-(9*60+15)
    if elapsed < 0 or elapsed % minutes != 0 or not (0 <= now.second <= 10): return False
    key=f"{now.hour}:{now.minute}:{minutes}"
    if LAST_CANDLE_KEYS.get(bot_name)==key: return False
    LAST_CANDLE_KEYS[bot_name]=key
    return True


def in_no_trade_window(bot):
    nt = bot["no_trade"]
    if nt is None:
        return False
    return nt[0] <= hhmm() <= nt[1]






# =============================================================================
#  SECTION 19 — PROFIT LOCK MANAGER
#  Called once per main loop iteration, before the per-bot loop.
#
#  State machine:
#    Phase 1: PnL < MAX_DAILY_PROFIT      → normal trading
#    Phase 2: PnL >= MAX_DAILY_PROFIT     → PROFIT_LOCK_ACTIVE=True, track peak
#    Phase 3: PnL drops TRAIL% from peak  → PROFIT_LOCK_SEALED=True,
#                                           force-exit all open trades,
#                                           no new entries for rest of day
# =============================================================================

def check_profit_lock(active_list, ltp_map):
    """
    Update SESSION_PEAK_PNL and fire profit-lock seal if trail is breached.
    active_list : list of bot dicts currently running
    ltp_map     : {symbol: ltp} dict already fetched this cycle
    """
    global SESSION_PEAK_PNL, PROFIT_LOCK_ACTIVE, PROFIT_LOCK_SEALED, _LIVE_UNREALISED_PNL

    if PROFIT_LOCK_SEALED:
        return   # already sealed — nothing more to do

    # v2.7-FIX2: Always compute unrealised PnL and update SESSION_PEAK_PNL
    # regardless of profit-lock state. Previously this only ran after
    # PROFIT_LOCK_ACTIVE=True, so the dashboard always showed Peak:Rs0.0
    # and the trail could be computed from Rs 0 at the moment of arming.
    unrealised = 0.0
    for bot in active_list:
        if bot["trade_open"] and bot.get("entry_symbol"):
            ltp = ltp_map.get(bot["entry_symbol"], bot["entry"])
            if ltp > 0:
                pts = ltp - bot["entry"]
                unrealised += pts * bot["qty"]

    _LIVE_UNREALISED_PNL = unrealised
    total_pnl_with_open = TOTAL_REALIZED_PNL + unrealised
    if total_pnl_with_open > SESSION_PEAK_PNL:
        SESSION_PEAK_PNL = total_pnl_with_open

    # Phase 2: arm once profit threshold crossed
    if BOTG_GLOBAL_PROFIT_LOCK_ENABLED and TOTAL_REALIZED_PNL >= MAX_DAILY_PROFIT and not PROFIT_LOCK_ACTIVE:
        PROFIT_LOCK_ACTIVE = True
        log(f"PROFIT LOCK  | Armed at Rs{round(TOTAL_REALIZED_PNL,2)}. "
            f"Peak so far: Rs{round(SESSION_PEAK_PNL,2)}. "
            f"Trail: {PROFIT_LOCK_TRAIL_PCT}% below peak.")
        save_state()
        return

    if not PROFIT_LOCK_ACTIVE:
        return

    # Phase 3: check if trail has been breached
    trail_level = SESSION_PEAK_PNL * (1.0 - PROFIT_LOCK_TRAIL_PCT / 100.0)
    if total_pnl_with_open <= trail_level:
        PROFIT_LOCK_SEALED = True
        log(f"PROFIT LOCK  | Trail breached! "
            f"PnL Rs{round(total_pnl_with_open,2)} <= "
            f"trail Rs{round(trail_level,2)} "
            f"(peak Rs{round(SESSION_PEAK_PNL,2)}). "
            f"Force-exiting all open trades. No new entries today.")
        save_state()
        # Force-exit all open positions immediately
        _force_exit_all(active_list, ltp_map, reason="PROFIT_LOCK_TRAIL")


def _force_exit_all(active_list, ltp_map, reason):
    """Exit every open bot position. Called by profit-lock seal."""
    for bot in active_list:
        if bot["trade_open"]:
            log(f"PROFIT LOCK EXIT | {bot['name']} force-closing due to {reason}")
            cancel_broker_sl_order(bot)
            ltp = ltp_map.get(bot.get("entry_symbol"), bot["entry"])
            if ltp <= 0:
                ltp = bot["entry"]
            if log_trade(bot, bot["side"], bot["entry"], ltp, reason, bot["qty"]):
                _close_bot(bot, cooldown=0)


# =============================================================================
#  SECTION 20 — DASHBOARD PRINT
# =============================================================================

def print_dashboard():
    # v3.19-LOGFIX1: display-only change. When nothing has changed since the
    # last dashboard tick (no trade, no PnL/peak/status movement), print a
    # single compact heartbeat line instead of the full repeated table.
    # Logging/data-fetch logic and all trading logic are untouched -- this
    # only decides whether to print the SAME information again.
    global _LAST_DASHBOARD_SIG
    mode_str    = "PAPER TRADE" if PAPER_TRADE else "LIVE"
    cb_str      = "LOCKED" if CIRCUIT_BREAKER_LOCKED else "OK"
    pl_str      = ("SEALED" if PROFIT_LOCK_SEALED
                   else "ARMED" if PROFIT_LOCK_ACTIVE
    else "OFF")
    dh_str      = "OK" if _DATA_HEALTHY else "DEGRADED"
    vix_str     = f"{_VIX_VALUE:.1f}" if _VIX_VALUE is not None else "N/A"
    if LOSING_STREAK_PER_BOT:
        parts = []
        for b in BOTS:
            if b["name"] not in ACTIVE_BOTS:
                continue
            s = _BOT_SL_STREAK.get(b["name"], 0)
            tag = "*" if _bot_streak_locked(b["name"]) else ""
            parts.append(f"{b['name'][-1]}:{s}{tag}/{LOSING_STREAK_LIMIT}")
        streak_str = " ".join(parts)
    else:
        streak_str  = f"{_CONSECUTIVE_SL_COUNT}/{LOSING_STREAK_LIMIT}"
    line        = "-" * 82
    active_list = BOTS if PAPER_TRADE else [b for b in BOTS if b["name"] in ACTIVE_BOTS]
    open_syms   = [b["entry_symbol"] for b in active_list
                   if b["trade_open"] and b.get("entry_symbol")]
    ltp_map     = get_multi_ltp(open_syms) if open_syms else {}

    rows = []
    for bot in active_list:
        mode_label = bot.get("mode", "")[:10]
        if bot["trade_open"]:
            ltp      = ltp_map.get(bot.get("entry_symbol"), bot["entry"])
            pnl_pts  = ltp - bot["entry"]
            open_pnl = round(pnl_pts * bot["qty"], 2)
            if ltp > 0 and bot["active_sl"] > 0:
                gap_pct = round((ltp - bot["active_sl"]) / ltp * 100, 1)
            else:
                gap_pct = 0.0
            rows.append(("OPEN", bot["name"], mode_label, bot["side"], bot["qty"],
                         bot["entry"], ltp, bot["active_sl"], gap_pct, open_pnl))
        else:
            if CIRCUIT_BREAKER_LOCKED:
                status = "CB-LOCK"
            elif (LOSING_STREAK_PER_BOT and not bot.get("losing_streak_exempt")
                  and _bot_streak_locked(bot["name"])):
                status = "SL-LOCK"
            elif PROFIT_LOCK_SEALED:
                status = "PL-SEAL"
            elif not _DATA_HEALTHY:
                status = "NO-DATA"
            elif "entry_windows" in bot:
                if not any(w[0] <= hhmm() <= w[1] for w in bot["entry_windows"]):
                    status = "OFF-WIN"
                elif in_no_trade_window(bot):
                    status = "NO-TRADE"
                else:
                    status = "WAITING"
            else:
                # v-G9-FIX2: BOT_G has neither entry_windows nor no_trade --
                # it uses its own gap-day-dependent watch window
                # (get_bot_g_windows()) and daily direction lock instead.
                _bg_watch, _ = get_bot_g_windows(bot.get("gap_day") or False)
                if not (_bg_watch <= hhmm() < FORCE_EXIT_G):
                    status = "OFF-WIN"
                elif bot.get("locked_side"):
                    status = f"LOCK-{bot['locked_side']}"
                else:
                    status = "WAITING"
            rows.append(("FLAT", bot["name"], mode_label, status))

    sig = (cb_str, pl_str, dh_str, vix_str, streak_str,
           round(TOTAL_REALIZED_PNL, 2), round(SESSION_PEAK_PNL, 2), tuple(rows))
    unchanged = (sig == _LAST_DASHBOARD_SIG)
    _LAST_DASHBOARD_SIG = sig

    if unchanged:
        print(f"  [{mode_str}]  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  |  "
              f"PnL:Rs{round(TOTAL_REALIZED_PNL,2)}  (no change since last update)")
        return

    print(f"\n{line}")
    print(f"  [{mode_str}]  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  |  "
          f"PnL:Rs{round(TOTAL_REALIZED_PNL,2)}  "
          f"Peak:Rs{round(SESSION_PEAK_PNL,2)}  "
          f"CB:{cb_str}  PL:{pl_str}  Data:{dh_str}  "
          f"VIX:{vix_str}  SLStreak:{streak_str}")
    print(line)
    print(f"  {'Bot':<8} {'Mode':<11} {'Status':<9} {'Side':<5} {'Qty':<5} "
          f"{'Entry':>7} {'LTP':>7} {'SL':>7} {'Gap%':>5} {'Open PnL':>10}")
    print(line)
    for row in rows:
        if row[0] == "OPEN":
            _, name, mode_label, side, qty, entry, ltp, sl, gap_pct, open_pnl = row
            sign = "+" if open_pnl >= 0 else ""
            print(f"  {name:<8} {mode_label:<11} {'OPEN':<9} {side:<5} "
                  f"{qty:<5} {entry:>7.1f} {ltp:>7.1f} "
                  f"{sl:>7.1f} {gap_pct:>4}% {sign}{open_pnl:>9.0f}")
        else:
            _, name, mode_label, status = row
            print(f"  {name:<8} {mode_label:<11} {status:<9} "
                  f"{'--':<5} {'--':<5} {'--':>7} {'--':>7} {'--':>7} {'--':>5} {'--':>10}")
    print(line + "\n")


# =============================================================================
#  SECTION 21 — MAIN LOOP
# =============================================================================



def main():
    global SYSTEM_EXIT, CIRCUIT_BREAKER_LOCKED

    if not PAPER_TRADE and not LIVE_TRADING_ARMED:
        raise RuntimeError("LIVE trading requested but LIVE_TRADING_ARMED=False. Set both PAPER_TRADE=False and LIVE_TRADING_ARMED=True only after live-readiness checks.")

    log("=" * 70)
    log("NIFTY WEEKLY OPTIONS BOT -- BOT_G, MULTI-STRIKE POOL (DPCR + Option-VWAP) -- STARTING UP")
    log(f"  INSTRUMENT            : Nifty 50 (RMoney/XTS EID {NIFTY_INSTRUMENT_ID})")
    log(f"  LOT SIZE              : {LOT_SIZE}"
        f"  |  QTY_BOT_G: {QTY_BOT_G} ({QTY_BOT_G // LOT_SIZE} lots)")
    log(f"  STRIKE ROUND          : nearest {STRIKE_ROUND_UNIT}"
        f"  |  EXPIRY: WEEKLY (Tuesday, NSE-holiday-aware; roll when <= {BOTG_ROLLOVER_MAX_DAYS_LEFT} trading day(s) left, v-E18)")
    log(f"  STRIKE POOL (v-G37)   : {BOTG_STRIKE_POOL_PROFILE}")
    log(f"  DPCR OI WINDOW (v-G37): DTE-scaled by weekday, {BOTG_DPCR_WINDOW_BY_WEEKDAY} "
        f"(default {BOTG_DPCR_WINDOW_DEFAULT})")
    log(f"  DPCR ZONE (VIX-scaled) : <{BOTG_DPCR_ZONE_VIX_LOW_MAX}:{BOTG_DPCR_ZONE_TIGHT}"
        f"  {BOTG_DPCR_ZONE_VIX_LOW_MAX}-{BOTG_DPCR_ZONE_VIX_MID_MAX}:{BOTG_DPCR_ZONE_MID}"
        f"  {BOTG_DPCR_ZONE_VIX_MID_MAX}-{BOTG_DPCR_ZONE_VIX_HIGH_MAX}:{BOTG_DPCR_ZONE_WIDE}"
        f"  >={BOTG_DPCR_ZONE_VIX_HIGH_MAX}:{BOTG_DPCR_ZONE_XWIDE}")
    log(f"  FLAT_BAND (VIX-scaled) : {BOTG_DPCR_FLAT_BAND_TIGHT}/{BOTG_DPCR_FLAT_BAND_MID}"
        f"/{BOTG_DPCR_FLAT_BAND_WIDE}/{BOTG_DPCR_FLAT_BAND_XWIDE}"
        f"  |  FALLING_BLOCK: {BOTG_DPCR_FALLING_THRESH_TIGHT}/{BOTG_DPCR_FALLING_THRESH_MID}"
        f"/{BOTG_DPCR_FALLING_THRESH_WIDE}/{BOTG_DPCR_FALLING_THRESH_XWIDE}"
        f"  |  LOOKBACK: {BOTG_DPCR_LOOKBACK_CANDLES} candles")
    log(f"  FLIP FORCE-EXIT        : {'below breakeven only' if BOTG_FLIP_FORCE_EXIT_BELOW_BE else 'disabled'}"
        f"  |  LOSING-STREAK HALT: {LOSING_STREAK_LIMIT} consecutive SL hits, "
        f"re-arm {LOSING_STREAK_COOLDOWN_SEC}s"
        f"  |  RE-ENTRY COOLDOWN: disabled for BOT_G")
    log(f"  ENTRY REJECTION GATE  : NEAR_VWAP_PTS={BOTG_NEAR_VWAP_PTS}"
        f"  |  ENTRY_CUTOFF={BOTG_ENTRY_CUTOFF_HHMM}")
    log(f"  CONFIRM VWAP BAND     : {BOTG_CONFIRM_VWAP_LOWER_TIGHT}/{BOTG_CONFIRM_VWAP_UPPER_TIGHT}"
        f"  {BOTG_CONFIRM_VWAP_LOWER_MID}/{BOTG_CONFIRM_VWAP_UPPER_MID}"
        f"  {BOTG_CONFIRM_VWAP_LOWER_WIDE}/{BOTG_CONFIRM_VWAP_UPPER_WIDE}"
        f"  {BOTG_CONFIRM_VWAP_LOWER_XWIDE}/{BOTG_CONFIRM_VWAP_UPPER_XWIDE}  (VIX-scaled, v-G30)")
    log(f"  SL / BE / TSL         : BE_R_MULT={BOTG_BE_R_MULT}"
        f"  |  TSL_ARM_R_MULT={BOTG_TSL_ARM_R_MULT}"
        f"  |  TSL_BUFFER_PTS={BOTG_TSL_BUFFER_PTS}"
        f"  |  SL_VWAP_CLAMP={'ON' if BOTG_SL_VWAP_CLAMP_ENABLED else 'OFF'} (buffer={BOTG_SL_VWAP_BUFFER}, v-G39/v-G41)")
    log(f"  PARTIAL BOOKING       : {BOTG_PARTIAL_R1_FRACTION*100:.0f}% @ MAX({BOTG_PARTIAL_R1_MULT}R,+{BOTG_PARTIAL_R1_PCT_FLOOR*100:.1f}%)"
        f"  |  {BOTG_PARTIAL_R15_FRACTION*100:.0f}% @ MAX({BOTG_PARTIAL_R15_MULT}R,+{BOTG_PARTIAL_R15_PCT_FLOOR*100:.1f}%)"
        f"  |  remainder trails (G4.3)")
    log(f"  ENTRY WINDOWS         : BOT_G normal={BOTG_TRADE_START_NORMAL_HHMM}"
        f" gap={BOTG_TRADE_START_GAP_HHMM}"
        f"  |  GAP_THRESHOLD={BOTG_GAP_THRESHOLD_PCT}%")
    log(f"  FORCE EXIT            : {FORCE_EXIT_G}"
        f"  |  THETA-DECAY CAP: {BOTG_MAX_HOLD_MINUTES_INITIAL}min (INITIAL stage only, v-G30)")
    log("  DAILY LOSS CAP        : OFF")
    log("  DAILY PROFIT CAP      : OFF")
    log("  BOT PROFIT CAP        : OFF")
    _tier_str = " / ".join(
        f"<=Rs{b if b != float('inf') else 'inf'}:{p}%" for b, p in PROFIT_PROTECT_TIERS
    )
    log("  GLOBAL PROFIT LOCK    : OFF")
    log(f"  STARTUP DATA READY    : {G4_STARTUP_DATA_HHMM}  | candle alignment origin={G4_DATA_ALIGNMENT_HHMM} (G4.4)" )
    log(f"  CACHE_SEC             : {CACHE_SEC}s"
        f"  |  MAX_PORTFOLIO_QTY: {MAX_PORTFOLIO_QTY}"
        f"  |  MAX_OPEN_TRADES: {MAX_OPEN_TRADES}")
    log(f"  MODE                  : {'PAPER TRADE' if PAPER_TRADE else 'LIVE'}")
    log(f"  TELEGRAM ALERTS       : {'ON' if tg.__code__.co_consts[1] else 'OFF (token not set)'}")
    log(f"  HEARTBEAT FILE        : {HEARTBEAT_FILE} every 60s")   # v-G70: now module-level
    log(f"  RUN ID (v-G75)        : {RUN_ID}  |  LOG: {LOG_FILE}  |  TRADES: {TRADE_FILE}")
    log(f"  vE6.2 (log-only)      : rollover by trading days (<= {BOTG_ROLLOVER_MAX_DAYS_LEFT} left -> next expiry) | "
        f"trackers {'ON' if BOTG_TRACK_ENABLED else 'OFF'} {BOTG_TRACK_MIN}m/{BOTG_TRACK_POLL_SEC}s | DATA_LOST after "
        f"{BOTG_DATA_LOST_SEC}s | live-vs-paper + charges (brokerage Rs{CHG_BROKERAGE_PER_ORDER}/order, STT {CHG_STT_SELL_PCT}%)")
    log(f"  vE6.14                : end-of-day cleanup {'ON' if V54_EOD_CLEANUP else 'OFF'} "
        f"(after the 15:10 close: verify upload zip, delete daily files; zips/.py/tokens kept) (v-E54)")
    log(f"  vE6.13                : strike pools {BOTG_STRIKE_POOL_LOW}/{BOTG_STRIKE_POOL_MID}/{BOTG_STRIKE_POOL_HIGH} (v-E52) | "
        f"VIX gate {'ON' if BOTG_VIX_GATE_ENABLED else 'OFF'}: no BOT_G entries when VIX at open lock <= {BOTG_VIX_GATE_MAX} (v-E53) | PAPER forward test")
    log(f"  vE6.12                : exit bid/ask quotes {'ON' if V51_EXIT_QUOTES else 'OFF'} -> {V51_EXIT_QUOTES_FILE} (v-E51, log-only)")
    log(f"  vE6.11                : BOT_G setup candle {BOTG_OPT_TF_MIN}m (v-E49) | 3m ST({BOTG_ST_FILTER_N},{BOTG_ST_FILTER_MULT}) filter "
        f"{'ON' if BOTG_ST_FILTER_ENABLED else 'OFF'} (v-E50) | BOT_GE {'ON' if BOTGE_ENABLED else 'OFF'}")
    log(f"  vE6.10                : CE call-add skip {'LOG-ONLY (entry taken)' if BOTG_CE_CALLADD_SKIP_LOGONLY else 'REAL SKIP'} (v-E48)")
    log(f"  vE6.9                 : shadow lock {'ON' if V46_SHADOW_LOCK else 'OFF'} (zone +/-{V46_ZONE:g}, "
        f"spot 30m sync {V46_SYNC_PTS} pts; v-E46) | option tape {'ON' if V47_OPTION_TAPE else 'OFF'} (ATM +/-{V47_STEPS}; v-E47) | log-only")
    log(f"  vE6.8                 : entry context line {'ON' if V45_ENTRY_CONTEXT else 'OFF'} (spot against = {V45_SPOT_AGAINST_PTS:g} pts / 15 min; v-E45, log-only)")
    log(f"  vE6.7                 : ZLM zero line {ZLM_REF_MODE} (v-E44, log-only)")
    log(f"  vE6.6                 : ZLM check at entry {'ON' if V43_ZLM_TAG else 'OFF'} (v-E43, log-only)"
        f" | 09:18 OI pre-snapshot {'ON' if V42_RMONEY_PRE_SNAPSHOT else 'OFF'} (v-E42)")
    log(f"  vE6.5                 : min-stop what-if {list(WHATIF_MS_PTS)} pts, LOW STOP flag < {WHATIF_LOW_STOP_PTS:g} pts (v-E40) | "
        f"upload zip {'ON' if V40_DAILY_ZIP else 'OFF'}; summary CSV {'ON' if V40_WRITE_SUMMARY_CSV else 'OFF'}, "
        f"post_exit_paths {'ON' if V40_WRITE_POST_EXIT_PATHS else 'OFF'}, zlm_shadow CSV {'ON' if ZLM_WRITE_CSV else 'OFF'} (v-E41)")
    log(f"  vE6.4                 : common first DPCR anchor {'ON' if V39_COMMON_ANCHOR else 'OFF'} "
        f"(closed 09:15 3m candle close, wait until {V39_ANCHOR_WAIT_UNTIL_HHMM}; v-E39)")
    log(f"  vE6.3                 : exit what-if {'ON' if WHATIF_ENABLED else 'OFF'} -> {WHATIF_FILE} "
        f"(early bank {WHATIF_EB_LOTS} lot @{WHATIF_EB_R}R, time stop {WHATIF_TS_MIN:g}m/+{WHATIF_TS_R}R; log-only, v-E36) | "
        f"brokerage Rs{CHG_BROKERAGE_PER_ORDER}/order (v-E37)")
    log(f"  vE6.2.4 (log-only)    : setup tags {'ON' if TAG_SETUP_ENABLED else 'OFF'} -> {SETUP_TAGS_FILE} (v-E35) | "
        f"ZLM same-minute lock check (v-E33)" + (f" | pre-open gate {BOTG_PREOPEN_UNTIL_HHMMSS} (v-E34)" if "BOTG_PREOPEN_UNTIL_HHMMSS" in globals() else ""))
    log(f"  vE6.2.3 (log-only)    : ZLM shadow {'ON' if ZLM_SHADOW_ENABLED else 'OFF'} -- no orders "
        f"(v-E31) | day open = 09:15 3m candle open (v-E32)")
    log(f"  vE6.2.2 (hotfix)      : holiday-aware spot history (v-E28/v-E29) | gap check re-try until "
        f"{BOTG_GAP_RECHECK_UNTIL_HHMM} (v-E30)")
    log(f"  vE6.2.1 (hotfix)      : stop exits signal = stop level (v-E23) | paper stop fill = trigger LTP "
        f"both brokers (v-E24) | DPCR first anchor on a 3-min boundary (v-E27)"
        f" | data from {G4_STARTUP_DATA_HHMM} (G4.4)")
    log(f"  vE6 RULES             : CE call-add skip={'ON' if BOTG_CE_CALLADD_SKIP_ENABLED else 'OFF'} "
        f"(BOT_G only, {BOTG_CE_CALLADD_SKIP_MIN}m carried flow dCE > {BOTG_CE_CALLADD_SKIP_THRESHOLD:,}; NA -> allow) | "
        f"stop band={'ON' if BOTG_STOP_BAND_ENABLED else 'OFF'} {100*BOTG_STOP_MIN_PCT:.0f}-{100*BOTG_STOP_MAX_PCT:.0f}% "
        f"of entry, hard max {BOTG_STOP_HARD_MAX_PTS} pts (G+GE) | CE profit lock="
        f"{'ON' if BOTG_CE_PROFIT_LOCK_ENABLED else 'OFF'} | TSL buffer {BOTG_TSL_BUFFER_PTS} pts")
    log(f"  DPCR RE-ANCHOR (vE5)  : mode={_oc_filter.REANCHOR_MODE} (half-window fraction {_oc_filter.REANCHOR_HALF_WINDOW_FRACTION}) | carry-forward={'ON' if BOTG_DPCR_CARRY_ENABLED else 'OFF'} | dashboard=signed DPCR, broker {DASH_BROKER}")
    log(f"  EARLY SLOT (vE4)      : {'BOT_GE ON' if BOTGE_ENABLED else 'OFF'} {BOTGE_TRADE_START_HHMM}-{BOTGE_ENTRY_END_HHMM} (not gap days) | "
        f"dir: DPCR sign + flow tier in {BOTGE_ALLOWED_TIERS} | BE {BOTGE_BE_R_MULT}R | "
        f"P1 max({BOTGE_P1_R_MULT}R,{BOTGE_P1_PCT_FLOOR*100:.0f}%) | P2 max({BOTGE_P2_R_MULT}R,{BOTGE_P2_PCT_FLOOR*100:.0f}%) | "
        f"TSL arm {BOTGE_TSL_ARM_R_MULT}R buf max({BOTGE_TSL_BUFFER_MIN_PTS},min({BOTGE_TSL_BUFFER_MAX_PTS},{BOTGE_TSL_BUFFER_R}R)) | "
        f"cap {BOTGE_MAX_HOLD_MINUTES_INITIAL}min | BOT_G waits while open: {BOTG_WAIT_FOR_EARLY_TRADE}")
    log(f"  PATH LOG (v-G84)      : {PATH_FILE if BOTG_PATH_LOG_ENABLED else 'OFF'}  |  "
        f"heartbeat {BOTG_PATH_HEARTBEAT_SEC}s  |  flush every {BOTG_PATH_FLUSH_ROWS} rows + every exit")
    log(f"  v2 FLAGS              : SL_CLAMP_CONTINUOUS={BOTG_SL_VWAP_CLAMP_CONTINUOUS} (v-G71)  |  "
        f"FALLING_BLOCK_SIDE_AWARE={BOTG_DPCR_FALLING_BLOCK_SIDE_AWARE} (v-G72)  |  "
        f"STREAK_LOSSES_ONLY={BOTG_STREAK_COUNT_LOSSES_ONLY} (v-G73)  |  "
        f"FLOW {BOTG_FLOW_WINDOW_MIN}m eps={BOTG_FLOW_FLAT_EPS} (v-G75, log-only)")
    log(f"  v3 DIAG (log-only)    : OI_DIAG={BOTG_OI_DIAG_ENABLED}  |  DPCR module: {_oc_filter.__name__}  |  "
        f"ATM delta~{BOTG_ATM_DELTA_APPROX}  |  ATM OI eps={BOTG_ATM_OI_FLAT_EPS}  |  resid eps={BOTG_ATM_RESID_FLAT_PTS}pts (v-G81)")
    log(f"  BROKER RECONCILE      : {'enabled on startup' if not PAPER_TRADE else 'skipped (PAPER mode)'}")
    log(f"  STALE DATA THRESHOLD  : {STALE_SEC}s -- blocks entries + manage")
    log(f"  LOG ROTATION          : 5MB x 30 files")
    _streak_scope = "per-bot" if LOSING_STREAK_PER_BOT else "global (shared across all bots)"
    _streak_unlock = (f"{LOSING_STREAK_COOLDOWN_SEC}s cooldown"
                      if LOSING_STREAK_COOLDOWN_SEC > 0 else "permanent for the day")
    log(f"  LOSING STREAK HALT    : {LOSING_STREAK_LIMIT} consecutive SL hits, "
        f"{_streak_scope}, re-arm: {_streak_unlock}")
    log("=" * 70)
    _verify_expiry_at_startup()

    tg(f"BOT STARTED — Nifty Weekly (BOT_G)\n"
       f"Mode: {'PAPER' if PAPER_TRADE else 'LIVE'}\n"
       f"QTY_BOT_G: {QTY_BOT_G} | QTY_BOT_G: {QTY_BOT_G}\n"
       f"Expiry: {getNiftyWeeklyExpiry()[0]} ({getNiftyWeeklyExpiry()[1].isoformat()})\n"
       f"DailyLoss limit: Rs{MAX_DAILY_LOSS}")

    load_state()

    # v2.9-E1: Broker reconciliation
    if not PAPER_TRADE:
        if LIVE_REQUIRE_BROKER_RECONCILE:
            _broker_reconcile()
        else:
            raise RuntimeError("LIVE_REQUIRE_BROKER_RECONCILE=False is not permitted for real-money BOT_G")
    else:
        log("RECONCILE     | PAPER mode — broker reconciliation skipped.")

    # v2.9-M5: Startup position reconciliation log
    open_bots = [b["name"] for b in BOTS if b.get("trade_open")]
    if open_bots:
        log("=" * 70)
        log(f"RECONCILE     | Restored open positions: {open_bots}")
        log(f"RECONCILE     | PLEASE VERIFY these match your broker app before")
        log(f"RECONCILE     | the first trade fires. If mismatch, stop bot immediately.")
        tg(f"POSITION RESTORED\nOpen bots: {open_bots}\n"
           f"VERIFY against broker app before first trade.")
        log("=" * 70)
    else:
        log("RECONCILE     | No open positions restored — clean start.")

    last_dashboard = 0

    # v-G23 (18-Aug-2026): write_summary()/save_state() previously only ran
    # on two narrow paths -- natural "all bots past force-exit" completion,
    # or a dashboard-triggered kill switch. Any OTHER way of stopping this
    # process (IDE stop button, Ctrl+C, terminal closed, unexpected crash)
    # bypassed both entirely -- almost certainly why no summary was showing
    # up day to day, since that's how these bots actually get stopped in
    # practice, not by waiting for 15:10 force-exit every single day.
    # try/finally now guarantees both run exactly once on ANY exit path.
    try:
        while True:

            # ── Circuit breaker ───────────────────────────────────────────────────
            if BOTG_DAILY_LOSS_CAP_ENABLED and not CIRCUIT_BREAKER_LOCKED and TOTAL_REALIZED_PNL <= MAX_DAILY_LOSS:
                CIRCUIT_BREAKER_LOCKED = True
                log(f"CIRCUIT BREAKER ENGAGED | "
                    f"PnL Rs{round(TOTAL_REALIZED_PNL,2)} <= limit Rs{MAX_DAILY_LOSS}. "
                    f"All new entries locked for the day.")
                tg(f"CIRCUIT BREAKER ENGAGED\n"
                   f"Daily PnL: Rs{round(TOTAL_REALIZED_PNL, 0)}\n"
                   f"Limit: Rs{MAX_DAILY_LOSS}\nNo new entries today.")
                save_state()

            # ── Data fetch ────────────────────────────────────────────────────────
            # G4.4: no stale-history hammering before 09:16. Logical candle
            # alignment remains 09:15; live readiness begins at 09:16.
            if hhmm() < G4_STARTUP_DATA_HHMM:
                time.sleep(1)
                continue
            # v3.14-STALE1: force a fresh fetch during the same 10s window
            # is_new_3m_candle() uses, so signal checks never run on a df3
            # snapshot taken before the candle they're supposed to act on had
            # even closed. See fetch_data()'s docstring for the full mechanism.
            _at_candle_boundary = (datetime.now().minute % 3 == 0
                                    and datetime.now().second <= 10)
            data = fetch_data(force_refresh=_at_candle_boundary)
            df3, spot = data["df3"], data["spot"]

            if any(v is None for v in [spot, df3]):
                log("[WAITING] Data pool not ready yet.")
                time.sleep(3)
                continue

            stale = data_is_stale()
            if stale:
                log(f"[DATA STALE] Last update {round(time.time()-CACHE['time'],0)}s ago. "
                    f"Skipping manage() AND new entries for all bots. (v2.9-D5)")
            try:   # vE6.2: day type (v-E20) + data-lost handling (v-E21)
                if not stale:
                    _day_track(spot, df3)   # v-E32: df3 for the 09:15 candle open
                _data_lost_check(stale)
            except Exception as _e62_err:
                log(f"vE6.2 | day/data-lost check error (ignored): {_e62_err}")
            try:   # v-E31 (vE6.2.3): ZLM shadow -- LOG-ONLY, no orders
                if not stale:
                    _zlm_tick(spot, df3)
            except Exception as _zlm_err:
                log(f"ZLM | shadow error (ignored, log-only): {_zlm_err}")

            active_list = BOTS if PAPER_TRADE else [b for b in BOTS if b["name"] in ACTIVE_BOTS]

            # ── Per-bot force-exit ─────────────────────────────────────────────────
            for bot in active_list:
                if force_exit(bot) and bot["trade_open"]:
                    log(f"FORCE EXIT   | {bot['name']} hit force_exit time {bot['force_exit']}")
                    cancel_broker_sl_order(bot)
                    open_ltp_map = get_multi_ltp([bot["entry_symbol"]]) if bot["entry_symbol"] else {}
                    ltp          = open_ltp_map.get(bot["entry_symbol"], bot["entry"])
                    pnl          = round((ltp - bot["entry"]) * bot["qty"], 0)
                    tg(f"FORCE EXIT {bot['name']} TIME\n"
                       f"Entry: {bot['entry']}  Exit: {round(ltp,1)}\nPnL: Rs{pnl}")
                    if log_trade(bot, bot["side"], bot["entry"], ltp, "FORCE_TIME_EXIT", bot["qty"]):
                        _close_bot(bot, cooldown=0)

            # ── Shutdown when all bots past force-exit ────────────────────────────
            all_done = all(force_exit(b) for b in active_list)
            if all_done:
                SYSTEM_EXIT = True
                log("ALL BOTS past force-exit time. Shutting down.")
                break

            # ── Batch LTP for open positions ──────────────────────────────────────
            # v3.13-API3: spot symbol folded into this same batched call when a
            # position is open, instead of fetch_data() fetching it separately —
            # cuts 2 API calls/tick down to 1 while a trade is running. Flat (no
            # open position) path is untouched — fetch_data() still fetches spot
            # alone on its normal CACHE_SEC cadence.
            open_symbols = [b["entry_symbol"] for b in active_list
                            if b["trade_open"] and b.get("entry_symbol")]
            if open_symbols:
                _fresh_ltp = get_multi_ltp(["NIFTY_SPOT"] + open_symbols)
                if _fresh_ltp is not None:
                    if "NIFTY_SPOT" in _fresh_ltp:
                        CACHE["spot"] = _fresh_ltp.pop("NIFTY_SPOT")
                        CACHE["time"] = time.time()
                    ltp_map = _fresh_ltp
                else:
                    ltp_map = {}
            else:
                ltp_map = {}

            # ── FIX-6: Profit lock check (runs every cycle) ───────────────────────
            check_profit_lock(active_list, ltp_map)

            # ── Dashboard heartbeat ─────────────────────────────────────────────────
            # v-G14: BOT_G and BOT_G each post their OWN P/L (realized + that
            # bot's own open-position unrealized) under their OWN dashboard ID,
            # instead of one combined "NIFTY_RMONEY_G" number -- the merged
            # version made it impossible to see which bot was actually winning,
            # defeating the reason for running them side by side. Both bots
            # still share this ONE process, so a "halt" from EITHER cell stops
            # BOTH bots (there's no per-bot pause, only a per-process one) --
            # logged clearly below so that's never ambiguous after the fact.
            _dash_halt_from = None
            for _b in active_list:
                if _b["name"] not in ("BOT_G", "BOT_GE"):   # v-E13: GE reports too
                    continue
                _unreal = 0.0
                if _b["trade_open"] and _b.get("entry_symbol"):
                    _ltp = ltp_map.get(_b["entry_symbol"], _b["entry"])
                    _unreal = (_ltp - _b["entry"]) * _b["qty"]
                _bot_pnl = _b.get("cum_realized_pnl", 0.0) + _unreal
                _cmd = send_dashboard_heartbeat(_bot_pnl, bot_id=f"NIFTY_RMONEY_{_b['name'].replace('BOT_', '')}")   # v-E13
                if _cmd == "halt":
                    _dash_halt_from = _b["name"]

            if _dash_halt_from:
                log(f"DASHBOARD KILL | Halt command received via {_dash_halt_from}'s cell -- "
                    f"shutting down the WHOLE process (BOT_G and BOT_G share one process, "
                    f"there is no per-bot pause).")
                tg(f"DASHBOARD KILL SWITCH\nBot halted via {_dash_halt_from}'s dashboard cell "
                   f"(stops BOTH BOT_G and BOT_G -- shared process).")
                break

            # v2.9-S7: VIX fetch at 09:20 and 12:30
            global _VIX_VALUE, _VIX_FETCH_HHMM
            _cur_hhmm = hhmm()
            for _vix_time in _VIX_FETCH_TIMES:
                if _cur_hhmm >= _vix_time and _VIX_FETCH_HHMM < _vix_time:
                    _fetched_vix = fetch_india_vix()
                    if _fetched_vix is not None:
                        _VIX_VALUE = _fetched_vix
                        _vix_regime_info = get_vix_regime()
                        log(f"VIX UPDATE   | India VIX={_fetched_vix:.2f} "
                            f"Regime: {_vix_regime_info['label']}")
                        tg(f"VIX Update\nIndia VIX: {_fetched_vix:.2f}\n"
                           f"Regime: {_vix_regime_info['label']}")
                    else:
                        log(f"VIX UPDATE   | Fetch failed at {_vix_time} — keeping last value")
                    _VIX_FETCH_HHMM = _vix_time

            # ── Per-bot loop ───────────────────────────────────────────────────────
            active_list = BOTS if PAPER_TRADE else [b for b in BOTS if b["name"] in ACTIVE_BOTS]
            for bot in active_list:
                now = time.time()

                # v-G9/v-G12: BOT_G and BOT_G don't go through signal()/
                # manage()/get_option_symbol() -- their entry/exit mechanics
                # don't fit the generic BOT_A-F shape (points-based SL,
                # rejection-candle arm, DPCR daily lock). Both routed to the
                # SAME self-contained handler (BOT_G shares every BOT_G
                # function -- only its vix_profile differs), which reuses
                # execute_entry()/log_trade()/register_entry()/_close_bot()
                # internally so state persistence, the trade CSV, and the
                # dashboard stay consistent with every other bot.
                if bot["name"] in ("BOT_G", "BOT_GE"):   # v-E6
                    bot_g_tick(bot, df3, spot, ltp_map, stale, now)
                    continue

            try:   # v-E19: post-exit / CE-skip trackers (log-only)
                if not stale:
                    _trackers_tick()
            except Exception as _tr_err:
                log(f"vE6.2 TRACK | tick error (ignored): {_tr_err}")

            # ── Dashboard every 60 s ──────────────────────────────────────────────
            if time.time() - last_dashboard >= 60:
                print_dashboard()
                last_dashboard = time.time()

            # v2.8-L7: heartbeat file for external watchdog
            global _last_heartbeat
            if time.time() - _last_heartbeat >= 60:
                try:
                    with open(HEARTBEAT_FILE, "w") as _hb:
                        _hb.write(str(time.time()))
                except Exception:
                    pass
                _last_heartbeat = time.time()

            time.sleep(1)

    except KeyboardInterrupt:
        log("SHUTDOWN | KeyboardInterrupt (Ctrl+C or IDE stop) -- writing "
            "today's summary and state before exiting (v-G23).")
    except Exception as e:
        log(f"SHUTDOWN | Unexpected crash: {e} -- writing today's summary "
            f"and state before exiting (v-G23).")
        import traceback
        log(traceback.format_exc())
    finally:
        # v-G23: this is now the ONLY place these two get called -- runs on
        # every exit path (natural completion, dashboard kill, Ctrl+C/IDE
        # stop, or an unexpected crash), never just the two narrow "clean"
        # paths this used to be limited to.
        try:   # vE6.2: unfinished trackers + LIVE vs PAPER block
            _track_flush_all()
            _write_livecmp()
        except Exception as _e62_err:
            log(f"vE6.2 | shutdown extras error (ignored): {_e62_err}")
        write_summary()
        save_state()
        _v47_write_tape()   # v-E47 (vE6.9), before the zip
        _v54_zip = _v41_daily_zip()   # v-E41 (vE6.5)
        log("BOT SHUTDOWN COMPLETE.")
        _v54_eod_cleanup(_v54_zip)   # v-E54 (vE6.14): last step, normal 15:10 shutdown only


# =============================================================================
if __name__ == "__main__":
    main()