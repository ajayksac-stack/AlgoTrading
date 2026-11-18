# =============================================================================
#  SENSEX WEEKLY OPTIONS BOT -- BOT_G + BOT_GE, MULTI-STRIKE POOL (DPCR + Option-VWAP)
#  Broker  : Fyers      Mode: PAPER (Sensex stays PAPER)
#  File    : BOT_fyers_sensex_g_pool_v8_9.py
#  Updated : 2026-11-06
#
#  v8.1 (19-Oct-2026) -- v8 + four changes decided by Anu after the first v8 session (19-Oct):
#    1. PRE-OPEN GATE: no quote / history calls before 09:14:30 (BOTG_PREOPEN_*). The 08:17 start of 19-Oct
#       wrote 2,241 error lines and made ~2,200 failed API calls (about 44% of Fyers' 5,000/day limit).
#    2. OPTION SYMBOL log line only on change / every 300 s (was 49% of the log). BOTG_OPTSYM_LOG_EVERY_CALL.
#    3. VWAP RESEARCH (log-only): vwap_research_*.csv (every pool strike, both sides, every closed 5m bar,
#       incl. while the lock is NOT_LOCKED / PAUSED, with session / rolling-12 / since-pool-entry VWAP and both
#       DPCR values) and pool_bars_*.csv (end-of-day 5m bars). Purpose: test other VWAP definitions offline
#       (19-Oct: after a 700-pt fall the option sat +65..+155 pts above its own full-day VWAP, 0 entries).
#    4. PAPER STOP FILL AT THE STOP LEVEL on Fyers (was already so on RMoney): both brokers now book the same
#       exit for SL / BREAKEVEN / TSL exits. Gap-through exits are booked at the stop (optimistic), as on RMoney.
#  v8.1.1 (20-Oct-2026) -- LOG-ONLY research data added (Anu: Sensex may move to 10-min candles / a DPCR-slope
#  rule later): pool_bars flushed during the day (not only at 15:05), pool_bars_10m_*.csv, spot_bars_*.csv
#  (index 5m + 10m), and DPCR-slope / OI-flow columns in vwap_research_*.csv. No trading logic touched.
#  v8.2 (24-Oct-2026) -- three changes ported from the Nifty vE6.2.3 handoff (Anu: "ok", 24-Oct); entry/exit rules untouched:
#    1. DAY OPEN FROM THE 09:15 3-MIN CANDLE (v-E32): _day_track(spot, df3). Before, the day open was the first spot
#       reading (broker-dependent: Nifty 22-Oct 22,657.75 vs 22,590.3) -> day_open / pct_from_open / day_type differed.
#    2. FYERS SPOT-HISTORY LOOKBACK follows the calendar (v-E29): max(BOTG_HISTORY_LOOKBACK_DAYS, days back to the
#       previous BSE trading day + 1). Only changes Mon 28-Dec-2026 (after the 25-Dec holiday): 5 days instead of 4.
#    3. ZLM SHADOW (v-E31, LOG-ONLY, no orders): zlm_shadow_sensex_v8_9.py -> zlm_shadow_*.csv. ZLM_* settings are the
#       Nifty ones scaled ~3.3x (margin 33, band 0->65 pts) and are UNTESTED on Sensex.
#    Not ported (decided with Anu): v-E27 first-anchor split (both brokers anchored 09:18 on the same strike 21-23-Oct),
#    v-E24 paper stop fill (Sensex keeps the stop-level fill), v-E23 (exit signal is already the stop level on Sensex paper).
#  v8.3 (26-Oct-2026) -- LOG-ONLY setup tags (Anu: "yes ... go by your suggestion", 26-Oct). NO entry / exit / sizing change.
#    Every ARM, ARM DROPPED, ARM EXPIRED, MIN_RISK skip and ENTRY writes one row to setup_tags_*.csv with the data needed to
#    decide, from live Sensex days, (a) how wide the stop is (cap 5/6/7/8 %, risk-based lots at Rs 3k/4k/5k, >8 % flag) and
#    (b) a late-entry rule (would-skip flags for start 11:30 / 12:00 / 13:00 and for |gap| or |ext_1015| >= 0.5 % / 0.75 %).
#    Join to the trades CSV on trade_id. ext_1015 = % move from the day open to the first spot reading at/after 10:15.
#    Hooks are one try/except-wrapped call each (_v83_tag) -- an error is logged (max 5/run) and ignored.
#  v8.3.1 (27-Oct-2026) -- DATA FIX, no strategy change (Anu: "yes", 27-Oct). Entry / exit / sizing rules untouched.
#    27-Oct Fyers took the 09:15 3-min candle open at 09:15:04, while the candle was 4 s old: 73,395.24 vs the true 73,484.38
#    (RMoney, reading a minute later, and both brokers' 5m bars: 73,484.38). Gap showed -0.29 % instead of -0.17 %, ext_1015
#    +0.289 % instead of +0.171 %; 26-Oct was 11 pts off. The gap-day check runs once at 09:15 and a gap near the 1.0 % limit
#    could have been misclassified (gap day = first trade 12:30, early slot off).
#    1. _day_track: the 09:15 candle replaces the first spot reading only after it has CLOSED (df3 holds a candle stamped 09:18 or later).
#    2. _v831_gap_recheck: once per day per bot, from 09:18, the gap check is re-run on the closed candle; gap_day / gap_pct are
#       corrected (log "v8.3.1 GAP RECHECK") if the 09:15 value differed. Also corrects a gap_day restored from state after a restart.
#  v8.3.2 (28-Oct-2026) -- Anu: "ok pl go ahead" (28-Oct). Entry / exit / sizing RULES unchanged; four measurement / realism fixes:
#    1. Brokerage per order set to the real plan: Fyers Rs15, RMoney Rs1 (was a Rs20 placeholder in both).
#    2. FYERS paper entry at the ASK (Nifty vE6.3 does the same) with a stale-quote guard: if the ask is more than
#       V832_ASK_GUARD_PCT (1.5 %) of the signal premium above it, the entry is ABORTED (ENTRY ABORT reason=STALE_QUOTE, tag row
#       ENTRY_ABORT_STALE_QUOTE) and the setup dropped. 28-Oct 13:27: signal 703.75 vs ask 725.25 -> the LTP lagged the book; the
#       "+Rs3,362" winner was not real. The 16 earlier Fyers fills had ask-signal between -2.6 and +3.7 pts (<= 0.5 %).
#       RMoney has no ask feed (unchanged).
#    3. PAPER stop fill after a data gap: if the previous good LTP tick of the open trade was more than V832_GAP_FILL_SEC (30 s) ago
#       and the first LTP after the gap is BELOW the stop, the paper exit fills at that LTP instead of the stop level
#       (log "PAPER GAP FILL"). 28-Oct RMoney 10:50: stop 712.65, first LTP after a 5-min outage 689.7 -> -Rs3,684 instead of -Rs1,848.
#       Ordinary stop-outs (no gap) are unchanged.
#    4. Exit what-if (log-only, WHATIF_ENABLED): every trade is replayed through BASE (replica of the live ladder), EB (1 lot banked at
#       +0.6R), TS (exit if +0.3R not touched in 5 min) and EBTS -> "WHATIF |" log line + exit_whatif_*.csv. Module exit_whatif_sensex_v8_9.py.
#  v8.3.3 (29-Oct-2026) -- Anu: "ok" (29-Oct 19:49). Entry / exit / sizing RULES unchanged. Three log-only additions + one alignment fix:
#    1. CONTEXT TAGS (log-only): every setup_tags row (ENTRY and every skipped / aborted / armed setup) now carries
#       spot_chg15 / spot_chg30 (spot change over the last 15 / 30 min, measured at the last closed 5-min bar), pullback_from_high +
#       mins_since_high, bounce_from_low + mins_since_low, dpcr_carried (decision value) vs dpcr_fresh (current-window value) with
#       fresh_vs_lock (WITH / AGAINST / FLAT / NA), early_flow_tier + early_flow_pass (would the early-slot rule -- 9-min flow tier MOST/HALF
#       AND carried-DPCR sign agrees with the side -- have allowed this trade?). The ENTRY also writes one "ENTRY CTX |" log line.
#    2. FALLING-KNIFE FLAG R1 (LOG-ONLY, fk_r1 column): 1 when the spot, signed for the trade side (CE: down, PE: up), moved against
#       the trade over BOTH the last 15 and the last 30 min (5-min closed bars). The trade is still taken; collect ~10 sessions first.
#    3. SKIP TRACKER: a MIN_RISK skip and (Fyers) a STALE_QUOTE abort now start a SKIP tracker like the CE call-add skip does, so each
#       gets a would-have outcome (SL_FIRST / P1_FIRST / NEITHER) in track_summary_*.csv (ref_id ...-SKIP-MINRISK-... / -STALEQ-...).
#    4. COMMON FIRST DPCR ANCHOR (normal days; V833_COMMON_ANCHOR): both brokers take the first anchor from the CLOSED 09:15 3-min candle
#       at 09:18 -- anchor = nearest 100 of that candle's close -- and use the same close as the "spot at anchor" for the re-anchor
#       drift. Before, Fyers anchored on the live spot at ~09:18 and RMoney on the live spot at 09:16 (100-pt different anchors on
#       19-, 27- and 29-Oct). Later re-anchors, the 150-pt trigger, the early-slot minimum |DPCR| and gap days (10:00 anchor) are unchanged.
#       The DPCR fetch simply waits (no bucket consumed) until the 09:15 candle has closed; if it has not by 09:20 the live spot is used.
#  v8.4 (30-Oct-2026) -- Anu: "ok v8.4" (30-Oct 20:38). Two changes, nothing else:
#    1. FALLING-KNIFE R1 ENFORCED (main slot only; V84_FK_ENFORCE, V84_FK_BOTS = BOT_G). Just before the order, if the spot -- signed for the
#       trade side (CE: down, PE: up) -- moved against the trade over BOTH the last 15 and the last 30 min (the v8.3.3 fk_r1 definition, 5-min
#       closed bars, V833_FK_MIN_PTS), the setup is dropped (log "ENTRY SKIP ... reason=FALLING_KNIFE_R1", tag ENTRY_SKIP_FK_R1, would-have
#       tracker ...-SKIP-FKR1-...). The pool is reset like the other skips. Early slot (BOT_GE) is NOT touched. If the 15/30-min spot change
#       is unavailable (restart, no history) the trade is allowed. Needs V833_MOM_TAGS = True. 30-Oct: both afternoon entries had fk_r1 = 1.
#    2. ZLM-DIRECTION VIEW (LOG-ONLY, V84_ZDIR_TAGS): replaces the "DPCR level beyond the no-trade zone" test by "spot beyond the ZLM reference
#       +/- (band + margin) on the trade side AND carried DPCR on the same side of zero by at least V84_ZDIR_FLOOR (0.05) AND the 3-candle DPCR
#       change not worse than -V84_ZDIR_FALL_TOL (0.02) against the side". It never gates anything. Written to: vwap_research_*.csv (4 new
#       columns at the end: zdir_dev, zdir_thr, zdir_side, zdir_allow -- zdir_allow is for the row's own side), the "v8.4 ZDIR |" log line
#       on every DPCR candle (flags ZDIR_ONLY when it would allow a side the zone gate blocks, ZONE_ONLY the opposite), and the ENTRY CTX line.
#       Needs the ZLM shadow (ZLM_SHADOW_ENABLED) for its reference level. Collect ~10 sessions, then decide on a live trend lock.
#  v8.5 (2-Nov-2026) -- Anu: "1 yes" (gap 0.75 %), zip request (2-Nov 17:12). Two changes, nothing else:
#    1. DAILY UPLOAD ZIP (V85_DAILY_ZIP, V85_ZIP_NAME): at shutdown (after "BOT SHUTDOWN COMPLETE") the bot writes
#       upload_sensex_<YYYYMMDD>_<broker>.zip with: bot_log (+ rotations .txt.N), trades, summary, livecmp, trade_paths, post_exit_paths,
#       post_exit_summary, vwap_research, pool_bars, pool_bars_10m, spot_bars, setup_tags, exit_whatif, zlm_shadow, dpcr_log, dpcr_window_shift,
#       heartbeat. NEVER the token / client-id files or the bot_state json. The originals stay untouched. Files accumulate over the weekly
#       series (same names), so the newest day is at the end. A hard kill (no shutdown) writes no zip -> upload the files the old way.
#    2. GAP-DAY THRESHOLD 1.0 % -> 0.75 % (BOTG_GAP_THRESHOLD_PCT, either direction, measured on the closed 09:15 candle as in v8.3.1). A gap day
#       = early slot (BOT_GE) off, DPCR watch / first anchor at 10:00, first BOT_G trade 12:30. 2-Nov (+0.97 %) was a normal day and all
#       five paper trades (11:15-12:26) lost; at 0.75 % the day would have had no trade before 12:30. First time this path runs live on Sensex.
#  v8.6 (3-Nov-2026) -- Anu: "5 min interval log is ok" + "yes" (ZLM reference). Two LOG-ONLY changes, no trading rule touched:
#    1. GAP-DAY IDLE LOG (V86_GAP_IDLE_LOG, V86_GAP_IDLE_LOG_MIN): on a gap day BOT_G logs one line every 5 min from 09:18 (closed-candle gap
#       confirmed) until the 10:00 DPCR watch: "GAP DAY | idle ... early slot off, DPCR watch 10:00, first trade 12:30". 03-Nov (+0.79 %) the log was
#       silent 09:20-10:00 and looked like a dead feed (bots restarted at 09:34 for nothing).
#    2. ZLM REFERENCE FROM THE CLOSED 09:15 CANDLE (V86_ZLM_REF_CANDLE): ref = close of today's closed 09:15 3m candle (same bar for both brokers, and
#       the same value the v8.3.3 common anchor uses) instead of the average of the spot polls 09:15-09:20 (poll-count dependent: Fyers vs RMoney
#       differed 12.4 pts on 03-Nov and 18.7 pts on 02-Nov, and a restart switched it to an OHLC/4 fallback). The old average is logged beside it
#       for comparison. Wait up to V86_ZLM_REF_WAIT_UNTIL_HHMM (09:30) for the closed candle, then the old method. ZLM shadow and the v8.4 ZDIR view
#       (both log-only) use it automatically. Nifty v-E44 equivalent.
#  v8.7 (4-Nov-2026) -- Anu: "ok pl go ahead". Nifty vE6.9 log-only items ported with Sensex values. NO trading rule touched:
#    1. SHADOW LOCK (V46_SHADOW_LOCK, V46_ZONE 0.10, V46_SYNC_PTS 35; Nifty v-E46): every 3m candle from trade start a second, hypothetical lock is
#       kept beside the real one: CE if carried DPCR >= +0.10, PE if <= -0.10, but a lock / flip is accepted only when the spot 30-min change agrees
#       by >= 35 pts; inside the zone it keeps its side. One line per candle: "SHADOW LOCK | DPCR .. spot30 .. | real .. | Z0.1+sync .. | SAME/DIFFERS".
#    2. ENTRY CTX TAIL: "against15/against30" (spot move against the trade, + = against), "gate15+30@65 ALLOW/SKIP" (would a 65-pt both-windows gate skip
#       it; the R1 gate at 0 pts is already enforced) and "shadow lock CE/PE/-". Recorded so the right threshold can be chosen from data.
#    3. OPTION TAPE (V47_OPTION_TAPE; Nifty v-E47): every 3m candle the CE and PE strikes ATM +/- 4 steps (100 pts) are noted; at shutdown, before the
#       zip, their 1-minute OHLCV for today is fetched (max 80 symbols, 0.25 s apart, errors skipped) -> option_tape_<YYYYMMDD>_<broker>.csv, added to
#       the upload zip. Lets any entry / stop / exit rule be replayed on both brokers' contracts afterwards (till now only the traded strikes existed).
#  v8.9 (9-Nov-2026) -- Anu: rules frozen; collect evidence on the DPCR pause margin (review ~18-Nov). LOG-ONLY, no trading rule touched.
#    PAUSE CF TAG: whenever the locked side's entries are PAUSED because |DPCR| is inside the no-trade zone (0.28) but the side-signed DPCR is
#    already >= zone - 0.03 (0.25), one "BOT_G PAUSE CF" log line + one row in pause_cf_*.csv per setup (side + last closed 5m bar = the rejection
#    candle; repeated ticks / scans of the same setup are recorded once). Row: time, side, spot, DPCR, zone, release threshold, strikes (OTM pool),
#    spot moves against the trade (fk_r1, against15/30), "other gate" flags (entry cutoff 14:30 passed, falling-DPCR block, falling-knife R1) and the
#    exact pause reason. Candle validity (VWAP distance, rejection, VPC, confirmation) and the shadow exit are NOT computed in the bot: they are
#    replayed afterwards from the option tape with pause_cf_replay.py (setup validity kept separate from hypothetical P&L).
#    V89_PAUSE_CF False restores v8.8. The tag never arms, places or changes a live / paper trade.
#  v8.8 (6-Nov-2026) -- Anu: shadow lock stays LOG-ONLY, and a lock / flip also needs the DPCR to be rising a bit (spot AND DPCR rising).
#    SHADOW LOCK (v-E46) now accepts a lock / flip to CE only if the spot 30-min change is >= +35 pts AND the carried DPCR rose >= +0.02 over the last
#    3 candles (9 min); PE mirrored. Replay on 12 sessions: the 0.02 rise changes almost nothing (it just means "not falling"); >= 0.10 would have delayed
#    or killed good trend-day locks (6-Nov, 26-Oct, 28-Oct). Log line gains "dpcr3c +0.052" at the end; new note "X wanted, spot ok but DPCR 3c ... not rising".
#    No trading rule is touched (V88_SHADOW_DPCR_RISE False restores the v8.7 shadow behaviour).
#  New file names (*_v8_9*), so state / log / CSV files start fresh. Nothing else differs from v8.
#
#  v8 (18-Oct-2026) -- BUILT FROM THE NIFTY vE6.2 FILE (BOT_fyers_nifty_g_pool_vE6.py), not
#  from Sensex v7. Reason (Anu, 18-Oct): Sensex must be the same as Nifty except the
#  accepted proposals, so debugging has ONE starting point and every log / CSV column / log
#  line is identical. Everything not listed below is Nifty's code, byte for byte, apart from
#  mechanical renames (nifty->sensex, NSE->BSE, Tuesday->Thursday).
#
#  SENSEX DIFFERENCES (each is marked "v8 Sensex" at its place in the code):
#    1. Instrument: BSE:SENSEX-INDEX, option symbols BSE:SENSEX..., strike step 100, lot 20,
#       weekly expiry THURSDAY, BSE holiday list (BSE_TRADING_HOLIDAYS), month-end = last Thursday.
#       Rollover = Nifty vE6.2 rule (<= 1 trading day left -> next week), so Wed and Thu trade next week.
#    2. Lots: 4 on every day (QTY_BOT_G_LOW_VIX = QTY_BOT_G_HIGH_VIX = 4 lots; Nifty: 8 lots at VIX<=13).
#    3. Strike pool: fixed ATM + OTM1 in every VIX band (Nifty mechanism, flat pools in config).
#    4. Entry rejection band -20/+30 pts around option VWAP (Nifty +/-4); Sensex-scaled
#       confirmation bands, candle-quality limits, TSL buffers, flow flat-eps (config only).
#    5. Min-risk skip: a confirmed setup with a chart stop < 15 pts away is skipped (Sensex only).
#    6. Switches in config: stop band OFF (3-6% kept, no hard max), CE call-add skip OFF
#       (50,000 kept) -- the cflow / chart-stop columns are still logged, so both can be assessed.
#    7. DPCR window by weekday for a Thursday expiry; re-anchor distance floor 150 pts on Wed/Thu.
#    8. Sensex data hardening: spot quote -> 1M history -> 3M close fallback chain, 4-day
#       spot-history lookback for the gap check (Mondays), future-dated option bars dropped.
#    9. Dashboard endpoints /sensex_reading + /sensex_spot (key sensex_spot), heartbeat ids SENSEX_FYERS_*.
#   10. Charges: BSE transaction charge 0.0325% (config CHG_TXN_PCT).
#  NOT carried over from Sensex v7 (Nifty's equivalent is used, or the file does not exist in Nifty):
#   funnel_*.csv, path_*.csv, post_entry_*.csv (Nifty: trade_paths_*.csv + post-entry columns in the
#   trade CSV), the Sensex-style tracker/day-type/livecmp/charges code (Nifty's v-E19..v-E22 used).
#  Daily loss cap / per-bot profit cap / global profit lock are OFF exactly as in Nifty's config
#  (Sensex v7 had the Rs1000 per-bot cap and the daily loss breaker ON).
#
#  ----- Nifty vE6.2 header (history) follows -----
#  v3 (30-Sep-2026) -- LOGGING/DIAGNOSTIC BUILD ONLY. Renamed from the v2
#  files so v2 data stays clean. NOTHING in entry / exit / SL / BE / P1 /
#  P2 / TSL / VWAP / DPCR lock / veto logic changed (verified by diff).
#  v-G79  Names: BOT_fyers_nifty_g_pool_v3.py + config_fyers_nifty_g_pool_v3.py,
#         output files <kind>_nifty_g_pool_v3_<series>_fyers.*, and a
#         broker-specific DPCR module copy option_chain_filter_nifty_fyers_v3.py
#         (DPCR logs dpcr_log_nifty_fyers_v3.txt). Old module untouched.
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
#  BOT_fyers_nifty_g_pool_vE6.py / config_fyers_nifty_g_pool_vE6.py /
#  option_chain_filter_nifty_fyers_vE6.py; outputs *_nifty_g_pool_vE6_*.
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
#        moves to the previous trading day (config BSE_TRADING_HOLIDAYS).
#        Tue 20-Oct-2026 (Dussehra) -> Mon 19-Oct (symbol 26O19...). Fixes
#        "Invalid symbol provided" for every option on 12-Oct. Month-end
#        (monthly-format) detection uses the nominal Tuesday, so a holiday-
#        shifted last-Tuesday (e.g. 24-Nov-2026 -> 23-Nov) stays monthly.
#  vE5 (09-Oct-2026) -- DPCR RE-ANCHOR + DASHBOARD. Renamed to BOT_fyers_nifty_g_pool_vE5.py
#  / config_fyers_nifty_g_pool_vE5.py / option_chain_filter_nifty_fyers_vE5.py;
#  outputs *_nifty_g_pool_vE5_<series>_fyers.*. Agreed 09-Oct:
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
#  vE4 (05-Oct-2026) -- EARLY-ENTRY SLOT. Renamed to BOT_fyers_nifty_g_pool_vE4.py
#  / config_fyers_nifty_g_pool_vE4.py / option_chain_filter_nifty_fyers_vE4.py;
#  outputs *_nifty_g_pool_vE4_<series>_fyers.*. Spec agreed 05-Oct:
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
#
#  ONE bot, ONE process, ONE open trade at a time. All tunables live in
#  config_fyers_nifty_g_pool_v2.py.
#
#  v2 (28-Sep-2026) -- renamed from BOT_fyers_nifty_g_pool_v1.py /
#  config_fyers_nifty_g_pool_v1.py so the new build cannot mix with the
#  old one. Motivated by the 28-Sep paper session (Fyers vs RMoney):
#  v-G70  File naming: every file this bot writes is now
#         <kind>_nifty_g_pool_v2_<series>_fyers.<ext> (bot_log / trades /
#         summary / bot_state) + heartbeat_nifty_g_pool_v2_fyers.txt --
#         identical to the RMoney v2 bot except the broker suffix.
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
#  v-G77  LIVE-only crash fix: log_trade() now accepts
#         broker_exit_already_filled (already passed by both BROKER_SL_FILLED
#         call sites) and skips sending a duplicate SELL when True.
#  Entry logic unchanged except v-G72 (which strikes may ARM while the
#  early-warning pause is active); exits unchanged except v-G71 (initial
#  SL can be up to BOTG_SL_VWAP_BUFFER lower when the rejection low sits
#  within buffer below VWAP).
#
#  v-G13 (12-Aug-2026): split out from the original BOT_A-F multi-bot suite
#  into this standalone process.
#
#  v-G37 (05-Sep-2026): explicit instruction (04/05-Sep-2026 session) --
#  BOT_GG REMOVED ENTIRELY (was a second, always-parallel bot trading a
#  single shallower strike; now redundant with the change below). BOT_G no
#  longer trades one fixed strike -- each cycle it watches a small POOL of
#  3 strikes at once (VIX-selected: ATM/OTM1/OTM2, OTM1/OTM2/OTM3, or
#  OTM2/OTM3/OTM4), each running its own independent rejection-candle/VWAP-
#  confirmation state machine off its own premium series. The first one to
#  qualify takes the trade (deepest-OTM wins on a same-tick tie); the
#  others are left completely untouched -- no fetch, no LTP check, nothing
#  -- until that trade reaches a logical end, at which point the pool scan
#  resumes fresh. Also: entry time moved to 10:15 (was 10:30), and the
#  DPCR OI-window now scales by trading-days-to-the-nearest-weekly-expiry
#  (see option_chain_filter_nifty.py's compute_dpcr()). Renamed from
#  BOT_fyers_nifty_gg_4LOT.py / config_fyers_nifty_gg_4LOT.py.
#
#  KEY HISTORY (BOT_G/BOT_GG only):
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
#  v-G12       BOT_GG added -- shares 100% of BOT_G's logic (same functions,
#              two BOTS[] dicts), differs only in VIX-based strike depth.
#              Shared DPCR fetch deduplicated via
#              _is_new_shared_dpcr_candle() (one fetch per 3-min candle
#              regardless of how many bots share the reading).
#  v-G15       BOT_GG's own trade_start_override (11:00/13:00 vs BOT_G's
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
#              no re-entry cooldown of any kind for BOT_G/BOT_GG.
#  v-G54 (16-Sep-2026) NOTE: the line above is a historical record of
#              v-G28's own change, not current truth -- a SEPARATE,
#              dedicated BOT_G streak counter/cooldown (LOSING_STREAK_
#              LIMIT/_COOLDOWN_SEC) was added later and is genuinely
#              active; see the STREAK/LOSING STREAK log lines. But
#              independent review found something more serious: BOT_G's
#              "losing_streak_exempt" flag makes allow_trade() -- the
#              ONLY place that actually enforces this lock during entry
#              -- skip the check entirely for BOT_G. The counter still
#              increments and logs "HALTED"/cooldown timing correctly
#              (that update path doesn't check the exempt flag), but
#              confirmed via full trace: nothing currently stops BOT_G
#              from entering again before that cooldown expires, if some
#              OTHER gate (DPCR zone, etc.) doesn't independently block
#              it too. On 16-Sep, DPCR happened to stay in the no-trade
#              zone for the whole 30-minute window, which is very
#              possibly why this went unnoticed -- not proof the lock
#              itself was doing anything. Flagged for an explicit
#              decision -- v-G56 (this session) resolved it: exemption
#              removed (see "losing_streak_exempt": False in BOT_DEFAULTS
#              below), so this gate now genuinely enforces for BOT_G.
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
#              (getSensexWeeklyExpiry() replaces the old monthly path).
#
#  NIFTY LOT SIZE : 65 (effective January 2026, NSE circular Oct 2025)
#  STRIKE ROUND   : nearest 50
#  EXPIRY         : WEEKLY (Tuesday, unconditional next-week rollover)
#  DEPENDENCIES   : helper_fyers, fyers_apiv3, option_chain_filter_nifty, pandas
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
from datetime import date, datetime, timedelta
from logging.handlers import RotatingFileHandler
import logging

