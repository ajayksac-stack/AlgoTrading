# =============================================================================
#  config_fyers_sensex_g_pool_v8_9.py  --  SENSEX WEEKLY OPTIONS BOT (Fyers)  [PAPER]
#  v8 (18-Oct-2026): BUILT FROM THE NIFTY vE6.2 CONFIG. Every name, section and
#  default is Nifty's; only the lines tagged "# v8 Sensex:" differ (the Nifty value
#  is quoted at the end of each such line), plus the block "SENSEX-ONLY (v8)" at the
#  bottom. Decisions of 18-Oct: 4 lots on both Sensex brokers; SL-VWAP clamp ON +
#  continuous (as Nifty); P1 0.9R/4% and last entry 14:30 (as Nifty); logging as Nifty.
#  Nifty vE6.2 header follows.
# =============================================================================
# =============================================================================
#  config_fyers_nifty_g_pool_vE4.py  --  NIFTY WEEKLY OPTIONS BOT (Fyers)
#  vE4 (05-Oct-2026): copy of config_fyers_nifty_g_pool_v3.py for
#  BOT_fyers_nifty_g_pool_vE4.py. Additions: BOT_GE early-slot block
#  (after BOTG_PATH_FLUSH_ROWS) and "BOT_GE" in ACTIVE_BOTS. Every BOT_G
#  value is identical to v3.2.
#  v3 (30-Sep-2026): copy of config_fyers_nifty_g_pool_v2.py for
#  BOT_fyers_nifty_g_pool_v3.py. Only additions: the v-G81 diagnostic
#  constants below BOTG_FLOW_FLAT_EPS and v-G83 BOTG_POST_ENTRY_MARKS_MIN /
#  v-G84 BOTG_PATH_* (all log-only). Every trading value is
#  identical to v2.
#  BOT_G only -- multi-strike VIX pool (DPCR + Option-VWAP strategy)
#  Updated: 2026-09-28 (v2: v-G70..v-G76)
#
#  ALL TUNABLE PARAMETERS for BOT_G live in this file.
#  BOT_fyers_nifty_g_pool_v2.py does `from config_fyers_nifty_g_pool_v2
#  import *` and does not hardcode a tunable value itself.
#
#  v2 (28-Sep-2026): renamed from config_fyers_nifty_g_pool_v1.py so the
#  new build cannot mix with the old one. New constants (all flag-gated,
#  set False to get the exact v1 behaviour back):
#    BOTG_SL_VWAP_CLAMP_CONTINUOUS        (v-G71, Section G, after SL buffer)
#    BOTG_DPCR_FALLING_BLOCK_SIDE_AWARE   (v-G72, Section G, after v-G28 thresholds)
#    BOTG_STREAK_COUNT_LOSSES_ONLY        (v-G73, Section H)
#    BOTG_FLOW_WINDOW_MIN / BOTG_FLOW_FLAT_EPS  (v-G75, Section G, log-only)
#
#  v-G13 (12-Aug-2026): split out from the shared BOT_A-F multi-bot config
#  into this standalone file.
#
#  v-G37 (05-Sep-2026): explicit instruction (04/05-Sep-2026 session) --
#  BOT_GG REMOVED ENTIRELY. Only one bot (BOT_G) runs now, and only one
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
#    G) BOT_G / BOT_GG Strategy  Q) Strike Selection / Rounding (legacy)
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
#  KEY HISTORY (BOT_G/BOT_GG only):
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
#  v-G12       BOT_GG added -- shares every function with BOT_G, differs
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
#              cooldown of any kind for BOT_G/BOT_GG -- confirmed, by
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
#  NOTE: helper_fyers.py is never modified by this file or any patch after
#  it -- all changes here are config + main-script only, per standing policy.
# =============================================================================

#  A) MODE & SAFETY
# ─────────────────────────────────────────────────────────────────────────────
PAPER_TRADE  = True          # True = paper (prints only, no real orders)
# False = LIVE — double-check ACTIVE_BOTS below

