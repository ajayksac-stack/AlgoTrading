# =============================================================================
#  config_rmoney_nifty_g_pool_vE4.py  --  NIFTY WEEKLY OPTIONS BOT (RMoney/XTS)
#  vE4 (05-Oct-2026): copy of config_rmoney_nifty_g_pool_v3.py for
#  BOT_rmoney_nifty_g_pool_vE4.py. Additions: BOT_GE early-slot block
#  (after BOTG_PATH_FLUSH_ROWS) and "BOT_GE" in ACTIVE_BOTS. Every BOT_G
#  value is identical to v3.2.
#  v3 (30-Sep-2026): copy of config_rmoney_nifty_g_pool_v2.py for
#  BOT_rmoney_nifty_g_pool_v3.py. Only additions: the v-G81 diagnostic
#  constants below BOTG_FLOW_FLAT_EPS and v-G83 BOTG_POST_ENTRY_MARKS_MIN /
#  v-G84 BOTG_PATH_* (all log-only). Every trading value is
#  identical to v2.
#  BOT_G only -- multi-strike VIX pool (DPCR + Option-VWAP strategy)
#  Updated: 2026-09-28 (v2: v-G70..v-G76 + v-G78)
#
#  v2 (28-Sep-2026): renamed from config_nifty_g_pool_v1.py; imported by
#  BOT_rmoney_nifty_g_pool_v2.py. (Older file names mentioned in the
#  header lines below are historical.) New constants, all flag-gated
#  (False = exact v1 behaviour):
#    BOTG_SL_VWAP_CLAMP_CONTINUOUS        (v-G71)
#    BOTG_DPCR_FALLING_BLOCK_SIDE_AWARE   (v-G72)
#    BOTG_STREAK_COUNT_LOSSES_ONLY        (v-G73)
#    BOTG_FLOW_WINDOW_MIN / BOTG_FLOW_FLAT_EPS  (v-G75, log-only)
#    BOTG_XTS_SYNTH_FORMING_BAR / _LAST_MIN_GRACE_SEC / _RETRY_SEC (v-G78,
#      next to BOTG_OPT_HIST_CACHE_SEC)
#
#  ALL TUNABLE PARAMETERS for BOT_G live in this file.
#  BOT_nifty_g_pool_v1.py does `from config_fyers_nifty_g_pool_v1
#  import *` and does not hardcode a tunable value itself.
#
#  v-G13 (12-Aug-2026): split out from the shared BOT_A-F multi-bot config
#  into this standalone file.
#
#  v-G37 (05-Sep-2026): explicit instruction (04/05-Sep-2026 session) --
#  BOT_G REMOVED ENTIRELY. Only one bot (BOT_G) runs now, and only one
#  trade can be open at a time. In exchange, BOT_G no longer trades a
#  single fixed strike -- it watches a small POOL of 3 strikes at once
#  (VIX-selected), takes the first one that qualifies, and the other two
#  stand down untouched until that trade reaches a logical end. Also adds
#  a DTE-scaled DPCR OI-window width (see option_chain_filter_nifty.py).
#  Renamed from config_fyers_nifty_gg_4LOT.py -- the matching bot file's
#  `from config_... import *` line was updated to this new filename.
#
#  Sections:
#    A) Mode & Safety             L) Data / API Timing
#    C) Quantities & Daily Risk   N) Same-Direction Re-entry Cooldown
#       Limits                   P) VIX Regime
#    G) BOT_G / BOT_G Strategy  Q) Strike Selection / Rounding (legacy)
#    H) Circuit Breaker /        R) Execution Engine Timing
#       Losing Streak
#    I) Tiered Profit Protection
#
#  (Section letters intentionally skip B/D/E/F/J/K/M/O/S/T -- those belonged
#  to BOT_A-F-only settings that no longer exist in this file. Kept the
#  surviving letters as-is rather than renumbering, so any old notes/diffs
#  that reference e.g. "Section G" or "Section P" still point to the right
#  place.)
#
#  KEY HISTORY (BOT_G/BOT_G only):
#  ─────────────────────────────────────────────────────────────────────────
#  v-G1        BOT_G's own strike-selection constant (BOTG_STRIKE_OTM_STEPS),
#              deliberately unsigned/always-OTM to avoid the legacy
#              STRIKE_ITM_STEPS sign-convention issue.
#  v-G2/v-G4   Option-own-VWAP touch threshold -- corrected 4%->2% off a
#              real 5-min PE walkthrough that showed the looser band letting
#              a fakeout through.
#  v-G5/v-G11/v-G16
#              BOT_G quantity: independent of LOTS_PER_BOT, 10 lots ->
#              8 lots -> 4 lots. The 4-lot figure isn't a standalone sizing
#              choice -- it's what makes the two-stage 50%/25%/25% partial-
#              booking split land on whole lots with zero rounding,
#              including the VIX-halved (2-lot) case.
#  v-G6        Full entry/exit spec, gap-dependent entry gate: normal-day
#              watch starts 09:15/earliest trade 10:30; gap-day watch starts
#              10:00/earliest trade 12:30 (replacement, not layered).
#  v-G11       VIX-based strike depth + position-size ladder, locked once
#              per day via its own fetch (independent of the 09:20/12:30
#              cadence, which starts too late for BOT_G's 09:16 anchor).
#              Two-stage R-multiple partial booking: 50% at 1R, 25% at 1.5R,
#              remaining 25% still trails via the existing BE/TSL machinery.
#  v-G12       BOT_G added -- shares every function with BOT_G, differs
#              only in its VIX->strike-depth ladder (shallower, starts from
#              ATM instead of OTM1). Reuses BOT_G's own 15/18 VIX thresholds
#              by explicit choice (shared risk-sizing decision).
#  v-G28       DPCR no-trade zone now 4-tier VIX-scaled (was 3-tier).
#              Daily lock can flip CE<->PE (was permanent once-per-day),
#              force-exits an open position ONLY if still below breakeven
#              at the moment of a flip -- at/above breakeven runs to
#              natural completion via BE/TSL/partial booking, untouched.
#              New falling-DPCR early-warning gate pauses fresh entries
#              only (does not affect an already-armed setup or an open
#              position). Both bots standardised on 5-min candles; the
#              10-min path (and its now-dead BOTG_CONSISTENCY_MIN_PCT
#              filter) removed. No losing-streak halt and no re-entry
#              cooldown of any kind for BOT_G/BOT_G -- confirmed, by
#              explicit instruction; their own profit-booking/exit
#              management is the only risk control after an exit.
#  v-G27       BOTG_DPCR_FLAT_BAND (used by the locked-side veto's slope
#              check) is now ALSO VIX-scaled, not a single fixed 0.05.
#              Root cause: 0.05 was proven too tight -- a normal ~0.07
#              DPCR wiggle could falsely veto BOTH arming a fresh setup
#              AND confirming one already armed. Must stay below each VIX
#              tier's own no-trade-zone half-width to have any early-
#              warning value at all (see config comment on
#              BOTG_DPCR_FLAT_BAND_TIGHT/MID/WIDE/XWIDE) -- otherwise DPCR
#              re-enters the zone, where a separate boundary check takes
#              over, before the slope ever earns the "falling" label.
#  v-G29       Root-cause fix for a symbol-construction bug that silently
#              blocked 100% of BOT_G's option-history fetches on
#              20/21-Aug-2026 (confirmed live: Fyers 'Invalid symbol
#              provided' on every strike/side) -- the week the weekly
#              expiry coincides with the monthly expiry, Fyers expects
#              the monthly-format symbol, not the ordinary weekly one.
#              Bot-file-only fix (_bot_g_symbol_expiry_code()); no config
#              constants involved.
#  v-G30       BOTG_CONFIRM_VWAP_LOWER/UPPER_TIGHT/MID/WIDE/XWIDE (new,
#              VIX-scaled): confirmation candle must land within an
#              asymmetric band around VWAP, not just have touched it at
#              some point -- filters out confirmations that stayed
#              meaningfully below VWAP the whole window (real losing
#              trades, 20-Aug: 2.7-3.0 points below at "confirmation").
#              BOTG_MAX_HOLD_MINUTES_INITIAL (new): theta-decay time cap,
#              force-exits an INITIAL-stage position (no SL/BE/partial
#              yet) that's shown no real progress within this many
#              minutes -- evidence-based from a real 19-Aug trade.
#
#  NOTE: helper_rmoney.py is never modified by this file or any patch after
#  it -- all changes here are config + main-script only, per standing policy.
# =============================================================================

#  A) MODE & SAFETY
# ─────────────────────────────────────────────────────────────────────────────
PAPER_TRADE  = True          # True = paper; False = LIVE
# v-RG2: second independent live-trading arming switch. Keep False until
# broker reconciliation/fill/SL checks have been validated in paper mode.
LIVE_TRADING_ARMED = False   # must be True in addition to PAPER_TRADE=False
# v-RG3 (bug fix): added to match Fyers' vRG2 build, which already had this.
# Independent review found RMoney's post-entry broker-SL failure path had
# no equivalent halt/emergency-flatten mechanism at all -- a genuinely
# failed SL placement right after a live entry could leave a real,
# unprotected options position with no safety net and no halt. See
# update_broker_sl_order() and _emergency_flatten() for the fix.
LIVE_REQUIRE_BROKER_SL = True   # mirrors Fyers' default
# False = LIVE — double-check ACTIVE_BOTS below
ACTIVE_BOTS  = ["BOT_G", "BOT_GE"]   # vE4: + early-entry slot  # v-G37: BOT_G removed entirely -- single bot,
                          # single open trade at a time (see pool-strike
                          # section below for how BOT_G now covers what
                          # used to be two separate bots).

ALLOW_DUPLICATE_POSITIONS = False  # False blocks any bot from entering the
# same side while another bot already holds it. (Historical root cause: two
# bots in the old A-F suite once took the identical CE simultaneously,
# doubling one bad signal into two losses -- guard kept as a general safety
# rule even though a single BOT_G process can't trigger this case itself.)


PROFIT_LOCK_TRAIL_PCT =     7.0   # % drop from intraday peak PnL to seal & exit all

# NOTE: this first LOSING_STREAK_LIMIT is intentionally overridden by the
# value in Section H below (kept only for historical continuity with v2.9
# logs). The Section H value (3) is what actually takes effect — edit it
# there, not here.
LOSING_STREAK_LIMIT = 4   # set 0 to disable  — SUPERSEDED, see Section H

# ─────────────────────────────────────────────────────────────────────────────
#  EXECUTION ENGINE CONFIG  (v1.0-EE)
#  USE_LIMIT_ORDERS = False → unchanged market order behaviour (paper safe)
#  USE_LIMIT_ORDERS = True  → aggressive limit, 2 attempts, then market
# ─────────────────────────────────────────────────────────────────────────────
USE_LIMIT_ORDERS       = False  # flip to True for live aggressive limit orders
EXEC_MIN_BUFFER        = 0.5   # Nifty: min Rs buffer above ask
EXEC_MAX_BUFFER        = 2.0   # Nifty: max Rs buffer above ask
EXEC_WAIT_SEC          = 1.0   # seconds to wait after limit order before polling
EXEC_MAX_SLIPPAGE_PCT  = 1.5   # abort if ask moved > 1.5% from signal ask