import pandas as pd

import helper_fyers as helper
from fyers_apiv3 import fyersModel

# v-G8 (10-Aug-2026): real DPCR feed for BOT_G -- module lives in the same
# folder, same convention as helper_fyers above. Only compute_dpcr() is used
# here; option_chain_filter_nifty.py's own __main__ smoke-test block does not
# run on import (guarded by if __name__ == "__main__").
import option_chain_filter_sensex_fyers_v8_9 as _oc_filter   # v8 Sensex (Nifty: option_chain_filter_nifty_fyers_vE6)

# v-G18-FIX1 (20-Aug-2026): config import was missing entirely -- every
# BOTG_/BOTGG_ constant (DPCR no-trade band, partial-booking R-multiples,
# trade-start windows, etc.) was relying on a wildcard import that never
# existed, causing NameError: BOTG_DPCR_NO_TRADE_LOW at module load.
from config_fyers_sensex_g_pool_v8_9 import *   # v8 Sensex (Nifty: config_fyers_nifty_g_pool_vE6)
import exit_whatif_sensex_v8_9 as _wi   # v8.3.2: exit what-if (log-only), shared by both brokers
import zlm_shadow_sensex_v8_9 as _zlm   # v8.2: ZLM shadow (log-only), shared by both brokers

# =============================================================================
#  SECTION 1 — BROKER LOGIN
# =============================================================================
# v-G18-FIX2 (20-Aug-2026): this build was also missing the Fyers client
# initialization entirely -- fetch_data(), _get_historical_sensex_safe(),
# compute_dpcr(), and every order-management call (positions/orderbook/
# quotes/place_order/modify_order/cancel_order) all reference the global
# `fyers` client, so without this block every historical fetch failed with:
# NameError: name 'fyers' is not defined. Pattern matches the working
# BankNifty/Sensex Fyers bots -- same token-file convention, unchanged.
APP_ID       = open("fyers_client_id.txt", encoding="utf-8").read().strip()
ACCESS_TOKEN = open("fyers_access_token.txt", encoding="utf-8").read().strip()

fyers = fyersModel.FyersModel(
    token=ACCESS_TOKEN,
    is_async=False,
    client_id=APP_ID,
)


# =============================================================================
#  SECTION 2 — WEEKLY EXPIRY
# =============================================================================



def _bse_trading_day_on_or_before(d):
    """v-E12 (vE5.1): step back from d over weekends and BSE_TRADING_HOLIDAYS
    (config). An expiry that falls on a holiday moves to the previous
    trading day, e.g. Tue 20-Oct-2026 (Dussehra) -> Mon 19-Oct-2026."""
    _hol = set(BSE_TRADING_HOLIDAYS)
    while d.weekday() >= 5 or d.isoformat() in _hol:
        d -= timedelta(days=1)
    return d


def _bse_trading_days_between(d, exp):
    """v-E18 (vE6.2): NSE trading days strictly after d, up to and including
    exp (weekends and BSE_TRADING_HOLIDAYS skipped). 0 when d == exp."""
    _hol = set(BSE_TRADING_HOLIDAYS)
    n, x = 0, d
    while x < exp:
        x += timedelta(days=1)
        if x.weekday() < 5 and x.isoformat() not in _hol:
            n += 1
    return n


def _nominal_expiry_thursday(d):
    """v-E12 (v8: Thursday): the Thursday of the expiry week that d belongs to (d itself
    if Thursday; for a holiday-shifted Wednesday/Tuesday expiry, the Thursday it
    replaced). v8 Sensex: weekly expiry is THURSDAY (Nifty: Tuesday)."""
    return d + timedelta(days=(3 - d.weekday()) % 7)


def is_sensex_expiry_day():
    """
    Returns True if today is THIS WEEK's Sensex weekly expiry (Thursday).

    BUG FOUND while converting to weekly (v-WEEKLY1): the old monthly-expiry
    version did `int(expiry_code[:2])` on a code like "26AUG" -- which parses
    the YEAR PREFIX "26" as if it were the expiry day-of-month. That's only
    accidentally correct for months where the expiry day happens to BE the
    26th. Fixed by comparing actual date objects, not substrings of a
    formatted code.
    """
    _d = date.today()   # v-E12: holiday-aware (Mon 19-Oct-2026 is an expiry day)
    return _d == _bse_trading_day_on_or_before(_nominal_expiry_thursday(_d))


def _verify_expiry_at_startup():
    """
    Startup sanity check for weekly expiry. Logs sample symbol for visual
    confirmation before first trade.
    """
    try:
        expiry_code, expiry_date = getSensexWeeklyExpiry()
    except Exception as e:
        raise ValueError(f"STARTUP ABORT | {e}")
    symbol_expiry_code = _bot_g_symbol_expiry_code(expiry_date)
    sample = f"BSE:SENSEX{symbol_expiry_code}80000CE"
    log(f"EXPIRY CHECK  | Weekly expiry code: {expiry_code} ({expiry_date.isoformat()})")
    log(f"EXPIRY CHECK  | Sample symbol: {sample}")
    if _is_month_end_weekly(expiry_date):
        log(f"EXPIRY CHECK  | NOTE: this week's expiry ({expiry_date.isoformat()}) is the "
            f"last Thursday of its month -- monthly-format symbol code "
            f"({symbol_expiry_code}) used for actual fetches/orders, not the "
            f"ordinary weekly code ({expiry_code}) shown above (v-G29)")
    # The traded contract is always the one with >1 day of runway left
    # (getSensexWeeklyExpiry() never returns a symbol expiring today or
    # tomorrow -- see _next_sensex_weekly_expiry_date(), v-G38), so being
    # within 1 day of the underlying index's own weekly expiry carries no
    # elevated gamma/pin risk for the contract actually held. Informational
    # log line only.
    _days_to_imminent_thu = (3 - date.today().weekday()) % 7   # v8: Thursday = weekday index 3
    if _days_to_imminent_thu <= BOTG_ROLLOVER_MAX_DAYS_LEFT:
        log("EXPIRY CHECK  | NOTE: today is within 1 day of THIS WEEK's expiry for the "
            "underlying index -- BOT_G is trading NEXT week's contract regardless "
            "(rollover is unconditional, not time-of-day gated, v-G38).")


_BOTG_WEEKLY_MONTH_CODE = {
    1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6",
    7: "7", 8: "8", 9: "9", 10: "O", 11: "N", 12: "D",
}   # Fyers weekly symbology: Jan-Sep = digit, Oct/Nov/Dec = O/N/D.
    # Collision-free by construction — no two months share a code, unlike
    # a naive first-letter scheme (which would clash on June/July, and on
    # January/June/July if 'J' were used for all three).


def _next_sensex_weekly_expiry_date(from_date=None):
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
    resolve to 1-Sep-2026, not 25-Aug-2026.
    """
    d = from_date or date.today()
    days_to_thu = (3 - d.weekday()) % 7   # v8 Sensex: Thursday = weekday index 3 (Nifty: Tuesday = 1)
    nominal = d + timedelta(days=days_to_thu)
    exp = _bse_trading_day_on_or_before(nominal)   # v-E12: holiday -> previous trading day
    if exp < d:   # this week's (holiday-shifted) expiry already passed
        nominal += timedelta(days=7)
        exp = _bse_trading_day_on_or_before(nominal)
    # v-E18 (vE6.2): runway counted in NSE TRADING days to the ACTUAL expiry
    # (was calendar days to the nominal Tuesday -> Fri 16-Oct-2026 traded the
    # Mon 19-Oct contract with 1 trading day left).
    if _bse_trading_days_between(d, exp) <= BOTG_ROLLOVER_MAX_DAYS_LEFT:
        exp = _bse_trading_day_on_or_before(nominal + timedelta(days=7))
    return exp


def getSensexWeeklyExpiry(from_date=None):
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
    exp_date = _next_sensex_weekly_expiry_date(from_date)
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
    v-G29 (22-Aug-2026; v8: LAST Thursday for Sensex): True if exp_date is the LAST Tuesday of its
    month -- i.e. this week's weekly expiry is simultaneously the
    month's own monthly expiry (adding 7 days would roll into next
    month). NSE/Fyers list that one specific contract under the MONTHLY
    symbol format (YY+3-letter-month, e.g. "26AUG"), not the ordinary
    weekly numeric-date format (YY+M+DD, e.g. "26825") -- there being
    only one contract for that date, exchanges publish it as "the
    monthly," not as a weekly that happens to coincide.
    """
    _thu = _nominal_expiry_thursday(exp_date)   # v-E12: judge on the nominal Thursday (v8 Sensex)
    return (_thu + timedelta(days=7)).month != _thu.month


def _bot_g_symbol_expiry_code(exp_date):
    """
    v-G29 (22-Aug-2026): ROOT-CAUSE FIX. getSensexWeeklyExpiry()'s ordinary
    weekly code (YY+M+DD) is what Fyers actually expects for a normal
    week, but for the one week per month where the weekly expiry IS the
    monthly expiry (_is_month_end_weekly() True), Fyers rejects that code
    outright: confirmed live, 20/21-Aug-2026, `fyers.history()` returning
    `{'code': -300, 'message': 'Invalid symbol provided'}` for EVERY
    strike and side tried (24000 PE, 24200 PE, 24400 CE) against the
    25-Aug-2026 expiry -- which is the last Tuesday of August. Every
    single option-history fetch failed silently (fetch_option_history_5m
    returning None -> find_bot_g_rejection_5m never even running), so
    BOT_G/BOT_GG could not arm a single rejection candle across two full
    trading days despite favorable price action and an open DPCR gate at
    the exact moments checked -- this, not the DPCR zone/threshold
    calibration, was the actual reason no trade fired on 19-Aug or
    20-Aug.

    Returns the code to use for the SYMBOL actually sent to Fyers
    (history fetch, order placement) -- YY+3-letter-month (e.g. "26AUG")
    for a month-end week, otherwise identical to getSensexWeeklyExpiry()'s
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


def get_option_symbol_bot_g(spot, side, otm_steps=None, bot_name="BOT_G", _log=True):   # v8.1: _log
    """
    v-G1: BOT_G's own symbol constructor -- ATM calc, logging, WEEKLY
    expiry, always-OTM depth (unsigned -- see config comment). Fully
    independent of the deleted BOT_A-F get_option_symbol() path (monthly
    expiry, signed ITM/OTM via STRIKE_ITM_STEPS) that used to live in
    this file.

    v-G40 (this session): the liquid-grid snap this docstring used to
    mention is gone -- see the removal note inline below for why.

    v-G11: otm_steps is now a parameter, not a hardcoded constant --
    v-G37: now set per-strike by the pool scan in _bot_g_try_entry(),
    which iterates bot["otm_pool"] (locked once daily by
    lock_bot_g_strike_pool()) instead of passing one fixed value.
    Defaults to BOTG_STRIKE_OTM_STEPS (the original fixed OTM4) if not
    passed, so any other caller that hasn't been updated still works.

    v-G12: bot_name added so BOT_GG (shares this function with BOT_G) gets
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
    # found live, this session: with the pool spaced 50pts apart (STRIKE_
    # ROUND_UNIT) but the old grid snapping to the nearest 100, ATM/OTM1/
    # OTM2 collapsed onto the SAME strike on every VIX<=13 day (confirmed
    # in a live log: OTM_STEPS 0/1/2 all resolving to strike 23600).
    # Silently neutered the whole pool on exactly the VIX regime it's most
    # often used in. Strikes are natively listed every 50pts on NIFTY and
    # liquid enough at that spacing -- the pool needs genuinely distinct
    # strikes to do what it's for, so this snap doesn't belong here
    # regardless of grid size chosen.

    expiry_code, expiry_date = getSensexWeeklyExpiry()
    # v-G29: the REAL symbol sent to Fyers uses _bot_g_symbol_expiry_code(),
    # not expiry_code directly -- they differ exactly one week per month
    # (the month-end week), see that function's docstring for why.
    symbol_expiry_code = _bot_g_symbol_expiry_code(expiry_date)
    symbol = f"BSE:SENSEX{symbol_expiry_code}{strike}{side}"   # v8 Sensex (Nifty: NSE:NIFTY...)
    # v8.1: this line was 49% of the 19-Oct Fyers log (printed on every call, ~2,990 times). Now printed
    # only when the symbol for this (bot, side, OTM step) changes, or every BOTG_OPTSYM_LOG_HEARTBEAT_SEC
    # seconds (BOTG_OPTSYM_LOG_EVERY_CALL = True restores the Nifty behaviour).
    _okey = (bot_name, side, otm_steps)
    _oprev = _V81_OPTSYM_LAST.get(_okey)
    _onow = time.time()
    if _log and (BOTG_OPTSYM_LOG_EVERY_CALL or _oprev is None or _oprev[0] != symbol
                 or (_onow - _oprev[1]) >= BOTG_OPTSYM_LOG_HEARTBEAT_SEC):
        _V81_OPTSYM_LAST[_okey] = (symbol, _onow)
        log(f"{bot_name} OPTION SYMBOL | Spot:{spot} ATM:{atm_strike} Strike:{strike} "
            f"(OTM_STEPS:{otm_steps}) Expiry:{expiry_date.isoformat()} "
            f"Symbol:{symbol}"
            + (" [MONTH-END WEEK -- monthly-format code, v-G29]" if _is_month_end_weekly(expiry_date) else ""))
    return symbol


_V81_OPTSYM_LAST = {}   # v8.1: (bot, side, otm) -> (symbol, time of last OPTION SYMBOL line)


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

_BOTG_OPT_CACHE = {}   # v-G37: was a single-symbol slot -- FIXED. With the
# multi-strike pool, up to 3 different symbols now get checked per tick,
# and a single-slot cache means each one evicts the last, so ALL of them
# would miss cache on EVERY tick (real fetch every ~1-3s instead of once
# per ~170s, per symbol). Now keyed by symbol: {symbol: {"time5":..,
# "df5":..}}, so each pool strike gets its own independent cache slot.


_BOTG_LAST_FORCED_5M_BOUNDARY = {}   # symbol -> bucket number of its last forced refresh

def _bot_g_should_force_5m_refresh(symbol):
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
    one extra forced fetch per pool symbol per 5-min boundary. Kept
    identical to the RMoney file.
    """
    global _BOTG_LAST_FORCED_5M_BOUNDARY
    now = datetime.now()
    elapsed = (now.hour * 60 + now.minute) - (9 * 60 + 15)
    if elapsed < 0:
        return False
    bucket = elapsed // 5
    if _BOTG_LAST_FORCED_5M_BOUNDARY.get(symbol) == bucket:
        return False
    _BOTG_LAST_FORCED_5M_BOUNDARY[symbol] = bucket
    return True

def fetch_option_history_5m(fyers, symbol, force_refresh=False):
    """
    v-G20: BOT_G 5-minute option history, session-scoped to today.

    v-G21 (18-Aug-2026): FIXED -- was fetching NATIVE 1-MINUTE bars
    (helper.getHistorical(symbol, 1, ...)) and resampling them up to
    5-min, when no part of this design actually needs 1-min granularity
    (explicit instruction: "1min data has no purpose here" -- API load
    concern, not a sub-bar/consistency-check requirement). Fetches native
    5-min bars directly now -- one call, no resample step at all, half
    the historical-candle count per fetch versus the 1-min version.

    v-G37 (05-Sep-2026): cache keyed per-symbol now (see _BOTG_OPT_CACHE
    comment above) -- required for the multi-strike pool, harmless no-op
    change in behavior for a single-symbol caller.
    """
    now = time.time()
    slot = _BOTG_OPT_CACHE.get(symbol)
    if (not force_refresh and slot is not None and slot.get("df5") is not None and
            (now - slot["time5"]) < BOTG_OPT_HIST_CACHE_SEC):
        return slot["df5"]
    try:
        raw = helper.getHistorical(symbol, 5, 2, fyers)   # v-G21: native 5, not 1+resample
    except Exception as e:
        log(f"[BOT_G 5M HIST ERROR] {symbol}: {e}")
        # v-G26-DIAG1 (20-Aug-2026): diagnostic-only, this file only (helper_fyers.py
        # intentionally untouched). helper.getHistorical() swallows Fyers' actual
        # error body into a bare KeyError('candles'), so on that specific failure
        # we make one extra RAW fyers.history() call -- same params helper uses
        # internally -- purely to log Fyers' real 's'/'message' fields. Same
        # candles KeyError also seen on the Sensex bot (both NSE and BSE option
        # symbols), so this is a general option-history issue, not exchange-
        # specific -- diagnostic added here to confirm the actual cause. Does not
        # change control flow or return value: still returns None below exactly
        # as before, same fail-soft contract as always.
        if isinstance(e, KeyError) and str(e).strip("'\"") == "candles":
            try:
                _diag_range_to = datetime.now()
                _diag_range_from = _diag_range_to - timedelta(days=2)
                _diag_resp = fyers.history(data={
                    "symbol": symbol,
                    "resolution": 1,
                    "date_format": "1",
                    "range_from": _diag_range_from.strftime("%Y-%m-%d"),
                    "range_to": _diag_range_to.strftime("%Y-%m-%d"),
                    "cont_flag": "1",
                })
                log(f"[BOT_G 5M HIST DIAG] {symbol}: raw Fyers response = {_diag_resp}")
            except Exception as _diag_e:
                log(f"[BOT_G 5M HIST DIAG] {symbol}: diagnostic call itself failed: {_diag_e}")
        return None
    if raw is None or not hasattr(raw, "columns") or len(raw) == 0:
        log(f"[BOT_G 5M HIST ERROR] {symbol}: empty/invalid history response")
        return None
    df5 = raw[raw.index.date == raw.index[-1].date()].copy()   # today only
    # v8 Sensex hardening (Sensex v-SEN14): some BSE history responses include the day's final
    # bar while the clock is still earlier. A future bar must never become df5.iloc[-1] (the
    # "forming" candle the arm/confirm logic uses). Index timezone left untouched.
    if len(df5):
        _now_ist = pd.Timestamp.now(tz="Asia/Kolkata")
        _idx_ist = (df5.index.tz_convert("Asia/Kolkata") if getattr(df5.index, "tz", None) is not None
                    else df5.index.tz_localize("Asia/Kolkata"))
        df5 = df5.loc[_idx_ist <= _now_ist]
    if len(df5) == 0:
        return None
    tp = (df5["high"] + df5["low"] + df5["close"]) / 3
    vol = df5["volume"].fillna(0)
    df5["vwap"] = (tp * vol).cumsum() / vol.cumsum().replace(0, float("nan"))
    _BOTG_OPT_CACHE[symbol] = {"time5": now, "df5": df5}
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
    rejection = bool(BOTG_NEAR_VWAP_LOWER_PTS <= dist <= BOTG_NEAR_VWAP_UPPER_PTS)   # v8 Sensex: asymmetric band (Nifty: abs(dist) <= BOTG_NEAR_VWAP_PTS)

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
            # Kept identical to the RMoney file's copy of this function.
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
    # direction, so no side-specific formula is needed.
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
        f"VolumeSignal:{volume_signal} "
        f"BearPressure:{round(bear_pressure,2)} VPCState:{vpc_state} "
        f"VPCVeto:{vpc_veto} VPCReason:{vpc_reason} "
        f"VWAPPenetration:{vwap_penetration:+.2f} Structure:{rejection_structure} (v-G52/v-G53/v-G54)")

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
    touched = bool(vwap_touched or BOTG_NEAR_VWAP_LOWER_PTS <= (ltp-vwap) <= BOTG_NEAR_VWAP_UPPER_PTS)   # v8 Sensex: asymmetric band
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
# CANDLES entries are ever read.
_BOTG_TOTAL_OI_ACTIVITY_HISTORY = []

# v-G58: EMA-based activity baseline for the FOURTH DPCR research variant
# below (activity_weighted_dpcr) -- a separate state variable from the
# v-G57 rolling-average buffer above, since this one uses an EMA (0.80/
# 0.20) rather than a simple mean over a fixed window.
_BOTG_DPCR_EMA_ACTIVITY_BASELINE = None

# v-G12: BOT_GG shares _bot_g_try_entry() with BOT_G (same function, two
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
    """v-G81 (Fyers): OI + LTP per strike from the SAME cached optionchain()
    response the DPCR module already fetched -- no extra API call.
    Returns (spot_at_fetch_or_None, {strike: {"CE": {oi, ltp}, "PE": {...}}})."""
    chain = {int(round(float(k))): v for k, v in (snap.get("chain") or {}).items()}
    out = {}
    for k in strikes:
        if k is None:
            continue
        row = chain.get(int(k)) or {}
        out[int(k)] = {s: {"oi": (row.get(s) or {}).get("oi"), "ltp": (row.get(s) or {}).get("ltp")}
                       for s in ("CE", "PE")}
    return snap.get("spot_at_fetch"), out


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
    atm = int(round(spot / STRIKE_ROUND_UNIT)) * STRIKE_ROUND_UNIT if spot else None   # v8 Sensex (Nifty: /50.0 * 50)
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
    the tick actually lands on. Kept identical to the RMoney file.
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


def get_bot_g_dpcr_window_today():
    """
    v-G37 (05-Sep-2026): plain calendar-weekday lookup into
    BOTG_DPCR_WINDOW_BY_WEEKDAY, computed fresh each call (cheap -- one
    dict lookup, no API call) rather than locked/cached, since weekday
    can't change mid-session anyway.

    Deliberately independent of _next_sensex_weekly_expiry_date() / BOT_G's
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


def get_bot_g_reanchor_pts_today():
    """v8 Sensex (Sensex v-SG-V6, option B): spot distance from the last anchor's spot that
    triggers a re-anchor = half the DPCR window's reach (Nifty rule) but not less than the
    weekday floor in BOTG_REANCHOR_MIN_PTS_BY_WEEKDAY (Wed/Thu windows are only +/-2 strikes)."""
    wd = date.today().weekday()
    half = (get_bot_g_dpcr_window_today() * _oc_filter.OC_STRIKE_GAP
            * _oc_filter.REANCHOR_HALF_WINDOW_FRACTION)
    return max(half, BOTG_REANCHOR_MIN_PTS_BY_WEEKDAY.get(wd, 0))


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