# v-RG-sync (this session): ported from the vRG2 execution-safety review
# that was previously done on this file but never merged back into the
# ongoing delivery -- confirmed missing entirely from this line of
# development until now, while RMoney's equivalent fix (v-RG3) had
# already been merged and carried forward. This brings Fyers back to
# parity with RMoney's current execution-safety level, per explicit
# instruction to synchronize before any further strategy work.
LIVE_TRADING_ARMED = False   # second independent switch; must be True in addition to PAPER_TRADE=False
LIVE_REQUIRE_BROKER_SL = True

ACTIVE_BOTS  = ["BOT_G", "BOT_GE"]   # vE4: + early-entry slot  # v-G37: BOT_GG removed entirely -- single bot,
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
LOT_SIZE     = 20   # v8 Sensex: BSE Sensex lot size (Nifty: 65)
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
# Not read by BOT_G/BOT_GG -- they deliberately skip this generic cooldown in
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
#  G) BOT_G / BOT_GG — OPTION CHAIN DPCR STRATEGY  (v-G1, piece 1: expiry + strike)
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
# 2026 session). REPLACES the old single-strike VIX ladder + BOT_GG's
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
BOTG_STRIKE_POOL_LOW  = [0, 1]   # v8 Sensex: fixed ATM+OTM1 - Sensex liquidity (Nifty: [0, 1, 2])
BOTG_STRIKE_POOL_MID  = [0, 1]   # v8 Sensex: fixed ATM+OTM1 (Nifty: [1, 2, 3])
BOTG_STRIKE_POOL_HIGH = [0, 1]   # v8 Sensex: fixed ATM+OTM1 (Nifty: [2, 3, 4])

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
QTY_BOT_G_LOW_VIX  = 4 * LOT_SIZE   # v8 Sensex: 4 lots fixed on Sensex - set to 8*LOT_SIZE to restore the Nifty VIX<=13 ladder (Nifty: 8 * LOT_SIZE)
QTY_BOT_G_HIGH_VIX = 4 * LOT_SIZE   # v8 Sensex: 4 lots fixed on Sensex (Nifty: 4 * LOT_SIZE)

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
BOTG_DPCR_WINDOW_BY_WEEKDAY = {   # v8 Sensex: weekly expiry is THURSDAY (Nifty: Tuesday)
    4: 5,   # Friday   : ATM +/- 5
    0: 4,   # Monday   : ATM +/- 4
    1: 3,   # Tuesday  : ATM +/- 3
    2: 2,   # Wednesday: ATM +/- 2
    3: 2,   # Thursday : ATM +/- 2 (expiry)
}
BOTG_DPCR_WINDOW_DEFAULT = 4   # fallback only -- NIFTY never actually
                                 # trades on a day not in the map above.

# v-G11/v-G57: two-stage hybrid partial booking; v-G57 moves P1 to max(0.90R, 4%)
# (12-Aug-2026 session), replacing the old single BE(0.75R)+TSL(1.5R-arm)-
# only scheme with: book 50% at 1R, another 25% at 1.5R, remaining 25%
# still trails via the EXISTING BE/TSL machinery in manage_bot_g_exit() --
# BOTG_BE_R_MULT/BOTG_TSL_ARM_R_MULT/BOTG_TSL_BUFFER_PTS below are
# unchanged and still apply to whatever quantity remains after both
# partial stages. Fractions are of the ORIGINAL qty_base, not the
# remaining qty at each stage -- confirmed by construction (8 or 4 lots),
# always whole-lot, no rounding helper needed.
BOTG_PARTIAL_R1_MULT     = 0.90    # first partial trigger, in R (risk_pts)
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
BOTG_PARTIAL_R1_PCT_FLOOR  = 0.04    # 4% of entry premium
BOTG_PARTIAL_R15_PCT_FLOOR = 0.075   # 7.5% of entry premium

# v-G36: per-bot daily profit cap, explicit instruction, same 28-Aug
# investigation. Once a bot's OWN cumulative realized P/L for the day
# reaches this, that bot stops taking NEW entries for the rest of the
# session -- explicitly a HARD STOP (not a trailing lock the bot can
# resume trading under if PnL dips back below the cap), per explicit
# choice: "in this case bot will keep running even when there is a
# small profit say 200 or 500" was the REJECTED alternative (a trailing
# mechanism), not this one. BOT_G and BOT_GG are capped INDEPENDENTLY --
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
BOTG_GAP_THRESHOLD_PCT      = 0.75   # v8.5 (2-Nov-2026, Anu): was 1.0. REAL (explicit instruction)
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
# this setting -- see that function's docstring.
BOTG_ROLLOVER_MAX_DAYS_LEFT = 1