# ─────────────────────────────────────────────────────────────────────────────
#  C) QUANTITIES & DAILY RISK LIMITS
# ─────────────────────────────────────────────────────────────────────────────
LOT_SIZE     = 65   # Nifty lot size — update here if SEBI changes it
LOTS_PER_BOT =  4   # nominal per-bot lot count used ONLY to size the
                     # per-lot monetary limits below (MAX_DAILY_LOSS/PROFIT,
                     # PROFIT_PROTECT_THRESHOLD) -- BOT_G's own actual live
                     # qty_base (4 or 8 lots, VIX-linked, see Section G) is
                     # independent of this constant, same as before v-G37.
                     # NOTE: on VIX<=13 days BOT_G now trades 8 lots, double
                     # this nominal sizing figure -- these Rs-based hard
                     # stops still apply at the same Rs level regardless,
                     # they just get reached in fewer/larger trades on
                     # those days. Not a bug, just worth knowing.

# Auto-derived quantities — do not edit below this line
QTY_PER_BOT  = LOT_SIZE * LOTS_PER_BOT

# ── Base re-entry cooldown ──────────────────────────────────────────────────
# Not read by BOT_G/BOT_G -- they deliberately skip this generic cooldown in
# favor of their own rejection-candle re-arm gate (see main-loop dispatch,
# v-G9-FIX5). Kept defined since the bot file's comments reference it by
# name when explaining that design choice.
BASE_REENTRY_COOLDOWN_SEC = 300

# ─────────────────────────────────────────────────────────────────────────────
#  PER-LOT MONETARY LIMITS
#  Calibrated for LOT_SIZE=65 (Nifty revised lot size effective Jan 2026).
# ─────────────────────────────────────────────────────────────────────────────
# BOT_G session-level P&L caps/locks are intentionally DISABLED for paper-trade testing.
# Individual trade SL/BE/P1/P2/TSL/force-exit rules remain active.
BOTG_DAILY_PROFIT_CAP_ENABLED = False
BOTG_DAILY_LOSS_CAP_ENABLED = False
BOTG_GLOBAL_PROFIT_LOCK_ENABLED = False

MAX_DAILY_LOSS_PER_LOT   = -1_300.0
DAILY_REWARD_RISK_RATIO  =     1.25   # daily profit target as a multiple of
                                        # the daily loss limit
MAX_DAILY_PROFIT_PER_LOT = abs(MAX_DAILY_LOSS_PER_LOT) * DAILY_REWARD_RISK_RATIO
PROFIT_PROTECT_PER_LOT   =    390.0

# Auto-computed — DO NOT EDIT
ACTIVE_BOT_COUNT        = len(ACTIVE_BOTS)
MAX_DAILY_LOSS           = MAX_DAILY_LOSS_PER_LOT   * LOTS_PER_BOT * ACTIVE_BOT_COUNT
MAX_DAILY_PROFIT         = MAX_DAILY_PROFIT_PER_LOT * LOTS_PER_BOT * ACTIVE_BOT_COUNT
PROFIT_PROTECT_THRESHOLD = PROFIT_PROTECT_PER_LOT   * LOTS_PER_BOT

# ─────────────────────────────────────────────────────────────────────────────
#  G) BOT_G / BOT_G — OPTION CHAIN DPCR STRATEGY  (v-G1, piece 1: expiry + strike)
#     Strike-selection constant kept deliberately UNSIGNED to avoid the
#     ITM/OTM sign-convention issue -- BOTG_STRIKE_OTM_STEPS is ALWAYS
#     interpreted as "this many steps OTM", never ITM.
# ─────────────────────────────────────────────────────────────────────────────
BOTG_STRIKE_OTM_STEPS   = 4      # 4 = OTM4 (~0.30 delta per the strategy
                                 # doc's own approximation). Always OTM —
                                 # unlike STRIKE_ITM_STEPS, there is no
                                 # sign flip here. Change only this value
                                 # to move strike depth; no code changes
                                 # needed in signal_bot_g()/get_option_
                                 # symbol_bot_g().
# BOT_G reuses STRIKE_ROUND_UNIT and STRIKE_LIQUID_GRID from section Q
# below (same 50-point grid, same 100-point liquidity snap) — no
# separate constants needed for those two.

# v-G2: option's-own-VWAP bounce gate (confirmed: option VWAP, not spot
# VWAP — spot's VWAP degrades to an unweighted average since the index
# carries no real volume; options do carry real volume).
# v-G4: tightened from 0.04 to 0.02 -- the looser 4% band let a false
# "touch" through on a candle that was actually 2.4% away from VWAP
# (caught via the 5-min PE walkthrough, where it produced a same-candle
# bounce signal on a fakeout that got immediately invalidated the very
# next candle). Verified 2% correctly excludes that fakeout while still
# catching the genuine touch one candle later on the same data.
                                 # UNVALIDATED starting value in the sense
                                 # that no live trade has used it yet, but
                                 # unlike the original 4%, this one is
                                 # backed by a real-data walkthrough, not
                                 # just the doc's 3-5% suggestion.
BOTG_OPT_HIST_CACHE_SEC = 170    # same de-dupe cadence as OC_CACHE_SEC in
                                 # option_chain_filter_nifty.py -- one
                                 # fetch per ~3m candle, not per tick.
# v-G78 (28-Sep-2026): XTS closed-candle lag fix -- see the v-G78 block in
# fetch_option_history_5m(). True = once a 5-min bucket has ended, add a
# placeholder row for the current bucket so the just-closed candle is
# scanned immediately (28-Sep: RMoney scanned the 13:25 candle at 13:32:57
# vs Fyers 13:30:04 and missed a +Rs597 trade). False = exact v1.
BOTG_XTS_SYNTH_FORMING_BAR   = True
BOTG_XTS_LAST_MIN_GRACE_SEC  = 20   # wait this long for the closed candle's last 1-min bar
BOTG_XTS_RETRY_SEC           = 3    # re-fetch interval while waiting (instead of the 170s cache)

# v-G5: BOT_G quantity -- deliberately separate from LOTS_PER_BOT, per
# explicit instruction: originally 10 lots for BOT_G.
# v-G11 (12-Aug-2026): reduced to 8 lots. This wasn't a standalone qty
# decision -- it's what makes the new partial-booking scheme's 50%/25%/25%
# split land on whole lots with zero rounding (4/2/2), including the
# VIX-halved case below (2/1/1) which also needs to divide cleanly.
# QTY_BOT_G is now the FULL-size base only -- lock_bot_g_vix_regime() may
# halve it for the day depending on VIX; the per-trade qty actually used is
# bot["qty_base"], set once daily, not this constant directly.
QTY_BOT_G = 4 * LOT_SIZE   # v-G16 (13-Aug-2026): reduced from 8 lots, explicit
                            # loss-control instruction. VIX-halved case now
                            # drops to 2 lots -- both partial-booking stages
                            # floor to 1 lot each (v-G16 lot-safe rounding),
                            # which together consume the ENTIRE 2-lot position.
                            # Expected, not a bug -- see check_bot_g_partial_booking()

# v-G37 (05-Sep-2026): MULTI-STRIKE POOL, explicit instruction (04/05-Sep-
# 2026 session). REPLACES the old single-strike VIX ladder + BOT_G's
# separate ladder entirely. Rationale (Anu's own words): sticking to one
# fixed strike meant real paper-trade setups were missed when THAT
# strike's own VWAP-distance check failed even though DPCR/slope were
# favorable -- a different strike's own premium series might have shown a
# valid rejection candle at the same moment. So instead of one strike,
# BOT_G now watches a small POOL of 3 strikes at once (still only ONE can
# ever be in a trade at a time -- see lock_bot_g_strike_pool() and the
# pool-scan loop in _bot_g_try_entry()).
#
# Bands, exactly as specified: lower band's upper bound and the middle
# band's upper bound are BOTH inclusive (VIX==13.0 -> low-VIX pool,
# VIX==16.0 -> mid-VIX pool).
#   VIX <= 13.0            -> ATM, OTM1, OTM2
#   13.0 < VIX <= 16.0     -> OTM1, OTM2, OTM3
#   VIX > 16.0             -> OTM2, OTM3, OTM4
# Strike depth is unsigned (0=ATM, N=OTM-N-steps) -- no ITM in the pool,
# so get_option_symbol_bot_g()'s existing always-OTM-or-ATM math needs no
# change to support this.
BOTG_POOL_VIX_LOW_MAX = 13.0   # VIX <= this  -> low-VIX pool
BOTG_POOL_VIX_MID_MAX = 16.0   # this < VIX <= this -> mid-VIX pool
                                 # VIX > this   -> high-VIX pool
BOTG_STRIKE_POOL_LOW  = [0, 1, 2]   # ATM, OTM1, OTM2
BOTG_STRIKE_POOL_MID  = [0, 1, 2]   # vE6.13 v-E52: ATM, OTM1, OTM2 (was OTM1-3)
BOTG_STRIKE_POOL_HIGH = [0, 1, 2]   # vE6.13 v-E52: ATM, OTM1, OTM2 (was OTM2-4)

# Tie-break when more than one pool strike qualifies on the same scan:
# deepest-OTM (cheapest premium) strike in that day's pool wins -- e.g.
# OTM2 over ATM/OTM1 in the low-VIX pool (explicit instruction). Not a
# separate constant -- implemented as "max value in the pool" directly in
# _bot_g_try_entry(), since the pool lists above are already ordered
# ascending by OTM depth.

# v-G37: quantity, now VIX-linked with exactly 2 slabs (explicit
# instruction) -- this REPLACES the old BOTG_VIX_HALF_QTY_MIN (VIX>=18 ->
# half qty) tier entirely. VIX<=13 gets the SAME threshold as the pool's
# own low-VIX cutoff above (re-used directly, not independently derived --
# both a calmer/more-predictable-market decision).
#   VIX <= 13.0  -> 8 lots (partial-books 4 then 2, existing 50/25/25 R-
#                   scheme -- this is a return to the pre-v-G16 base size)
#   VIX >  13.0  -> 4 lots (today's existing base, unchanged)
QTY_BOT_G_LOW_VIX  = 8 * LOT_SIZE   # VIX <= 13.0
QTY_BOT_G_HIGH_VIX = 4 * LOT_SIZE   # VIX >  13.0 -- same as QTY_BOT_G below

# v-G37: single profile dict consumed by lock_bot_g_strike_pool() (replaces
# the old per-bot lock_bot_g_vix_regime()/BOTG_VIX_PROFILE/BOTGG_VIX_
# PROFILE shape). "pools" must have exactly 3 entries, ordered low/mid/high
# VIX, matching len(vix_thresholds)+1.
BOTG_STRIKE_POOL_PROFILE = {
    "vix_thresholds":    [BOTG_POOL_VIX_LOW_MAX, BOTG_POOL_VIX_MID_MAX],
    "pools":             [BOTG_STRIKE_POOL_LOW, BOTG_STRIKE_POOL_MID, BOTG_STRIKE_POOL_HIGH],
    "qty_vix_threshold": BOTG_POOL_VIX_LOW_MAX,   # re-uses the same 13.0 cutoff
    "qty_low_vix":       QTY_BOT_G_LOW_VIX,
    "qty_high_vix":      QTY_BOT_G_HIGH_VIX,
}

