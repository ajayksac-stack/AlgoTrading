"""
setup_tags_nifty_vE6.py -- vE6.2.4 (26-Oct-2026) v-E35 SETUP TAGS, LOG-ONLY
============================================================================
Same idea and columns as Sensex v8.3 `setup_tags_*` (Nifty lot 65, budgets
scaled). One CSV row per BOT_G/BOT_GE setup event so the stop-width and
start-time rules can be replayed later WITHOUT changing what the bot does:
  ARM, ARM_EXPIRED, ARM_DROPPED, ENTRY_ABORT, CE_SKIP, ENTRY
Pure functions + a CSV writer. No broker, order or bot-state access here.
"""
import os

HEADER = ("date,time,event,trade_id,bot,symbol,side,otm,locked_side,spot,day_open,gap_pct,ext_1015_pct,"
          "ext_src,pct_from_open,day_type,entry,sl,stop_pts,stop_pct,wide_flag,cap5_pts,cap6_pts,cap7_pts,"
          "cap8_pts,lots_b1,lots_b2,lots_b3,risk_inr_max_lots,skip_t1130,skip_t1200,skip_t1300,big_05,big_075,"
          "skip_c05_t1200,skip_c075_t1200,detail")


def _f(x, nd=2):
    try:
        return "" if x is None or x == "" else round(float(x), nd)
    except Exception:
        return ""


def build_row(now, event, trade_id, bot, symbol, side, otm, locked_side, spot, day_open, gap_pct, ext_pct,
              ext_src, pct_from_open, day_type, entry, sl, detail, cfg):
    """Return the CSV row as a list (strings/numbers). cfg: TAG_* settings."""
    hm = now.hour * 100 + now.minute
    stop_pts = stop_pct = wide = ""
    caps = ["", "", "", ""]
    lots = ["", "", ""]
    risk_max = ""
    e, s = _f(entry), _f(sl)
    if e != "" and s != "" and e > 0:
        stop_pts = round(e - s, 2)
        stop_pct = round(100 * stop_pts / e, 2)
        wide = 1 if stop_pct > cfg["wide_pct"] else 0
        caps = [round(min(stop_pts, c / 100.0 * e), 2) for c in (5, 6, 7, 8)]
        if stop_pts > 0:
            lots = [min(cfg["max_lots"], int(b // (stop_pts * cfg["lot_qty"]))) for b in cfg["budgets"]]
            risk_max = round(stop_pts * cfg["lot_qty"] * cfg["max_lots"], 0)
    g, x = _f(gap_pct, 3), _f(ext_pct, 3)

    def big(th):
        if g == "" and x == "":
            return ""
        return 1 if ((g != "" and abs(g) >= th) or (x != "" and abs(x) >= th)) else 0
    b05, b075 = big(cfg["big1"]), big(cfg["big2"])
    sc05 = "" if b05 == "" else (1 if b05 and hm < 1200 else 0)
    sc075 = "" if b075 == "" else (1 if b075 and hm < 1200 else 0)
    return [now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"), event, trade_id or "", bot, symbol or "",
            side or "", otm if otm is not None else "", locked_side or "", _f(spot), _f(day_open), g, x,
            ext_src or "", _f(pct_from_open, 3), day_type or "", e, s, stop_pts, stop_pct, wide, *caps, *lots,
            risk_max, 1 if hm < 1130 else 0, 1 if hm < 1200 else 0, 1 if hm < 1300 else 0, b05, b075, sc05,
            sc075, str(detail or "").replace(",", ";").replace("\n", " ")]


def write(path, row):
    new = not os.path.exists(path)
    with open(path, "a", encoding="utf-8") as fh:
        if new:
            fh.write(HEADER + "\n")
        fh.write(",".join(str(v) for v in row) + "\n")