# v-G15 (13-Aug-2026): NO NEW entries after this time, for BOTH BOT_G and
# BOT_GG. Real, explicit instruction based on an observed pattern (option
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
BOTG_NEAR_VWAP_PTS = 30.0   # v8 Sensex: = upper edge of the asymmetric band below; kept for names that still read it (Nifty: 4.0)
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
BOTG_CQ_UPPER_SHADOW_WARN_PTS = 14.0   # v8 Sensex: Sensex-scaled (Nifty: 2.05)
BOTG_CQ_UPPER_SHADOW_VERY_LARGE_PTS = 27.0   # v8 Sensex: Sensex-scaled (Nifty: 3.70)
BOTG_CQ_RANGE_WARN_PTS = 48.0   # v8 Sensex: Sensex-scaled (Nifty: 6.0)
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
# in the meantime.
BOTG_VOLUME_BASELINE_CANDLES_SHORT = 3    # research window option 1
BOTG_VOLUME_BASELINE_CANDLES_MID   = 5    # research window option 2 (used for the primary tier)
BOTG_VOLUME_BASELINE_CANDLES_LONG  = 20   # research window option 3 (v-G51's original)

# Level 1 -- volume strength tiers (relative to the mid/5-candle baseline)
BOTG_VOLUME_TIER_WEAK_MAX   = 0.75   # < this -> WEAK
BOTG_VOLUME_TIER_NORMAL_MAX = 1.25   # WEAK..this -> NORMAL, above -> STRONG.. see next
BOTG_VOLUME_TIER_STRONG_MAX = 1.75   # NORMAL..this -> STRONG, above -> VERY_STRONG

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
# example to check it against.
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
BOTG_CONFIRM_VWAP_LOWER_TIGHT = -3.20   # v8 Sensex: Sensex-scaled confirmation band (Nifty: -1.00)
BOTG_CONFIRM_VWAP_UPPER_TIGHT =  18.00   # v8 Sensex: Sensex-scaled confirmation band (Nifty: 4.00)
BOTG_CONFIRM_VWAP_LOWER_MID   = -4.80   # v8 Sensex: Sensex-scaled confirmation band (Nifty: -1.50)
BOTG_CONFIRM_VWAP_UPPER_MID   =  22.00   # v8 Sensex: Sensex-scaled confirmation band (Nifty: 5.00)
BOTG_CONFIRM_VWAP_LOWER_WIDE  = -5.60   # v8 Sensex: Sensex-scaled confirmation band (Nifty: -1.75)
BOTG_CONFIRM_VWAP_UPPER_WIDE  =  25.00   # v8 Sensex: Sensex-scaled confirmation band (Nifty: 5.50)
BOTG_CONFIRM_VWAP_LOWER_XWIDE = -6.40   # v8 Sensex: Sensex-scaled confirmation band (Nifty: -2.00)
BOTG_CONFIRM_VWAP_UPPER_XWIDE =  27.00   # v8 Sensex: Sensex-scaled confirmation band (Nifty: 6.00)
BOTG_CONFIRM_VWAP_LOWER_TOL = -3.20   # v8 Sensex: Sensex-scaled confirmation band (Nifty: -1.00)
BOTG_CONFIRM_VWAP_UPPER_TOL =  18.00   # v8 Sensex: Sensex-scaled confirmation band (Nifty: 4.00)
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
BOTG_TSL_BUFFER_PTS = 25.0   # v8 Sensex: Sensex-scaled (Nifty: 8.0)
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
# best-scoring value. Re-check this whenever revisited again.
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
# zone. Kept identical to the RMoney config.
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
# considered as a decision input.
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
BOTG_FLOW_FLAT_EPS   = 50000   # v8 Sensex: Sensex 25th percentile of |9-min change| (PLACEHOLDER) (Nifty: 500000)
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
BOTGE_ENABLED                  = True
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
BOTGE_TSL_BUFFER_MIN_PTS       = 10.0   # v8 Sensex: Sensex-scaled (Nifty: 3.0)
BOTGE_TSL_BUFFER_MAX_PTS       = 25.0   # v8 Sensex: Sensex-scaled (Nifty: 8.0)
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
STRIKE_ROUND_UNIT       = 100   # v8 Sensex: Sensex strike spacing (Nifty: 50)
# (this config no longer has a live consumer for it -- BOT_G/BOT_GG use
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
STRIKE_LIQUID_GRID      = 100   # v8 Sensex: Sensex (unused by BOT_G) (Nifty: 100)
#  R) EXECUTION ENGINE — internal timing
# ═════════════════════════════════════════════════════════════════════════════
EXEC_SPREAD_BUFFER_FRACTION = 0.30
EXEC_CANCEL_WAIT_SEC        = 0.5
EXEC_SPREAD_FALLBACK_PCT    = 0.01
# v-G55 (bug fix): this constant was defined but never actually read
# anywhere -- _wait_for_fill() hardcoded 0.25 directly. Confirmed via
# independent review. Set to 0.25 here (not the pre-existing 0.5) so
# wiring it in changes nothing about actual runtime behavior; the poll
# interval is now genuinely configurable in one place instead of a
# hardcoded magic number, but today's fill-detection speed is unchanged.
EXEC_FILL_POLL_WAIT_SEC     = 0.25