# v-G37: DPCR OI-window width, now scaled by trading days to the NEAREST
# (imminent) weekly Tuesday expiry -- confirmed this is a completely
# separate concept from which contract BOT_G itself trades (BOT_G always
# rolls to NEXT week's contract; DPCR's own option-chain fetch has no
# expiry param, so Fyers returns the nearest/front-week chain by default --
# see option_chain_filter_nifty.py's compute_dpcr() docstring). PLACEHOLDER:
# plain calendar-weekday lookup, NOT holiday-aware -- explicit instruction
# (05-Sep-2026 session) to keep this simple and only add an NSE holiday
# calendar later if a holiday week actually shows a bad reading in the log.
# date.weekday(): Mon=0, Tue=1, Wed=2, Thu=3, Fri=4.
BOTG_DPCR_WINDOW_BY_WEEKDAY = {
    2: 5,   # Wednesday: ATM +/- 5
    3: 4,   # Thursday : ATM +/- 4
    4: 3,   # Friday   : ATM +/- 3
    0: 2,   # Monday   : ATM +/- 2
    1: 2,   # Tuesday  : ATM +/- 2 (expiry)
}
BOTG_DPCR_WINDOW_DEFAULT = 4   # fallback only -- NIFTY never actually
                                 # trades on a day not in the map above.

# v-G11: two-stage R-multiple partial booking, explicit instruction
# (12-Aug-2026 session), replacing the old single BE(0.75R)+TSL(1.5R-arm)-
# only scheme with: book 50% at 1R, another 25% at 1.5R, remaining 25%
# still trails via the EXISTING BE/TSL machinery in manage_bot_g_exit() --
# BOTG_BE_R_MULT/BOTG_TSL_ARM_R_MULT/BOTG_TSL_BUFFER_PTS below are
# unchanged and still apply to whatever quantity remains after both
# partial stages. Fractions are of the ORIGINAL qty_base, not the
# remaining qty at each stage -- confirmed by construction (8 or 4 lots),
# always whole-lot, no rounding helper needed.
BOTG_PARTIAL_R1_MULT     = 0.9    # first partial trigger, in R (risk_pts)
BOTG_PARTIAL_R1_FRACTION = 0.5    # 50% of qty_base booked here
BOTG_PARTIAL_R15_MULT    = 1.5    # second partial trigger
BOTG_PARTIAL_R15_FRACTION = 0.25  # 25% more of qty_base booked here
                                    # (remaining 25% trails)

# v-G36 (29-Aug-2026): HYBRID profit-target floor, explicit instruction
# following a real-data investigation (28-Aug-2026 session replay). Root
# problem: a PURE R-based target degenerates when the rejection candle's
# own risk (R) is small relative to the entry premium -- confirmed live,
# 28-Aug: a trade with R = 1% of entry had its 1R target sitting just
# 1% above entry, close enough to be noise rather than a real profit
# signal. But the NAIVE fix (a flat % target, tried first as 5%/10%,
# then 5%/7.5%) has the OPPOSITE problem: on a trade with genuinely
# large R (a well-defined, high-conviction setup), a fixed % target sits
# CLOSER than the R-based one would, capping profit earlier than the
# real risk taken justifies -- also confirmed live, same session (a
# 7.7%-of-entry-R trade lost ~Rs200 of real profit to an over-tight 7.5%
# cap in isolated testing). The two failure modes cancel out only by
# taking the FARTHER of the two on each individual trade:
#     target = entry + max(R_MULT * risk_pts, PCT_FLOOR * entry)
# Replayed against the same real 28-Aug session data: this hybrid beat
# BOTH the pure-R and every pure-% variant tested, because it captured
# the low-R trade's better %-based outcome AND the high-R trade's
# better R-based outcome simultaneously, rather than committing to one
# formula for every trade regardless of that trade's own risk profile.
# 5%/7.5% chosen (not 5%/10%) as the pct floor -- the 10% second target
# was never once reached across the correctly-attributed real trades in
# the replay (peaks fell just short every time), making it a dead
# fallback in practice; 7.5% is reachable and still clearly above noise.
# v-G63 (this session): P1 threshold lowered further, 1.0R/5% -> 0.9R/4%
# (P2 unchanged at 1.5R/7.5%). Evidence: real trade replay on TWO
# independent sessions, both using the v-G36 hybrid formula as the
# baseline for comparison --
#   24-Sep-2026 (8 real trades, both Fyers+RMoney): 3 trades missed the
#   old P1 by under a point (0.17/0.88/0.38 pts, 85-97% of the way
#   there) and banked Rs0 or a small loss on their full remaining
#   quantity. Lowering P1 to 0.9R/4% converts all three into real
#   partial bookings. Net change across all 8 trades: +Rs3,107.21.
#   28-Aug-2026 (14 real trades, cross-validated retroactively against
#   the same rule): same mechanism, same direction -- 2 near-miss trades
#   flip from 0 to a real booking, a few comfortable winners give back a
#   modest amount on the P1 leg only. Net change: +Rs268.39.
# Same trade-off both times: trades that already cleared the old P1
# comfortably give back a small amount (fill a bit earlier/lower);
# near-miss trades that fell just short convert to real bookings, and
# that gain has dominated on both days tested so far. P2/BE/TSL
# untouched by this change -- only the first-stage target moved.
# Sample size caveat: ~20 non-SL trades across 2 days is corroborating,
# not yet a large-sample validation on the scale of v-G53's VPC-Veto
# (18 trades on ITS OWN specific question). Revisit if a longer run
# shows the trade-off reversing.
BOTG_PARTIAL_R1_PCT_FLOOR  = 0.04    # 4% of entry premium (was 5%)
BOTG_PARTIAL_R15_PCT_FLOOR = 0.075   # 7.5% of entry premium (unchanged)

# v-G36: per-bot daily profit cap, explicit instruction, same 28-Aug
# investigation. Once a bot's OWN cumulative realized P/L for the day
# reaches this, that bot stops taking NEW entries for the rest of the
# session -- explicitly a HARD STOP (not a trailing lock the bot can
# resume trading under if PnL dips back below the cap), per explicit
# choice: "in this case bot will keep running even when there is a
# small profit say 200 or 500" was the REJECTED alternative (a trailing
# mechanism), not this one. BOT_G and BOT_G are capped INDEPENDENTLY --
# one bot reaching its cap does not affect the other's ability to keep
# trading. Any position already open at the moment the cap is crossed is
# NOT force-closed -- it continues to be managed normally by the
# existing SL/BE/TSL/partial-booking machinery to its own natural exit;
# only NEW entries are blocked. Explicit caveat from the investigation,
# worth remembering: this cap's real-world value is unverified beyond
# one replayed session (28-Aug) where the day's best trade happened to
# be first -- it is not yet known whether this helps or hurts on a
# typical day where the good trades come later.
BOTG_DAILY_PROFIT_CAP_PER_BOT = 1000.0

# ─────────────────────────────────────────────────────────────────────────────
#  v-G6 (session of 09-Aug-2026): full entry/exit spec for BOT_G, worked out
#  against real 7-Aug 1-min/10-min option-premium data. Each constant below
#  is marked REAL (backed by an actual replayed number this session) or
#  PLACEHOLDER (no data existed to test it — DPCR needs an intraday OI time
#  series, which isn't available outside live market hours; NSE's own
#  post-close PCR is a single merged end-of-day number and can't be used to
#  reconstruct the intraday shape this needs). PLACEHOLDER values are a
#  reasonable starting guess only — same status BOTG_VWAP_TOUCH_PCT had
#  before it got corrected from 4% to 2% off one real walkthrough. Expect to
#  revisit every PLACEHOLDER after the log-only observation period.
# ─────────────────────────────────────────────────────────────────────────────

# v-G7 (session of 09-Aug-2026): entry gate is now GAP-DEPENDENT, not a
# single fixed window. Nifty spot itself (from the same 2-day df3 already
# fetched for A-F) defines "gap": today's session open vs yesterday's last
# close, >= BOTG_GAP_THRESHOLD_PCT either direction.
#   Normal day: DPCR watching (slope-building) starts 9:15; earliest a
#     direction lock/trade can happen is 10:30.
#   Gap day: watching starts 10:00; earliest lock/trade is 12:30. This is a
#     REPLACEMENT of the normal-day timing, not layered on top of it.
# Both cases share the same FORCE_EXIT_G (15:10) as the trading-window end
# -- no separate cutoff needed. The old static WINDOW_G tuple (this file's
# previous session) is superseded by the four constants below -- this was
# my own prior addition, not original codebase, so replaced directly
# rather than left-in-place-for-rollback per the usual convention.
BOTG_GAP_THRESHOLD_PCT      = 1.0    # REAL (explicit instruction)
BOTG_WATCH_START_NORMAL_HHMM = 915
BOTG_TRADE_START_NORMAL_HHMM = 1015   # v-G37: was 1030 (explicit instruction,
                                       # 04-Sep-2026). Gap-day start below is
                                       # deliberately UNCHANGED -- not asked.
BOTG_WATCH_START_GAP_HHMM    = 1000
BOTG_TRADE_START_GAP_HHMM    = 1230
FORCE_EXIT_G = 1510

# v-G38 (this session): explicit instruction -- which weekly contract BOT_G
# actually trades rolls forward once the imminent Tuesday is within this
# many days, not just on expiry day itself. 1 = roll forward on Monday AND
# Tuesday (current behavior); 0 = the original Tuesday-only rollover.
# Consumed by _next_nifty_weekly_expiry_date() in the bot file. Deliberately
# NOT used by DPCR's own expiry resolution (_nearest_nifty_weekly_expiry_
# date()), which always reads the genuinely nearest chain regardless of
# this setting -- see that function's docstring. Kept identical to the
# Fyers config.
BOTG_ROLLOVER_MAX_DAYS_LEFT = 1

# v-G15 (13-Aug-2026): NO NEW entries after this time, for BOTH BOT_G and
# BOT_G. Real, explicit instruction based on an observed pattern (option
# premiums tend to trade below their own VWAP after ~14:30, likely theta-
# decay driven) -- but the exact number is provisional pending real-data
# observation, not yet independently validated the way e.g. the DPCR
# no-trade zone was. Scope: entries ONLY. A position already open before
# this time keeps running completely normally (SL/BE/TSL/partial-booking
# all continue), and still exits at FORCE_EXIT_G (15:10) as before -- this
# constant is entirely separate from that one.
BOTG_ENTRY_CUTOFF_HHMM = 1430

# "Near VWAP" — REAL. Absolute points, deliberately NOT a percentage, so the
# band doesn't stretch/shrink as the option's own premium level changes
# through the day (same reasoning applied consistently to buffer below).
# Governs the REJECTION candle's own qualifying check (symmetric, either
# side of VWAP) -- NOT the confirmation candle, which uses the separate,
# asymmetric BOTG_CONFIRM_VWAP_* band below (v-G30).
BOTG_NEAR_VWAP_PTS = 4.0