def get_current_dpcr(spot=None, gap_day=False, dpcr_window=None, reanchor_pts=None):   # v8 Sensex: reanchor_pts
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
    """
    if spot is None:
        log("BOT_G DPCR   | get_current_dpcr() called without spot -- cannot compute, returning None")
        return None, None

    snap = _oc_filter.compute_dpcr(fyers, spot=spot, bot_name="BOT_G", gap_day=gap_day, dpcr_window=dpcr_window,
                                   reanchor_pts=reanchor_pts, anchor_ref=_v833_anchor_ref_for_call(gap_day))   # v8 Sensex / v8.3.3
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
    try:   # v8.1 research (log-only): remember the carried (decision) and the fresh-window DPCR
        _V81_DPCR.update(carried=signed_dpcr, reset=compute_signed_dpcr(pe_delta, ce_delta), t=time.time())
    except Exception as _e81:
        _v81_err("dpcr capture", _e81)
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
    # ever be considered as a decision input, not a same-day swap.
    total_activity = abs(pe_delta) + abs(ce_delta)
    _prior_activity = list(_BOTG_TOTAL_OI_ACTIVITY_HISTORY[-BOTG_MAGNITUDE_DPCR_BASELINE_CANDLES:])
    rolling_avg_activity = (sum(_prior_activity) / len(_prior_activity)) if _prior_activity else None
    magnitude_dpcr = ((pe_delta - ce_delta) / rolling_avg_activity) if rolling_avg_activity else None
    _BOTG_TOTAL_OI_ACTIVITY_HISTORY.append(total_activity)
    if len(_BOTG_TOTAL_OI_ACTIVITY_HISTORY) > BOTG_MAGNITUDE_DPCR_BASELINE_CANDLES * 3:
        del _BOTG_TOTAL_OI_ACTIVITY_HISTORY[0]

    # v-G58: FIFTH-ish/fourth DPCR research variant -- an independently-
    # proposed EMA + log-scaled alternative, found in an uploaded file
    # that had (incorrectly) made it the PRIMARY decision metric while
    # only PARTIALLY updating the codebase for its 1.0-centred convention
    # (the zone/no-trade-zone config constants were correctly co-updated,
    # but there was no historical replay validating it before deployment,
    # and no evidence the flat-band/falling-block thresholds -- delta-
    # based, so insensitive to the constant shift, but NOT necessarily to
    # the new formula's different typical change-magnitudes -- still
    # fit). Restored here as a FOURTH research-only candidate instead of
    # discarding the idea, alongside v-G57's own magnitude_dpcr, so both
    # can be compared against real outcomes via replay before either is
    # ever trusted with a real decision. signed_dpcr remains untouched
    # and is still the only value in _BOTG_DPCR_HISTORY.
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
    log(f"BOT_G DPCR   | PRIMARY={signed_dpcr:+.3f}(0=neutral) RAW_RATIO={raw_ratio:+.3f}(1.0=neutral) "
        f"MagnitudeDPCR={f'{magnitude_dpcr:+.3f}' if magnitude_dpcr is not None else 'NA'}(0=neutral,v-G57) "
        f"ActivityWeightedDPCR={activity_weighted_dpcr:+.3f}(1.0=neutral,v-G58) | "
        f"PE:{pe_delta:+.0f} CE:{ce_delta:+.0f}")

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
    try:   # v8.1.1 research (log-only): fresh-window DPCR series, same cadence as the decision series
        _V81_RESET_HIST.append(_V81_DPCR.get("reset"))
        if len(_V81_RESET_HIST) > BOTG_DPCR_HISTORY_MAX:
            _V81_RESET_HIST.pop(0)
    except Exception as _e81:
        _v81_err("reset history", _e81)
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
    days of history, per _get_historical_sensex_safe()) -- no new data
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

    v-G15: trade_start_override_normal/gap added -- BOT_GG starts trading
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
    log line alongside the real signed_dpcr zone. Kept identical to the
    RMoney file's copy of this function.
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

    v-G12: bot_name added purely for log labeling -- BOT_G and BOT_GG each
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
    skips this clamp entirely and behaves exactly as before.

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
    v-G11: REAL, explicit instruction (12-Aug-2026 session). Two-stage
    partial profit booking (points, not rupees -- consistent with BOT_G's
    whole points-based design, unlike A-F's rupee-PnL-triggered
    apply_partial_booking()).

    v-G36 (29-Aug-2026): targets are now HYBRID, not pure R-multiple --
    each stage uses whichever is FARTHER from entry: the R-based level,
    or a flat %-of-entry floor. Root-caused via a real-data replay
    (28-Aug-2026 session): pure R-based degenerates to a near-noise
    target when risk_pts is small relative to entry; a pure flat-%
    target correspondingly caps a genuinely high-conviction (large-R)
    trade earlier than its own risk justifies. Taking the farther of the
    two on each individual trade avoided both failure modes in the
    replay -- see BOTG_PARTIAL_R1_PCT_FLOOR/BOTG_PARTIAL_R15_PCT_FLOOR in
    config for the full investigation notes.

      Stage 1 @ entry + max(BOTG_PARTIAL_R1_MULT  * risk_pts, BOTG_PARTIAL_R1_PCT_FLOOR  * entry) -> book
               BOTG_PARTIAL_R1_FRACTION  (50%) of qty_base
      Stage 2 @ entry + max(BOTG_PARTIAL_R15_MULT * risk_pts, BOTG_PARTIAL_R15_PCT_FLOOR * entry) -> book
               BOTG_PARTIAL_R15_FRACTION (25%) of qty_base

    Both fractions are of the ORIGINAL qty_base (not whatever qty remains
    at each stage), so together they book 75% of the position, leaving
    25% to trail via the EXISTING BE(0.75R)/TSL(1.5R-arm, 8pt buffer)
    machinery in manage_bot_g_exit() -- unchanged, still runs on whatever
    qty remains after this function does its own booking. Note risk_pts/
    be_level/arm_level themselves are UNCHANGED by v-G36 -- SL placement
    and the BE/TSL triggers stay purely R-based; only these two
    profit-taking targets get the hybrid treatment.

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

    # v-G36 (29-Aug-2026): HYBRID target -- max of the R-based level and a
    # %-of-entry floor, per trade, not a single formula applied uniformly.
    # See BOTG_PARTIAL_R1_PCT_FLOOR/BOTG_PARTIAL_R15_PCT_FLOOR in config
    # for the full replay-tested rationale. This deliberately does NOT
    # change risk_pts, be_level, or arm_level -- SL placement and BE/TSL
    # triggers stay exactly R-based as before (v-G6 onward); only the
    # PROFIT-TAKING targets get this treatment.
    r1_level, r15_level = _botg_targets(bot, bot["entry"], bot["risk_pts"])   # v-E4

    if not bot["partial1_done"] and check_high >= r1_level:
        book_qty = _lot_safe_qty(bot["qty_base"] * BOTG_PARTIAL_R1_FRACTION, bot["qty"])
        if book_qty <= 0:
            return False

        # v-G57: LIVE SAFETY FIX -- execute the broker SELL FIRST and only
        # mutate local qty/state after Fyers confirms the fill. The previous
        # code changed bot["qty"] locally and called log_partial_trade() but
        # never invoked place_partial_exit_order(), leaving the broker with
        # the original full position while the bot believed 50% was closed.
        oid, fill_price, filled_qty = place_partial_exit_order(bot, book_qty, r1_level)
        if not oid or not fill_price or filled_qty <= 0:
            if not PAPER_TRADE:
                _halt_live_execution(f"P1 partial SELL not confirmed for {bot['name']}")
            return False
        if filled_qty > bot["qty"]:
            _halt_live_execution(f"P1 fill qty {filled_qty} exceeds local qty {bot['qty']} for {bot['name']}")
            return False

        bot["partial1_done"]       = True
        bot["partial1_booked_qty"] = filled_qty
        bot["qty"] -= filled_qty
        log_partial_trade(bot, bot["side"], bot["entry"], fill_price, filled_qty, "BOTG_PARTIAL_R1")
        _r1_via = "%floor" if bot.get("p1_pct_floor", BOTG_PARTIAL_R1_PCT_FLOOR) * bot["entry"] > bot.get("p1_r_mult", BOTG_PARTIAL_R1_MULT) * bot["risk_pts"] else "R"
        log(f"{bot['name']} PARTIAL | Stage 1 ({_r1_via} target={round(r1_level,2)}): "
            f"sold {filled_qty} qty ({filled_qty // LOT_SIZE} lots) @ {round(fill_price,2)} -- "
            f"Remaining:{bot['qty']} ({bot['qty'] // LOT_SIZE} lots) (v-G57)")
        tg(f"{bot['name']} PARTIAL BOOK ({_r1_via})\nSold {filled_qty // LOT_SIZE} lot(s) "
           f"@ {round(fill_price,1)}\nRemaining {bot['qty'] // LOT_SIZE} lot(s) running")
        if bot["qty"] <= 0:
            _close_fully_via_partial("Stage 1")
            return True
        if not update_broker_sl_order(bot, bot["active_sl"]):
            _emergency_flatten(bot, "Stage 1 partial completed but broker SL could not be verified")
            raise RuntimeError("LIVE SAFETY: broker SL protection failed after Stage 1 partial")

    if not bot["partial2_done"] and check_high >= r15_level:
        book_qty = _lot_safe_qty(bot["qty_base"] * BOTG_PARTIAL_R15_FRACTION, bot["qty"])
        if book_qty <= 0:
            return False

        # v-G57: same transactional rule for P2. Never mark the stage done
        # or reduce local qty until the broker confirms the SELL fill.
        oid, fill_price, filled_qty = place_partial_exit_order(bot, book_qty, r15_level)
        if not oid or not fill_price or filled_qty <= 0:
            if not PAPER_TRADE:
                _halt_live_execution(f"P2 partial SELL not confirmed for {bot['name']}")
            return False
        if filled_qty > bot["qty"]:
            _halt_live_execution(f"P2 fill qty {filled_qty} exceeds local qty {bot['qty']} for {bot['name']}")
            return False

        bot["partial2_done"]       = True
        bot["partial2_booked_qty"] = filled_qty
        bot["qty"] -= filled_qty
        log_partial_trade(bot, bot["side"], bot["entry"], fill_price, filled_qty, "BOTG_PARTIAL_R15")
        _r15_via = "%floor" if bot.get("p2_pct_floor", BOTG_PARTIAL_R15_PCT_FLOOR) * bot["entry"] > bot.get("p2_r_mult", BOTG_PARTIAL_R15_MULT) * bot["risk_pts"] else "R"
        log(f"{bot['name']} PARTIAL | Stage 2 ({_r15_via} target={round(r15_level,2)}): "
            f"sold {filled_qty} qty ({filled_qty // LOT_SIZE} lots) @ {round(fill_price,2)} -- "
            f"Remaining:{bot['qty']} ({bot['qty'] // LOT_SIZE} lots) (v-G57)")
        tg(f"{bot['name']} PARTIAL BOOK ({_r15_via})\nSold {filled_qty // LOT_SIZE} lot(s) "
           f"@ {round(fill_price,1)}\nRemaining {bot['qty'] // LOT_SIZE} lot(s) running")
        if bot["qty"] <= 0:
            _close_fully_via_partial("Stage 2")
            return True
        if not update_broker_sl_order(bot, bot["active_sl"]):
            _emergency_flatten(bot, "Stage 2 partial completed but broker SL could not be verified")
            raise RuntimeError("LIVE SAFETY: broker SL protection failed after Stage 2 partial")

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

    # vRG2: broker-side SL may have triggered between ticks. Reconcile the
    # actual position before sending any new SELL, so an already-flat broker
    # position can never receive a duplicate exit order.
    if not PAPER_TRADE:
        _bqty, _bavg, _bok = _get_net_position(bot.get("entry_symbol"))
        if not _bok:
            _halt_live_execution(f"Live position reconciliation failed while managing {bot['name']}")
            return
        if _bqty <= 0:
            _slid = bot.get("sl_order_id")
            _slfill = None
            if _slid:
                _st, _px, _q = _get_order_status_fyers(_slid)
                if _st == "FILLED" and _px:
                    _slfill = _px
            if _slfill is not None:
                log(f"BROKER SL EXIT | {bot['name']} broker SL {_slid} filled @ {_slfill}; no duplicate SELL will be sent.")
                bot["sl_order_id"] = None
                if log_trade(bot, bot["side"], bot["entry"], _slfill, "BROKER_SL_FILLED", bot["qty"], broker_exit_already_filled=True):
                    _close_bot(bot, cooldown=0)
                    bot["stage"] = "INITIAL"; bot["armed"] = False; bot["_botg_last_broker_sl"] = None
                return
            _halt_live_execution(f"Broker reports {bot['entry_symbol']} flat but no broker SL fill was recoverable for {bot['name']}")
            return

    bot["highest"] = max(bot["highest"], ltp)
    bot["_last_ltp"] = ltp; bot["_last_ltp_hhmm"] = hhmm()   # v-E21
    _v832_gap_mark(bot)        # v8.3.2: seconds since the previous good tick (paper stop-fill rule)
    _v832_wi_tick(bot, ltp)    # v8.3.2: exit what-if (log-only)
    # v-G59: per-trade peak-unrealized tracker (LOGGING ONLY). Uses current
    # remaining qty at each tick, matching how SESSION_PEAK_PNL computes
    # unrealized elsewhere -- so a trade that has already taken a partial
    # reports peak unrealized on its remaining size, not the original.
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
        if not PAPER_TRADE and bot.get("sl_order_id"):
            _sl_before = bot.get("sl_order_id")
            cancel_broker_sl_order(bot)
            if bot.get("sl_order_id"):
                _st, _px, _q = _get_order_status_fyers(_sl_before)
                if _st == "FILLED" and _px:
                    bot["sl_order_id"] = None
                    if log_trade(bot, bot["side"], bot["entry"], _px, "BROKER_SL_FILLED", bot["qty"], broker_exit_already_filled=True):
                        _close_bot(bot, cooldown=0)
                        bot["stage"] = "INITIAL"; bot["armed"] = False; bot["_botg_last_broker_sl"] = None
                    return
                log(f"EXIT BLOCKED | {bot['name']} broker SL {_sl_before} could not be cancelled safely.")
                return
        # v8.1 (Anu, 19-Oct): PAPER stop-triggered exits are filled at the stop level, as the RMoney
        # bot has done since G4.1, instead of the polled LTP (19-Oct: Fyers -2.4 pts / -Rs192 on a
        # breakeven exit that RMoney booked at Rs0). Both Sensex brokers now book the same exit.
        exit_price = ltp
        if PAPER_TRADE and G4_PAPER_STOP_AT_TRIGGER and reason in ("SL_EXIT", "BREAKEVEN_EXIT", "TSL_EXIT"):
            stop_level = bot.get("active_sl")
            if stop_level is not None and stop_level > 0:
                exit_price = float(stop_level)
                log(f"PAPER STOP FILL | {bot['name']} {reason} TriggerLTP:{round(ltp,2)} "
                    f"Stop:{round(exit_price,2)} -> using stop level for paper fill (G4.1, v8.1)")
                if (V832_GAP_FILL_ENABLED and bot.get("_v832_gap_s", 0) > V832_GAP_FILL_SEC and ltp < exit_price):
                    log(f"PAPER GAP FILL | {bot['name']} {reason} data gap {round(bot['_v832_gap_s'])}s > {V832_GAP_FILL_SEC}s: "
                        f"first post-gap LTP {round(ltp,2)} is below the stop {round(exit_price,2)} -> filled at the LTP (v8.3.2)")
                    exit_price = float(ltp)
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


_V86_IDLE = {"slot": None, "date": None}


def _v86_gap_idle_log(bot, spot, now_hhmm, watch_start_hhmm, trade_start_hhmm):
    """v8.6 (LOG-ONLY): on a gap day, one BOT_G line every V86_GAP_IDLE_LOG_MIN minutes from 09:18 until the DPCR watch starts,
    so a silent morning does not look like a dead feed. Never raises, never touches state."""
    try:
        if not V86_GAP_IDLE_LOG or bot.get("name") != "BOT_G" or not bot.get("gap_day") or now_hhmm < 918:
            return
        _mins = (now_hhmm // 100) * 60 + (now_hhmm % 100)
        _slot = _mins // max(1, int(V86_GAP_IDLE_LOG_MIN))
        _today = date.today()
        if _V86_IDLE["date"] != _today:
            _V86_IDLE.update(date=_today, slot=None)
        if _V86_IDLE["slot"] == _slot:
            return
        _V86_IDLE["slot"] = _slot
        _w = f"{watch_start_hhmm // 100:02d}:{watch_start_hhmm % 100:02d}"
        _tr = f"{trade_start_hhmm // 100:02d}:{trade_start_hhmm % 100:02d}"
        log(f"BOT_G GAP DAY | idle (by design) -- gap {bot.get('gap_pct')}% >= {BOTG_GAP_THRESHOLD_PCT}%: early slot off, DPCR watch starts {_w}, "
            f"first BOT_G trade {_tr} | now {now_hhmm // 100:02d}:{now_hhmm % 100:02d} spot {round(float(spot), 2) if spot else 'NA'} "
            f"(v8.6, log-only; next line in {int(V86_GAP_IDLE_LOG_MIN)} min)")
    except Exception as _e86:
        try:
            log(f"v8.6 GAP IDLE LOG | error (ignored): {_e86}")
        except Exception:
            pass


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
        _v86_gap_idle_log(bot, spot, now_hhmm, watch_start_hhmm, trade_start_hhmm)   # v8.6 log-only
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
    if not _v833_anchor_wait(bot) and is_new_3m_candle(bot["name"]):   # v8.3.3: wait (without consuming the bucket) for the closed 09:15 candle
        # v-G12 (historical): the fetch+append is bot-AGNOSTIC (shared
        # history, one real DPCR per candle) -- gated on
        # _is_new_shared_dpcr_candle(), not on is_new_3m_candle() (kept
        # this way even after BOT_GG's removal since it's still correct
        # and harmless for a single bot). dpcr_history is still re-read
        # fresh every time regardless -- cheap, no API call, just a list copy.
        # v-G47: defensive init -- _raw_ratio_for_dashboard is only assigned
        # inside the _is_new_shared_dpcr_candle() branch below, but is now
        # also read further down (at the lock_bot_g_daily_bias() call) on
        # every is_new_3m_candle() tick, not just ticks where the shared
        # candle also just rolled. Without this default it would raise
        # NameError on any tick where the two conditions diverge -- caught
        # before shipping, not from a live crash. Kept identical to the
        # RMoney file.
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
                spot=spot, gap_day=gap_day, dpcr_window=get_bot_g_dpcr_window_today(),
                reanchor_pts=get_bot_g_reanchor_pts_today())   # v8 Sensex
            if _signed_dpcr is not None:
                # v-G9-FIX4: this call existed in heartbeat_snippet.py but was
                # never actually wired anywhere -- without it, /botg_series stays
                # empty and the dashboard's DPCR/Nifty charts have nothing to
                # plot, even with BOT_G fully live.
                # v-E10: signed DPCR (+ raw ratio, broker, zone) -- was raw only.
                send_botg_reading(_signed_dpcr, _raw_ratio_for_dashboard, spot,
                                  bot.get("dpcr_no_trade_high"))
        _v87_note_strikes(spot)   # v8.7 log-only (option tape strikes)
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
        _v87_shadow_lock(bot, spot, dpcr_history, now_hhmm, trade_start_hhmm)   # v8.7 log-only
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
        _v84_zdir_log(bot, spot, dpcr_history)   # v8.4 (log-only)
        _v89_pause_cf(bot, spot, dpcr_history, now_hhmm)   # v8.9 (log-only): counterfactual tag for zone-paused scans

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
    if bot["gap_day"] is None:
        is_gap, gap_pct = detect_bot_g_gap_day(df3)
        bot["gap_day"], bot["gap_pct"] = is_gap, gap_pct
    _v831_gap_recheck(bot, df3)   # v8.3.1

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
    # BOT_G and BOT_GG are capped INDEPENDENTLY of each other -- this
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
                fyers, candidate_symbol, force_refresh=_bot_g_should_force_5m_refresh(candidate_symbol))
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
                # trades CSV when the trade closes.
                st["rejection_setup_type"] = rej.get("setup_type")
                st["rejection_close_location"] = rej.get("close_location")
                st["rejection_rel_vol_5"] = rej.get("rel_volume_5")
                st["rejection_vwap_penetration"] = rej.get("vwap_penetration")
                log(f"{bot['name']} ARMED | OTM{otm_val} TF:5m side={side} Symbol:{candidate_symbol} "
                    f"Type:{rej.get('setup_type')} O:{rej.get('open')} H:{rej.get('high')} "
                    f"L:{rej['low']} C:{rej['close']} VWAP:{rej['vwap']} "
                    f"Dist:{rej['close']-rej['vwap']:+.2f} Body:{rej.get('body',0):.2f} "
                    f"Range:{rej.get('range',0):.2f} UpperW:{rej.get('upper_shadow',0):.2f} "
                    f"LowerW:{rej.get('lower_shadow',0):.2f} CloseLoc:{rej.get('close_location',0):.0%} "
                    f"-- next candle only: {closed_key} -> confirmation window (v-G41)")
                _v83_tag("ARM", bot, otm_val, candidate_symbol, side, spot,
                         detail=f"type={rej.get('setup_type')} rejC={rej['close']} rejL={rej['low']} vwap={rej['vwap']}")   # v8.3
            continue

        candidate_symbol = st["rejection_symbol"]
        df_setup = fetch_option_history_5m(
            fyers, candidate_symbol, force_refresh=_bot_g_should_force_5m_refresh(candidate_symbol))
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
        # Kept identical to the RMoney file's copy of this function.
        rejection_ts = datetime.strptime(st["rejection_candle_key"], "%Y-%m-%d %H:%M")
        current_forming_ts = df_setup.index[-1]
        current_forming_key = current_forming_ts.strftime("%Y-%m-%d %H:%M")
        next_candle_key = (rejection_ts + pd.Timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M")

        if current_forming_key != next_candle_key:
            _reason = st.get("_botg_last_confirm_fail_reason", "NOT_TOUCHED")
            _dist = st.get("_botg_last_confirm_dist")
            log(f"{bot['name']} ARM EXPIRED | OTM{otm_val} Symbol:{candidate_symbol} "
                f"rejection candle {st['rejection_candle_key']} "
                f"closed without confirmation -- current candle {current_forming_key}; "
                f"last reason: {_reason}"
                + (f" (dist to VWAP: {_dist:+.2f})" if _dist is not None else "") + " (v-G45)")
            _v83_tag("ARM_EXPIRED", bot, otm_val, candidate_symbol, side, spot, detail=f"reason={_reason} dist={_dist}")   # v8.3
            bot["pool_state"][key] = _fresh_pool_strike_state()
            continue

        fresh_candidate = get_option_symbol_bot_g(spot, side, otm_steps=otm_val, bot_name=bot["name"])
        if fresh_candidate != candidate_symbol:
            log(f"{bot['name']} ARM DROPPED | OTM{otm_val} strike shifted "
                f"{candidate_symbol} -> {fresh_candidate} (v-G40)")
            _v83_tag("ARM_DROPPED", bot, otm_val, candidate_symbol, side, spot, detail=f"shifted_to={fresh_candidate}")   # v8.3
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
        # v8 Sensex (Sensex v-SG-V4): skip a confirmed setup whose chart stop is closer than
        # BOTG_MIN_RISK_PTS (tiny risk -> R-multiples/targets meaningless). Pool slot reset.
        _mr_sl = compute_bot_g_initial_sl(candidate_ltp, st["rejection_low"], st.get("rejection_vwap"))
        _mr_risk = candidate_ltp - _mr_sl
        if BOTG_MIN_RISK_ENABLED and _mr_risk < BOTG_MIN_RISK_PTS:
            log(f"{bot['name']} ENTRY SKIP | OTM{otm_val} Symbol:{candidate_symbol} MIN_RISK -- risk "
                f"{round(_mr_risk,2)} pts (entry {candidate_ltp} - SL {round(_mr_sl,2)}) < BOTG_MIN_RISK_PTS "
                f"{BOTG_MIN_RISK_PTS} (v8 Sensex). Dropping arm.")
            _v83_tag("MIN_RISK_SKIP", bot, otm_val, candidate_symbol, side, spot, entry=candidate_ltp, sl=_mr_sl)   # v8.3
            _v833_skip_track(bot, "MINRISK", candidate_symbol, side, candidate_ltp, _mr_sl, spot)   # v8.3.3
            bot["pool_state"][key] = _fresh_pool_strike_state()
            continue

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
        _lc_ask, _lc_bid = _get_ask_bid_fyers(candidate_symbol)
    except Exception:
        _lc_ask, _lc_bid = None, None
    # v8.3.2: stale-quote guard (PAPER, Fyers). If the ask is far above the signal premium the LTP is lagging the book (28-Oct 13:27:
    # signal 703.75, ask 725.25). Abort and drop the setup (pool already reset above, same as the other skips).
    if PAPER_TRADE and V832_ASK_FILL_ENABLED and _lc_ask and candidate_ltp and candidate_ltp > 0:
        _v832_over = float(_lc_ask) - float(candidate_ltp)
        _v832_lim = V832_ASK_GUARD_PCT / 100.0 * float(candidate_ltp)
        if _v832_over > _v832_lim:
            log(f"{bot['name']} ENTRY ABORT | OTM{winner_otm} Symbol:{candidate_symbol} reason=STALE_QUOTE signal {candidate_ltp} "
                f"ask {_lc_ask} (+{round(_v832_over,2)} pts > {V832_ASK_GUARD_PCT}% = {round(_v832_lim,2)} pts) -- LTP lagging the book; "
                f"setup dropped (v8.3.2)")
            _v83_tag("ENTRY_ABORT_STALE_QUOTE", bot, winner_otm, candidate_symbol, side, spot, entry=candidate_ltp,
                     detail=f"ask={_lc_ask} over={round(_v832_over,2)} lim={round(_v832_lim,2)}")   # v8.3.2
            try:
                _v833_skip_track(bot, "STALEQ", candidate_symbol, side, candidate_ltp,
                                 compute_bot_g_initial_sl(candidate_ltp, rejection_low, rejection_vwap), spot)   # v8.3.3
            except Exception as _e833:
                _v833_err("stale-quote skip track", _e833)
            return
    # v8.4: falling-knife R1 enforced in the main slot (pool already reset above, same as the other skips).
    _v84_blk, _v84_c15, _v84_c30 = _v84_fk_check(bot, side, spot)
    if _v84_blk:
        log(f"{bot['name']} ENTRY SKIP | OTM{winner_otm} Symbol:{candidate_symbol} reason=FALLING_KNIFE_R1 {side} signal {candidate_ltp} -- spot moved "
            f"against the trade over both 15 min ({_v84_c15:+} pts) and 30 min ({_v84_c30:+} pts); setup dropped (v8.4)")
        _v83_tag("ENTRY_SKIP_FK_R1", bot, winner_otm, candidate_symbol, side, spot, entry=candidate_ltp,
                 detail=f"spot_chg15={_v84_c15} spot_chg30={_v84_c30}")   # v8.4
        try:
            _v833_skip_track(bot, "FKR1", candidate_symbol, side, candidate_ltp,
                             compute_bot_g_initial_sl(candidate_ltp, rejection_low, rejection_vwap), spot)   # v8.4
        except Exception as _e84:
            _v84_err("fk skip track", _e84)
        return
    bot["entry_symbol"]=candidate_symbol; bot["qty"]=bot["qty_base"]
    order_id,fill_price,filled_qty=execute_entry(bot,side)
    if order_id is None and not PAPER_TRADE: return
    if filled_qty is not None and filled_qty != bot["qty"] and not PAPER_TRADE: bot["qty"]=filled_qty
    fetched_premium=fill_price if fill_price is not None and fill_price>0 and not PAPER_TRADE else (candidate_ltp or get_multi_ltp([candidate_symbol]).get(candidate_symbol,0))
    if not fetched_premium or fetched_premium<=0: return
    if PAPER_TRADE and V832_ASK_FILL_ENABLED and _lc_ask and float(_lc_ask) > fetched_premium:
        fetched_premium = round(float(_lc_ask), 2)   # v8.3.2: paper entry at the ask (inside the stale-quote guard above)
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
    bot["peak_unrealized_pnl"] = 0.0
    bot["p1_target"] = _botg_targets(bot, fetched_premium, risk_pts)[0]   # v-E4
    register_entry(bot, side)
    update_broker_sl_order(bot, initial_sl)
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
    log(f"{bot['name']} ENTRY CONFIRMED | OTM{winner_otm} TF:5m Symbol:{candidate_symbol} Entry:{fetched_premium} "
        f"VWAP touch + confirmation above rejection close"
        + (f" (dist to VWAP: {_dist_at_entry:+.2f}, v-G30)" if _dist_at_entry is not None else "")
        + (f" [SL CLAMPED: rej_low {rejection_low} rej_vwap {round(rejection_vwap,2)} -> "
           f"chart SL {round(_chart_sl,2)} (vwap-{BOTG_SL_VWAP_BUFFER}), v-G39/v-G71]" if _sl_clamped else ""))
    _v83_tag("ENTRY", bot, winner_otm, candidate_symbol, side, spot, entry=fetched_premium, sl=initial_sl,
             detail=f"qty={bot['qty']} chartSL={round(_chart_sl,2)} clamped={int(bool(_sl_clamped))}")   # v8.3
    _v833_entry_log(bot, side, spot)   # v8.3.3
    _v832_wi_start(bot, side, candidate_symbol)   # v8.3.2
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
    # No longer used by anything now that BOT_GG is gone, kept only so
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
    # v-G37 (05-Sep-2026): BOT_GG entry REMOVED ENTIRELY -- explicit
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
                                     # enforcement. On 16-Sep, DPCR happened
                                     # to sit in the no-trade zone for the
                                     # whole 30-min window, which is very
                                     # possibly why this went unnoticed --
                                     # if DPCR had cleared mid-window, a 4th
                                     # trade could have fired with zero
                                     # streak protection. Now False: 3
                                     # consecutive SL/TSL exits genuinely
                                     # halt new BOT_G entries for
                                     # LOSING_STREAK_COOLDOWN_SEC, independent
                                     # of DPCR or any other gate. The
                                     # counter/timer code itself was already
                                     # correct and is unchanged -- only this
                                     # exemption flag flips.
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

# v-WEEKLY1: switched from getNiftyMonthlyExpiry() to getSensexWeeklyExpiry()
# -- the comment below's own invariant ("always agrees with what the bot is
# actually trading") would otherwise become false the moment
# get_option_symbol() switched to weekly, since file naming would silently
# stay on the old monthly cadence while actual trades moved to weekly.
# Bonus effect: log/trade/summary/state files now roll over weekly instead
# of monthly, which matches the new weekly trading cadence.
_SERIES_CODE = getSensexWeeklyExpiry()[0]

# v-G70: one naming pattern for every file either broker's v2 bot writes:
#   <kind>_<_FILE_STEM>_<series>_<_BROKER_TAG>.<ext>
# RMoney v2 uses the identical stem, only _BROKER_TAG differs.
_FILE_STEM   = "sensex_g_pool_v8_9"   # v8 Sensex (Nifty: nifty_g_pool_vE6)
_BROKER_TAG  = "fyers"
LOG_FILE       = f"bot_log_{_FILE_STEM}_{_SERIES_CODE}_{_BROKER_TAG}.txt"
TRADE_FILE     = f"trades_{_FILE_STEM}_{_SERIES_CODE}_{_BROKER_TAG}.csv"
SUMMARY_FILE   = f"summary_{_FILE_STEM}_{_SERIES_CODE}_{_BROKER_TAG}.csv"
STATE_FILE     = f"bot_state_{_FILE_STEM}_{_SERIES_CODE}_{_BROKER_TAG}.json"
HEARTBEAT_FILE = f"heartbeat_{_FILE_STEM}_{_BROKER_TAG}.txt"   # was plain heartbeat.txt

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
BOT_ID = "SENSEX_FYERS_G"   # v-G37: BOT_GG gone, dropped "GG" suffix
_LIVE_UNREALISED_PNL = 0.0  # kept fresh inside check_profit_lock() each cycle

def send_dashboard_heartbeat(pnl, status="running", bot_id=None):
    """
    v-G14: bot_id param added -- BOT_G and BOT_GG now each post their own
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
DASH_BROKER = "FYERS"   # v-E10: tags this bot's dashboard series