# v-G57 (bug fix): LIVE_FILL_TIMEOUT_SEC was referenced by _wait_for_fill()
# but never defined anywhere in this config -- confirmed via independent
# cross-file check: this would have raised NameError on the very first
# LIVE entry or partial-exit fill-wait, a hard crash on first live order
# despite the "LIVE_READY" label. RMoney's equivalent build already had
# this properly defined (LIVE_FILL_TIMEOUT_SEC = 5.0) -- using the same
# value here for consistency between the two bots' fill-wait behavior.
LIVE_FILL_TIMEOUT_SEC       = 5.0

# =============================================================================
#  END CONFIG — do not edit below this line unless you know what you're doing
# =============================================================================

# ── Derived portfolio limits (auto-set from PAPER_TRADE above) ────────────────
# NOTE: the hardcoded "6" in PAPER_TRADE mode predates the BOT_G/BOT_GG split
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
BSE_TRADING_HOLIDAYS = [   # v8 Sensex (was NSE_TRADING_HOLIDAYS). ADD 2027 BEFORE 1-Jan-2027.
    "2026-01-15", "2026-01-26", "2026-02-15", "2026-03-03",
    "2026-03-21", "2026-03-26", "2026-03-31", "2026-04-03",
    "2026-04-14", "2026-05-01", "2026-05-28", "2026-06-26",
    "2026-08-15", "2026-09-14", "2026-10-02", "2026-10-20",
    "2026-11-08", "2026-11-10", "2026-11-24", "2026-12-25",
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
BOTG_CE_CALLADD_SKIP_ENABLED   = False   # v8 Sensex: CE call-add skip OFF on Sensex; cflow columns still logged (Nifty: True)
BOTG_CE_CALLADD_SKIP_MIN       = 9
BOTG_CE_CALLADD_SKIP_THRESHOLD = 50000   # v8 Sensex: Sensex scale (only used if the skip is switched on) (Nifty: 500000)
# the entry premium, then a separate hard limit in points, then tick
# rounding; R/BE/TSL-arm/P1/P2 are computed from the adjusted stop.
# 6% ~ 8 pts at a typical 130 premium. Hard limit 12 pts = Rs780/lot.
BOTG_STOP_BAND_ENABLED = False   # v8 Sensex: stop band OFF on Sensex (3-6% band kept for the day it is switched on) (Nifty: True)
BOTG_STOP_MIN_PCT      = 0.03
BOTG_STOP_MAX_PCT      = 0.06
BOTG_STOP_HARD_MAX_PTS = float("inf")   # v8 Sensex: no hard max on Sensex (Nifty: 12.0)
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
# v-E21 data lost
BOTG_DATA_LOST_SEC = 300        # stale this long with an open trade -> DATA_LOST
# v-E22 charges -- ESTIMATES, VERIFY AGAINST YOUR CONTRACT NOTE.
# NSE index options, from 1-Apr-2026: STT 0.15% on sell premium; NSE txn
# 0.03553% of premium; SEBI Rs10/crore; stamp 0.003% on buy; GST 18% on
# brokerage + txn + SEBI. Brokerage per executed order: set for your plan.
CHG_BROKERAGE_PER_ORDER = 15.0   # v8.3.2: real brokerage per executed order (Fyers); was a Rs20 placeholder
CHG_STT_SELL_PCT        = 0.15
CHG_TXN_PCT             = 0.0325   # v8 Sensex: BSE index options transaction charge 0.0325% of premium (VERIFY vs contract note) (Nifty: 0.03553)
CHG_SEBI_PER_CRORE      = 10.0
CHG_STAMP_BUY_PCT       = 0.003
CHG_GST_PCT             = 18.0


# =============================================================================
#  SENSEX-ONLY (v8) -- the only names that Nifty's config does not have
# =============================================================================
# Entry rejection band: asymmetric, in option points around the option's VWAP
# (Nifty uses +/-BOTG_NEAR_VWAP_PTS). Accepted on Sensex 10-Oct, provisional.
BOTG_NEAR_VWAP_LOWER_PTS = -20.0
BOTG_NEAR_VWAP_UPPER_PTS =  30.0
# Skip a confirmed entry whose stop is closer than this (option points).
BOTG_MIN_RISK_ENABLED = True
BOTG_MIN_RISK_PTS     = 15.0
# DPCR re-anchor: half the window's reach, but not less than this floor
# (Wed/Thu windows are +/-2 strikes = 100 pts reach -> floor 150).
BOTG_REANCHOR_MIN_PTS_BY_WEEKDAY = {2: 150, 3: 150}
# Spot history for the gap check: calendar days fetched (Nifty: 2). 2 days on a
# Monday starts on Saturday, so Friday's session is missing -> gap status unknown.
BOTG_HISTORY_LOOKBACK_DAYS = 4


# =============================================================================
#  v8.1 (19-Oct-2026) -- Sensex additions (decisions of Anu, 19-Oct)
# =============================================================================
# 1. Pre-open gate. Fyers returns yesterday's last candle until 09:15, so a bot started early made two
#    failed API calls every 3 s and wrote ~2,200 error lines (19-Oct). No data calls before this time.
BOTG_PREOPEN_GATE_ENABLED     = True
BOTG_PREOPEN_RESUME_HHMMSS    = "09:14:30"
BOTG_PREOPEN_STATUS_SEC       = 600       # one status line per this many seconds while waiting
# 2. "OPTION SYMBOL" log line: 49% of the 19-Oct Fyers log. False = print only when the symbol for a
#    (bot, side, OTM step) changes, or every BOTG_OPTSYM_LOG_HEARTBEAT_SEC seconds. True = Nifty behaviour.
BOTG_OPTSYM_LOG_EVERY_CALL    = False
BOTG_OPTSYM_LOG_HEARTBEAT_SEC = 300
# 3. VWAP research (log-only): vwap_research_*.csv + pool_bars_*.csv. Never read by trading logic.
BOTG_VWAP_RESEARCH_ENABLED    = True
BOTG_VWAP_RESEARCH_START_HHMM = 920
BOTG_VWAP_RESEARCH_ROLL_BARS  = 12        # rolling-VWAP window, 5m bars (= 60 min)
BOTG_VWAP_RESEARCH_DEFAULT_POOL = [0, 1]  # used until the 10:15 pool lock sets bot["otm_pool"]
BOTG_V81_BARS_DUMP_HHMM       = 1505      # final bars flush at this time (and at shutdown if not yet done)
# v8.1.1 (20-Oct-2026): intraday flushes of pool_bars_*.csv / pool_bars_10m_*.csv / spot_bars_*.csv (log-only).
# A restart after one of these times flushes once. Each flush = one extra spot-history call.
BOTG_V811_BARS_FLUSH_HHMM     = [1030, 1130, 1230, 1330, 1430]
# 4. Paper stop fill at the stop level (Fyers; the RMoney bot defines the same name in its BOT file).
G4_PAPER_STOP_AT_TRIGGER      = True

# =============================================================================
# v8.2 (24-Oct-2026) -- ZLM shadow (LOG-ONLY; Nifty v-E31). Nifty values x ~3.3 for Sensex: UNTESTED, tune from the shadow CSV.
# =============================================================================
ZLM_SHADOW_ENABLED    = True
ZLM_MARGIN_PTS        = 33      # Nifty 10
ZLM_BAND_MAX_PTS      = 65      # band 0 at 09:20 -> this at 15:30 (Nifty 20)
ZLM_ENTRY_CUTOFF_HHMM = 1500
ZLM_EXIT_HHMM         = 1510
ZLM_TRAIL_ARM_PCT     = 10      # trail arms once the premium is +10% from entry ...
ZLM_TRAIL_PCT         = 10      # ... and exits when it falls 10% from its peak
ZLM_G_MAX_FLIPS       = 2       # "ZLM-G" book: no new entry after this many lock flips
ZLM_LOT_QTY           = 20      # Sensex lot, for the Rs-per-lot column only

# =============================================================================
# v8.3 (26-Oct-2026) -- setup tags (LOG-ONLY): setup_tags_*.csv. Nothing here changes an entry, exit or lot count.
# =============================================================================
TAG_LOG_ENABLED     = True
TAG_WIDE_STOP_PCT   = 8.0                # wide_flag = stop > this % of entry
TAG_CAP_PCTS        = (5, 6, 7, 8)       # capN_pts = stop distance if capped at N % of entry
TAG_RISK_BUDGETS    = (3000, 4000, 5000) # lots_3k/4k/5k = floor(budget / (stop pts x lot qty)), max TAG_MAX_LOTS (0 = would not trade)
TAG_MAX_LOTS        = 4
TAG_LOT_QTY         = 20                 # Sensex lot
TAG_START_HHMMS     = (1130, 1200, 1300) # skip_tHHMM = 1 if this entry would fall before that start time
TAG_BIG_PCTS        = (0.5, 0.75)        # big_* = 1 if |gap| or |ext_1015| >= this %
TAG_COND_START_HHMM = 1200               # skip_cNN_t1200 = big_NN and time < this

# =============================================================================
# v8.3.2 (28-Oct-2026) -- realism / measurement fixes (see the bot header). Rules for entries, exits and lots are unchanged.
# =============================================================================
V832_ASK_FILL_ENABLED = True       # Fyers PAPER: fill at the ask + abort on a stale quote (RMoney has no ask feed)
V832_ASK_GUARD_PCT    = 1.5        # abort the entry if ask > signal premium x (1 + this %)
V832_GAP_FILL_ENABLED = True       # PAPER: stop exit after a data gap fills at the first post-gap LTP if that is below the stop
V832_GAP_FILL_SEC     = 30         # a gap = more than this many seconds since the open trade's previous good LTP tick
WHATIF_ENABLED = True              # log-only exit what-if (exit_whatif_*.csv + "WHATIF |" lines)
WHATIF_EB_R    = 0.6               # EB plan: bank WHATIF_EB_LOTS lot(s) at entry + this x R
WHATIF_EB_LOTS = 1
WHATIF_TS_SEC  = 300               # TS plan: exit everything if entry + WHATIF_TS_R x R has not been touched this long after entry
WHATIF_TS_R    = 0.3

# =============================================================================
# v8.3.3 (29-Oct-2026) -- log-only context tags + common first DPCR anchor (see the bot header). Entry / exit / sizing rules unchanged.
# =============================================================================
V833_COMMON_ANCHOR = True          # first DPCR anchor from the CLOSED 09:15 3m candle close on both brokers (normal days)
V833_ANCHOR_WAIT_UNTIL_HHMM = 920  # defer the first DPCR fetch until the 09:15 candle has closed; after this time use the live spot
V833_ANCHOR_REF_UNTIL_HHMM = 930   # a (re)start after this time anchors on the live spot, not the 09:15 close
V833_MOM_TAGS = True               # spot-momentum / DPCR-fresh / early-flow columns in setup_tags + "ENTRY CTX" log line (log-only)
V833_FK_MIN_PTS = 0                # falling-knife R1 (LOG-ONLY): side-signed spot change must be worse than -this over both 15 and 30 min
V833_SKIP_TRACK = True             # would-have tracker for MIN_RISK / STALE_QUOTE skips (needs BOTG_TRACK_ENABLED)

# =============================================================================
# v8.4 (30-Oct-2026) -- falling-knife R1 enforced (main slot) + ZLM-direction view (log-only). Everything else unchanged.
# =============================================================================
V84_FK_ENFORCE = True              # drop a main-slot setup when the falling-knife R1 condition holds (needs V833_MOM_TAGS = True)
V84_FK_BOTS = ("BOT_G",)           # which bots the enforcement applies to; the early slot (BOT_GE) is deliberately not listed
V84_ZDIR_TAGS = True               # ZLM-direction view: vwap_research zdir_* columns + "v8.4 ZDIR |" log line + ENTRY CTX suffix (log-only)
V84_ZDIR_FLOOR = 0.05              # carried DPCR must be at least this far on the trade side of zero (replay: flat from 0.01 to 0.05)
V84_ZDIR_FALL_TOL = 0.02           # the 3-candle DPCR change may be at most this much against the side

# =============================================================================
# v8.5 (2-Nov-2026) -- daily upload zip + gap-day threshold 0.75 % (BOTG_GAP_THRESHOLD_PCT above). Everything else unchanged.
# =============================================================================
V85_DAILY_ZIP = True               # write one upload zip at shutdown (originals stay untouched)
V85_ZIP_NAME = "upload_sensex_{ymd}_{broker}.zip"

# =============================================================================
# v8.6 (3-Nov-2026) -- two LOG-ONLY changes (no trading rule touched).
# =============================================================================
V86_GAP_IDLE_LOG = True             # gap day: one BOT_G "GAP DAY | idle" line every V86_GAP_IDLE_LOG_MIN minutes from 09:18 until the DPCR watch
V86_GAP_IDLE_LOG_MIN = 5
V86_ZLM_REF_CANDLE = True           # ZLM reference = close of the closed 09:15 3m candle (False = old average of spot polls 09:15-09:20)
V86_ZLM_REF_WAIT_UNTIL_HHMM = 930   # wait for the closed candle until this time, then fall back to the old method

# =============================================================================
# v8.7 (4-Nov-2026) -- Nifty vE6.9 ported, all LOG-ONLY (no trading rule touched).
# =============================================================================
V46_SHADOW_LOCK = True              # "SHADOW LOCK |" line every 3m candle from trade start (hypothetical lock: zone + spot-30m sync)
V46_ZONE = 0.10                     # carried DPCR zone for the shadow lock (real lock uses the VIX-scaled zone, tier 3 = 0.28)
V46_SYNC_PTS = 35                   # spot 30-min change must agree by this many points to accept a shadow lock / flip (Nifty: 10)
V47_GATE_AGAINST_PTS = 65           # ENTRY CTX "gate15+30" verdict threshold (both 15m and 30m move against the trade); the moves themselves are logged too
V47_OPTION_TAPE = True              # end-of-day 1-min OHLCV of the noted strikes -> option_tape_<ymd>_<broker>.csv (included in the upload zip)
V47_STEPS = 4                       # strikes noted: ATM +/- 4 steps (STRIKE_ROUND_UNIT = 100 pts), CE and PE
V47_MAX_SYMBOLS = 80                # fetch cap (nearest-to-ATM first)
V47_SLEEP_SEC = 0.25                # pause between symbol fetches
V47_TAPE_NAME = "option_tape_{ymd}_{broker}.csv"

# =============================================================================
# v8.8 (6-Nov-2026) -- shadow lock also needs the DPCR rising (LOG-ONLY).
# =============================================================================
V88_SHADOW_DPCR_RISE = True         # a shadow lock / flip to CE needs the carried DPCR up >= V88_DPCR_RISE over the last 3 candles (PE: down); False = v8.7 behaviour
V88_DPCR_RISE = 0.02

# =============================================================================
# v8.9 (9-Nov-2026) -- LOG-ONLY counterfactual tag for scans PAUSED by the DPCR no-trade zone.
# Real rule unchanged: |DPCR| < zone (0.28 at VIX 14-18) pauses entries. This only RECORDS, for each paused setup, whether it
# would have been released at |DPCR| >= zone - V89_PAUSE_MARGIN (0.25). It never arms, places or alters a trade.
# =============================================================================
V89_PAUSE_CF = True                 # False = no tag / no CSV (v8.8 behaviour)
V89_PAUSE_MARGIN = 0.03             # counterfactual release when the side-signed DPCR is within this of the zone edge (0.28 -> 0.25)