# ============================================================================
# v-G41 — CANDLE QUALITY TEST (paper calibration)
# ----------------------------------------------------------------------------
# First-stage implementation of the VWAP-side-aware candle logic discussed
# 11-Sep-2026. These switches are deliberately isolated so the experiment
# can be turned off without changing the rest of BOT_G.
#
# Type A: price is ABOVE its rejection-candle VWAP and pulls back in a RED
# candle, while still closing above VWAP. A red candle is acceptable here: it
# represents the pullback toward support.
# Type B: price is BELOW VWAP but the candle must genuinely RECLAIM VWAP
# (open below VWAP, close above VWAP). Merely approaching VWAP while closing
# below is not accepted by the test.
#
# Shadows/range are measured and logged first. Their hard thresholds are kept
# OFF until 1-minute validation proves that they improve P&L without removing
# too many winners. The current upper-shadow reference bands are dataset-based:
# median ~1.10, 75th percentile ~2.05, 90th percentile ~3.71 points.
# ============================================================================
BOTG_CANDLE_QUALITY_ENABLED = True
BOTG_CQ_ABOVE_VWAP_RED_ENABLED = True
BOTG_CQ_BELOW_VWAP_RECLAIM_ENABLED = True

# Research-only diagnostics (NOT hard gates yet)
BOTG_CQ_UPPER_SHADOW_WARN_PTS = 2.05
BOTG_CQ_UPPER_SHADOW_VERY_LARGE_PTS = 3.70
BOTG_CQ_RANGE_WARN_PTS = 6.0
BOTG_CQ_SHADOW_HARD_FILTER_ENABLED = False
BOTG_CQ_RANGE_HARD_FILTER_ENABLED = False

# v-G51 (this session): "green volume candle" research metric, LOGGING
# ONLY, no hard gate (BOTG_VOLUME_HARD_FILTER_ENABLED stays False;
# there's no plan to flip it until this has a real multi-day sample).
# Idea: at a rejection candle where volume is genuinely elevated
# (relative to that day's own recent 5-min candles, not any external/
# prior-day baseline), price should be moving up or flat -- a high-
# volume RED candle (price fell on a volume spike) is a weaker signal
# than a high-volume GREEN one.
#
# v-G52 (this session): refined from a binary high/low + green/red/doji
# split to a proper 3-level scheme, per explicit instruction --
# Level 1 (volume strength): tiered, not a single cutoff.
# Level 2 (price response): reuses the existing direction field.
# Level 3 (close location): tiered too, not folded into direction alone.
# Combined into one of GREEN_VOLUME / NEUTRAL_VOLUME / RED_VOLUME /
# LOW_VOLUME. Baseline now computed over 3, 5, AND 20 prior same-day
# candles (all three logged), since we don't yet know which window is
# most predictive -- the 5-candle ratio is used as the primary one for
# tier classification, as a reasonable middle ground; 3 and 20 stay
# available in the log for comparison once more data accumulates.
#
# Checked directly against 11-Sep's 9 real trades (proper 1-minute P&L):
# every genuinely high-volume candle that day was directionally correct
# -- 3 high-vol RED-leaning candles all lost or scratched (-52, -130, 0),
# both of that day's big losses (-3744, -1872) shared a candle right at
# the tier boundary (not clearly elevated by the tiered thresholds
# below -- correctly falls to LOW_VOLUME, not RED_VOLUME, under this
# more conservative scheme), and the single VERY_STRONG-volume GREEN
# candle produced the day's biggest winner (+5642). But checked against
# 8-Sep too: every rejection candle that day was LOW volume, so that
# whole day gives ZERO evidence either way -- the real sample here is
# one day's worth of high-volume observations (6), not two days of
# confirmation. Not enough to gate on yet; logging this on every future
# day is how that sample actually grows, without touching live trading
# in the meantime. Kept identical to the Fyers config.
BOTG_VOLUME_BASELINE_CANDLES_SHORT = 3    # research window option 1
BOTG_VOLUME_BASELINE_CANDLES_MID   = 5    # research window option 2 (used for the primary tier)
BOTG_VOLUME_BASELINE_CANDLES_LONG  = 20   # research window option 3 (v-G51's original)

# Level 1 -- volume strength tiers (relative to the mid/5-candle baseline)
BOTG_VOLUME_TIER_WEAK_MAX   = 0.75   # < this -> WEAK
BOTG_VOLUME_TIER_NORMAL_MAX = 1.25   # WEAK..this -> NORMAL, above -> STRONG.. see next
BOTG_VOLUME_TIER_STRONG_MAX = 1.75   # NORMAL..this -> STRONG, above -> VERY_STRONG

# v-G64 (this session): LOGGING-ONLY low-liquidity flag, explicit
# instruction. Distinct from BOTG_VOLUME_TIER_WEAK_MAX above -- WEAK
# already exists as part of the high-volume-focused VolTier/VolumeSignal/
# VPC-Veto framework (v-G51/G52/G53), which by its own design has
# nothing to say about low-volume candles ("anything WEAK/NORMAL stays
# LOW_VOLUME regardless of price action"). This is a SEPARATE question:
# real 24-Sep-2026 data showed a pattern VPC-Veto/RED_VOLUME don't
# address at all -- weak/low volume correlating with weaker outcomes
# INDEPENDENT of price-rejection quality (a strong-looking rejection
# still only produced a breakeven on low volume; a 0.48x-volume setup
# went to full stop-loss). Only 4 data points -- nowhere near the
# 18-trade bar that earned VPC-Veto its live gate (v-G53). This flag is
# PURELY DIAGNOSTIC: logged on every candidate, armed or not, so real
# evidence accumulates over many more trades before any gating decision
# is considered. Does NOT touch quality_pass. 0.5 is a placeholder
# roughly below today's single bad-outcome data point (0.48) -- not a
# calibrated threshold, revisit once real accumulated data exists.
BOTG_LOW_LIQUIDITY_WARN_MAX = 0.5   # RelVol5 < this -> LOW_LIQUIDITY_WARNING (diagnostic only)

# Level 3 -- close-location tiers
BOTG_VOLUME_CLOSE_LOC_WEAK_MAX    = 0.50   # < this -> WEAK
BOTG_VOLUME_CLOSE_LOC_STRONG_MIN  = 0.70   # >= this -> STRONG (0.50-0.70 is ACCEPTABLE)

BOTG_VOLUME_HARD_FILTER_ENABLED = False

# v-G53 (this session): "Volume-Price Confirmation" (VPC) -- a SEPARATE,
# independently-validated gate, distinct from the v-G52 tier system
# above (that one's "high volume" starts at 1.25x, which real data
# shows is too strict for this specific purpose -- see below). Explicit
# instruction to enable this LIVE now, justified specifically by paper
# trading: a false veto here costs a missed paper-profit opportunity,
# not real money, while running it live gives genuine execution
# evidence instead of only backtested simulation.
#
# VETO rule: RelVol5 >= 0.85 AND CloseLoc <= 0.30 AND price declining
# (close < open) on the rejection candle -> do not ARM.
#
# Tested against ALL 18 real, validated trades across four separate
# days (7/8/9/11-Sep) before shipping -- this exact threshold set:
#   7 correct catches (real losses), 1 false positive (8-Sep 10:54,
#   a genuine +2.90 winner), improves the 18-trade total from 8083 to
#   13885 points.
# An alternative version proposed at RelVol>=1.20 + BearPressure>=0.40
# was tested on the SAME 18 trades and performs far worse: only 2
# correct catches (missing BOTH of 11-Sep's biggest losses, -3744 and
# -1872, worth -5616 combined) while keeping the same false positive --
# 8083 to only 8262. 1.20 is simply too strict for this instrument;
# 0.85 is what the data actually supports. bear_pressure is still
# logged below for future research, just not used in this gate.
#
# Known limitation, accepted deliberately: no "absorption/recovery"
# exception is implemented (a candle with a large low-to-close recovery
# that still nominally satisfies the three conditions). That idea came
# from an unvalidated hypothetical (8-Sep ~11:50) that was never
# actually a live decision point that day (the bot was very likely
# still managing an already-open trade through that window) -- adding
# an untested exception now risks quietly weakening a validated rule.
# Revisit once live paper data with this gate active gives a real
# example to check it against. Kept identical to the Fyers config.
BOTG_VPC_MIN_REL_VOL = 0.85
BOTG_VPC_MAX_CLOSE_LOCATION = 0.30
BOTG_VPC_VETO_ENABLED = True


# v-G30 (22-Aug-2026): VIX-scaled asymmetric tolerance band for the
# CONFIRMATION candle's distance to VWAP -- separate from, and narrower
# than, BOTG_NEAR_VWAP_PTS above. Root cause: the plain "touched + close >
# rejection_close" check let through confirmations where price stayed
# meaningfully BELOW VWAP the entire rejection+confirmation window (real
# 20-Aug trades: -2.68 to -3.00 points below VWAP at the moment of
# "confirmation") -- these read as noise inside a still-bearish-for-the-
# premium gap, not a genuine reclaim of the VWAP pivot, and lost. Real
# trades that DID work confirmed within +0.07 to +3.54 of VWAP -- solidly
# inside this band. Asymmetric on purpose: a confirmation can run well
# ABOVE VWAP (that's a strong breakout, not a red flag) but only barely
# below it (a small dip is noise; a real dip means it never reclaimed the
# pivot at all).
#
# TIGHT tier calibrated from real trading experience at the current
# (low) VIX regime. MID/WIDE/XWIDE are placeholder widenings for higher
# VIX -- UNVALIDATED, pending real experience at those levels; override
# freely once there's real data to calibrate against.
BOTG_CONFIRM_VWAP_LOWER_TIGHT = -1.00   # VIX < BOTG_DPCR_ZONE_VIX_LOW_MAX
BOTG_CONFIRM_VWAP_UPPER_TIGHT =  4.00
BOTG_CONFIRM_VWAP_LOWER_MID   = -1.50   # LOW_MAX <= VIX < MID_MAX
BOTG_CONFIRM_VWAP_UPPER_MID   =  5.00
BOTG_CONFIRM_VWAP_LOWER_WIDE  = -1.75   # MID_MAX <= VIX < HIGH_MAX
BOTG_CONFIRM_VWAP_UPPER_WIDE  =  5.50
BOTG_CONFIRM_VWAP_LOWER_XWIDE = -2.00   # VIX >= HIGH_MAX
BOTG_CONFIRM_VWAP_UPPER_XWIDE =  6.00

# Fallback only -- used when vix_value is None (VIX fetch failed).
BOTG_CONFIRM_VWAP_LOWER_TOL = -1.00
BOTG_CONFIRM_VWAP_UPPER_TOL =  4.00

# v-G30: theta-decay time cap. An option-BUYING bot loses to time decay
# the longer a position sits without reaching breakeven -- if neither the
# stop-loss nor any real progress (breakeven arm, partial booking) has
# happened within this many minutes of entry, force-exit and go look for
# a fresh setup rather than let theta keep eroding a stalled position.
# Scope: ONLY while stage == "INITIAL" (matches the "no SL or target hit
# yet" condition exactly) -- a position that has already armed breakeven
# or booked a partial has made real progress and is exempt; BE/TSL/
# partial-booking alone govern it from that point on, same as today.
# REAL, evidence-based: a real 19-Aug trade (entry 12:09) was still only
# marginally down at the 90-minute mark, but eventually gave back much
# more before its ordinary SL finally caught it 29 minutes later.
# UNVALIDATED beyond that one example -- watch real trades under this
# rule before trusting the exact number.
BOTG_MAX_HOLD_MINUTES_INITIAL = 90