def send_botg_reading(dpcr, raw, sensex_spot, zone=None):
    """v-E10 (v8 Sensex endpoint): dpcr = SIGNED DPCR (-1..+1, the decision value); raw = PE/CE
    ratio (display only); zone = upper edge of today's no-trade zone. Posts to /sensex_reading
    with key sensex_spot (the Sensex dashboard series), silent like Nifty's."""
    try:
        _dash_requests.post(
            f"{DASHBOARD_URL}/sensex_reading",
            json={"dpcr": dpcr, "raw": raw, "sensex_spot": float(sensex_spot),
                  "broker": DASH_BROKER, "zone": zone},
            timeout=2,
        )
    except Exception:
        pass


def send_sensex_spot(sensex_spot):
    """v8 Sensex: keep the dashboard spot line continuous even when DPCR is unavailable."""
    try:
        _dash_requests.post(f"{DASHBOARD_URL}/sensex_spot",
                            json={"sensex_spot": float(sensex_spot)}, timeout=2)
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
# response). 360s = 2 candle-widths, giving a little slack for normal
# close-of-candle lag without letting a genuinely stalled feed (like
# the 91-minute one on 2026-08-03) pass silently.
STALE_CANDLE_SEC = 360


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
    v2.9-E1: Startup broker reconciliation via Fyers positions API.
    Broker truth overrides JSON on mismatch.

    v-RG-sync (this session): this never returned a proper True/False
    signal on any path -- API errors and exceptions just logged a
    warning and fell through to an implicit `return None`, same as
    RMoney's update_broker_sl_order() before its own v-RG3 fix. The
    caller in main() needs this to distinguish "reconciliation
    genuinely completed" from "we have no idea what the broker's real
    position is" so it can abort a live start on the latter, matching
    the vRG2 fail-closed design. Returns False only when the broker's
    true state genuinely couldn't be verified (API error or exception);
    True once a real query completed, whether or not mismatches were
    found and handled.
    """
    log("RECONCILE    | Querying live Fyers positions...")
    try:
        resp = fyers.positions()
        if resp.get("s") != "ok":
            log(f"RECONCILE    | Fyers positions API error: {resp} "
                "— proceeding with JSON state. Verify manually.")
            return False

        broker_positions = {}
        for pos in resp.get("netPositions", []):
            sym = pos.get("symbol", "")
            qty = int(pos.get("netQty", 0))
            if qty != 0:
                broker_positions[sym] = qty

        mismatches = []
        for bot in BOTS:
            if bot.get("trade_open") and bot.get("entry_symbol"):
                sym        = bot["entry_symbol"]
                broker_qty = broker_positions.get(sym, 0)
                json_qty   = bot.get("qty", 0)
                if broker_qty == 0:
                    mismatches.append(
                        f"{bot['name']}: JSON says OPEN qty={json_qty} "
                        f"but Fyers shows NO position — clearing JSON state"
                    )
                    bot["trade_open"]   = False
                    bot["entry"]        = 0.0
                    bot["entry_symbol"] = None
                    bot["active_sl"]    = 0.0
                    bot["highest"]      = 0.0
                elif broker_qty != json_qty:
                    mismatches.append(
                        f"{bot['name']}: JSON qty={json_qty} vs Fyers qty={broker_qty} "
                        f"— using Fyers qty"
                    )
                    bot["qty"] = broker_qty

        tracked_syms = {b["entry_symbol"] for b in BOTS
                        if b.get("trade_open") and b.get("entry_symbol")}
        for sym, qty in broker_positions.items():
            if sym not in tracked_syms and "SENSEX" in sym:
                mismatches.append(
                    f"UNTRACKED Fyers position: {sym} qty={qty} "
                    "— not in any bot state. Manual review required."
                )

        if mismatches:
            log("=" * 70)
            log("RECONCILE    | *** MISMATCH DETECTED ***")
            for m in mismatches:
                log(f"RECONCILE    | {m}")
            log("RECONCILE    | Pausing 30s for manual review.")
            log("=" * 70)
            tg(f"RECONCILE MISMATCH\n" + "\n".join(mismatches) +
               "\nBot pausing 30s — verify Fyers app NOW.")
            time.sleep(30)
        else:
            log("RECONCILE    | Fyers positions match JSON state — clean start.")
        return True

    except Exception as e:
        log(f"RECONCILE    | Exception: {e} — proceeding with JSON state.")
        return False


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
_logger = logging.getLogger("bot_fyers")
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
                params={"chat_id": chatid, "text": f"[NF-Fyers]\n{msg}"},
                timeout=5
            )
        except Exception:
            pass
    threading.Thread(target=_send, daemon=True).start()


_last_heartbeat = 0.0   # v2.8-L7: heartbeat tracker
_LAST_DASHBOARD_SIG = None   # v3.19-LOGFIX1: last-printed dashboard signature
LIVE_EXECUTION_HALT = False  # v-RG-sync: fail-closed live execution latch, ported
                              # from the vRG2 review -- see config comment for why
                              # this was missing from this line of development


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

# =============================================================================
#  v8.1 (19-Oct-2026) -- Sensex additions, decided by Anu on 19-Oct after the first v8 session.
#  Everything in this block is LOG-ONLY or pure noise reduction: no entry / exit / sizing
#  decision reads anything defined here.
#    1. Pre-open gate        : no data calls before BOTG_PREOPEN_RESUME_HHMMSS (09:14:30).
#    2. OPTION SYMBOL log    : printed when the symbol for a (bot, side, OTM step) changes, or every
#                              BOTG_OPTSYM_LOG_HEARTBEAT_SEC seconds -- not on every call.
#    3. VWAP research files  : vwap_research_*.csv (one row per pool strike per closed 5m bar, both
#                              sides, with the lock state) and pool_bars_*.csv (5m bars of every pool
#                              strike) -- to test other VWAP definitions offline.
#  v8.1.1 (20-Oct-2026) -- more LOG-ONLY research data (Anu: Sensex may move to 10-min candles and to a
#  DPCR-slope rule later; the data must exist by then):
#    4. pool_bars_*.csv is now flushed during the day (10:30, 11:30, 12:30, 13:30, 14:30), again at 15:05 and at
#       shutdown -- incremental, no duplicates -- instead of once at 15:05 (a crash lost the whole day).
#    5. pool_bars_10m_*.csv : the same bars aggregated into exact 10-min bars (09:15-based buckets, VWAP at the
#       bucket end). spot_bars_*.csv : Sensex index 5m and 10m bars (one extra history call per flush).
#    6. vwap_research_*.csv has 6 more columns: DPCR slope (carried, fresh-window) and the 9-min OI-flow tier.
# =============================================================================
VWAP_RES_FILE  = f"vwap_research_{_FILE_STEM}_{_SERIES_CODE}_{_BROKER_TAG}.csv"
POOL_BARS_FILE = f"pool_bars_{_FILE_STEM}_{_SERIES_CODE}_{_BROKER_TAG}.csv"
BARS10_FILE    = f"pool_bars_10m_{_FILE_STEM}_{_SERIES_CODE}_{_BROKER_TAG}.csv"      # v8.1.1
SPOT_BARS_FILE = f"spot_bars_{_FILE_STEM}_{_SERIES_CODE}_{_BROKER_TAG}.csv"           # v8.1.1
_VWAP_RES_HDR = ("ts,run_id,bot,gate_state,locked_side,role,side,otm,symbol,strike,bar_time,"
                 "open,high,low,close,volume,vwap_session,dist_session,in_band,"
                 "vwap_roll,dist_roll,roll_bars,vwap_pool,dist_pool,pool_bars,pool_first_bar,"
                 "spot,dpcr_carried,dpcr_reset,dpcr_age_s,vix,"
                 "dpcr_slope3,dpcr_slope_label,dpcr_reset_slope3,flow_tier,flow_net_supportive,flow_minutes,"
                 "zdir_dev,zdir_thr,zdir_side,zdir_allow")
_POOL_BARS_HDR = "run_id,symbol,bar_time,open,high,low,close,volume,vwap_session"
_BARS10_HDR = "run_id,symbol,bar_time,open,high,low,close,volume,vwap_session,n_bars"
_SPOT_BARS_HDR = "run_id,tf_min,bar_time,open,high,low,close,volume"
_V81_RESET_HIST = []        # v8.1.1: fresh-window DPCR per reading (same cadence as _BOTG_DPCR_HISTORY)
_V81_DPCR = {"carried": None, "reset": None, "t": 0.0}     # filled by get_current_dpcr()
_V81_RES_LAST_BAR = {}      # symbol -> last bar_time already written
_V81_POOL_FIRST = {}        # symbol -> bar_time of the first closed bar seen in the pool
_V81_ERR = {"n": 0}
_V81_STATE = {"bars_dumped": False, "preopen_last_log": 0.0, "preopen_last_hb": 0.0,
              "flushed": set(), "keys5": set(), "keys10": set(), "keys_spot": set()}


def _v81_err(where, e):
    """Log research / gate errors (at most 5 per run) -- they must never touch trading."""
    _V81_ERR["n"] += 1
    if _V81_ERR["n"] <= 5:
        log(f"v8.1 | {where} error (ignored, log-only): {e}")


def _v81_preopen_wait():
    """v8.1: True while the clock is before BOTG_PREOPEN_RESUME_HHMMSS -- the main loop then
    skips this cycle (no quote / history calls, no [DATA FETCH ERROR] / [WAITING] lines).
    Never gates when a position is open (restored from state) or after the resume time."""
    try:
        now_dt = datetime.now()
        h, m, s = [int(x) for x in BOTG_PREOPEN_RESUME_HHMMSS.split(":")]
        resume = now_dt.replace(hour=h, minute=m, second=s, microsecond=0)
        if now_dt >= resume:
            return False
        if any(b.get("trade_open") for b in BOTS):
            return False
        t = time.time()
        if t - _V81_STATE["preopen_last_log"] >= BOTG_PREOPEN_STATUS_SEC:
            log(f"PRE-OPEN      | waiting for the market -- data calls resume at {BOTG_PREOPEN_RESUME_HHMMSS} "
                f"(no fetches until then, v8.1)")
            _V81_STATE["preopen_last_log"] = t
        if t - _V81_STATE["preopen_last_hb"] >= 60:
            try:
                with open(HEARTBEAT_FILE, "w") as _hb:
                    _hb.write(str(t))
            except Exception:
                pass
            _V81_STATE["preopen_last_hb"] = t
        time.sleep(min(10.0, max(1.0, (resume - now_dt).total_seconds())))
        return True
    except Exception as e:
        _v81_err("pre-open gate", e)
        return False


def _v81_vwap_of(df, lo, hi):
    """Volume-weighted typical price of rows lo:hi (positional), or None."""
    sub = df.iloc[lo:hi]
    if len(sub) == 0:
        return None
    tp = (sub["high"] + sub["low"] + sub["close"]) / 3
    vol = sub["volume"].fillna(0)
    v = float(vol.sum())
    if v <= 0:
        return None
    return float((tp * vol).sum() / v)


def _v81_fmt(x, nd=2):
    return "" if x is None or (isinstance(x, float) and x != x) else f"{x:.{nd}f}"


def _v81_research_tick(bot, spot):
    """v8.1 (log-only): VWAP research rows for BOT_G's pool strikes on BOTH sides, including while the
    lock is NOT_LOCKED / PAUSED / FALLING_BLOCK, when the normal scan does not run."""
    if not BOTG_VWAP_RESEARCH_ENABLED or not spot:
        return
    if bot.get("early_slot") or bot.get("trade_open"):
        return
    hh = hhmm()
    if hh >= BOTG_V81_BARS_DUMP_HHMM and not _V81_STATE["bars_dumped"]:
        _v81_dump_pool_bars()
    if hh < BOTG_VWAP_RESEARCH_START_HHMM or hh >= BOTG_ENTRY_CUTOFF_HHMM:
        return
    pool = bot.get("otm_pool") or list(BOTG_VWAP_RESEARCH_DEFAULT_POOL)
    locked = bot.get("locked_side")
    if locked is None:
        gate = "NOT_LOCKED"
    elif not bot.get("_botg_veto_ok", False):
        gate = "PAUSED"
    elif bot.get("_botg_falling_blocked"):
        gate = "FALLING_BLOCK"
    else:
        gate = "SCANNING"
    dp_age = (time.time() - _V81_DPCR["t"]) if _V81_DPCR["t"] else None
    # v8.1.1: DPCR slope (decision series, same definition as the veto: change over BOTG_DPCR_LOOKBACK_CANDLES
    # readings) and slope of the fresh-window series; 9-min OI-flow (same function BOT_GE uses).
    try:
        _sl_lbl, _sl_cur, _sl_chg = compute_bot_g_dpcr_slope(list(_BOTG_DPCR_HISTORY), bot.get("vix_value"))
    except Exception:
        _sl_lbl, _sl_chg = None, None
    _rh = _V81_RESET_HIST
    _lb = BOTG_DPCR_LOOKBACK_CANDLES
    _rs_chg = (_rh[-1] - _rh[-1 - _lb]) if (len(_rh) > _lb and _rh[-1] is not None and _rh[-1 - _lb] is not None) else None
    try:
        _flow = compute_bot_g_flow()
    except Exception:
        _flow = None
    _zd84 = _v84_zdir(spot, _sl_chg)   # v8.4 (log-only)
    rows = []
    for side in ("CE", "PE"):
        for otm in pool:
            sym = get_option_symbol_bot_g(spot, side, otm_steps=otm, bot_name=bot["name"], _log=False)
            slot = _BOTG_OPT_CACHE.get(sym)
            forced = _bot_g_should_force_5m_refresh(sym)
            if forced or slot is None or slot.get("df5") is None:
                df5 = fetch_option_history_5m(fyers, sym, force_refresh=True)
            else:
                df5 = slot["df5"]
            if df5 is None or len(df5) < 2:
                continue
            n_closed = len(df5) - 1                       # last row is the forming bar
            keys = [ix.strftime("%Y-%m-%d %H:%M") for ix in df5.index[:n_closed]]
            last_done = _V81_RES_LAST_BAR.get(sym)
            if last_done is None:
                todo = [n_closed - 1]                    # first sight: only the latest closed bar
            else:
                todo = [i for i in range(n_closed) if keys[i] > last_done]
            if not todo:
                continue
            first = _V81_POOL_FIRST.setdefault(sym, keys[todo[0]])
            first_pos = next((i for i, k in enumerate(keys) if k >= first), 0)
            for i in todo:
                r = df5.iloc[i]
                close_ = float(r["close"])
                v_sess = r.get("vwap")
                v_sess = None if v_sess is None or v_sess != v_sess else float(v_sess)
                v_roll = _v81_vwap_of(df5, max(0, i + 1 - BOTG_VWAP_RESEARCH_ROLL_BARS), i + 1)
                v_pool = _v81_vwap_of(df5, first_pos, i + 1) if i >= first_pos else None
                d_sess = None if v_sess is None else close_ - v_sess
                d_roll = None if v_roll is None else close_ - v_roll
                d_pool = None if v_pool is None else close_ - v_pool
                in_band = ("" if d_sess is None else
                           int(BOTG_NEAR_VWAP_LOWER_PTS <= d_sess <= BOTG_NEAR_VWAP_UPPER_PTS))
                strike = "".join(ch for ch in sym.split("SENSEX", 1)[-1][5:] if ch.isdigit()) if "SENSEX" in sym else ""
                try:
                    _ft, _fn = classify_bot_g_flow(side, _flow)
                except Exception:
                    _ft, _fn = "NA", None
                rows.append(",".join([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"), RUN_ID, bot["name"], gate, str(locked or ""),
                    ("LOCKED" if side == locked else ("OTHER" if locked else "")), side, str(otm), sym, strike, keys[i],
                    _v81_fmt(float(r["open"])), _v81_fmt(float(r["high"])), _v81_fmt(float(r["low"])), _v81_fmt(close_),
                    _v81_fmt(float(r["volume"]) if r["volume"] == r["volume"] else None, 0),
                    _v81_fmt(v_sess), _v81_fmt(d_sess), str(in_band),
                    _v81_fmt(v_roll), _v81_fmt(d_roll), str(min(BOTG_VWAP_RESEARCH_ROLL_BARS, i + 1)),
                    _v81_fmt(v_pool), _v81_fmt(d_pool), str(i + 1 - first_pos if i >= first_pos else 0), first,
                    _v81_fmt(spot), _v81_fmt(_V81_DPCR["carried"], 3), _v81_fmt(_V81_DPCR["reset"], 3),
                    _v81_fmt(dp_age, 0), _v81_fmt(bot.get("vix_value")),
                    _v81_fmt(_sl_chg, 3), str(_sl_lbl or ""), _v81_fmt(_rs_chg, 3)]
                    + [str(_ft), _v81_fmt(_fn, 0), _v81_fmt(_flow["minutes"], 1) if _flow else ""]
                    + _v84_zcols(_zd84, side)) + "\n")
                _V81_RES_LAST_BAR[sym] = keys[i]
    if rows:
        _append_csv(VWAP_RES_FILE, _VWAP_RES_HDR, rows)


def _v81_naive(ts):
    """tz-naive wall-clock Timestamp for comparisons with datetime.now()."""
    return ts.tz_localize(None) if getattr(ts, "tzinfo", None) is not None else ts


def _v81_bucket10(ts):
    """10-min bucket number of a bar start time, counted from 09:15."""
    return ((ts.hour * 60 + ts.minute) - (9 * 60 + 15)) // 10


def _v81_closed_rows(df, final):
    """Rows of a cached 5m frame that are certainly complete. All but the last row (the forming bar; on
    RMoney a synthetic zero-volume placeholder). With final=True the last row too, but only once its own 5
    minutes are over by the wall clock."""
    if df is None or len(df) == 0:
        return df
    if final:
        end = _v81_naive(df.index[-1]) + pd.Timedelta(minutes=5)
        if pd.Timestamp(datetime.now()) >= end:
            return df
    return df.iloc[:-1]


def _v81_agg10(df5c, final):
    """Exact 10-min bars from CLOSED 5m rows. [(bucket_start, o, h, l, c, v, vwap_at_end, n_bars)].
    A bucket is written when both 5m halves are present, or when it is provably over: a later row exists
    (RMoney has no 5m row for a half-hour without trades) or, at the final dump, the wall clock is past it."""
    out = []
    if df5c is None or len(df5c) == 0:
        return out
    groups = {}
    for pos, ix in enumerate(df5c.index):
        groups.setdefault(_v81_bucket10(ix), []).append(pos)
    last_bk = max(groups)
    now_bk = _v81_bucket10(pd.Timestamp(datetime.now()))
    for bk, poss in sorted(groups.items()):
        if len(poss) < 2 and not (bk < last_bk or (final and bk < now_bk)):
            continue
        sub = df5c.iloc[poss]
        vol = sub["volume"].fillna(0)
        vw = sub["vwap"].iloc[-1] if "vwap" in sub.columns else None
        vw = None if vw is None or vw != vw else float(vw)
        out.append((sub.index[0].strftime("%Y-%m-%d %H:%M"), float(sub["open"].iloc[0]), float(sub["high"].max()),
                    float(sub["low"].min()), float(sub["close"].iloc[-1]), float(vol.sum()), vw, len(sub)))
    return out


def _v81_spot_5m_df():
    """Sensex index 5m bars (native 5m; the same BSE future-bar guard as fetch_option_history_5m)."""
    raw = helper.getHistorical("BSE:SENSEX-INDEX", 5, _v82_lookback_days(), fyers)
    if raw is None or not hasattr(raw, "columns") or len(raw) == 0:
        return None
    df = raw[raw.index.date == raw.index[-1].date()].copy()
    _now_ist = pd.Timestamp.now(tz="Asia/Kolkata")
    _idx_ist = (df.index.tz_convert("Asia/Kolkata") if getattr(df.index, "tz", None) is not None
                else df.index.tz_localize("Asia/Kolkata"))
    return df.loc[_idx_ist <= _now_ist]


def _v81_flush_spot(final):
    """Sensex index 5m + 10m bars, appended once each (dedup by timeframe + bar time). One history call."""
    df = _v81_spot_5m_df()
    if df is None or len(df) == 0:
        return 0
    today = datetime.now().date()
    df = df[df.index.date == today]
    if len(df) == 0:
        return 0
    closed = _v81_closed_rows(df, final)
    rows = []

    def _row(tf, bt, o, h, l, c, v):
        return ",".join([RUN_ID, str(tf), bt, _v81_fmt(o), _v81_fmt(h), _v81_fmt(l), _v81_fmt(c), _v81_fmt(v, 0)]) + "\n"
    for ix, r in closed.iterrows():
        k = (5, ix.strftime("%Y-%m-%d %H:%M"))
        if k in _V81_STATE["keys_spot"]:
            continue
        _V81_STATE["keys_spot"].add(k)
        v = float(r["volume"]) if "volume" in closed.columns and r["volume"] == r["volume"] else None
        rows.append(_row(5, k[1], float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"]), v))
    for bt, o, h, l, c, v, _vw, _n in _v81_agg10(closed, final):
        k = (10, bt)
        if k in _V81_STATE["keys_spot"]:
            continue
        _V81_STATE["keys_spot"].add(k)
        rows.append(_row(10, bt, o, h, l, c, v))
    if rows:
        _append_csv(SPOT_BARS_FILE, _SPOT_BARS_HDR, rows)
    return len(rows)


def _v81_flush_bars(final=False):
    """v8.1.1 (log-only): append the not-yet-written CLOSED 5m bars of every cached pool strike (with the
    session VWAP) to pool_bars_*.csv, the exact 10-min aggregates to pool_bars_10m_*.csv, and the index bars to
    spot_bars_*.csv. Reads the in-memory cache only, except one spot-history call."""
    rows5, rows10, nsym = [], [], 0
    for sym, slot in list(_BOTG_OPT_CACHE.items()):
        df5 = slot.get("df5") if isinstance(slot, dict) else None
        if df5 is None or len(df5) == 0:
            continue
        nsym += 1
        closed = _v81_closed_rows(df5, final)
        for ix, r in closed.iterrows():
            bt = ix.strftime("%Y-%m-%d %H:%M")
            if (sym, bt) in _V81_STATE["keys5"]:
                continue
            _V81_STATE["keys5"].add((sym, bt))
            vw = r.get("vwap")
            vw = None if vw is None or vw != vw else float(vw)
            rows5.append(",".join([RUN_ID, sym, bt,
                                   _v81_fmt(float(r["open"])), _v81_fmt(float(r["high"])),
                                   _v81_fmt(float(r["low"])), _v81_fmt(float(r["close"])),
                                   _v81_fmt(float(r["volume"]) if r["volume"] == r["volume"] else None, 0),
                                   _v81_fmt(vw)]) + "\n")
        for bt, o, h, l, c, v, vw, n in _v81_agg10(closed, final):
            if (sym, bt) in _V81_STATE["keys10"]:
                continue
            _V81_STATE["keys10"].add((sym, bt))
            rows10.append(",".join([RUN_ID, sym, bt, _v81_fmt(o), _v81_fmt(h), _v81_fmt(l), _v81_fmt(c),
                                    _v81_fmt(v, 0), _v81_fmt(vw), str(n)]) + "\n")
    if rows5:
        _append_csv(POOL_BARS_FILE, _POOL_BARS_HDR, rows5)
    if rows10:
        _append_csv(BARS10_FILE, _BARS10_HDR, rows10)
    nspot = 0
    try:
        nspot = _v81_flush_spot(final)
    except Exception as e:
        _v81_err("spot bars flush", e)
    log(f"v8.1.1 | bars {'FINAL ' if final else ''}flushed: +{len(rows5)} 5m rows, +{len(rows10)} 10m rows "
        f"({nsym} symbols), +{nspot} spot rows -> {POOL_BARS_FILE} / {BARS10_FILE} / {SPOT_BARS_FILE}")


def _v81_dump_pool_bars():
    """Final flush (15:05 or shutdown). Kept under its v8.1 name; runs at most once."""
    if _V81_STATE["bars_dumped"]:
        return
    try:
        _v81_flush_bars(True)
        _V81_STATE["bars_dumped"] = True
    except Exception as e:
        _v81_err("pool bars dump", e)


def _v81_maybe_flush():
    """Called after every BOT_G entry cycle: scheduled intraday flushes + the 15:05 final flush."""
    if not BOTG_VWAP_RESEARCH_ENABLED:
        return
    hh = hhmm()
    due = [h for h in BOTG_V811_BARS_FLUSH_HHMM if h <= hh and h not in _V81_STATE["flushed"]]
    if due:
        _V81_STATE["flushed"].update(due)       # one flush also covers flushes missed after a restart
        if hh < BOTG_V81_BARS_DUMP_HHMM:
            try:
                _v81_flush_bars(False)
            except Exception as e:
                _v81_err("bars flush", e)
    if hh >= BOTG_V81_BARS_DUMP_HHMM and not _V81_STATE["bars_dumped"]:
        _v81_dump_pool_bars()


_bot_g_try_entry_core = _bot_g_try_entry   # v8.1: the Nifty vE6.2 function, untouched


def _bot_g_try_entry(bot, df3, spot, stale, now):
    """v8.1 wrapper: runs the unchanged entry logic, then the log-only VWAP research tick."""
    try:
        return _bot_g_try_entry_core(bot, df3, spot, stale, now)
    finally:
        try:
            if not stale:
                _v81_research_tick(bot, spot)
        except Exception as _e81:
            _v81_err("research tick", _e81)
        try:
            _v81_maybe_flush()          # v8.1.1: also while a trade is open / on a stale cycle (cache only)
        except Exception as _e81:
            _v81_err("bars flush", _e81)

_TRACK_HDR = "ts,kind,ref_id,bot,symbol,side,ref_price,elapsed_sec,ltp"
_TRACK_SUM_HDR = ("ts,kind,ref_id,bot,symbol,side,ref_price,entry,sl,p1,p2,max_ltp,max_sec,"
                  "min_ltp,min_sec,ltp_5m,ltp_15m,ltp_30m,outcome,outcome_sec,polls,day_type,"
                  "pct_from_open,cflow9_dce,status")
_BOTG_TRACK = []
_TRACK_STATE = {"last": 0.0}
_BOTG_DAY = {"date": None, "open": None, "high": None, "low": None, "hist": [], "open_915": False, "ext_1015": None, "ext_1015_hhmm": None}   # v8.3: ext_1015   # v8.2: open_915
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


def _v831_915_closed(df3):
    """v8.3.1: True once today's 09:15 3m candle has CLOSED, i.e. df3's last row is stamped 09:18 or later.
    Callers only use it after zlm.candle_915(df3) found today's 09:15 candle, so the last row is also today's."""
    try:
        _last = df3.index[-1]
        if getattr(_last, "tzinfo", None) is not None:
            _last = _last.tz_convert("Asia/Kolkata")
        return (_last.hour * 60 + _last.minute) >= 9 * 60 + 18
    except Exception:
        return False


_V831_GAP = {}


def _v831_gap_recheck(bot, df3):
    """v8.3.1: re-run the gap check once per day per bot on the CLOSED 09:15 candle (from 09:18) and correct gap_day / gap_pct
    if the 09:15 value (taken from a forming candle) differed. Never raises."""
    try:
        _key = (date.today(), bot.get("name"))
        if _key in _V831_GAP or hhmm() < 918 or df3 is None or not _zlm.candle_915(df3) or not _v831_915_closed(df3):
            return
        _V831_GAP[_key] = True
        _g, _p = detect_bot_g_gap_day(df3, bot.get("name") or "BOT_G")
        if _p is None:
            return
        if (_g, _p) != (bot.get("gap_day"), bot.get("gap_pct")):
            log(f"{bot.get('name')} v8.3.1 GAP RECHECK | closed 09:15 candle: gap {_p}% day={'GAP' if _g else 'NORMAL'} "
                f"(was {bot.get('gap_pct')}% day={'GAP' if bot.get('gap_day') else 'NORMAL'}) -> corrected")
            bot["gap_day"], bot["gap_pct"] = _g, _p
    except Exception as _e831:
        log(f"v8.3.1 GAP RECHECK | error (ignored): {_e831}")


def _day_track(spot, df3=None):   # v8.2: df3 -> 09:15 candle open (v-E32)
    """v-E20: day open (first reading at/after 09:15 -- approximate after a
    mid-day restart), running high/low and a 40-min spot history."""
    if not spot or spot <= 0:
        return
    st = _BOTG_DAY
    if st["date"] != date.today():
        st.update(date=date.today(), open=None, high=None, low=None, hist=[], open_915=False, ext_1015=None, ext_1015_hhmm=None,
                  ref915=None, high_t=None, low_t=None)   # v8.3.3
    if hhmm() < 915:
        return
    now = time.time()
    if st["open"] is None:
        st["open"] = spot
        log(f"vE6.2 DAY OPEN | first spot reading {spot} used as day open (v-E20)")
    if not st.get("open_915") and df3 is not None:   # v8.2 (v-E32): the 09:15 3m candle open replaces the first reading
        try:
            _c915 = _zlm.candle_915(df3)
            if _c915 and _v831_915_closed(df3):   # v8.3.1: only once the 09:15 candle has closed
                log(f"v8.2 DAY OPEN | 09:15 3m candle open {round(_c915[0], 2)} used (first reading was {round(st['open'], 2)}) (v-E32)")
                st["open"] = _c915[0]
                st["open_915"] = True
        except Exception as _e82:
            log(f"v8.2 DAY OPEN | 09:15 candle lookup error (ignored): {_e82}")
    if V833_COMMON_ANCHOR and st.get("ref915") is None and df3 is not None:   # v8.3.3: closed 09:15 3m candle close = common first-anchor reference
        try:
            _c915r = _zlm.candle_915(df3)
            if _c915r and _v831_915_closed(df3):
                st["ref915"] = round(_c915r[3], 2)
                log(f"v8.3.3 COMMON ANCHOR | closed 09:15 3m candle close {st['ref915']} (live spot {round(spot, 2)}) = first-anchor reference")
        except Exception as _e833:
            log(f"v8.3.3 COMMON ANCHOR | 09:15 candle lookup error (ignored): {_e833}")
    if st["high"] is None or spot > st["high"]:   # v8.3.3: when the day high / low was made (log-only tags)
        st["high_t"] = now
    if st["low"] is None or spot < st["low"]:
        st["low_t"] = now
    st["high"] = spot if st["high"] is None else max(st["high"], spot)
    st["low"] = spot if st["low"] is None else min(st["low"], spot)
    if not st["hist"] or now - st["hist"][-1][0] >= 15:
        st["hist"].append((now, spot))
    st["hist"] = [x for x in st["hist"] if x[0] >= now - 40 * 60]
    if st.get("ext_1015") is None and st["open"] and hhmm() >= 1015:   # v8.3: move from the day open to the first reading at/after 10:15
        st["ext_1015"] = round(100.0 * (spot - st["open"]) / st["open"], 3)
        st["ext_1015_hhmm"] = hhmm()
        log(f"v8.3 EXT1015 | {st['ext_1015']:+.3f}% from day open {round(st['open'], 2)} (read at {hhmm()}) (log-only)")


def _v82_lookback_days():
    """v8.2 (v-E29): spot-history lookback in calendar days = max(config, days back to the previous BSE trading day + 1)."""
    try:
        _prev = _bse_trading_day_on_or_before(date.today() - timedelta(days=1))
        _need = (date.today() - _prev).days + 1
    except Exception:
        _need = BOTG_HISTORY_LOOKBACK_DAYS
    return max(BOTG_HISTORY_LOOKBACK_DAYS, _need, 2)


ZLM_FILE = f"zlm_shadow_{_FILE_STEM}_{_BROKER_TAG}.csv"   # v8.2
_V82_ZLM = {"cfg": False}


def _v82_zlm_write(line):
    _append_csv(ZLM_FILE, _zlm.CSV_HDR, [line])


def _v82_zlm_hook(spot, df3):
    """v8.2 (v-E31): ZLM shadow, LOG-ONLY. Never places an order, never touches bot state; any error is logged and ignored."""
    if not ZLM_SHADOW_ENABLED:
        return
    try:
        if not _V82_ZLM["cfg"]:
            _zlm.configure(
                log, lambda s: get_multi_ltp([s]).get(s),
                lambda sp, side: get_option_symbol_bot_g(sp, side, 0, "ZLM", _log=False),
                _v82_zlm_write, _BROKER_TAG,
                {k: globals()[k] for k in ("ZLM_SHADOW_ENABLED", "ZLM_MARGIN_PTS", "ZLM_BAND_MAX_PTS", "ZLM_ENTRY_CUTOFF_HHMM",
                                           "ZLM_EXIT_HHMM", "ZLM_TRAIL_ARM_PCT", "ZLM_TRAIL_PCT", "ZLM_G_MAX_FLIPS", "ZLM_LOT_QTY",
                                           "V86_ZLM_REF_CANDLE", "V86_ZLM_REF_WAIT_UNTIL_HHMM")})
            _V82_ZLM["cfg"] = True
        _bg = next((b for b in BOTS if b.get("name") == "BOT_G"), None)
        _zlm.on_tick(spot, _bg.get("locked_side") if _bg else None, df3)
    except Exception as _e82:
        log(f"v8.2 ZLM | error (ignored, log-only): {_e82}")


TAG_FILE = f"setup_tags_{_FILE_STEM}_{_BROKER_TAG}.csv"   # v8.3
WHATIF_FILE = f"exit_whatif_{_FILE_STEM}_{_BROKER_TAG}.csv"   # v8.3.2
PAUSECF_FILE = f"pause_cf_{_FILE_STEM}_{_BROKER_TAG}.csv"   # v8.9
_V83_ERR = {"n": 0}
_V833_COLS = ["spot_chg15", "spot_chg30", "pullback_from_high", "mins_since_high", "bounce_from_low", "mins_since_low", "fk_r1",
              "dpcr_carried", "dpcr_fresh", "fresh_vs_lock", "early_flow_tier", "early_flow_pass"]   # v8.3.3
_TAG_HDR = ",".join(
    ["date", "time", "event", "trade_id", "symbol", "side", "otm", "locked_side", "spot", "day_open", "gap_pct",
     "ext_1015_pct", "ext_src", "pct_from_open", "day_type", "entry", "sl", "stop_pts", "stop_pct", "wide_flag"]
    + [f"cap{c}_pts" for c in TAG_CAP_PCTS] + [f"lots_{b // 1000}k" for b in TAG_RISK_BUDGETS] + ["risk_inr_max_lots"]
    + [f"skip_t{h}" for h in TAG_START_HHMMS] + [f"big_{str(p).replace('.', '')}" for p in TAG_BIG_PCTS]
    + [f"skip_c{str(p).replace('.', '')}_t{TAG_COND_START_HHMM}" for p in TAG_BIG_PCTS] + _V833_COLS + ["detail"])


def _v83_tag(event, bot, otm=None, symbol="", side="", spot=None, entry=None, sl=None, detail=""):
    """v8.3: LOG-ONLY setup tag row. Never touches bot state or orders; any error is logged (max 5/run) and ignored."""
    if not TAG_LOG_ENABLED:
        return
    try:
        _now = datetime.now()
        _hm = _now.hour * 100 + _now.minute
        _d = _BOTG_DAY if _BOTG_DAY.get("date") == date.today() else {}
        _o = _d.get("open")
        _pfo = round(100.0 * (spot - _o) / _o, 3) if (spot and _o) else ""
        _gap = bot.get("gap_pct")
        _gap = round(float(_gap), 3) if _gap is not None else ""
        _ext = _d.get("ext_1015")
        _ext_src = "" if _ext is None else ("ok" if (_d.get("ext_1015_hhmm") or 9999) <= 1018 else "late")
        try:
            _dt = _day_type_diag(spot)["day_type"] if spot else ""
        except Exception:
            _dt = ""
        _sp = _spc = _wide = _risk = ""
        _caps = [""] * len(TAG_CAP_PCTS)
        _lots = [""] * len(TAG_RISK_BUDGETS)
        if entry and sl is not None and entry > 0:
            _sp = round(entry - sl, 2)
            _spc = round(100.0 * _sp / entry, 2)
            _wide = int(_spc > TAG_WIDE_STOP_PCT)
            _caps = [round(min(_sp, entry * c / 100.0), 2) for c in TAG_CAP_PCTS]
            _lots = [(min(TAG_MAX_LOTS, int(b // (_sp * TAG_LOT_QTY))) if _sp > 0 else TAG_MAX_LOTS) for b in TAG_RISK_BUDGETS]
            _risk = round(_sp * TAG_LOT_QTY * TAG_MAX_LOTS)
        _skip_t = [int(_hm < h) for h in TAG_START_HHMMS]
        _big = [int((_gap != "" and abs(_gap) >= p) or (_ext is not None and abs(_ext) >= p)) for p in TAG_BIG_PCTS]
        _skip_c = [int(b and _hm < TAG_COND_START_HHMM) for b in _big]
        _row = ([_now.strftime("%Y-%m-%d"), _now.strftime("%H:%M:%S"), event,
                 (bot.get("trade_id") if event == "ENTRY" else ""), symbol, side, otm, bot.get("locked_side") or "",
                 round(spot, 2) if spot else "", round(_o, 2) if _o else "", _gap,
                 _ext if _ext is not None else "", _ext_src, _pfo, _dt,
                 entry if entry is not None else "", round(sl, 2) if sl is not None else "", _sp, _spc, _wide]
                + _caps + _lots + [_risk] + _skip_t + _big + _skip_c + _v833_cols(bot, side, spot) + [detail])
        _append_csv(TAG_FILE, _TAG_HDR, [",".join(str(v).replace(",", ";") for v in _row) + "\n"])
    except Exception as _e83:
        _V83_ERR["n"] += 1
        if _V83_ERR["n"] <= 5:
            log(f"v8.3 TAG | {event} error (ignored, log-only): {_e83}")


_V832_ERR = {"n": 0}


def _v832_err(where, e):
    _V832_ERR["n"] += 1
    if _V832_ERR["n"] <= 5:
        log(f"v8.3.2 {where} error (ignored): {e}")


def _v832_gap_mark(bot):
    """v8.3.2: seconds since this open trade's previous GOOD LTP tick (first tick: since entry). Read by the paper stop-fill rule."""
    try:
        _t = time.time()
        _prev = bot.get("_v832_prev_t")
        _e = bot.get("entry_epoch") or _t
        if not _prev or _prev < _e:
            _prev = _e
        bot["_v832_gap_s"] = _t - _prev
        bot["_v832_prev_t"] = _t
    except Exception as _e:
        bot["_v832_gap_s"] = 0.0
        _v832_err("gap mark", _e)


