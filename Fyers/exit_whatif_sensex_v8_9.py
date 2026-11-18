# -*- coding: utf-8 -*-
"""
exit_whatif_sensex_v8_9.py  --  LOG-ONLY exit "what-if" replay for the Sensex BOT_G / BOT_GE bots (v8.3.2).

Shared by the Fyers and RMoney bots.  It contains NO broker code, places NO orders and never changes bot
state.  For every trade it replays the live LTP polls the bot already receives through four plans:

    BASE  replica of the bot's current exit ladder (BE, P1, P2, TSL, 90-min initial cap)
    EB    early bank: sell 1 lot at +0.6R; P1 then books one lot less (>= 1 lot always stays open)
    TS    time stop: exit everything if +0.3R has not been touched 5 minutes after entry and no target/EB was hit
    EBTS  both

Fills: at the polled LTP for time stops, at the target level for P1 / P2 / EB (as the paper bot does), at the
stop level for stop exits (the paper-stop rule G4.1) -- except after a data gap > gap_fill_sec, when a stop exit
fills at the first post-gap LTP if that is below the stop (same rule as the v8.3.2 bot).  A plan still open when
the real trade closes is closed at the real exit price.  P&L is GROSS (no charges).

Usage from the bot (all calls wrapped in try/except there):
    start(trade_id, ...), tick(trade_id, ltp), finish(trade_id, real_exit_px, actual_pnl, reason, csv_path, log)
"""
import csv
import os
import time
from datetime import datetime

PLANS = (("BASE", False, False), ("EB", True, False), ("TS", False, True), ("EBTS", True, True))

CSV_COLS = ["date", "trade_id", "bot", "side", "symbol", "entry_time", "entry", "risk_pts", "qty0",
            "p1_level", "p2_level", "be_level", "arm_level", "eb_level", "ts_level", "peak_r", "real_exit", "real_reason",
            "actual_pnl", "base_pnl", "eb_pnl", "ts_pnl", "ebts_pnl",
            "base_events", "eb_events", "ts_events", "ebts_events"]


def _lot_safe(target_qty, remaining, lot):
    if remaining <= 0:
        return 0
    lots = max(int(round(target_qty / float(lot))), 1)
    return int(min(lots * lot, remaining))


class _Plan(object):
    def __init__(self, name, eb, ts, c):
        self.name, self.eb, self.ts, self.c = name, eb, ts, c
        self.qty = c["qty0"]
        self.realized = 0.0
        self.stage = "INITIAL"
        self.sl = c["entry"] - c["risk"]
        self.armed = False
        self.hcs = c["entry"]
        self.p1_done = self.p2_done = self.eb_done = False
        self.eb_qty = 0
        self.closed = False
        self.exit_px = None
        self.exit_reason = ""
        self.events = []

    # -- bookkeeping -------------------------------------------------------
    def _book(self, q, px, tag):
        q = int(q)
        if q <= 0:
            return
        self.realized += q * (px - self.c["entry"])
        self.qty -= q
        self.events.append("%s@%s" % (tag, round(px, 2)))

    def _close(self, px, reason):
        if self.closed:
            return
        self.realized += self.qty * (px - self.c["entry"])
        self.events.append("%s@%s" % (reason, round(px, 2)))
        self.qty = 0
        self.closed = True
        self.exit_px = px
        self.exit_reason = reason

    # -- one LTP poll ------------------------------------------------------
    def step(self, ltp, t, high, gap_s):
        if self.closed or ltp <= 0:
            return
        c = self.c
        e = c["entry"]
        lot = c["lot"]
        # 90-min initial-stage cap (THETA_DECAY_EXIT)
        if self.stage == "INITIAL" and c.get("max_hold_min") and (t - c["t0"]) >= c["max_hold_min"] * 60:
            self._close(ltp, "THETA")
            return
        # early bank (EB plans): once, at +eb_r R, keeps >= 1 lot open
        if self.eb and not self.eb_done and high >= c["eb_level"]:
            q = min(c["eb_lots"] * lot, self.qty - lot)
            self.eb_done = True
            if q > 0:
                self.eb_qty = q
                self._book(q, c["eb_level"], "EB")
        # P1 / P2 (planned size minus anything already banked early; >= 1 lot stays open)
        if not self.p1_done and high >= c["p1_level"]:
            self.p1_done = True
            q = _lot_safe(c["qty0"] * c["p1_frac"], self.qty, lot) - self.eb_qty
            if self.eb:
                q = min(q, self.qty - lot)   # EB plans always keep >= 1 lot open
            if q > 0:
                self._book(q, c["p1_level"], "P1")
        if not self.p2_done and high >= c["p2_level"]:
            self.p2_done = True
            q = _lot_safe(c["qty0"] * c["p2_frac"], self.qty, lot)
            if self.eb:
                q = min(q, self.qty - lot)
            if q > 0:
                self._book(q, c["p2_level"], "P2")
        if self.qty <= 0:
            self.closed = True
            return
        # stop / BE / TSL (mirror of manage_bot_g_exit)
        if ltp <= self.sl:
            px = self.sl
            if gap_s is not None and gap_s > c["gap_fill_sec"] and ltp < self.sl:
                px = ltp
            self._close(px, "TSL" if self.stage == "TRAILING" else "BE" if self.stage == "BREAKEVEN" else "SL")
            return
        if self.stage != "TRAILING" and high >= c["be_level"] and self.sl < e:
            self.sl = e
            self.stage = "BREAKEVEN"
        if high >= c["arm_level"]:
            self.armed = True
        if self.armed:
            if ltp > self.hcs:
                self.hcs = ltp
            new_sl = self.hcs - c["tsl_buf"]
            if new_sl > self.sl:
                self.sl = new_sl
                self.stage = "TRAILING"
                if ltp <= self.sl:
                    self._close(self.sl, "TSL")
                    return
        # time stop (TS plans): +ts_r R never touched ts_sec after entry, nothing banked
        if (self.ts and not self.closed and (t - c["t0"]) >= c["ts_sec"]
                and high < c["ts_level"] and not (self.p1_done or self.eb_done)):
            self._close(ltp, "TIMESTOP")