# v-G10 (11-Aug-2026): LOG-ONLY comparison thresholds -- does NOT change
# what actually gates a rejection/arm (BOTG_NEAR_VWAP_PTS above is still the
# only one that does that). find_bot_g_rejection() logs whether each of
# these would ALSO have called it a rejection, purely so real data
# accumulates on whether 4.0 is too loose. Two days of manual replay
# already showed a tighter 3.0 band would have cut both winners AND
# losers on different days -- genuinely unclear from that sample size,
# hence this log-only comparison instead of just picking a new number.
# Review after ~15-20 days before touching BOTG_NEAR_VWAP_PTS itself.
BOTG_NEAR_VWAP_COMPARE_PTS = [3.0, 3.5]

# v-G18 (15-Aug-2026): "Option 1" directional-consistency filter, added to
# find_bot_g_rejection() alongside the existing distance check above. A
# candle only counts as a rejection if its own 3-min sub-bars agree (a
# majority closed on the same side of their own contemporaneous VWAP),
# not just if the candle's FINAL close happens to land near VWAP --
# filters out candles that whipsawed across VWAP repeatedly and only
# landed close to it by chance at the very end.
#
# Validated via backtesting across BOTH Nifty and BankNifty, multiple real
# days (13-15 Aug 2026 session) -- the original validation used finer
# 1-min sub-bar data (where a clean 70% threshold made sense); this bot
# only has 3-4 sub-bars per 10-min candle from its existing 3-min fetch
# (df3), which restricts the achievable values to {33%, 50%, 67%, 75%,
# 100%} -- no clean 70% is reachable. Explicit choice: 75% ("strong
# majority") over 67% ("simple majority") -- the higher bar filters real
# losses (roughly half, across the days tested) at the cost of
# occasionally cutting a genuine winner too, versus 67% which kept every
# winner tested but barely filtered anything. Confirmed this is a real
# trade-off, not free -- worth revisiting once more paper-trading data
# exists under this rule specifically.
#
# LEGACY, UNUSED (v-G20/v-G28): this only ever applied to the 10-min
# rejection path (find_bot_g_rejection()), which was removed once both
# bots standardised on 5-min (v-G20). Kept defined only because the bot
# file's comments reference it by name for historical context -- no code
# reads this value anymore.
BOTG_CONSISTENCY_MIN_PCT = 0.75

# Single-candle rejection is enough to arm the next candle for a live/
# intrabar buy check — REAL, explicit instruction, accepted knowing it lets
# some mid-decline fakeouts through (e.g. the 14:55 7-Aug case) in exchange
# for more trade frequency than the earlier two-rejection version.
BOTG_REJECTIONS_REQUIRED = 1

# Initial SL — REAL. The rejection candle's OWN LOW (not N candles back —
# that broke down: for a still-declining-into-VWAP setup, a further-back
# candle's close can sit ABOVE entry, which is unusable as a long SL).
# NOTE: confirmed but UNCAPPED — the 13:55 7-Aug trade showed this can be
# looser than needed when the rejection candle itself is a wide/volatile
# single bar (3.54% risk there vs ~1.5-2% on the other three trades that
# day). A max-risk cap (mirroring compute_initial_sl()'s tighter-of-two
# pattern used by BOT_A-F) was FLAGGED, not approved — deliberately left
# out here rather than inventing a cap value that wasn't discussed.

# Breakeven — REAL. Arms once price reaches this fraction of initial risk
# (R), moving SL to entry. Exists specifically to stop a trade that stalls
# short of the TSL-arm level from giving back its entire favorable move.
BOTG_BE_R_MULT = 0.75

# TSL arm — REAL. Once price reaches this multiple of initial risk (R),
# trailing begins. This is BOT_G's own "target" concept, per the original
# design note (R:R 1:1.5) -- NOT a fixed exit; it's where SL protection
# switches from "limit the loss" to "protect the gain while it keeps running".
BOTG_TSL_ARM_R_MULT = 1.5

# TSL trail buffer — REAL, but recalibrated once for update frequency. A 2%
# / ~5pt buffer worked well when re-evaluated only once per 10-min candle
# close, but was too tight once checked every 1-min close (ratchets far more
# often, so the same absolute buffer gets breached by ordinary noise). 8pts
# tested well at 1-min resolution on the one trade replayed this session
# (11:35 7-Aug) -- landed close to what the 10-min/2% version captured.
# Points, not %, same reasoning as BOTG_NEAR_VWAP_PTS.
BOTG_TSL_BUFFER_PTS = 8.0

# v-G39 (this session): explicit instruction -- SL is clamped to never sit
# above the rejection candle's own VWAP. If rejection_low > rejection_vwap
# (SL would sit above VWAP), SL is widened to rejection_vwap - this buffer
# instead; otherwise SL stays exactly the rejection candle's low, unchanged.
# Rationale: a rejection candle whose own low never reached VWAP still gets
# taken, but its stop is given room to actually test the VWAP support/
# resistance zone the whole entry thesis depends on, rather than being
# defended at a level the thesis itself never validated.
# Tested across 3-Sep and 7-Sep (23800 PE, both with validated native
# VWAP): combined result improved from 18.22 to 24.01 points vs. the
# unclamped baseline (+5.79). A narrower alternative (skip the trade
# entirely when SL>VWAP) was also tested and performed worse (16.23).
#
# v-G41 (same session): DISABLED. First live day (9-Sep, RMoney) fired 6
# times -- 4 losing trades made worse (extra -5215.6 Rs / -10.03 points
# at qty=520 combined), 2 winning trades where the wider stop was never
# even tested (both ran straight up from entry, no dip near either the
# natural or clamped SL at any point). Net across the 3 days of evidence
# on hand at that point (2 backtested + 1 live): -4.24 points.
#
# v-G43 (this session): RE-ENABLED. Explicit instruction -- 9-Sep's result
# was confounded by two other bugs active that same day, both since fixed:
# (1) the liquid-grid strike collapse (v-G40), meaning the "pool" was
# actually re-testing the SAME single strike all day instead of genuinely
# diversifying, and (2) DPCR flipped direction 3x that session (a
# genuinely hard day for any directional entry, unrelated to this clamp).
# Attributing the full -10.03 points to the clamp specifically, on a day
# with these two confounders already stacked against it, risks discarding
# a change the two CLEAN backtested days still show net positive on. Re-
# enabled now that both confounders are fixed, to see how it performs on
# an unconfounded day rather than deciding permanently off one bad,
# confounded sample. If a future *clean* day (no known bugs, no extreme
# DPCR whipsaw) still shows the clamp net negative, that would be much
# stronger evidence to disable it again than 9-Sep was.
# Buffer value (1.0) was checked against 0.5/1.5/2.0/2.5/3.0 on the
# original two backtested days; 0.5-2.5 showed a smooth downtrend
# (tighter buffers scored better), with a discontinuous jump at 3.0
# traced to a single-day trade-consolidation effect, not a stable
# improvement -- 1.0 remains a reasonable middle ground, not the single
# best-scoring value. Re-check this whenever revisited again. Kept
# identical to the Fyers config.
BOTG_SL_VWAP_CLAMP_ENABLED = True
BOTG_SL_VWAP_BUFFER = 1.0
# v-G71 (28-Sep-2026): the v-G39 clamp only fired when rejection_low was
# ABOVE VWAP, so a low 0.01 BELOW VWAP got a TIGHTER stop (the low itself)
# than a low 0.01 ABOVE it (VWAP - buffer). Real case, 28-Sep 13:45, same
# 22800PE setup on both brokers: Fyers low 136.60 vs VWAP 136.59 -> clamp
# -> SL 135.59 -> survived a dip to 136.4, exited at BE (-Rs26); RMoney
# VWAP 136.61 -> no clamp -> SL 136.60 -> stopped out (-Rs780).
# True = SL is min(rejection_low, VWAP - BOTG_SL_VWAP_BUFFER) whenever the
# clamp is enabled -- continuous, no cliff at VWAP. Can only ever widen a
# stop by at most BOTG_SL_VWAP_BUFFER relative to v1. False = exact v1.
BOTG_SL_VWAP_CLAMP_CONTINUOUS = True

# v-G50 (this session): explicit instruction -- confirmation-window
# integrity check. Tracks a genuine TICK-BY-TICK running low of LTP
# throughout the confirmation window (not a backward look at any closed
# candle); if that running low has already breached what the proposed
# initial SL would be, entry is blocked -- the setup has already
# violated its own risk boundary before the bot could act on it.
#
# This started as a proposal to check the confirmation candle's closed
# low, but that version has two real problems, both confirmed against
# real trade data before this was built: (1) it's not always achievable
# live -- one of the two 11-Sep losses this was built to catch (13:41,
# -3744) had its adverse move happen in the SAME minute as entry, after
# the entry tick fired; no real-time check can undo that. (2) an
# independently-built version of this idea (uploaded, not shipped) had
# an indexing bug reading the REJECTION candle instead of the
# confirmation candle, which would have blocked essentially every
# unclamped entry going forward, including 11-Sep's single biggest
# winner (+5642) -- verified directly against real numbers before being
# rejected.
#
# This version avoids both: it's a live-trackable running minimum, and
# it reads the actual confirmation-window LTP stream, not any closed
# candle. Tested (as a zero-ambiguity, prior-completed-minutes-only
# standard) against all 9 of 11-Sep's real trades: correctly catches
# the 13:43 loss (-1872) with ZERO false positives against any of that
# day's winners, including both of the day's biggest (+4967, +5642).
# Does not catch the 13:41 loss, for the real-time reason above -- that
# remains an open problem, not something this check claims to solve.
# Kept identical to the Fyers config.
BOTG_CONFIRM_INTEGRITY_ENABLED = True

# ── DPCR direction gate — entry conditions discussed this session, but      ─
#    UNTESTED end-to-end: no intraday OI time series was available to       ─
#    replay against (paid vendor feed "to be arranged later" per instruction)─
# v-G31 (23-Aug-2026): REPLACES v-G28's numbers entirely -- the DPCR
# metric itself changed (see compute_signed_dpcr() docstring: bounded
# signed formula, replaces the old unstable raw ratio). Recomputed the
# REAL distribution of this new formula retroactively from actual
# Nifty/Sensex log data (raw net_ce_doi/net_pe_doi deltas already
# existed in both logs) -- real readings spread across most of [-1,+1]
# on both instruments (Nifty median -0.594, Sensex median +0.125; both
# show p5/p95 near the +-1 boundary), NOT tightly clustered near 0.
#
# EXPLICIT INSTRUCTION: same zone numbers shared identically between
# Nifty and Sensex, for consistency/memorability and so both bots' logs
# read the same way -- not independently calibrated per instrument this
# time. Symmetric now (unlike the old ratio's zone), since the new
# formula has no reason to be lopsided -- both +1 and -1 are equally
# extreme. Zone half-width matches your worked "no-trade" examples
# (near-balanced CE/PE deltas landed around +-0.05); TIGHT set slightly
# wider than that for real-world margin.
BOTG_DPCR_NO_TRADE_LOW  = -0.10   # fallback only — used when vix_value is None
BOTG_DPCR_NO_TRADE_HIGH =  0.10