def _v832_wi_start(bot, side, symbol):
    """v8.3.2: LOG-ONLY exit what-if, start. Never touches bot state or orders."""
    if not WHATIF_ENABLED:
        return
    try:
        _p1, _p2 = _botg_targets(bot, bot["entry"], bot["risk_pts"])
        _wi.start(bot["trade_id"], bot["name"], side, symbol, bot["entry"], bot["risk_pts"], bot["qty"],
                  bot.get("entry_epoch") or time.time(), bot.get("entry_time", ""), _p1, _p2, bot["be_level"], bot["arm_level"],
                  BOTG_PARTIAL_R1_FRACTION, BOTG_PARTIAL_R15_FRACTION, _botg_tsl_buffer(bot), LOT_SIZE,
                  max_hold_min=bot.get("max_hold_min", BOTG_MAX_HOLD_MINUTES_INITIAL), eb_r=WHATIF_EB_R, eb_lots=WHATIF_EB_LOTS,
                  ts_sec=WHATIF_TS_SEC, ts_r=WHATIF_TS_R, gap_fill_sec=(V832_GAP_FILL_SEC if V832_GAP_FILL_ENABLED else 10 ** 9), log=log)
    except Exception as _e:
        _v832_err("whatif start", _e)


def _v832_wi_tick(bot, ltp):
    if not WHATIF_ENABLED:
        return
    try:
        _wi.tick(bot.get("trade_id"), ltp, time.time())   # the bot's own clock (same clock as entry_epoch)
    except Exception as _e:
        _v832_err("whatif tick", _e)


def _v832_wi_finish(bot, exit_price, trade_pnl, reason):
    if not WHATIF_ENABLED:
        return
    try:
        _wi.finish(bot.get("trade_id"), exit_price, trade_pnl, reason, WHATIF_FILE, log=log)
    except Exception as _e:
        _v832_err("whatif finish", _e)


_V833 = {"anchor_called": False, "wait_logged": False, "err": 0}


def _v833_err(where, e):
    _V833["err"] += 1
    if _V833["err"] <= 5:
        log(f"v8.3.3 {where} error (ignored): {e}")


def _v833_anchor_ref_for_call(gap_day):
    """v8.3.3: the closed 09:15 3m candle close to use for the FIRST DPCR anchor (same on both brokers), else None -> the option-chain
    module falls back to the live spot. Normal days only (the gap-day 10:00 anchor is unchanged) and only before V833_ANCHOR_REF_UNTIL_HHMM
    (a later restart anchors on the live spot)."""
    try:
        ref = None
        if V833_COMMON_ANCHOR and not gap_day and hhmm() < V833_ANCHOR_REF_UNTIL_HHMM and _BOTG_DAY.get("date") == date.today():
            ref = _BOTG_DAY.get("ref915")
        if not _V833["anchor_called"]:
            _V833["anchor_called"] = True
            log(f"v8.3.3 COMMON ANCHOR | first DPCR call at {hhmm()}: reference {'closed 09:15 candle close ' + str(ref) if ref else 'NONE (live spot used)'}"
                f"{' [gap day: unchanged]' if gap_day else ''}")
        return ref
    except Exception as _e:
        _v833_err("anchor ref", _e)
        return None


def _v833_anchor_wait(bot):
    """v8.3.3: True while the common first anchor is waiting for the CLOSED 09:15 candle (normal day, before V833_ANCHOR_WAIT_UNTIL_HHMM, no DPCR
    call yet). Evaluated BEFORE is_new_3m_candle(), so no candle bucket is consumed while waiting."""
    try:
        if not V833_COMMON_ANCHOR or bot.get("gap_day") or _V833["anchor_called"]:
            return False
        if hhmm() >= V833_ANCHOR_WAIT_UNTIL_HHMM or _BOTG_DAY.get("ref915") is not None:
            return False
        if not _V833["wait_logged"]:
            _V833["wait_logged"] = True
            log(f"v8.3.3 COMMON ANCHOR | waiting for the closed 09:15 3m candle (DPCR fetch deferred, max until {V833_ANCHOR_WAIT_UNTIL_HHMM})")
        return True
    except Exception as _e:
        _v833_err("anchor wait", _e)
        return False


def _v833_spot_at(ts, tol=45):
    """v8.3.3: spot from the 15-s day history at/just before epoch `ts` (within `tol` s), else None."""
    h = _BOTG_DAY.get("hist") or []
    best = None
    for _t, _s in h:
        if _t <= ts:
            best = (_t, _s)
        else:
            break
    return best[1] if (best and ts - best[0] <= tol) else None


def _v833_cols(bot, side, spot):
    """v8.3.3: LOG-ONLY context columns (order = _V833_COLS). Never raises, never touches state."""
    out = {k: "" for k in _V833_COLS}
    try:
        if not V833_MOM_TAGS:
            return [out[k] for k in _V833_COLS]
        d = _BOTG_DAY if _BOTG_DAY.get("date") == date.today() else {}
        nowt = time.time()
        dt = datetime.now()
        b = nowt - ((dt.minute % 5) * 60 + dt.second + dt.microsecond / 1e6)             # last 5-min bar boundary
        t915 = nowt - ((dt.hour * 3600 + dt.minute * 60 + dt.second) - (9 * 3600 + 15 * 60))

        def _at(ts):
            if ts <= t915 + 45 and d.get("open"):
                return d["open"]                                                           # look-back reaches before the open
            return _v833_spot_at(ts)
        s0 = _at(b)
        chg = {}
        for lb in (15, 30):
            s1 = _at(b - lb * 60)
            chg[lb] = round(s0 - s1, 2) if (s0 is not None and s1 is not None) else None
            out[f"spot_chg{lb}"] = "" if chg[lb] is None else chg[lb]
        if spot and d.get("high") is not None:
            out["pullback_from_high"] = round(d["high"] - spot, 2)
            if d.get("high_t"):
                out["mins_since_high"] = round((nowt - d["high_t"]) / 60.0, 1)
        if spot and d.get("low") is not None:
            out["bounce_from_low"] = round(spot - d["low"], 2)
            if d.get("low_t"):
                out["mins_since_low"] = round((nowt - d["low_t"]) / 60.0, 1)
        if side in ("CE", "PE") and chg[15] is not None and chg[30] is not None:
            _m = V833_FK_MIN_PTS
            out["fk_r1"] = int((chg[15] < -_m and chg[30] < -_m) if side == "CE" else (chg[15] > _m and chg[30] > _m))
        _h = get_bot_g_dpcr_history()
        _cur = _h[-1] if _h else None
        _fresh = _V81_DPCR.get("reset")
        out["dpcr_carried"] = "" if _cur is None else round(_cur, 3)
        out["dpcr_fresh"] = "" if _fresh is None else round(_fresh, 3)
        _ref = bot.get("locked_side") or (side if side in ("CE", "PE") else None)
        if _ref in ("CE", "PE"):
            if _fresh is None:
                out["fresh_vs_lock"] = "NA"
            elif _fresh == 0:
                out["fresh_vs_lock"] = "FLAT"
            else:
                out["fresh_vs_lock"] = "WITH" if ((_fresh > 0) == (_ref == "CE")) else "AGAINST"
        if side in ("CE", "PE"):
            _tier = classify_bot_g_flow(side, compute_bot_g_flow())[0]
            _sg = _cur is not None and ((side == "CE" and _cur > 0) or (side == "PE" and _cur < 0))
            out["early_flow_tier"] = _tier
            out["early_flow_pass"] = int(_tier in BOTGE_ALLOWED_TIERS and _sg)
    except Exception as _e:
        _v833_err("cols", _e)
    return [out[k] for k in _V833_COLS]