class WhatIf(object):
    def __init__(self, trade_id, c):
        self.trade_id = trade_id
        self.c = c
        self.high = c["entry"]
        self.prev_t = None
        self.plans = [_Plan(n, eb, ts, c) for (n, eb, ts) in PLANS]

    def tick(self, ltp, t):
        if ltp is None or ltp <= 0:
            return
        gap = None if self.prev_t is None else (t - self.prev_t)
        self.prev_t = t
        self.high = max(self.high, ltp)
        for p in self.plans:
            p.step(ltp, t, self.high, gap)

    def finish(self, real_exit_px):
        for p in self.plans:
            if not p.closed:
                p._close(real_exit_px, "REAL_EXIT")
        return dict((p.name, p) for p in self.plans)


_ACTIVE = {}
_ERR = {"n": 0}


def start(trade_id, bot_name, side, symbol, entry, risk_pts, qty0, entry_epoch, entry_time,
          p1_level, p2_level, be_level, arm_level, p1_frac, p2_frac, tsl_buf, lot,
          max_hold_min=90, eb_r=0.6, eb_lots=1, ts_sec=300, ts_r=0.3, gap_fill_sec=30, log=None):
    c = dict(bot=bot_name, side=side, symbol=symbol, entry=float(entry), risk=float(risk_pts), qty0=int(qty0),
             t0=float(entry_epoch), entry_time=entry_time, p1_level=float(p1_level), p2_level=float(p2_level),
             be_level=float(be_level), arm_level=float(arm_level), p1_frac=p1_frac, p2_frac=p2_frac,
             tsl_buf=float(tsl_buf), lot=int(lot), max_hold_min=max_hold_min,
             eb_level=float(entry) + eb_r * float(risk_pts), eb_lots=int(eb_lots), ts_sec=ts_sec,
             ts_level=float(entry) + ts_r * float(risk_pts), gap_fill_sec=gap_fill_sec)
    _ACTIVE[trade_id] = WhatIf(trade_id, c)
    if log:
        log("%s WHATIF START | %s entry %s risk %s | EB +%sR=%s (%s lot) | TS +%sR=%s within %ss | P1 %s P2 %s BE %s ARM %s buf %s "
            "(v8.3.2, log-only)" % (bot_name, trade_id, c["entry"], c["risk"], eb_r, round(c["eb_level"], 2), eb_lots, ts_r,
                                     round(c["ts_level"], 2), ts_sec, round(c["p1_level"], 2), round(c["p2_level"], 2),
                                     round(c["be_level"], 2), round(c["arm_level"], 2), c["tsl_buf"]))


def tick(trade_id, ltp, t=None):
    w = _ACTIVE.get(trade_id)
    if w is not None:
        w.tick(ltp, time.time() if t is None else t)


def finish(trade_id, real_exit_px, actual_pnl, reason, csv_path, log=None):
    w = _ACTIVE.pop(trade_id, None)
    if w is None:
        return None
    res = w.finish(float(real_exit_px))
    c = w.c
    pn = dict((k, round(p.realized, 2)) for k, p in res.items())
    ev = dict((k, ";".join(p.events)) for k, p in res.items())
    peak_r = round((w.high - c["entry"]) / c["risk"], 2) if c["risk"] else ""
    row = [datetime.now().strftime("%Y-%m-%d"), trade_id, c["bot"], c["side"], c["symbol"], c["entry_time"], c["entry"],
           c["risk"], c["qty0"], round(c["p1_level"], 2), round(c["p2_level"], 2), round(c["be_level"], 2),
           round(c["arm_level"], 2), round(c["eb_level"], 2), round(c["ts_level"], 2), peak_r, round(float(real_exit_px), 2),
           reason, round(float(actual_pnl), 2), pn["BASE"], pn["EB"], pn["TS"], pn["EBTS"],
           ev["BASE"], ev["EB"], ev["TS"], ev["EBTS"]]
    if csv_path:
        new = not os.path.exists(csv_path)
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            wr = csv.writer(f)
            if new:
                wr.writerow(CSV_COLS)
            wr.writerow(row)
    if log:
        log("%s WHATIF | %s actual %+.0f | BASE %+.0f | EB %+.0f | TS %+.0f | EBTS %+.0f | peak %sR | EB:[%s] TS:[%s] "
            "(v8.3.2, log-only, gross)" % (c["bot"], trade_id, float(actual_pnl), pn["BASE"], pn["EB"], pn["TS"],
                                            pn["EBTS"], peak_r, ev["EB"], ev["TS"]))
    return dict(pnl=pn, events=ev, peak_r=peak_r)