# v-G31: VIX breakpoints for the no-trade zone AND the falling-DPCR
# early-warning threshold below — same breakpoints drive both, since the
# underlying reasoning is identical (higher VIX -> noisier DPCR -> need a
# bigger move before trusting it as a real signal).
BOTG_DPCR_ZONE_VIX_LOW_MAX  = 12   # VIX <  this -> tightest zone
BOTG_DPCR_ZONE_VIX_MID_MAX  = 14   # VIX <  this -> mid zone
BOTG_DPCR_ZONE_VIX_HIGH_MAX = 18   # VIX <  this -> wide zone; >= this -> widest

BOTG_DPCR_ZONE_TIGHT  = (-0.10, 0.10)   # VIX < BOTG_DPCR_ZONE_VIX_LOW_MAX
BOTG_DPCR_ZONE_MID    = (-0.18, 0.18)   # LOW_MAX <= VIX < MID_MAX
BOTG_DPCR_ZONE_WIDE   = (-0.28, 0.28)   # MID_MAX <= VIX < HIGH_MAX
BOTG_DPCR_ZONE_XWIDE  = (-0.40, 0.40)   # VIX >= BOTG_DPCR_ZONE_VIX_HIGH_MAX

# v-G47 (this session): explicit instruction -- parallel VIX-scaled no-
# trade zone for raw_ratio (the OLD, centered-at-1.0 DPCR metric,
# previously sent only to the dashboard and never logged). DISPLAY/LOG
# ONLY -- does not drive any decision; signed_dpcr and the zones above
# remain the sole basis for the actual lock/flip/flat-band/falling-block
# logic, unchanged. Same VIX tier breakpoints as the signed_dpcr zones
# (BOTG_DPCR_ZONE_VIX_LOW_MAX/MID_MAX/HIGH_MAX), same half-widths, just
# re-centered on 1.0 instead of 0.0, so both zones stay in lockstep if
# either is ever recalibrated. Note: raw_ratio is a true ratio and can
# swing far outside this band when one side's OI-delta is near zero
# (confirmed live: the NIFTY dashboard panel showed a range of -536.11
# to +75.12 on 11-Sep) -- the zone will look like a thin sliver near 1.0
# on days like that; that's the metric's own nature, not a bug in this
# zone.
BOTG_DPCR_RAW_NO_TRADE_LOW  = 0.90   # fallback only — used when vix_value is None
BOTG_DPCR_RAW_NO_TRADE_HIGH = 1.10
BOTG_DPCR_RAW_ZONE_TIGHT  = (0.90, 1.10)   # VIX < BOTG_DPCR_ZONE_VIX_LOW_MAX
BOTG_DPCR_RAW_ZONE_MID    = (0.82, 1.18)   # LOW_MAX <= VIX < MID_MAX
BOTG_DPCR_RAW_ZONE_WIDE   = (0.72, 1.28)   # MID_MAX <= VIX < HIGH_MAX
BOTG_DPCR_RAW_ZONE_XWIDE  = (0.60, 1.40)   # VIX >= BOTG_DPCR_ZONE_VIX_HIGH_MAX

# PLACEHOLDER — how many DPCR candles back to compare against when judging
# rising/falling. Picked small+interpretable (9 minutes at 3-min DPCR
# candles) specifically because there's no data yet to tune it against.
# Shared by BOTH the coarse lock/flip slope calc (BOTG_DPCR_FLAT_BAND) and
# the finer new-entry falling-block below — same lookback, different
# thresholds. Unaffected by the v-G31 formula change.
BOTG_DPCR_LOOKBACK_CANDLES = 3

# v-G57 (this session): explicit instruction, correctly scoped this time --
# a THIRD DPCR variant, signed and magnitude-preserving, but built with a
# stable rolling-average denominator instead of the unstable PE/CE ratio
# an earlier attempt used (which is mathematically identical to raw_ratio,
# already proven to disagree with signed_dpcr's direction on real 17-Sep
# data). LOGGING/RESEARCH ONLY -- signed_dpcr remains the sole value any
# decision reads. Needs a full historical replay before ever being
# considered as a decision input. Kept identical to the Fyers config.
BOTG_MAGNITUDE_DPCR_BASELINE_CANDLES = 20

# v-G31: VIX-scaled, used by check_bot_g_locked_side_veto()'s slope check
# (via compute_bot_g_dpcr_slope()) -- this is the ONLY thing that can
# pause new entries on the currently-locked side while DPCR is still
# outside the no-trade zone but trending back toward it.
#
# CRITICAL CONSTRAINT, discovered by tracing the actual veto logic: this
# must stay BELOW each tier's own no-trade-zone half-width, or it's dead
# weight -- DPCR will already have drifted back inside the zone (where
# the veto's separate zone-boundary check takes over unconditionally)
# before the slope ever earns the "falling" label. ~80% of each tier's
# own zone half-width, same ratio as before, recomputed for the new
# formula's zone widths.
BOTG_DPCR_FLAT_BAND_TIGHT = 0.08   # VIX < BOTG_DPCR_ZONE_VIX_LOW_MAX  (zone half-width 0.10)
BOTG_DPCR_FLAT_BAND_MID   = 0.14   # LOW_MAX <= VIX < MID_MAX          (zone half-width 0.18)
BOTG_DPCR_FLAT_BAND_WIDE  = 0.22   # MID_MAX <= VIX < HIGH_MAX         (zone half-width 0.28)
BOTG_DPCR_FLAT_BAND_XWIDE = 0.32   # VIX >= HIGH_MAX                   (zone half-width 0.40)

# Fallback only -- used when vix_value is None (VIX fetch failed).
BOTG_DPCR_FLAT_BAND = 0.08

# v-G31: falling-DPCR early-warning thresholds — blocks NEW entries only
# (existing open positions are unaffected; they just get logged as
# "reversal watch", per explicit instruction). This gates a DIFFERENT
# thing from BOTG_DPCR_FLAT_BAND_* above (arming a fresh rejection
# candle, vs. pausing an already-locked side) -- the two don't need to
# stay in strict numeric order relative to each other. ~65% of each
# tier's own zone half-width, same ratio as before.
BOTG_DPCR_FALLING_THRESH_TIGHT = 0.07   # VIX < BOTG_DPCR_ZONE_VIX_LOW_MAX
BOTG_DPCR_FALLING_THRESH_MID   = 0.12   # LOW_MAX <= VIX < MID_MAX
BOTG_DPCR_FALLING_THRESH_WIDE  = 0.18   # MID_MAX <= VIX < HIGH_MAX
BOTG_DPCR_FALLING_THRESH_XWIDE = 0.26   # VIX >= HIGH_MAX
# v-G72 (28-Sep-2026): the v-G28 docstring says the early-warning gate is
# meant to catch a POSSIBLE direction change "either way", but the code
# only ever blocked on a FALLING signed DPCR (toward PE). On a PE-locked
# day that blocks entries exactly when DPCR moves further IN FAVOUR of PE
# (seen 28-Sep 14:23/14:25, change=-0.148, PE lock), and never blocks on
# a rise back toward CE. True = block on a move AGAINST the locked side
# (CE lock: change <= -thresh; PE lock: change >= +thresh). Same
# thresholds as above. False = exact v1 (falling-only, both sides).
BOTG_DPCR_FALLING_BLOCK_SIDE_AWARE = True

# v-G75 (28-Sep-2026): DPCR FLOW diagnostics -- LOG/CSV ONLY, never read by
# any entry/exit decision. Recent change in the window's intraday net CE
# and PE OI over the last ~BOTG_FLOW_WINDOW_MIN minutes, classified per
# trade side into MOST / HALF / MIXED / NOT favourable:
#   CE buy favourable = PE OI up AND/OR CE OI down
#   PE buy favourable = PE OI down AND/OR CE OI up
# BOTG_FLOW_FLAT_EPS: a 9-min change smaller than this (in OI units) is
# "flat". PLACEHOLDER -- ~25th percentile of |9-min change| across the
# 8-Aug..25-Sep Nifty dpcr_log (556k overall; 370k-810k by hour).
BOTG_FLOW_WINDOW_MIN = 9
BOTG_FLOW_FLAT_EPS   = 500000

# v-G81 (30-Sep-2026): OI / ATM diagnostics -- LOG/CSV ONLY, never read by
# any entry/exit decision. False = no OI DIAG / ATM DIAG lines at all.
BOTG_OI_DIAG_ENABLED    = True
# ATM premium residual = dLTP - (+) delta x dSpot for CE (PE). 0.5 is the
# textbook ATM delta; raw LTP/spot are logged too, so the residual can be
# recomputed later with a better delta or IV. PLACEHOLDER.
BOTG_ATM_DELTA_APPROX   = 0.5
# Single-strike, ~3-min thresholds for the WRITING/BUYING/... label only.
# PLACEHOLDERS -- to be set from the logged distribution.
BOTG_ATM_OI_FLAT_EPS    = 50000   # |dOI| below this = flat
BOTG_ATM_RESID_FLAT_PTS = 0.5     # |residual| below this = unclear

# v-G83 (v3.1): post-entry response marks, minutes after entry. LOG/CSV
# ONLY -- the option price at each mark goes into the trade CSV together
# with the lowest/highest price since entry (MAE/MFE).
BOTG_POST_ENTRY_MARKS_MIN = (1, 3, 5, 9)

# v-G84 (v3.2): per-trade price-path log (trade_paths_*.csv), LOG ONLY --
# used to replay BE / P1 / P2 / trailing-buffer variants offline.
BOTG_PATH_LOG_ENABLED   = True
BOTG_PATH_HEARTBEAT_SEC = 5     # write a row at least this often even if LTP is unchanged
BOTG_PATH_FLUSH_ROWS    = 25    # buffered rows before writing (also flushed on every exit)

# ─────────────────────────────────────────────────────────────────────────────
#  vE4 (05-Oct-2026): EARLY-ENTRY SLOT BOT_GE -- spec agreed 05-Oct.
#  Same entry mechanics as BOT_G; direction by DPCR sign + flow tier (no
#  lock, no no-trade zone); not on gap days; exits below. All exit numbers
#  are STARTING PLACEHOLDERS, to be tuned from the price-path replay.
# ─────────────────────────────────────────────────────────────────────────────
BOTGE_ENABLED                  = False   # vE6.11: off (backtest -14.9k, PF 0.64)
BOTGE_TRADE_START_HHMM         = 945    # first arm/entry
BOTGE_ENTRY_END_HHMM           = 1015   # no NEW early entry from here (open trade runs on)
BOTGE_ALLOWED_TIERS            = ("MOST", "HALF")   # 9-min flow tier for the trade side
BOTGE_BE_R_MULT                = 0.6
BOTGE_P1_R_MULT                = 0.75   # 50% (same fraction as BOT_G)
BOTGE_P1_PCT_FLOOR             = 0.03
BOTGE_P2_R_MULT                = 1.25   # 25%
BOTGE_P2_PCT_FLOOR             = 0.06
BOTGE_TSL_ARM_R_MULT           = 1.25
BOTGE_TSL_BUFFER_R             = 1.0    # buffer = max(MIN, min(MAX, R x risk_pts))
BOTGE_TSL_BUFFER_MIN_PTS       = 3.0
BOTGE_TSL_BUFFER_MAX_PTS       = 8.0
BOTGE_MAX_HOLD_MINUTES_INITIAL = 30     # time cap while still below BE
# Option (B): BOT_G opens no new trade while a BOT_GE trade is open
# (its DPCR/lock/VIX updates still run). False = fully independent slots.
BOTG_WAIT_FOR_EARLY_TRADE      = True