def _v84_ctx_zdir(bot, side, spot):
    """v8.4: ' | zdir ...' suffix for the ENTRY CTX line (log-only)."""
    try:
        _h = get_bot_g_dpcr_history()
        _chg = compute_bot_g_dpcr_slope(_h, bot.get("vix_value"))[2] if _h else None
        _z = _v84_zdir(spot, _chg)
        if not _z["ok"]:
            return " | zdir NA"
        return f" | zdir_side={_z['side'] or 'none'} zdir_allow={int(_z['ce'] if side == 'CE' else _z['pe'])} zdir_dev={_z['dev']:+} zdir_thr={_z['thr']}"
    except Exception as _e:
        _v84_err("ctx zdir", _e)
        return ""


def _v833_entry_log(bot, side, spot):
    """v8.3.3: one readable log line with the same context as the ENTRY tag row (log-only)."""
    try:
        if not V833_MOM_TAGS:
            return
        _c = _v833_cols(bot, side, spot)
        log(f"{bot['name']} v8.3.3 ENTRY CTX | {side} " + " ".join(f"{k}={v}" for k, v in zip(_V833_COLS, _c))
            + (" | FALLING-KNIFE R1 flag set (trade taken: early slot / enforcement off)" if _c[_V833_COLS.index("fk_r1")] == 1 else "")
            + _v84_ctx_zdir(bot, side, spot) + _v87_ctx(bot, side, spot) + " (log-only)")
    except Exception as _e:
        _v833_err("entry log", _e)


_V84 = {"err": 0}


def _v84_err(where, e):
    _V84["err"] += 1
    if _V84["err"] <= 5:
        log(f"v8.4 {where} error (ignored): {e}")


def _v84_fk_check(bot, side, spot):
    """v8.4: (block, chg15, chg30). True only for the main slot, when the v8.3.3 falling-knife R1 condition holds. Fail-open on missing data."""
    try:
        if not V84_FK_ENFORCE or bot.get("early_slot") or bot.get("name") not in V84_FK_BOTS:
            return False, None, None
        _c = _v833_cols(bot, side, spot)
        _fk = _c[_V833_COLS.index("fk_r1")]
        return (_fk == 1), _c[_V833_COLS.index("spot_chg15")], _c[_V833_COLS.index("spot_chg30")]
    except Exception as _e:
        _v84_err("fk check", _e)
        return False, None, None


def _v84_zdir(spot, chg3):
    """v8.4 (LOG-ONLY): ZLM-direction view. dict(ok, ref, thr, dev, carried, chg3, ce, pe, side). Never raises, never touches state."""
    out = dict(ok=False, ref=None, thr=None, dev=None, carried=None, chg3=chg3, ce=False, pe=False, side="")
    try:
        if not V84_ZDIR_TAGS or not spot:
            return out
        _cfg = _zlm._C.get("cfg") or {}
        _ref = _zlm._S.get("ref")
        _car = _V81_DPCR.get("carried")
        if _ref is None or not _cfg or _car is None:
            return out
        _n = datetime.now()
        _thr = _zlm._band(_n.hour * 60 + _n.minute) + _cfg["ZLM_MARGIN_PTS"]
        _dev = float(spot) - float(_ref)
        _ch = 0.0 if chg3 is None else float(chg3)
        _ce = (_dev >= _thr) and (_car >= V84_ZDIR_FLOOR) and (_ch >= -V84_ZDIR_FALL_TOL)
        _pe = (_dev <= -_thr) and (_car <= -V84_ZDIR_FLOOR) and (_ch <= V84_ZDIR_FALL_TOL)
        out.update(ok=True, ref=round(_ref, 2), thr=round(_thr, 1), dev=round(_dev, 1), carried=round(_car, 3), ce=bool(_ce), pe=bool(_pe),
                   side="CE" if _ce else ("PE" if _pe else ""))
    except Exception as _e:
        _v84_err("zdir", _e)
    return out


def _v84_zcols(z, side):
    """v8.4: the 4 vwap_research columns (zdir_dev, zdir_thr, zdir_side, zdir_allow for `side`); blanks when unavailable."""
    if not z.get("ok"):
        return ["", "", "", ""]
    return [str(z["dev"]), str(z["thr"]), z["side"], str(int(z["ce"] if side == "CE" else z["pe"]))]


def _v84_zdir_log(bot, spot, dpcr_history):
    """v8.4 (LOG-ONLY): one line per DPCR candle comparing the zone gate with the ZLM-direction view."""
    try:
        if not V84_ZDIR_TAGS:
            return
        _sl, _cur, _chg = compute_bot_g_dpcr_slope(dpcr_history, bot.get("vix_value"))
        _z = _v84_zdir(spot, _chg)
        if not _z["ok"]:
            return
        _lk = bot.get("locked_side")
        _zone_ok = bool(_lk in ("CE", "PE") and bot.get("_botg_veto_ok") and not bot.get("_botg_falling_blocked"))
        _flag = ""
        if _z["side"] and not (_zone_ok and _lk == _z["side"]):
            _flag = " | ZDIR_ONLY (zone gate would NOT allow this side)"
        elif _zone_ok and _lk != _z["side"]:
            _flag = " | ZONE_ONLY (ZLM-direction would NOT allow the locked side)"
        log(f"{bot['name']} v8.4 ZDIR | spot {round(spot, 1)} ref {_z['ref']} dev {_z['dev']:+} thr {_z['thr']} | carried {_z['carried']} "
            f"chg3 {'NA' if _chg is None else _chg} floor {V84_ZDIR_FLOOR} -> ZLM-direction {_z['side'] or 'none'} | zone gate: locked "
            f"{_lk or 'none'} veto_ok {bool(bot.get('_botg_veto_ok'))} falling_block {bool(bot.get('_botg_falling_blocked'))}{_flag} (log-only)")
    except Exception as _e:
        _v84_err("zdir log", _e)