# v-G28: if DPCR flips against an OPEN position while it's still below
# breakeven (stage == "INITIAL"), force-exit it rather than letting it run.
# A position already at/above breakeven (BREAKEVEN/TRAILING stage) is left
# alone regardless of a flip — its own BE/TSL/partial booking keeps
# managing it to natural completion, unchanged from before. Toggle here in
# case this needs to be tested with the force-exit switched off.
BOTG_FLIP_FORCE_EXIT_BELOW_BE = True

# v-G8: cap on the in-memory DPCR reading history get_current_dpcr() now
# accumulates internally (module-level list in the main bot file, not this
# config) -- same HISTORY_MAX=50 pattern used in option_chain_filter_nifty.py.
BOTG_DPCR_HISTORY_MAX = 50


# ─────────────────────────────────────────────────────────────────────────────
#  H) CIRCUIT BREAKER / LOSING STREAK  (v3.0)
#     Per-bot streak tracking with timed cooldown, replacing the old global
#     all-day lock. Set LOSING_STREAK_PER_BOT=False and COOLDOWN_SEC=0 to
#     restore the old (v2.9) behaviour: one shared counter, permanent lock.
#     This is the value that actually applies (overrides Section A's copy).
# ─────────────────────────────────────────────────────────────────────────────
LOSING_STREAK_LIMIT        = 3      # consecutive SL/TSL exits before a halt
LOSING_STREAK_PER_BOT      = True   # True = each bot tracked/halted independently
LOSING_STREAK_COOLDOWN_SEC = 1800   # seconds until an auto re-arm (0 = permanent lock)
# v-G73 (28-Sep-2026): SL/TSL exits were counted toward the losing streak
# even when the trade made money -- 28-Sep Fyers +Rs2,980 trade (final
# TSL leg +Rs1,573) logged "consecutive SL count: 1/3"; RMoney went to
# 2/3 after a +Rs2,782 trade. True = an SL/TSL exit counts only if the
# WHOLE trade (partials + final leg) is <= 0; a whole-trade profit resets
# the streak. False = exact v1.
BOTG_STREAK_COUNT_LOSSES_ONLY = True

# ─────────────────────────────────────────────────────────────────────────────
#  I) TIERED PROFIT PROTECTION  (v3.0 — replaces flat PROFIT_PROTECT_FLOOR_PCT)
#     Floor % of peak open PnL to protect, scaled by how large the peak got.
#     v3.2 FIX: boundaries are now PER-LOT and auto-scaled by LOTS_PER_BOT,
#     matching every other monetary limit in this file. Previously the
#     boundaries (Rs400/Rs800) were flat regardless of lot size, while
#     PROFIT_PROTECT_THRESHOLD (the arming trigger) was already lot-scaled —
#     at higher LOTS_PER_BOT the arming trigger would land past the fixed
#     tier boundaries and lock the tightest 85% floor almost immediately
#     after arming, cutting winners short. Expressing the boundaries as
#     PER_LOT and multiplying by LOTS_PER_BOT keeps the same tier shape (in
#     premium-move terms) at any lot size.
#     NOTE (v3.1, still true): the SHAPE of these tiers (50/70/85%) was left
#     unchanged on purpose — the 2026-07-02 BOT_A exit that blew through its
#     70% floor (peak 494 -> exit 117) looked like a lag/liquidity issue on
#     the option LTP, not a tier-percentage problem. Only the lot-scaling
#     mechanism changed here, not the percentages themselves.
# ─────────────────────────────────────────────────────────────────────────────
PROFIT_PROTECT_TIERS_PER_LOT = [
    (400.0,        60.0),   # peak <= Rs400/lot           -> protect 60% of peak (was 50%, v3.3-T1)
    (800.0,        70.0),   # Rs400/lot < peak <= Rs800/lot -> protect 70%
    (float("inf"), 85.0),   # peak > Rs800/lot            -> protect 85%
]

# Auto-computed — DO NOT EDIT
PROFIT_PROTECT_TIERS = [
    (bound * LOTS_PER_BOT if bound != float("inf") else bound, floor_pct)
    for bound, floor_pct in PROFIT_PROTECT_TIERS_PER_LOT
]

# ─────────────────────────────────────────────────────────────────────────────
#  L) DATA / API TIMING  (v3.0 — ported from RMoney's two-tier cache)
# ─────────────────────────────────────────────────────────────────────────────
# v3.12-API2: CACHE_SEC moved here from the bot script — was hardcoded
# directly in fetch_data(), unlike HIST_CACHE_SEC below which was already
# config-driven. Same organizational fix already applied to RMoney.
CACHE_SEC      = 3    # spot price refresh interval (lightweight)
HIST_CACHE_SEC = 20   # v3.5-X8: was 45s (safe for 3 sequential calls w/ sleeps).
                       # Now 1 call, no sleeps (v3.5-X6) — tightened to 20s, matching
                       # the BankNifty-Fyers bot. No documented Fyers rate-limit spec
                       # exists to derive an exact safe floor from — watch the log for
                       # [DATA FETCH ERROR] on the first live session; tighten further
                       # only if a session runs clean.


# ═════════════════════════════════════════════════════════════════════════════
#  N) SAME-DIRECTION RE-ENTRY COOLDOWN  (v3.1 — NEW)
#     Root cause fix for the 2026-07-01 BOT_B trade #3: it re-entered CE
#     just 29 seconds after its existing 600s post-exit cooldown expired —
#     same direction as the trade that had just been stopped out, into a
#     market that had merely chopped back to where trade #1 started. The
#     existing SL_EXIT_COOLDOWN_SEC (mirrors the old hardcoded 600s) still
#     applies to ALL exits in either direction. SL_SAME_DIR_COOLDOWN_SEC
#     adds an EXTRA, longer, direction-aware lock specifically for
#     re-entering the SAME side after a SL/TSL (losing) exit.
# ═════════════════════════════════════════════════════════════════════════════
REENTRY_COOLDOWN_FILTER  = True
SL_SAME_DIR_COOLDOWN_SEC = 1200   # ADDITIONAL cooldown before re-entering the SAME
                                    # direction after a SL/TSL exit


# ═════════════════════════════════════════════════════════════════════════════
#  P) VIX REGIME
# ═════════════════════════════════════════════════════════════════════════════
VIX_LOW_MAX          = 12.0
VIX_NORMAL_MAX       = 20.0
VIX_ELEVATED_MAX     = 25.0


# ═════════════════════════════════════════════════════════════════════════════
#  Q) STRIKE SELECTION / ROUNDING  (legacy BOT_A-F constants, kept only for
#     the comment context in the bot file -- see note below)
# ═════════════════════════════════════════════════════════════════════════════
STRIKE_ROUND_UNIT       = 50

# STRIKE_ITM_STEPS: legacy from the deleted BOT_A-F get_option_symbol() path
# (this config no longer has a live consumer for it -- BOT_G/BOT_G use
# BOTG_STRIKE_OTM_STEPS / the VIX-based ladders in Section G instead). Left
# defined only because a bot-file comment references it by name for context.
#     0  -> ATM (at-the-money)
#   > 0  -> ITM by that many steps (e.g. 4 = ITM4, deeper in-the-money)
#   < 0  -> OTM by that many steps (e.g. 2 = OTM2)
STRIKE_ITM_STEPS        = -4

# STRIKE_LIQUID_GRID: v-G40 (this session) -- get_option_symbol_bot_g() no
# longer snaps to this. Found live: with the pool spaced 50pts apart
# (STRIKE_ROUND_UNIT) but this grid at 100, ATM/OTM1/OTM2 collapsed onto
# the same strike on every VIX<=13 day, silently neutering the pool on
# exactly the regime it's most often used in. Kept defined only in case
# something else still references the name -- no live consumer in BOT_G.
# Kept identical to the Fyers config.
STRIKE_LIQUID_GRID      = 100

# ═════════════════════════════════════════════════════════════════════════════
#  R) EXECUTION ENGINE — internal timing
# ═════════════════════════════════════════════════════════════════════════════
EXEC_SPREAD_BUFFER_FRACTION = 0.30
EXEC_CANCEL_WAIT_SEC        = 0.5
EXEC_SPREAD_FALLBACK_PCT    = 0.01
EXEC_FILL_POLL_WAIT_SEC     = 0.5
# v-RG2 live fail-closed execution controls
LIVE_FILL_TIMEOUT_SEC       = 5.0   # maximum time to verify a market order fill
LIVE_FILL_POLL_SEC          = 0.25  # order/trade-book poll interval
LIVE_REQUIRE_BROKER_RECONCILE = True

# =============================================================================
#  END CONFIG — do not edit below this line unless you know what you're doing
# =============================================================================

# ── Derived portfolio limits (auto-set from PAPER_TRADE above) ────────────────
# NOTE: the hardcoded "6" in PAPER_TRADE mode predates the BOT_G/BOT_G split
# (was sized for the old 6-bot A-F suite). Left untouched -- review before
# relying on it as a meaningful cap for a 2-bot process.
MAX_PORTFOLIO_QTY  = (QTY_PER_BOT * 6                    if PAPER_TRADE
                      else QTY_PER_BOT * ACTIVE_BOT_COUNT)  # v2.8-L11
MAX_OPEN_TRADES    = 6             if PAPER_TRADE else ACTIVE_BOT_COUNT
PORTFOLIO_COOLDOWN = 0             if PAPER_TRADE else 300


# ─────────────────────────────────────────────────────────────────────────
# vE5 (09-Oct-2026)
# v-E9 (B'): carry the DPCR score across re-anchors (True) or reset it to
# zero at every re-anchor as before (False). Both values are logged.
BOTG_DPCR_CARRY_ENABLED = True

# v-E12 (vE5.1, 12-Oct-2026): NSE trading holidays (equity derivatives). An
# expiry that falls on one of these moves to the previous trading day.
# Source: NSE 2026 holiday list. ADD NEXT YEAR'S LIST BEFORE 1-Jan-2027.
NSE_TRADING_HOLIDAYS = [
    "2026-01-15", "2026-01-26", "2026-03-03", "2026-03-26", "2026-03-31",
    "2026-04-03", "2026-04-14", "2026-05-01", "2026-05-28", "2026-06-26",
    "2026-09-14", "2026-10-02", "2026-10-20", "2026-11-10", "2026-11-24",
    "2026-12-25",
]

# =============================================================================
# vE6 (15-Oct-2026) -- agreed after replaying 42 BOT_G trades (6-14 Oct).
# =============================================================================
# v-E14 carried flow (separate history; never resets at a re-anchor).
BOTG_CARRIED_FLOW_LOG_WINDOWS  = (3, 6, 9, 12, 15)  # logged at every entry (log/CSV only)
BOTG_CARRIED_FLOW_KEEP_MIN     = 25      # minutes of readings kept
BOTG_CARRIED_FLOW_MAX_AGE_SEC  = 360     # latest reading older than this -> flow NA

# v-E15 main-slot (BOT_G) CE skip when calls are being added. 9-min carried
# flow, dCE > threshold -> skip. 15 such CE trades 6-14 Oct: 1 win, -11.0R.
# Flow NA -> entry allowed. BOT_GE and PE entries are NOT affected.
BOTG_CE_CALLADD_SKIP_ENABLED   = True
BOTG_CE_CALLADD_SKIP_MIN       = 9
BOTG_CE_CALLADD_SKIP_THRESHOLD = 500000
# v-E48 (vE6.10): True = log the would-have skip and TAKE the entry (12 blocked
# setups went to P1 first vs 7 to SL first, 26-Oct..6-Nov). False = real skip.
BOTG_CE_CALLADD_SKIP_LOGONLY   = False   # vE6.11: real skip again (backtest: would-skip trades -26.3k)

# ============================================================================
# vE6.11 (09-Nov-2026) -- backtest-led, 205 days Jan-Oct 2026
# v-E49: BOT_G option setup candle in minutes (rejection candle, next-candle
# confirmation, option VWAP). 10-min: BOT_G -20.0k -> +20.8k, better in 8 of 10
# months. 5 = old behaviour. BOT_GE always uses 5.
BOTG_OPT_TF_MIN        = 10
# v-E50: BOT_G entries only WITH the 3-min spot Supertrend (last closed candle).
# Trades against ST(10,3) lost -23.7k in Jun-Oct. False = filter off.
BOTG_ST_FILTER_ENABLED = True
BOTG_ST_FILTER_N       = 10
BOTG_ST_FILTER_MULT    = 3.0

# ============================================================================
# vE6.12 (10-Nov-2026) -- LOG-ONLY
# v-E51: at every BOT_G exit leg, fetch bid/ask and log what a real SELL would get
# (paper exits use LTP/mid). Rows in exit_quotes_nifty_<broker>.csv, added to the zip.
V51_EXIT_QUOTES        = True
# vE6.13 (15-Nov-2026) v-E53: VIX gate. VIX at the 10:15 open lock <= max -> no new
# BOT_G entries that day. Backtest: low-VIX days lost -36.3k (2025), +3.7k (2026).
BOTG_VIX_GATE_ENABLED  = True
BOTG_VIX_GATE_MAX      = 13.0
# vE6.14 (18-Nov-2026) v-E54: end-of-day cleanup. After the NORMAL 15:10 shutdown the
# upload zip is verified, then the bot's own daily files are deleted. upload_*.zip,
# .py, configs and token files are never deleted. Mid-day stops delete nothing.
V54_EOD_CLEANUP        = True
V51_EXIT_QUOTES_FILE   = "exit_quotes_nifty_rmoney.csv"

# v-E16 stop band, BOT_G + BOT_GE, CE + PE. Stop distance held to 3%..6% of
# the entry premium, then a separate hard limit in points, then tick
# rounding; R/BE/TSL-arm/P1/P2 are computed from the adjusted stop.
# 6% ~ 8 pts at a typical 130 premium. Hard limit 12 pts = Rs780/lot.
BOTG_STOP_BAND_ENABLED = True
BOTG_STOP_MIN_PCT      = 0.03
BOTG_STOP_MAX_PCT      = 0.06
BOTG_STOP_HARD_MAX_PTS = 12.0     # separate absolute cap, applied even if band OFF
BOTG_STOP_TICK         = 0.05

# v-E17 CE profit lock -- configurable, OFF. When ON: once a CE trade's high
# reaches entry + TRIGGER_R x R, SL moves to entry + LEVEL_R x R.
BOTG_CE_PROFIT_LOCK_ENABLED   = False
BOTG_CE_PROFIT_LOCK_MAIN_ONLY = True    # True: BOT_G only (BOT_GE untouched)
BOTG_CE_LOCK_TRIGGER_R        = 0.5
BOTG_CE_LOCK_LEVEL_R          = 0.1

# =============================================================================
# vE6.2 (17-Oct-2026)
# =============================================================================
# v-E19 trackers (log-only): follow each exited option and each skipped CE.
BOTG_TRACK_ENABLED   = True
BOTG_TRACK_MIN       = 30     # minutes to follow
BOTG_TRACK_POLL_SEC  = 10     # one batched quote call per poll (Prime plan ok)
BOTG_TRACK_MAX       = 6      # max symbols followed at once
# v-E20 day type (log-only)
BOTG_DAYTYPE_TREND_PCT = 0.40   # |% from day open| for TREND_UP/DOWN
BOTG_DAYTYPE_RANGE_POS = 0.70   # and spot in the top (bottom) 30% of the day range
# v-E30 (vE6.2.2): re-try an undetermined gap check every 3 min until this time
BOTG_GAP_RECHECK_UNTIL_HHMM = 930
# v-E31 (vE6.2.3): ZLM (Zero-Line Momentum) SHADOW -- LOG-ONLY, no orders.
# See claude/nifty-spot-momentum-study.md. False = completely off.
ZLM_SHADOW_ENABLED = True
ZLM_MARGIN_PTS = 10             # Nifty must be this far beyond ref +/- band
ZLM_BAND_END_PTS = 20           # band 0 at 09:20 widening to this at 15:30
ZLM_TRAIL_ARM_PCT = 0.10        # trail starts once LTP is +10% over entry
ZLM_TRAIL_PCT = 0.10            # then exit on a 10% fall from the peak LTP
ZLM_LAST_ENTRY_HHMM = 1500
ZLM_EOD_HHMM = 1510
ZLM_LOT_QTY = 65
ZLM_CHARGES_PER_TRADE = 65      # Rs, for the per-lot result in the log/CSV
ZLM_GUARD_MAX_FLIPS = 2         # ZLM-G variant: no new entry after this many lock flips
ZLM_STATUS_EVERY_MIN = 3
ZLM_REF_MIN_TICKS = 3           # fewer 09:15-09:19 readings -> 09:15 candle fallback
ZLM_CSV_DIR = "."
ZLM_REF_MODE = "CLOSE915"   # v-E44 (vE6.7): zero line = closed 09:15 3m candle close; "TICKAVG" = old spot average
ZLM_WRITE_CSV = False          # v-E41 (vE6.5): zlm_shadow CSV off (same lines are in the log)
# v-E35 (vE6.2.4): setup tags CSV -- LOG-ONLY (see setup_tags_nifty_vE6.py)
TAG_SETUP_ENABLED = True
TAG_BIG_PCT_1 = 0.5             # big morning: |gap| or |ext_1015| >= this % (main flag)
TAG_BIG_PCT_2 = 0.75            # second flag
TAG_WIDE_PCT = 8.0              # wide_flag when stop > this % of entry
TAG_LOT_BUDGETS = (1500, 2000, 3000)   # Rs risk per trade -> lots_b1/b2/b3 (0 = would not trade)
TAG_MAX_LOTS = 4
TAG_LOT_QTY = 65
# v-E36 (vE6.3): exit what-if shadow -- LOG-ONLY (exit_whatif_nifty_vE6.py)
WHATIF_ENABLED = True
WHATIF_EB_R = 0.6       # early bank: book WHATIF_EB_LOTS lot(s) at entry + 0.6 x R
WHATIF_EB_LOTS = 1
WHATIF_TS_MIN = 5       # time stop: exit all if not reached entry + WHATIF_TS_R x R within this many minutes
WHATIF_TS_R = 0.3
WHATIF_LOT_QTY = 65
# v-E39 (vE6.4): common first DPCR anchor from the closed 09:15 3-min candle close
V39_COMMON_ANCHOR = True
V39_ANCHOR_WAIT_UNTIL_HHMM = 920   # wait for the reference until this time, then live spot
V39_ANCHOR_REF_UNTIL_HHMM = 930    # the reference is used for a first anchor only before this time
# v-E40 (vE6.5): min-stop what-if plans (log-only) + LOW STOP flag
WHATIF_MS_PTS = (4.0, 5.0)    # MS4 / MS5: initial stop at least this many points below entry
WHATIF_LOW_STOP_PTS = 4.0     # WHATIF START line flags 'LOW STOP' when R is below this
WHATIF_TAIL_MAX_MIN = 35      # MS plans after a real stop-out: give up after this many minutes
# v-E41 (vE6.5): fewer files
V40_DAILY_ZIP = True               # upload_YYYYMMDD_<broker>.zip at shutdown
V40_WRITE_SUMMARY_CSV = False      # summary_*.csv (the log summary block is still written)
V40_WRITE_POST_EXIT_PATHS = False  # post_exit_paths_*.csv (post_exit_summary still written)
# v-E43 (vE6.6): ZLM check at entry (log + setup-tag detail only)
V43_ZLM_TAG = True
# v-E45 (vE6.8): ENTRY CONTEXT line (DPCR / ZLM / spot 15-30 min / flow tier), log-only
V45_ENTRY_CONTEXT = True
V45_SPOT_AGAINST_PTS = 20   # spot 15-min move against the trade side that counts as AGAINST
# v-E46 (vE6.9): shadow lock, zone +/-0.10 + spot 30-min sync (log-only)
V46_SHADOW_LOCK = True
V46_ZONE = 0.10
V46_SYNC_PTS = 10          # spot 30-min change that counts as 'in sync' (CE up / PE down)
# v-E47 (vE6.9): option tape -- 1-min OHLCV of the day's ATM +/-4 strikes at shutdown (log-only)
V47_OPTION_TAPE = True
V47_STEPS = 4
V47_MAX_SYMBOLS = 80
V47_SLEEP_SEC = 0.25
# v-E42 (vE6.6): 09:18 OI pre-snapshot = first DPCR baseline when the 09:15 reference is late
V42_RMONEY_PRE_SNAPSHOT = True
# v-E21 data lost
BOTG_DATA_LOST_SEC = 300        # stale this long with an open trade -> DATA_LOST
# v-E22 charges -- ESTIMATES, VERIFY AGAINST YOUR CONTRACT NOTE.
# NSE index options, from 1-Apr-2026: STT 0.15% on sell premium; NSE txn
# 0.03553% of premium; SEBI Rs10/crore; stamp 0.003% on buy; GST 18% on
# brokerage + txn + SEBI. Brokerage per executed order: set for your plan.
CHG_BROKERAGE_PER_ORDER = 1.0   # v-E37 (vE6.3): Anu's real brokerage (was 20.0)
CHG_STT_SELL_PCT        = 0.15
CHG_TXN_PCT             = 0.03553
CHG_SEBI_PER_CRORE      = 10.0
CHG_STAMP_BUY_PCT       = 0.003
CHG_GST_PCT             = 18.0