def _v833_skip_track(bot, why, symbol, side, entry, sl, spot):
    """v8.3.3: start a would-have SKIP tracker (SL / P1 as the bot would have set them) for a skipped / aborted setup. Log-only."""
    if not (V833_SKIP_TRACK and BOTG_TRACK_ENABLED):
        return
    try:
        if not entry or sl is None or entry <= sl:
            return
        _p1, _p2 = _botg_targets(bot, entry, entry - sl)
        try:
            _dtd = _day_type_diag(spot)
        except Exception:
            _dtd = {}
        _track_start("SKIP", bot["name"], f"{bot['name']}-SKIP-{why}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                     symbol, side, entry, entry=entry, sl=round(sl, 2), p1=round(_p1, 2), p2=round(_p2, 2), extra=_dtd)
    except Exception as _e:
        _v833_err("skip track", _e)


_DAY_KEYS = ["day_open", "day_high", "day_low", "pct_from_open", "pos_in_range", "spot_30m_chg", "day_type"]


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
    _append_csv(TRACK_FILE, _TRACK_HDR, rows)
    for x in done:
        _BOTG_TRACK.remove(x)
        _track_finish(x)


def _track_flush_all():
    """v-E19: at shutdown, write whatever unfinished trackers have so far."""
    while _BOTG_TRACK:
        _track_finish(_BOTG_TRACK.pop(0), "INCOMPLETE_SHUTDOWN")


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
            # date-stamped — archive/rename any existing trades_nifty_monthly_
            # fyers.csv before running this version, or the new columns will
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


def log_trade(bot, side, entry, exit_price, reason, qty, broker_exit_already_filled=False):
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
    # v-G77 (28-Sep-2026, LIVE-only bug found during the v2 review): both
    # BROKER_SL_FILLED call sites in _bot_g_manage() pass
    # broker_exit_already_filled=True, but this function never accepted
    # that argument -> TypeError crash the first time a real broker SL
    # filled. Accepting it is not enough on its own: the position is
    # already flat at the broker, so we must also NOT send another SELL
    # (that would open a fresh short). Paper mode never reached this path.
    if not PAPER_TRADE and not broker_exit_already_filled:
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
    _v832_wi_finish(bot, exit_price, _trade_total_pnl, reason)   # v8.3.2: exit what-if (log-only)
    try:
        _path_flush()   # v-G84: path rows for this trade on disk before its exit row
    except Exception:
        pass
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
    with open(TRADE_FILE, "a", encoding="utf-8") as f:
        f.write(_v2_trade_row(bot, side, qty, entry, exit_price, pnl, reason, "PARTIAL",
                              signal_price=_ps, slip_pts=(round(exit_price - _ps, 4) if _ps else ""),
                              slip_inr=(round((exit_price - _ps) * qty, 2) if _ps else "")))   # v-G76/v-E22
    log(f"PARTIAL BOOK| Bot:{bot['name']} Locked 50% qty:{qty} "
        f"PnL:Rs{pnl}  Remaining qty:{bot['qty']}  "
        f"Session:Rs{round(TOTAL_REALIZED_PNL,2)}")
    save_state()


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


_V87 = {"date": None, "shadow": None, "err": 0, "noted": {}, "tape_file": None}


def _v87_err(where, e):
    _V87["err"] += 1
    if _V87["err"] <= 5:
        try:
            log(f"v8.7 {where} error (ignored): {e}")
        except Exception:
            pass


def _v87_day():
    """v8.7: reset the per-day state when the date changes."""
    if _V87["date"] != date.today():
        _V87.update(date=date.today(), shadow=None, noted={}, tape_file=None)


def _v87_shadow_lock(bot, spot, dpcr_history, now_hhmm, trade_start_hhmm):
    """v8.7 (LOG-ONLY, Nifty v-E46): hypothetical lock = DPCR zone + spot-30m sync. One line per 3m candle from trade start. Never raises."""
    try:
        if not V46_SHADOW_LOCK or bot.get("name") != "BOT_G":
            return
        _v87_day()
        if now_hhmm < trade_start_hhmm or not dpcr_history:
            return
        cur = dpcr_history[-1]
        if cur is None:
            return
        cols = _v833_cols(bot, None, spot)
        c15 = cols[_V833_COLS.index("spot_chg15")]
        c30 = cols[_V833_COLS.index("spot_chg30")]
        d3 = round(cur - dpcr_history[-4], 3) if (len(dpcr_history) >= 4 and dpcr_history[-4] is not None) else None   # v8.8: DPCR change over 3 candles (9 min), rounded so +0.02 counts
        want = "CE" if cur >= V46_ZONE else ("PE" if cur <= -V46_ZONE else None)
        old = _V87["shadow"]
        note = ""
        if want is None:
            note = "inside zone, keeps " + (old or "-")
        elif want == old:
            note = "unchanged"
        elif c30 == "" or c30 is None:
            note = f"{want} wanted but spot 30m n/a"
        elif (want == "CE" and c30 >= V46_SYNC_PTS) or (want == "PE" and c30 <= -V46_SYNC_PTS):
            if V88_SHADOW_DPCR_RISE and not (d3 is not None and ((want == "CE" and d3 >= V88_DPCR_RISE) or (want == "PE" and d3 <= -V88_DPCR_RISE))):
                note = (f"{want} wanted, spot ok but DPCR 3c {('%+.3f' % d3) if d3 is not None else 'n/a'} not rising "
                        f"(>= {V88_DPCR_RISE} in its direction needed)")
            else:
                _V87["shadow"] = want
                note = f"shadow lock -> {want} (v-E46, log-only)"
        else:
            note = f"{want} wanted but spot 30m {c30} not in sync (>= {V46_SYNC_PTS} pts needed)"
        real = bot.get("locked_side")
        shadow = _V87["shadow"]
        log(f"{bot['name']} SHADOW LOCK | DPCR {cur:+.3f} spot30 {c30 if c30 != '' else 'NA'} | real {real or '-'} | "
            f"Z{V46_ZONE}+sync {shadow or '-'} | {'SAME' if (real or None) == shadow else 'DIFFERS'} | {note} | dpcr3c {('%+.3f' % d3) if d3 is not None else 'NA'}")
    except Exception as _e:
        _v87_err("shadow lock", _e)


def _v87_ctx(bot, side, spot):
    """v8.7 (LOG-ONLY): ENTRY CTX tail -- side-signed spot moves against the trade, the 65-pt both-windows verdict, the shadow lock. Never raises."""
    try:
        if not V833_MOM_TAGS:
            return ""
        _c = _v833_cols(bot, side, spot)
        c15 = _c[_V833_COLS.index("spot_chg15")]
        c30 = _c[_V833_COLS.index("spot_chg30")]
        if side not in ("CE", "PE") or c15 == "" or c30 == "" or c15 is None or c30 is None:
            a15 = a30 = "NA"
            gate = "NA"
        else:
            sg = 1 if side == "CE" else -1
            a15 = round(-sg * c15, 2)      # + = spot moved against the trade
            a30 = round(-sg * c30, 2)
            gate = "SKIP" if (a15 >= V47_GATE_AGAINST_PTS and a30 >= V47_GATE_AGAINST_PTS) else "ALLOW"
        _v87_day()
        return f" | against15={a15} against30={a30} gate15+30@{V47_GATE_AGAINST_PTS} {gate} | shadow lock {_V87['shadow'] or '-'}"
    except Exception as _e:
        _v87_err("ctx", _e)
        return ""


_V89 = {"date": None, "seen": {}, "paused": 0, "yes": 0, "err": 0}
_PAUSECF_COLS = ["date", "time", "run_id", "bot", "side", "setup_key", "rej_bar_start", "conf_bar_end", "spot", "dpcr", "zone_lo", "zone_hi",
                 "margin", "release_at", "release_cf", "vix", "pause_reason", "otm_pool", "symbols", "spot_chg15", "spot_chg30",
                 "against15", "against30", "fk_r1", "dpcr_falling_block", "past_entry_cutoff", "other_gate_blocked", "detail"]


def _v89_err(where, e):
    _V89["err"] += 1
    if _V89["err"] <= 5:
        try:
            log(f"v8.9 {where} error (ignored): {e}")
        except Exception:
            pass


def _v89_pause_cf(bot, spot, dpcr_history, now_hhmm):
    """v8.9 (LOG-ONLY): counterfactual tag for a scan PAUSED by the DPCR no-trade zone. Reads state, writes a log line + a CSV row. Never raises,
    never arms / places / alters anything, does not call the veto again and fetches no candles."""
    try:
        if not V89_PAUSE_CF or bot.get("name") != "BOT_G" or bot.get("early_slot"):
            return
        side = bot.get("locked_side")
        if side not in ("CE", "PE") or not dpcr_history or dpcr_history[-1] is None:
            return
        lo, hi = bot.get("dpcr_no_trade_low"), bot.get("dpcr_no_trade_high")
        if lo is None or hi is None:
            return
        cur = dpcr_history[-1]
        if not (lo <= cur <= hi):
            return                                   # not paused by the zone -> nothing to tag
        if _V89["date"] != date.today():
            _V89.update(date=date.today(), seen={}, paused=0, yes=0)
        _V89["paused"] += 1
        m = float(V89_PAUSE_MARGIN)
        if side == "CE":
            thr = round(hi - m, 3)
            rel = round(cur, 3) >= thr
        else:
            thr = round(lo + m, 3)
            rel = round(cur, 3) <= thr
        if not rel:
            return                                   # same-side DPCR still short of the counterfactual edge (or on the other sign)
        _V89["yes"] += 1
        dt = datetime.now()
        b = dt.replace(second=0, microsecond=0) - timedelta(minutes=(dt.minute % 5) + 5)   # last CLOSED 5m bar = the rejection candle a scan would use
        key = f"{side}@{b:%H:%M}"
        if key in _V89["seen"]:
            return                                   # same setup already recorded
        _V89["seen"][key] = 1
        _c = _v833_cols(bot, side, spot)
        c15 = _c[_V833_COLS.index("spot_chg15")]
        c30 = _c[_V833_COLS.index("spot_chg30")]
        fk = _c[_V833_COLS.index("fk_r1")]
        sg = 1 if side == "CE" else -1
        a15 = round(-sg * c15, 2) if c15 not in ("", None) else ""
        a30 = round(-sg * c30, 2) if c30 not in ("", None) else ""
        past_cut = int(now_hhmm >= BOTG_ENTRY_CUTOFF_HHMM)
        fall = int(bool(bot.get("_botg_falling_blocked")))
        other = int(bool(past_cut or fall or (fk == 1)))
        pool = list(bot.get("otm_pool") or [])
        syms = []
        for ov in pool:
            try:
                syms.append(str(get_option_symbol_bot_g(spot, side, otm_steps=ov, bot_name="TAPE", _log=False)))
            except Exception:
                syms.append("?")
        reason = "DPCR_IN_NO_TRADE_ZONE"
        flags = [n for n, f in (("entry_cutoff", past_cut), ("falling_dpcr", fall), ("fk_r1", fk == 1)) if f]
        log(f"{bot['name']} PAUSE CF | side={side} DPCR={round(cur, 3)} zone=[{lo},{hi}] release@{thr} YES | spot {round(spot, 2)} | "
            f"pool {pool} {syms} | against15={a15 if a15 != '' else 'NA'} against30={a30 if a30 != '' else 'NA'} fk_r1={fk if fk != '' else 'NA'} | "
            f"other gates: {','.join(flags) if flags else 'none'} | setup {key} | still PAUSED (v8.9, log-only)")
        row = {"date": date.today().isoformat(), "time": dt.strftime("%H:%M:%S"), "run_id": globals().get("RUN_ID", ""), "bot": bot["name"],
               "side": side, "setup_key": key, "rej_bar_start": f"{b:%H:%M}", "conf_bar_end": f"{(b + timedelta(minutes=10)):%H:%M}",
               "spot": round(spot, 2), "dpcr": round(cur, 3), "zone_lo": lo, "zone_hi": hi, "margin": m, "release_at": thr, "release_cf": 1,
               "vix": bot.get("vix_value") if bot.get("vix_value") is not None else "", "pause_reason": reason, "otm_pool": "|".join(str(x) for x in pool),
               "symbols": "|".join(syms), "spot_chg15": c15, "spot_chg30": c30, "against15": a15, "against30": a30, "fk_r1": fk,
               "dpcr_falling_block": fall, "past_entry_cutoff": past_cut, "other_gate_blocked": other, "detail": ",".join(flags)}
        new = not os.path.isfile(PAUSECF_FILE)
        with open(PAUSECF_FILE, "a", newline="") as _fh:
            w = csv.DictWriter(_fh, fieldnames=_PAUSECF_COLS)
            if new:
                w.writeheader()
            w.writerow(row)
    except Exception as _e:
        _v89_err("pause cf", _e)


def _v89_summary():
    """v8.9: one line at shutdown. Never raises."""
    try:
        if V89_PAUSE_CF and _V89["date"] == date.today():
            log(f"PAUSE CF | day summary: zone-paused ticks {_V89['paused']}, counterfactual-release ticks {_V89['yes']}, setups recorded {len(_V89['seen'])} -> {PAUSECF_FILE}")
    except Exception as _e:
        _v89_err("summary", _e)


def _v87_note_strikes(spot):
    """v8.7 (LOG-ONLY, Nifty v-E47): remember the CE/PE symbols ATM +/- V47_STEPS steps for the end-of-day tape. Never raises."""
    try:
        if not V47_OPTION_TAPE or not spot:
            return
        _v87_day()
        for j in range(-int(V47_STEPS), int(V47_STEPS) + 1):
            for sd in ("CE", "PE"):
                sym = get_option_symbol_bot_g(spot, sd, otm_steps=j, bot_name="TAPE", _log=False)
                cur = _V87["noted"].get(sym)
                if cur is None:
                    _V87["noted"][sym] = {"n": len(_V87["noted"]), "j": abs(j)}
                elif abs(j) < cur["j"]:
                    cur["j"] = abs(j)
    except Exception as _e:
        _v87_err("note strikes", _e)


def _v87_parse_sym(sym):
    import re
    m = re.match(r"^(?:BSE:)?SENSEX(.+?)(\d{5})(CE|PE)$", str(sym))
    return (m.group(1), int(m.group(2)), m.group(3)) if m else ("", "", "")


def _v87_option_tape():
    """v8.7 (LOG-ONLY, Nifty v-E47): at shutdown fetch today's 1-min OHLCV of the noted symbols -> option_tape_<ymd>_<broker>.csv (goes in the zip). Never raises."""
    try:
        if not V47_OPTION_TAPE:
            return None
        _v87_day()
        noted = _V87["noted"]
        if not noted:
            log("OPTION TAPE | no strikes were noted today -- nothing fetched")
            return None
        syms = [s for s, _ in sorted(noted.items(), key=lambda kv: (kv[1]["j"], kv[1]["n"]))][:int(V47_MAX_SYMBOLS)]
        today = date.today()
        out_rows, ok = [], 0
        for sym in syms:
            try:
                rows = _v87_fetch_rows(sym, today)
            except Exception as _e:
                log(f"OPTION TAPE | {sym}: fetch error (skipped): {_e}")
                rows = None
            if rows:
                ok += 1
                exp, strike, sd = _v87_parse_sym(sym)
                for (dt, o, h, l, c, v) in rows:
                    if dt.date() != today:
                        continue
                    out_rows.append([today.isoformat(), dt.strftime("%H:%M"), sym, exp, strike, sd, o, h, l, c, v])
            time.sleep(float(V47_SLEEP_SEC))
        fn = V47_TAPE_NAME.format(ymd=today.strftime("%Y%m%d"), broker=_BROKER_TAG)
        if out_rows:
            with open(fn, "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                w.writerow(["date", "time", "symbol", "expiry", "strike", "side", "open", "high", "low", "close", "volume"])
                w.writerows(out_rows)
            _V87["tape_file"] = fn
        log(f"OPTION TAPE | {fn if out_rows else 'no file'}: {ok}/{len(syms)} symbols, {len(out_rows)} rows (noted {len(noted)}, cap {int(V47_MAX_SYMBOLS)}) (v8.7, log-only)")
        return fn if out_rows else None
    except Exception as _e:
        _v87_err("option tape", _e)
        return None


def _v87_fetch_rows(sym, today):
    """v8.7: Fyers 1-min candles for one symbol -> [(datetime IST, o, h, l, c, v)]. Fyers epochs are UTC -> IST = +5h30."""
    d = today.strftime("%Y-%m-%d")
    resp = fyers.history(data={"symbol": sym, "resolution": "1", "date_format": "1", "range_from": d, "range_to": d, "cont_flag": "1"})
    cands = (resp or {}).get("candles") or []
    out = []
    for c in cands:
        dt = datetime(1970, 1, 1) + timedelta(seconds=int(c[0]) + 19800)   # UTC epoch -> IST, no deprecated utcfromtimestamp
        out.append((dt, c[1], c[2], c[3], c[4], c[5]))
    return out


def _v85_zip_members():
    """v8.5: base names of the files that go into the daily zip (resolved at call time; missing ones are skipped)."""
    out = []
    for _nm in ("LOG_FILE", "TRADE_FILE", "SUMMARY_FILE", "PATH_FILE", "TRACK_FILE", "TRACK_SUM_FILE", "LIVECMP_FILE", "VWAP_RES_FILE",
                "POOL_BARS_FILE", "BARS10_FILE", "SPOT_BARS_FILE", "TAG_FILE", "PAUSECF_FILE", "WHATIF_FILE", "ZLM_FILE", "HEARTBEAT_FILE"):
        _v = globals().get(_nm)
        if _v:
            out.append(_v)
    for _nm in ("DPCR_LOG_FILE", "DPCR_SHIFT_LOG_FILE"):
        _v = getattr(_oc_filter, _nm, None)
        if _v:
            out.append(_v)
    _tf = _V87.get("tape_file")   # v8.7: option tape written just before the zip
    if _tf:
        out.append(_tf)
    return out


def _v85_daily_zip():
    """v8.5: write upload_sensex_<YYYYMMDD>_<broker>.zip (whitelist only -- never tokens, client id or bot_state). Never raises."""
    tmp = None
    try:
        if not V85_DAILY_ZIP:
            return None
        import zipfile, glob
        files = []
        for _f in _v85_zip_members():
            if os.path.isfile(_f) and _f not in files:
                files.append(_f)
            if _f == LOG_FILE:
                for _r in sorted(glob.glob(LOG_FILE + ".*")):
                    if os.path.isfile(_r) and _r not in files:
                        files.append(_r)
        zname = V85_ZIP_NAME.format(ymd=date.today().strftime("%Y%m%d"), broker=_BROKER_TAG)
        if not files:
            log(f"v8.5 ZIP | nothing to zip (no research files found) -> {zname} not written")
            return None
        tmp = zname + ".tmp"
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as _z:
            for _f in files:
                _z.write(_f, arcname=os.path.basename(_f))
        os.replace(tmp, zname)
        log(f"v8.5 ZIP | wrote {zname}: {len(files)} files, {os.path.getsize(zname) // 1024} KB -- upload this one file")
        return zname
    except Exception as _e:
        try:
            if tmp and os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
        try:
            log(f"v8.5 ZIP | error (ignored): {_e}")
        except Exception:
            pass
        return None


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
            for bname in ["BOT_G", "BOT_GE"]:   # v-E6;   # v-G37: BOT_GG removed
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


def _get_historical_sensex_safe(fyers, retries=2, retry_delay=1.5):
    """
    v3.19-NIFTYFIX1: Nifty-only wrapper around helper.getHistorical().

    Root cause of the 2026-08-03 morning outage: helper_fyers.getHistorical()
    calls pd.concat() on a list built from grouping the day's candles, with
    no guard for the list being empty. That happens whenever fyers.history()
    returns zero candles for the requested symbol/range -- pandas then
    raises "No objects to concatenate", which is what showed up in the logs
    as [HISTORICAL PIPELINE ERROR]. Confirmed via code review that
    helper_fyers.py itself is unchanged and shared by every other bot
    (BankNifty/Sensex, both brokers), so it is intentionally NOT modified
    here -- everything below is local to this Nifty script only.

    What this adds on top of the plain helper.getHistorical() call:
      1. Up to `retries` extra attempts (short pause between) before giving
         up -- BankNifty's identical call succeeded seconds apart the
         morning this happened, so the empty-candle response looks
         transient/symbol-specific rather than a hard break; a couple of
         retries costs a few seconds and may well recover on its own.
      2. Only if every attempt still fails: one extra raw fyers.history()
         call, built to the same shape helper.getHistorical() uses
         internally, made purely to log Fyers' actual response (an error
         code/message vs. a genuinely empty candle list are very different
         problems). This diagnostic call never feeds into any trading
         decision -- df3 stays None either way and fetch_data()'s existing
         [DATA FETCH ERROR] / _on_fetch_fail() path handles it exactly as
         before.
    """
    for attempt in range(1, retries + 2):  # e.g. retries=2 -> 3 total attempts
        try:
            return helper.getHistorical("BSE:SENSEX-INDEX", 3, _v82_lookback_days(), fyers)   # v8 Sensex (Nifty: NSE:NIFTY50-INDEX, 2 days)
        except Exception as e:
            log(f"[HISTORICAL PIPELINE ERROR] attempt {attempt}/{retries + 1}: {e}")
            if attempt <= retries:
                time.sleep(retry_delay)

    try:
        range_to = datetime.today()
        range_from = range_to - timedelta(_v82_lookback_days())
        diag = fyers.history(data={
            "symbol": "BSE:SENSEX-INDEX",
            "resolution": 1,
            "date_format": "1",
            "range_from": range_from.strftime("%Y-%m-%d"),
            "range_to": range_to.strftime("%Y-%m-%d"),
            "cont_flag": "1",
        })
        log(f"[HISTORICAL DIAG] raw fyers.history() response after "
            f"{retries + 1} failed attempts: {diag}")
    except Exception as diag_e:
        log(f"[HISTORICAL DIAG] raw diagnostic call itself failed: {diag_e}")

    return None


def fetch_data(force_refresh=False):
    """
    v3.0: Two-tier fetch, ported from RMoney.
    - Spot price: fetched every CACHE_SEC (3s) — lightweight.
    - Historical candles: fetched only every HIST_CACHE_SEC (45s) — heavy,
      rate-limited by Fyers. Reused from cache between refreshes so the
      bot still evaluates every tick using the last known candles.
    Previously this section fetched df3/df5/df15 live on every call gated
    only by CACHE_SEC=3s — roughly 3 historical API calls every 3 seconds,
    which is what produced the mid-session 429 rate-limit errors.

    v3.14-STALE1: force_refresh added. HIST_CACHE_SEC (45s) and
    is_new_3m_candle()'s boundary check (fires in the 10s window right
    after minute%3==0) run on two independent, unsynchronized clocks. If
    the last 45s refresh happened to land just BEFORE a candle closed,
    the signal check at the boundary was evaluating a df3 snapshot in
    which that just-closed candle still looked "currently forming" —
    signal_bot_e()'s df3.iloc[:-1] then dropped it, silently signaling
    off the candle BEFORE it. Confirmed via Zerodha/TV cross-check on
    2026-07-28: three flagged BOT_E entries all matched the RSI of the
    candle one full 3-min interval earlier than the one assumed, to
    within 0.04. force_refresh=True (passed by main() during the
    candle-boundary window) bypasses both the CACHE_SEC spot-cache gate
    and the HIST_CACHE_SEC hist-cache gate below, guaranteeing df3 is
    pulled fresh — reflecting the candle that JUST closed — before any
    signal function runs. No effect outside that window; normal 45s
    cadence and API load are unchanged the rest of the time.
    """
    global _FETCH_FAIL_COUNT, _DATA_HEALTHY
    now = time.time()
    if not force_refresh and now - CACHE["time"] < CACHE_SEC:
        return CACHE

    try:
        spot = None
        quote = None
        try:
            quote = fyers.quotes({"symbols": "BSE:SENSEX-INDEX"})
            if quote.get("s") != "error":
                try:
                    inner = quote["d"][0]["v"]
                    if inner.get("s") != "error" and inner.get("lp") is not None:
                        spot = float(inner["lp"])
                except (KeyError, IndexError, TypeError, ValueError):
                    pass
        except Exception as _quote_e:
            quote = {"exception": str(_quote_e)}

        if spot is None:
            _spot1m_now = time.time()
            if (_spot1m_now - CACHE.get("spot_1m_time", 0)) < 15 and CACHE.get("spot") is not None:
                spot = float(CACHE["spot"])
            else:
                try:
                    _spot1m = helper.getHistorical("BSE:SENSEX-INDEX", 1, 2, fyers)
                    if _spot1m is not None and hasattr(_spot1m, "columns") and len(_spot1m):
                        _spot1m = _spot1m.dropna(subset=["close"])
                        if len(_spot1m):
                            spot = float(_spot1m["close"].iloc[-1])
                            CACHE["spot_1m_time"] = _spot1m_now
                            if CACHE.get("_spot_1m_fallback_logged_date") != date.today():
                                log(f"[SPOT LIVE QUOTE UNAVAILABLE] using latest completed 1M Sensex close "
                                    f"={spot} from BSE:SENSEX-INDEX; quote response={quote} "
                                    f"(further occurrences today logged silently) (v8 Sensex-hardening)")
                                CACHE["_spot_1m_fallback_logged_date"] = date.today()
                except Exception as _spot1m_e:
                    if CACHE.get("_spot_1m_fallback_error_logged_date") != date.today():
                        log(f"[SPOT 1M FALLBACK ERROR] {_spot1m_e} -- will try existing 3M history (v8 Sensex-hardening)")
                        CACHE["_spot_1m_fallback_error_logged_date"] = date.today()

        if spot is None:
            if CACHE.get("_spot_fallback_logged_date") != date.today():
                log(f"[SPOT QUOTE UNAVAILABLE] falling back to 3M historical close "
                    f"-- raw response: {quote} (further occurrences today logged silently)")
                CACHE["_spot_fallback_logged_date"] = date.today()

        need_hist = force_refresh or (now - CACHE["hist_time"]) >= HIST_CACHE_SEC
        if need_hist or CACHE["df3"] is None or spot is None:
            # v3.5-X6: 3m-only. Macro/trend for every bot now comes from the
            # EMA5/15/50 stack on this same df3 (_resolve_macro_3m_stack),
            # so the old 5m/15m calls and sleeps are gone — real API-load
            # reduction here (3 calls -> 1 per 45s cycle), same as BankNifty.
            df3  = _get_historical_sensex_safe(fyers)

            if df3 is None or not hasattr(df3, "columns"):
                log("[DATA FETCH ERROR] 3m timeframe returned invalid data.")
                _on_fetch_fail()
                return CACHE

            # v3.19-STALEFIX1: the check above only catches an EMPTY/invalid
            # response -- it says nothing about whether the data is
            # current. Confirmed on 2026-08-03: Fyers' historical feed can
            # keep returning a valid, non-empty df3 whose *last candle*
            # simply isn't advancing (this is what happened to the
            # BankNifty/Sensex siblings for 91 minutes that morning, same
            # root feed stall Nifty hit as an explicit no_data instead).
            # Bar-count-based checks (see v3.19-LOGFIX1 below) can't catch
            # this -- a stalled feed can return the same count every cycle.
            # This checks the actual timestamp of the last bar instead.
            _last_bar_age = (pd.Timestamp.now(tz="Asia/Kolkata") - df3.index[-1]).total_seconds()
            if _last_bar_age > STALE_CANDLE_SEC:
                log(f"[DATA FETCH ERROR] Last 3m candle is {int(_last_bar_age)}s old "
                    f"(>{STALE_CANDLE_SEC}s) — feed not advancing, reusing cached candles")
                _on_fetch_fail()
                return CACHE

            if spot is None:
                spot = float(df3["close"].iloc[-1])

            CACHE["df3"]       = df3
            CACHE["hist_time"] = now
            # v8 Sensex: visibility for the gap check -- sessions df3 spans, logged when the count changes.
            try:
                _sess = sorted({str(x.date()) for x in df3.index.normalize().unique()})
                if CACHE.get("_last_logged_sessions") != len(_sess):
                    CACHE["_last_logged_sessions"] = len(_sess)
                    log(f"[HISTORY] df3 spans {len(_sess)} session(s): {', '.join(_sess)} "
                        f"(lookback {BOTG_HISTORY_LOOKBACK_DAYS}d, v8 Sensex)")
            except Exception as _hs_err:
                log(f"[HISTORY] session log error (ignored): {_hs_err}")

            # v3.19-LOGFIX1: the candle-boundary force_refresh correctly
            # re-fetches on every tick during that 10s window, but was also
            # re-printing VWAP CHECK on every one of those ticks even though
            # the bar count hadn't actually changed yet — a burst of several
            # near-identical log lines every 3 minutes. Only log when the
            # bar count actually changed since the last time we logged it.
            # The fetch/cache/signal-timing logic above is untouched.
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

        if spot is None:
            log("[DATA FETCH ERROR] no spot available from either quote or historical fallback.")
            _on_fetch_fail()
            return CACHE

        CACHE["spot"] = spot
        CACHE["time"] = now

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
    v2.9-S7: Fetch India VIX from Fyers quotes API.

    v-G35 (25-Aug-2026): "NSE:INDIA VIX" (space, no suffix) confirmed
    failing all session (v-G32's diagnostic: inner error, "Please provide
    a valid symbol"). Never actually tried an alternate candidate before
    now -- every other NSE index confirmed working elsewhere in this
    codebase uses the "SYMBOL-INDEX" convention (e.g. "NSE:NIFTY50-
    INDEX"), no space. Tries that pattern first now ("NSE:INDIAVIX-
    INDEX"), falls back to the original string if it also fails --
    learned from the Sensex spot-symbol lesson (v-SG12/13) not to guess
    once and wait another round-trip; try multiple candidates with clear
    per-candidate diagnostics so whichever (if either) works is evident
    from a single run.

    Returns float VIX value or None on failure.
    """
    for candidate in ("NSE:INDIAVIX-INDEX", "NSE:INDIA VIX"):
        try:
            quote = fyers.quotes({"symbols": candidate})
            if quote.get("s") == "error":
                log(f"[VIX FETCH DIAG] '{candidate}' outer error -- raw response: {quote}")
                continue
            d_list = quote.get("d", [])
            if not d_list:
                log(f"[VIX FETCH DIAG] '{candidate}' empty 'd' list -- raw response: {quote}")
                continue
            inner = d_list[0].get("v", {})
            if inner.get("s") == "error":
                log(f"[VIX FETCH DIAG] '{candidate}' inner error -- raw response: {quote}")
                continue
            lp = inner.get("lp")
            if lp is None:
                log(f"[VIX FETCH DIAG] '{candidate}' no 'lp' in inner response -- raw response: {quote}")
                continue
            log(f"[VIX FETCH DIAG] '{candidate}' SUCCEEDED -- VIX={lp}")
            return float(lp)
        except Exception as e:
            log(f"[VIX FETCH ERROR] '{candidate}': {e}")
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
    # v-G28 (20-Aug-2026): losing_streak_exempt -- BOT_G/BOT_GG no longer
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



def _halt_live_execution(reason):
    """vRG2: latch the live engine OFF after an execution/reconciliation ambiguity."""
    global LIVE_EXECUTION_HALT
    LIVE_EXECUTION_HALT = True
    log(f"LIVE SAFETY HALT | {reason}")
    tg(f"LIVE SAFETY HALT\n{reason}\nNo further live orders will be submitted until the process is restarted and reconciled.")


def _live_ready(action="order"):
    """vRG2: every live order path must pass this guard."""
    if PAPER_TRADE:
        return True
    if not LIVE_TRADING_ARMED:
        log(f"LIVE SAFETY | {action} blocked: LIVE_TRADING_ARMED=False")
        tg(f"LIVE ORDER BLOCKED\n{action} requested while LIVE_TRADING_ARMED=False")
        return False
    if LIVE_EXECUTION_HALT:
        log(f"LIVE SAFETY | {action} blocked: execution safety latch is HALTED")
        return False
    return True


def _get_net_position(symbol):
    """vRG2: return (qty, avg_price, api_ok). Zero is distinct from API failure."""
    try:
        resp = fyers.positions()
        if resp.get("s") != "ok":
            return 0, None, False
        for pos in resp.get("netPositions", []):
            if pos.get("symbol") == symbol:
                return int(pos.get("netQty", 0) or 0), float(pos.get("netAvg", 0) or 0), True
        return 0, None, True
    except Exception as e:
        log(f"[POSITION QUERY ERROR] {e}")
        return 0, None, False


def _wait_for_fill(order_id, expected_qty, symbol, action):
    """vRG2: poll orderbook and reconcile; never invent a fill."""
    deadline = time.time() + LIVE_FILL_TIMEOUT_SEC
    last = ("UNKNOWN", None, 0)
    while time.time() < deadline:
        status, price, qty = _get_order_status_fyers(order_id)
        last = (status, price, qty or 0)
        if status == "FILLED" and qty:
            return price, qty, True
        if status == "REJECTED":
            return None, 0, False
        time.sleep(EXEC_FILL_POLL_WAIT_SEC)

    # Re-query the order once before deciding anything.
    status, price, qty = _get_order_status_fyers(order_id)
    if status == "FILLED" and qty:
        return price, qty, True

    if action == "ENTRY":
        pos_qty, pos_avg, api_ok = _get_net_position(symbol)
        if api_ok and pos_qty > 0:
            log(f"LIVE RECOVERY | Entry {order_id} not confirmed in orderbook, but broker position={pos_qty}; recovering.")
            return (pos_avg if pos_avg and pos_avg > 0 else price), pos_qty, True
        if api_ok and pos_qty == 0:
            _cancel_order_fyers(order_id)
            time.sleep(EXEC_FILL_POLL_WAIT_SEC)
            st2, _, _ = _get_order_status_fyers(order_id)
            if st2 in ("CANCELLED", "REJECTED"):
                return None, 0, False
    else:
        # EXIT/PARTIAL: never guess. Cancel only if still pending, then require
        # a clean broker position reconciliation. Any ambiguity halts live trading.
        if status in ("PENDING", "UNKNOWN", "PENDING_CANCEL"):
            _cancel_order_fyers(order_id)
            time.sleep(EXEC_FILL_POLL_WAIT_SEC)
        pos_qty, _avg, api_ok = _get_net_position(symbol)
        if api_ok:
            if action == "EXIT" and pos_qty == 0:
                _halt_live_execution(f"{action} {order_id} closed broker position but fill price was not conclusively recovered")
                return None, 0, False
            if action == "PARTIAL EXIT" and pos_qty >= 0 and last[2] > 0:
                _halt_live_execution(f"Partial exit {order_id} was not fully reconciled; broker position={pos_qty}, order={last}")
                return None, 0, False

    _halt_live_execution(f"{action} order {order_id} could not be conclusively reconciled; last={last}")
    return None, 0, False


def _get_order_fill(order_id):
    """
    v2.9-E2/E3: Query Fyers order book for fill price and filled qty.
    Returns (fill_price, filled_qty) or (None, None) on failure.
    """
    try:
        resp = fyers.orderbook()
        if resp.get("s") != "ok":
            return None, None
        for order in resp.get("orderBook", []):
            if str(order.get("id", "")) == str(order_id):
                fill_price = order.get("tradedPrice", 0)
                filled_qty = order.get("filledQty", 0)
                if fill_price and float(fill_price) > 0:
                    return float(fill_price), int(filled_qty)
        return None, None
    except Exception as e:
        log(f"[ORDER FILL QUERY ERROR] {e}")
        return None, None


def _check_existing_position(symbol):
    """vRG2: safe position check; API failure is treated as UNKNOWN, not flat."""
    qty, _avg, ok = _get_net_position(symbol)
    if not ok:
        return None
    return qty if qty > 0 else 0



# =============================================================================
#  EXECUTION ENGINE v1.0 — Fyers (v1.0-EE)
#  USE_LIMIT_ORDERS=False → delegates to place_market_order() unchanged.
#  USE_LIMIT_ORDERS=True  → aggressive limit, 2 attempts, market fallback.
# =============================================================================

def _get_ask_bid_fyers(symbol):
    """Fetch live ask/bid for a Fyers symbol. Returns (ask, bid) or (None, None)."""
    try:
        q = fyers.quotes({"symbols": symbol})
        if q.get("s") != "ok" or not q.get("d"):
            return None, None
        v   = q["d"][0]["v"]
        ask = float(v.get("ask") or v.get("lp") or 0)
        bid = float(v.get("bid") or 0)
        return (ask if ask > 0 else None), (bid if bid > 0 else None)
    except Exception:
        return None, None


def _place_limit_fyers(bot, side, limit_price):
    """Place a LIMIT BUY via Fyers. Returns (order_id, status_str)."""
    try:
        order_data = {
            "symbol":       bot["entry_symbol"],
            "qty":          bot["qty"],
            "type":         1,
            "side":         1,
            "productType":  "INTRADAY",
            "limitPrice":   round(limit_price, 1),
            "stopPrice":    0,
            "validity":     "DAY",
            "disclosedQty": 0,
            "offlineOrder": False,
        }
        resp = fyers.place_order(order_data)
        if resp.get("s") == "ok":
            return resp.get("id", "FYERS_LIMIT"), "PLACED"
        return None, f"REJECTED:{resp.get('message','')}"
    except Exception as e:
        return None, f"ERROR:{e}"


def _get_order_status_fyers(order_id):
    """Poll Fyers orderbook. Returns (status, fill_price, filled_qty)."""
    try:
        resp = fyers.orderbook()
        if resp.get("s") != "ok":
            return "UNKNOWN", None, None
        for o in resp.get("orderBook", []):
            if str(o.get("id", "")) == str(order_id):
                s   = str(o.get("status", ""))
                fpx = float(o.get("tradedPrice", 0) or 0)
                fqt = int(o.get("filledQty", 0))
                if s in ("2", "TRADED", "FILLED"):
                    return "FILLED", fpx if fpx > 0 else None, fqt
                if s in ("1", "CANCELLED"):
                    return "CANCELLED", None, None
                if s in ("5", "REJECTED"):
                    return "REJECTED", None, None
                if s in ("6", "PENDING_CANCEL"):
                    return "PENDING_CANCEL", None, None
                return "PENDING", None, None
        return "UNKNOWN", None, None
    except Exception as e:
        log(f"[ORDER STATUS ERROR] {e}")
        return "UNKNOWN", None, None


def _cancel_order_fyers(order_id):
    """Cancel a Fyers order. Returns True if accepted."""
    try:
        resp = fyers.cancel_order({"id": order_id})
        return resp.get("s") == "ok"
    except Exception:
        return False


def _check_open_orders_fyers(symbol):
    """Returns True if any open/pending order exists for symbol."""
    try:
        resp = fyers.orderbook()
        if resp.get("s") != "ok":
            return False
        for o in resp.get("orderBook", []):
            if (o.get("symbol") == symbol and
                    str(o.get("status", "")) in ("3", "4", "PENDING", "TRANSIT")):
                return True
        return False
    except Exception:
        return False


def execute_entry(bot, side):
    """
    Execution Engine v1.0 — Fyers.
    USE_LIMIT_ORDERS=False → place_market_order() directly (no change).
    USE_LIMIT_ORDERS=True  → aggressive limit with 2 attempts then market.
    Returns (order_id, fill_price, filled_qty).
    """
    if not PAPER_TRADE and not _live_ready("ENTRY"):
        return None, None, None
    if not USE_LIMIT_ORDERS or PAPER_TRADE:
        return place_market_order(bot, side)

    symbol     = bot["entry_symbol"]
    qty        = bot["qty"]
    bot_name   = bot["name"]

    ask0, bid0 = _get_ask_bid_fyers(symbol)
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
    if (_check_existing_position(symbol) not in (0, None)) or _check_existing_position(symbol) is None or _check_open_orders_fyers(symbol):
        log(f"EXEC ENGINE  | {bot_name} position/order exists — aborting")
        return None, None, None

    lim1 = round(ask0 + _buf(ask0, bid0), 1)
    log(f"EXEC ENGINE  | {bot_name} Att1 LIMIT={lim1} Ask={ask0} Bid={bid0}")
    oid1, s1 = _place_limit_fyers(bot, side, lim1)
    if oid1 is None:
        log(f"EXEC ENGINE  | {bot_name} Att1 failed ({s1}) — market fallback")
        return place_market_order(bot, side)

    time.sleep(EXEC_WAIT_SEC)
    st1, fp1, fq1 = _get_order_status_fyers(oid1)
    if st1 == "FILLED":
        log(f"EXEC ENGINE  | {bot_name} Att1 FILLED at {fp1}")
        return oid1, fp1, fq1 or qty
    if st1 in ("PENDING", "UNKNOWN", "PENDING_CANCEL"):
        _cancel_order_fyers(oid1)
        time.sleep(EXEC_CANCEL_WAIT_SEC)

    # Attempt 2
    ask2, bid2 = _get_ask_bid_fyers(symbol)
    if ask2 is None or not _ok(ask2):
        return None, None, None
    if (_check_existing_position(symbol) not in (0, None)) or _check_existing_position(symbol) is None or _check_open_orders_fyers(symbol):
        log(f"EXEC ENGINE  | {bot_name} position/order appeared — aborting")
        return None, None, None

    lim2 = round(ask2 + _buf(ask2, bid2), 1)
    log(f"EXEC ENGINE  | {bot_name} Att2 LIMIT={lim2} Ask={ask2} Bid={bid2}")
    oid2, s2 = _place_limit_fyers(bot, side, lim2)
    if oid2 is None:
        log(f"EXEC ENGINE  | {bot_name} Att2 failed ({s2}) — market fallback")
        return place_market_order(bot, side)

    time.sleep(EXEC_WAIT_SEC)
    st2, fp2, fq2 = _get_order_status_fyers(oid2)
    if st2 == "FILLED":
        log(f"EXEC ENGINE  | {bot_name} Att2 FILLED at {fp2}")
        return oid2, fp2, fq2 or qty
    if st2 in ("PENDING", "UNKNOWN", "PENDING_CANCEL"):
        _cancel_order_fyers(oid2)
        time.sleep(EXEC_CANCEL_WAIT_SEC)

    # Market fallback
    askf, _ = _get_ask_bid_fyers(symbol)
    if askf is None or not _ok(askf):
        return None, None, None
    log(f"EXEC ENGINE  | {bot_name} market fallback after 2 limit attempts")
    return place_market_order(bot, side)


def place_market_order(bot, side):
    """
    v2.9-E2/E3/E4: Enhanced order placement.
    Returns (order_id, fill_price, filled_qty) in LIVE mode.
    Returns ("SIM_ENTRY_ORDER_ID", None, None) in paper mode.
    """
    log(f"ORDER ENTRY  | {bot['name']} BUY {side} QTY:{bot['qty']} "
        f"{'[PAPER]' if PAPER_TRADE else '[LIVE]'}")

    if PAPER_TRADE:
        return "SIM_ENTRY_ORDER_ID", None, None

    # v2.9-E4: Pre-placement position check
    existing_qty = _check_existing_position(bot["entry_symbol"])
    if existing_qty is None:
        _halt_live_execution(f"ENTRY position check failed for {bot["entry_symbol"]}")
        return None, None, None
    if existing_qty > 0:
        log(f"PRE-RETRY GUARD | {bot['name']} position already exists "
            f"qty={existing_qty} — skipping order to prevent double buy")
        tg(f"PRE-RETRY GUARD {bot['name']}\n"
           f"Position already exists qty={existing_qty}\nOrder skipped.")
        return "FYERS_EXISTING_POSITION", None, existing_qty

    order_data = {
        "symbol":       bot["entry_symbol"],
        "qty":          bot["qty"],
        "type":         2,
        "side":         1,
        "productType":  "INTRADAY",
        "limitPrice":   0,
        "stopPrice":    0,
        "validity":     "DAY",
        "disclosedQty": 0,
        "offlineOrder": False,
    }
    try:
        response = fyers.place_order(order_data)
        if response.get("s") == "ok":
            order_id = response.get("id", "FYERS_ORDER")
            log(f"ORDER PLACED | {bot['name']} OrderID:{order_id}")

            fill_price, filled_qty, ok = _wait_for_fill(order_id, bot["qty"], bot["entry_symbol"], "ENTRY")
            if not ok or fill_price is None or filled_qty <= 0:
                return None, None, None

            if filled_qty != bot["qty"]:
                log(f"PARTIAL FILL | {bot['name']} ordered={bot['qty']} "
                    f"filled={filled_qty} fill_price={fill_price}")
                tg(f"PARTIAL FILL {bot['name']}\n"
                   f"Ordered: {bot['qty']}  Filled: {filled_qty}\n"
                   f"Fill price: {fill_price}\nUsing actual filled qty.")

            return order_id, fill_price, filled_qty

        else:
            msg = response.get("message", str(response))
            log(f"ORDER REJECTED | {bot['name']} {side} — {msg}")
            tg(f"ORDER REJECTED {bot['name']} {side}\n"
               f"Symbol: {bot['entry_symbol']}\n"
               f"Reason: {msg}\nNo position opened.")
            return None, None, None
    except Exception as e:
        log(f"ORDER ERROR  | {bot['name']} {e}")
        tg(f"ORDER ERROR {bot['name']} {side}\n{e}\nNo position opened.")
        return None, None, None


def place_exit_order(bot):
    """vRG2: real-money-safe closing SELL with broker-position reconciliation."""
    log(f"ORDER EXIT   | {bot['name']} SELL {bot['side']} QTY:{bot['qty']} "
        f"{'[PAPER]' if PAPER_TRADE else '[LIVE]'}")
    if PAPER_TRADE:
        return "FYERS_EXIT_ORDER_PAPER", None, bot["qty"]
    if not _live_ready("EXIT"):
        return None, None, None

    symbol = bot["entry_symbol"]
    qty, _avg, api_ok = _get_net_position(symbol)
    if not api_ok:
        _halt_live_execution(f"EXIT position check failed for {symbol}")
        return None, None, None
    if qty <= 0:
        _halt_live_execution(f"EXIT requested for {symbol}, but broker reports no long position")
        return None, None, None
    sell_qty = min(bot["qty"], qty)
    order_data = {
        "symbol": symbol, "qty": sell_qty, "type": 2, "side": -1,
        "productType": "INTRADAY", "limitPrice": 0, "stopPrice": 0,
        "validity": "DAY", "disclosedQty": 0, "offlineOrder": False,
    }
    try:
        response = fyers.place_order(order_data)
        if response.get("s") != "ok":
            msg = response.get("message", str(response))
            log(f"EXIT ORDER REJECTED | {bot['name']} — {msg}")
            tg(f"EXIT ORDER REJECTED {bot['name']}\n{msg}\nPosition remains at broker.")
            return None, None, None
        order_id = response.get("id", "FYERS_EXIT_ORDER")
        log(f"ORDER PLACED | {bot['name']} EXIT OrderID:{order_id}")
        fill_price, filled_qty, ok = _wait_for_fill(order_id, sell_qty, symbol, "EXIT")
        if not ok or fill_price is None or filled_qty <= 0:
            return None, None, None
        return order_id, fill_price, filled_qty
    except Exception as e:
        log(f"EXIT ORDER ERROR | {bot['name']} {e}")
        tg(f"EXIT ORDER ERROR {bot['name']}\n{e}\nPosition may still be open at broker.")
        return None, None, None


def place_partial_exit_order(bot, qty, target_price):
    """
    vRG2: actual broker SELL for P1/P2 before local bookkeeping changes.

    v-G65 (bug fix, this session): PAPER_TRADE branch previously returned
    bot.get("entry", 0) as the simulated fill price -- confirmed live,
    25-Sep-2026: a real Stage 1 booking correctly computed its target
    (%floor target=90.48) but was then logged and accounted as sold @
    87.0 (=entry), a real Rs904.8 of profit silently reported as Rs0.
    This affected every partial booking in Fyers paper mode this whole
    session -- RMoney's equivalent function was NOT affected (it already
    falls back to r1_level/r15_level when its own paper-mode fill price
    is unset). Fixed the same way here: paper mode now returns the
    actual computed target level (passed in by the caller, which already
    has it) instead of a hardcoded, unrelated entry price.
    """
    if PAPER_TRADE:
        return "SIM_PARTIAL", target_price, qty
    if not _live_ready("PARTIAL EXIT"):
        return None, None, 0
    symbol = bot["entry_symbol"]
    broker_qty, _avg, ok = _get_net_position(symbol)
    if not ok:
        _halt_live_execution(f"PARTIAL position check failed for {symbol}")
        return None, None, 0
    if broker_qty <= 0:
        _halt_live_execution(f"PARTIAL requested for {symbol}, but broker reports no position")
        return None, None, 0
    sell_qty = min(qty, broker_qty, bot["qty"])
    if sell_qty <= 0:
        return None, None, 0
    try:
        resp = fyers.place_order({"symbol":symbol,"qty":sell_qty,"type":2,"side":-1,
                                  "productType":"INTRADAY","limitPrice":0,"stopPrice":0,
                                  "validity":"DAY","disclosedQty":0,"offlineOrder":False})
        if resp.get("s") != "ok":
            log(f"PARTIAL ORDER REJECTED | {bot['name']} {resp}")
            tg(f"PARTIAL EXIT REJECTED {bot['name']}\nPosition remains at broker.")
            return None, None, 0
        oid = resp.get("id", "FYERS_PARTIAL_EXIT")
        fill_price, filled_qty, ok = _wait_for_fill(oid, sell_qty, symbol, "PARTIAL EXIT")
        if not ok or not filled_qty:
            return None, None, 0
        return oid, fill_price, filled_qty
    except Exception as e:
        _halt_live_execution(f"PARTIAL exit exception for {bot['name']}: {e}")
        return None, None, 0


def _modify_order_fyers(order_id, new_stop_price, qty=None):
    """
    v-MONEY-SLM1: modify a resting SL-M order's trigger price via Fyers
    API v3's modify_order call. Used to trail the broker-side stop as
    TSL/breakeven tighten it, instead of cancelling and re-placing, which
    would leave a brief window with no resting protection between calls.
    """
    try:
        data = {"id": order_id, "type": 3, "stopPrice": round(new_stop_price, 1)}
        if qty is not None:
            data["qty"] = int(qty)
        resp = fyers.modify_order(data)
        return resp.get("s") == "ok"
    except Exception as e:
        log(f"[SL MODIFY ERROR] {e}")
        return False


def update_broker_sl_order(bot, new_sl):
    """
    v-MONEY-SLM1: places/trails a REAL resting SL-M (type:3) order in LIVE
    mode. Previously this was a pure stub regardless of PAPER_TRADE. Paper
    mode behavior below is unchanged.

    If placement/modify fails, sl_order_id is left as-is (None -> retries
    next tick; an existing ID -> stays pointed at the last-known-good
    order still resting at its old price) rather than silently pretending
    the new level took effect.
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
        order_data = {
            "symbol":       bot["entry_symbol"],
            "qty":          bot["qty"],
            "type":         3,        # Stop Order (SL-M)
            "side":         -1,       # SELL, closes the long option
            "productType":  "INTRADAY",
            "limitPrice":   0,
            "stopPrice":    trigger,
            "validity":     "DAY",
            "disclosedQty": 0,
            "offlineOrder": False,
        }
        try:
            response = fyers.place_order(order_data)
            if response.get("s") == "ok":
                order_id = response.get("id", "FYERS_SL_ORDER")
                bot["sl_order_id"] = order_id
                time.sleep(0.15)
                _st, _px, _q = _get_order_status_fyers(order_id)
                if _st in ("REJECTED", "CANCELLED", "UNKNOWN"):
                    bot["sl_order_id"] = None
                    _halt_live_execution(f"Broker SL order {order_id} was not confirmed active; status={_st}")
                    return False
                log(f"SL SET       | {bot['name']} broker SL-M placed OrderID:{order_id} @ {trigger} status={_st}")
            else:
                msg = response.get("message", str(response))
                log(f"SL SET FAILED | {bot['name']} could not place broker SL-M @ {trigger} — {msg}")
                tg(f"SL PLACEMENT FAILED {bot['name']}\n"
                   f"Position currently has NO broker-side stop.\nCheck manually.")
                _halt_live_execution(f"Broker SL placement failed for {bot['name']}")
                return False
        except Exception as e:
            log(f"SL SET ERROR | {bot['name']} {e}")
            tg(f"SL PLACEMENT ERROR {bot['name']}\n{e}\nPosition currently has NO broker-side stop.")
            _halt_live_execution(f"Broker SL placement exception for {bot['name']}: {e}")
            return False
    else:
        ok = _modify_order_fyers(bot["sl_order_id"], trigger, bot["qty"])
        if ok:
            log(f"SL UPDATE    | {bot['name']} broker SL moved to premium {trigger}")
        else:
            log(f"SL UPDATE FAILED | {bot['name']} could not move broker SL to {trigger} "
                f"— still resting at previous trigger")
            tg(f"SL MODIFY FAILED {bot['name']}\n"
               f"Could not trail SL to {trigger} — still at old level.\nCheck manually.")
            if LIVE_REQUIRE_BROKER_SL:
                _halt_live_execution(f"Broker SL modify failed for {bot['name']} at {trigger}")
                return False
    return True


def _emergency_flatten(bot, reason):
    """vRG2: emergency broker flatten that bypasses the normal live-ready latch."""
    if PAPER_TRADE or not bot.get("entry_symbol"):
        return False
    symbol = bot["entry_symbol"]
    qty, _avg, ok = _get_net_position(symbol)
    if not ok or qty <= 0:
        return ok and qty == 0
    log(f"EMERGENCY FLATTEN | {bot['name']} {symbol} qty={qty} reason={reason}")
    try:
        resp = fyers.place_order({"symbol":symbol,"qty":qty,"type":2,"side":-1,
                                  "productType":"INTRADAY","limitPrice":0,"stopPrice":0,
                                  "validity":"DAY","disclosedQty":0,"offlineOrder":False})
        if resp.get("s") != "ok":
            _halt_live_execution(f"Emergency flatten rejected for {symbol}: {resp}")
            return False
        oid = resp.get("id", "FYERS_EMERGENCY_EXIT")
        fill, fq, ok2 = _wait_for_fill(oid, qty, symbol, "EMERGENCY EXIT")
        if not ok2 or fq < qty:
            _halt_live_execution(f"Emergency flatten {oid} did not fully confirm")
            return False
        log(f"EMERGENCY FLATTEN CONFIRMED | {symbol} qty={fq} fill={fill}")
        return True
    except Exception as e:
        _halt_live_execution(f"Emergency flatten exception for {symbol}: {e}")
        return False


def cancel_broker_sl_order(bot):
    if not bot["sl_order_id"]:
        return
    if PAPER_TRADE:
        log(f"SL CANCEL    | {bot['name']} SL order cleared")
        bot["sl_order_id"] = None
        return
    order_id = bot["sl_order_id"]
    ok = _cancel_order_fyers(order_id)
    if ok:
        log(f"SL CANCEL    | {bot['name']} broker SL order cancelled")
        bot["sl_order_id"] = None
    else:
        # vRG2: never erase an unconfirmed broker order ID. It may still be live.
        log(f"SL CANCEL FAILED | {bot['name']} could not cancel broker SL order "
            f"{order_id} — keeping ID and blocking unsafe exit/re-entry")
        tg(f"SL CANCEL FAILED {bot['name']}\n"
           f"Order {order_id} may still be resting at broker.\nManual verification required.")



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
    if not symbols:
        return {}
    try:
        data   = fyers.quotes({"symbols": ",".join(symbols)})
        result = {}
        for item in data.get("d", []):
            sym         = item.get("n") or item.get("v", {}).get("symbol", "")
            result[sym] = float(item["v"]["lp"])
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
    rationale. Kept identical to the RMoney file.
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

    log("=" * 70)
    log("SENSEX WEEKLY OPTIONS BOT -- BOT_G, MULTI-STRIKE POOL (DPCR + Option-VWAP) -- STARTING UP  [v8 = Nifty vE6.2 logic]")
    log(f"  INSTRUMENT            : Sensex (BSE:SENSEX-INDEX)")
    log(f"  LOT SIZE              : {LOT_SIZE}"
        f"  |  QTY (low-VIX<=13)  : {QTY_BOT_G_LOW_VIX} ({QTY_BOT_G_LOW_VIX // LOT_SIZE} lots)"
        f"  |  QTY (VIX>13)       : {QTY_BOT_G_HIGH_VIX} ({QTY_BOT_G_HIGH_VIX // LOT_SIZE} lots)")
    log(f"  STRIKE ROUND          : nearest {STRIKE_ROUND_UNIT}"
        f"  |  EXPIRY: WEEKLY (Thursday; rolls to next week when <= {BOTG_ROLLOVER_MAX_DAYS_LEFT} trading day left)")
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
    log(f"  ENTRY REJECTION GATE  : BAND {BOTG_NEAR_VWAP_LOWER_PTS}/{BOTG_NEAR_VWAP_UPPER_PTS} pts around option VWAP"
        f"  |  MIN_RISK={'ON ' + str(BOTG_MIN_RISK_PTS) + 'pts' if BOTG_MIN_RISK_ENABLED else 'OFF'}"
        f"  |  ENTRY_CUTOFF={BOTG_ENTRY_CUTOFF_HHMM}")
    log(f"  CONFIRM VWAP BAND     : {BOTG_CONFIRM_VWAP_LOWER_TIGHT}/{BOTG_CONFIRM_VWAP_UPPER_TIGHT}"
        f"  {BOTG_CONFIRM_VWAP_LOWER_MID}/{BOTG_CONFIRM_VWAP_UPPER_MID}"
        f"  {BOTG_CONFIRM_VWAP_LOWER_WIDE}/{BOTG_CONFIRM_VWAP_UPPER_WIDE}"
        f"  {BOTG_CONFIRM_VWAP_LOWER_XWIDE}/{BOTG_CONFIRM_VWAP_UPPER_XWIDE}  (VIX-scaled, v-G30)")
    log(f"  SL / BE / TSL         : BE_R_MULT={BOTG_BE_R_MULT}"
        f"  |  TSL_ARM_R_MULT={BOTG_TSL_ARM_R_MULT}"
        f"  |  TSL_BUFFER_PTS={BOTG_TSL_BUFFER_PTS}"
        f"  |  SL_VWAP_CLAMP={'ON' if BOTG_SL_VWAP_CLAMP_ENABLED else 'OFF'} (buffer={BOTG_SL_VWAP_BUFFER}, v-G39/v-G41)")
    log(f"  PARTIAL BOOKING       : {BOTG_PARTIAL_R1_FRACTION*100:.0f}% @ {BOTG_PARTIAL_R1_MULT}R"
        f"  |  {BOTG_PARTIAL_R15_FRACTION*100:.0f}% @ {BOTG_PARTIAL_R15_MULT}R"
        f"  |  remainder trails")
    log(f"  ENTRY WINDOW          : normal={BOTG_TRADE_START_NORMAL_HHMM}"
        f" gap={BOTG_TRADE_START_GAP_HHMM}"
        f"  |  GAP_THRESHOLD={BOTG_GAP_THRESHOLD_PCT}%")
    log(f"  FORCE EXIT            : {FORCE_EXIT_G}"
        f"  |  THETA-DECAY CAP: {BOTG_MAX_HOLD_MINUTES_INITIAL}min (INITIAL stage only, v-G30)")
    log("  DAILY LOSS CAP        : OFF")
    log("  DAILY PROFIT CAP      : OFF")
    log("  PER-BOT PROFIT CAP    : OFF")
    _tier_str = " / ".join(
        f"<=Rs{b if b != float('inf') else 'inf'}:{p}%" for b, p in PROFIT_PROTECT_TIERS
    )
    log("  GLOBAL PROFIT LOCK    : OFF")
    log(f"  CACHE_SEC             : {CACHE_SEC}s"
        f"  |  MAX_PORTFOLIO_QTY: {MAX_PORTFOLIO_QTY}"
        f"  |  MAX_OPEN_TRADES: {MAX_OPEN_TRADES}")
    log(f"  MODE                  : {'PAPER TRADE' if PAPER_TRADE else 'LIVE'}")
    log(f"  TELEGRAM ALERTS       : {'ON' if tg.__code__.co_consts[1] else 'OFF (token not set)'}")
    log(f"  HEARTBEAT FILE        : {HEARTBEAT_FILE} every 60s")
    log(f"  RUN ID (v-G75)        : {RUN_ID}  |  LOG: {LOG_FILE}  |  TRADES: {TRADE_FILE}")
    log(f"  vE6.2 (log-only)      : rollover by trading days (<= {BOTG_ROLLOVER_MAX_DAYS_LEFT} left -> next expiry) | "
        f"trackers {'ON' if BOTG_TRACK_ENABLED else 'OFF'} {BOTG_TRACK_MIN}m/{BOTG_TRACK_POLL_SEC}s | DATA_LOST after "
        f"{BOTG_DATA_LOST_SEC}s | live-vs-paper + charges (brokerage Rs{CHG_BROKERAGE_PER_ORDER}/order, STT {CHG_STT_SELL_PCT}%)")
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
    log(f"  v8.1 (19-Oct)         : pre-open gate {('ON, data calls from ' + BOTG_PREOPEN_RESUME_HHMMSS) if BOTG_PREOPEN_GATE_ENABLED else 'OFF'}  |  "
        f"OPTION SYMBOL log {'every call' if BOTG_OPTSYM_LOG_EVERY_CALL else ('on change / ' + str(BOTG_OPTSYM_LOG_HEARTBEAT_SEC) + 's')}  |  "
        f"paper stop fill {'AT STOP LEVEL (G4.1)' if G4_PAPER_STOP_AT_TRIGGER else 'at LTP'}")
    log(f"  v8.1 VWAP RESEARCH    : {('ON -> ' + VWAP_RES_FILE + ' + ' + POOL_BARS_FILE) if BOTG_VWAP_RESEARCH_ENABLED else 'OFF'}  (log-only, never read by trading logic)")
    log(f"  v8.1.1 (20-Oct)       : {('10m bars -> ' + BARS10_FILE + ' + ' + SPOT_BARS_FILE + ' | flushes at ' + str(BOTG_V811_BARS_FLUSH_HHMM) + ' + ' + str(BOTG_V81_BARS_DUMP_HHMM) + ' + shutdown | DPCR slope + flow columns') if BOTG_VWAP_RESEARCH_ENABLED else 'OFF'}")
    log(f"  v8.2 (24-Oct)         : day open from the 09:15 3m candle (v-E32)" + (f" | spot lookback {_v82_lookback_days()}d (v-E29)" if "_v82_lookback_days" in globals() else "") +
        f" | ZLM shadow {('ON -> ' + ZLM_FILE + f' (margin {ZLM_MARGIN_PTS}, band 0->{ZLM_BAND_MAX_PTS} pts, log-only)') if ZLM_SHADOW_ENABLED else 'OFF'}")
    log("  v8.3.1 (27-Oct)       : day open + gap check use the 09:15 candle only after it has closed (09:18); gap rechecked once at 09:18")
    log(f"  v8.9 (9-Nov)          : pause counterfactual tag {('ON release at |DPCR| >= zone - %s -> ' % V89_PAUSE_MARGIN + PAUSECF_FILE) if V89_PAUSE_CF else 'OFF'} (log-only, never arms / places / alters a trade)")
    log(f"  v8.8 (6-Nov)          : shadow lock also needs DPCR rising >= {V88_DPCR_RISE} over 3 candles: {'ON' if V88_SHADOW_DPCR_RISE else 'OFF'} (log-only)")
    log(f"  v8.7 (4-Nov)          : shadow lock {('ON zone %s + spot30 sync %s pts' % (V46_ZONE, V46_SYNC_PTS)) if V46_SHADOW_LOCK else 'OFF'}"
        f" | option tape {('ON +/-%s strikes, max %s symbols' % (V47_STEPS, V47_MAX_SYMBOLS)) if V47_OPTION_TAPE else 'OFF'} | entry gate fields @{V47_GATE_AGAINST_PTS} (all log-only)")
    log(f"  v8.6 (3-Nov)          : gap-day idle log {('every %s min' % V86_GAP_IDLE_LOG_MIN) if V86_GAP_IDLE_LOG else 'OFF'}"
        f" | ZLM reference {('closed 09:15 3m candle close (wait until %s, then old average)' % V86_ZLM_REF_WAIT_UNTIL_HHMM) if V86_ZLM_REF_CANDLE else 'average of spot polls 09:15-09:20'} (both log-only)")
    log(f"  v8.5 (2-Nov)          : daily upload zip {(V85_ZIP_NAME.format(ymd='YYYYMMDD', broker=_BROKER_TAG)) if V85_DAILY_ZIP else 'OFF'}"
        f" | gap-day threshold {BOTG_GAP_THRESHOLD_PCT}% either direction (gap day: early slot off, watch 10:00, first trade 12:30)")
    log(f"  v8.4 (30-Oct)         : falling-knife R1 {('ENFORCED for ' + ','.join(V84_FK_BOTS) + ' (early slot untouched)') if V84_FK_ENFORCE else 'OFF'}"
        f" | ZLM-direction view {('ON log-only, floor %s, fall tol %s' % (V84_ZDIR_FLOOR, V84_ZDIR_FALL_TOL)) if V84_ZDIR_TAGS else 'OFF'}")
    log(f"  v8.3.3 (29-Oct)       : common first DPCR anchor {'ON (closed 09:15 candle close, wait until %s)' % V833_ANCHOR_WAIT_UNTIL_HHMM if V833_COMMON_ANCHOR else 'OFF'}"
        f" | context tags {'ON' if V833_MOM_TAGS else 'OFF'} (falling-knife R1 log-only, min {V833_FK_MIN_PTS} pts) | skip tracker {'ON' if V833_SKIP_TRACK else 'OFF'}")
    log(f"  v8.3.2 (28-Oct)       : brokerage Rs{CHG_BROKERAGE_PER_ORDER}/order | ask-fill+stale guard {'ON %s%%' % V832_ASK_GUARD_PCT if V832_ASK_FILL_ENABLED else 'OFF'}"
        f" | post-gap paper stop fill {'ON >%ss' % V832_GAP_FILL_SEC if V832_GAP_FILL_ENABLED else 'OFF'}"
        f" | exit what-if {('ON -> ' + WHATIF_FILE + ' (log-only)') if WHATIF_ENABLED else 'OFF'}")
    log(f"  v8.3 (26-Oct)         : setup tags {('ON -> ' + TAG_FILE + ' (log-only)') if TAG_LOG_ENABLED else 'OFF'}")
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

    tg(f"BOT STARTED — Sensex Weekly (BOT_G, multi-strike pool) v8\n"
       f"Mode: {'PAPER' if PAPER_TRADE else 'LIVE'}\n"
       f"QTY: {QTY_BOT_G_LOW_VIX} (VIX<=13) / {QTY_BOT_G_HIGH_VIX} (VIX>13)\n"
       f"Expiry: {getSensexWeeklyExpiry()[0]} ({getSensexWeeklyExpiry()[1].isoformat()})\n"
       f"DailyLoss limit: Rs{MAX_DAILY_LOSS}")

    load_state()

    # v-RG-sync (this session): fail-closed live start gate, ported from
    # the vRG2 review -- the previous version called _broker_reconcile()
    # but never checked its result, so a genuinely failed reconciliation
    # (API error, exception) would silently continue into live trading
    # anyway. Now aborts startup entirely if either the second arming
    # switch is off or reconciliation couldn't actually verify the
    # broker's true position.
    if not PAPER_TRADE:
        if not LIVE_TRADING_ARMED:
            raise RuntimeError("LIVE START ABORTED | PAPER_TRADE=False but LIVE_TRADING_ARMED=False")
        if not _broker_reconcile():
            raise RuntimeError("LIVE START ABORTED | broker reconciliation failed")
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

            if BOTG_PREOPEN_GATE_ENABLED and _v81_preopen_wait():   # v8.1: no data calls before 09:14:30
                continue

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

            send_sensex_spot(spot)   # v8 Sensex: dashboard spot line even when DPCR is unavailable

            stale = data_is_stale()
            if stale:
                log(f"[DATA STALE] Last update {round(time.time()-CACHE['time'],0)}s ago. "
                    f"Skipping manage() AND new entries for all bots. (v2.9-D5)")
            try:   # vE6.2: day type (v-E20) + data-lost handling (v-E21)
                if not stale:
                    _day_track(spot, df3)   # v8.2: df3
                    _v82_zlm_hook(spot, df3)   # v8.2: ZLM shadow (log-only, own try/except)
                _data_lost_check(stale)
            except Exception as _e62_err:
                log(f"vE6.2 | day/data-lost check error (ignored): {_e62_err}")

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
                # v8 Sensex: the spot symbol is NOT added to this batch (Nifty adds NSE:NIFTY50-INDEX).
                # A BSE index symbol in the option batch only produced "invalid symbol" noise; the
                # spot comes from fetch_data() at the top of the loop, as when flat.
                _fresh_ltp = get_multi_ltp(open_symbols)
                if _fresh_ltp is not None:
                    ltp_map = _fresh_ltp
                else:
                    ltp_map = {}
            else:
                ltp_map = {}

            # ── FIX-6: Profit lock check (runs every cycle) ───────────────────────
            check_profit_lock(active_list, ltp_map)

            # ── Dashboard heartbeat ─────────────────────────────────────────────────
            # v-G14: BOT_G posts its OWN P/L (realized + open-position
            # unrealized) under its own dashboard ID.
            _dash_halt_from = None
            for _b in active_list:
                if _b["name"] not in ("BOT_G", "BOT_GE"):   # v-E13: GE reports too
                    continue
                _unreal = 0.0
                if _b["trade_open"] and _b.get("entry_symbol"):
                    _ltp = ltp_map.get(_b["entry_symbol"], _b["entry"])
                    _unreal = (_ltp - _b["entry"]) * _b["qty"]
                _bot_pnl = _b.get("cum_realized_pnl", 0.0) + _unreal
                _cmd = send_dashboard_heartbeat(_bot_pnl, bot_id=f"SENSEX_FYERS_{_b['name'].replace('BOT_', '')}")
                if _cmd == "halt":
                    _dash_halt_from = _b["name"]

            if _dash_halt_from:
                log(f"DASHBOARD KILL | Halt command received via {_dash_halt_from}'s cell -- "
                    f"shutting down.")
                tg(f"DASHBOARD KILL SWITCH\nBot halted via {_dash_halt_from}'s dashboard cell.")
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

                # v-G9: BOT_G doesn't go through signal()/manage()/
                # get_option_symbol() -- its entry/exit mechanics don't fit
                # the generic BOT_A-F shape (points-based SL, rejection-
                # candle arm, DPCR daily lock, multi-strike pool scan).
                # Routed to its own self-contained handler, which reuses
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
                    with open(HEARTBEAT_FILE, "w") as _hb:   # v-G70
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
        try:   # v8.1: end-of-day 5m bars of every pool strike (log-only)
            _v81_dump_pool_bars()
        except Exception as _e81:
            _v81_err("shutdown bars dump", _e81)
        write_summary()
        save_state()

    _v89_summary()   # v8.9 (log-only)
    _v87_option_tape()   # v8.7 (log-only): 1-min tape of the noted strikes, before the zip so it is included
    log("BOT SHUTDOWN COMPLETE.")
    _v85_daily_zip()   # v8.5: after the last log line, so the zip holds the whole log


# =============================================================================
if __name__ == "__main__":
    main()