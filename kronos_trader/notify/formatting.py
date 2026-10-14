"""Human-readable (Telegram HTML) rendering of analyses, setups and forecasts."""
from __future__ import annotations

import re
from html import escape
from typing import Iterable, Optional, Tuple

from ..config import SymbolSpec
from ..core.types import Analysis, Bias, ForecastSummary, POIStatus, TradeMode, TradeSetup

ARROWS = {Bias.BULLISH: "▲", Bias.BEARISH: "▼", Bias.NEUTRAL: "◆"}


def _price(value: float, spec: Optional[SymbolSpec]) -> str:
    decimals = spec.price_decimals if spec else 5
    return f"{value:.{decimals}f}"


def format_forecast(fc: ForecastSummary) -> str:
    return (f"Kronos {fc.timeframe.label} x{fc.horizon}: {ARROWS[fc.direction]} {fc.direction} "
            f"{fc.confidence:.0%} conf, {fc.pct_change:+.2f}% "
            f"(range {fc.expected_low:.5g}-{fc.expected_high:.5g}, {fc.paths} paths)")


def format_setup(setup: TradeSetup, forecast: Optional[ForecastSummary] = None, spec: Optional[SymbolSpec] = None) -> str:
    side = "BUY" if setup.direction.value > 0 else "SELL"
    pips = (lambda d: f"{d / spec.pip_size:.1f} pips") if spec else (lambda d: f"{d:.5g}")
    lines = [
        f"<b>{escape(setup.symbol)} {side}</b>  {setup.poi.timeframe.label} POI - {setup.confirmation.type.value} on {setup.confirmation.timeframe.label}",
        f"Entry <code>{_price(setup.entry, spec)}</code>",
        f"SL    <code>{_price(setup.stop, spec)}</code>  ({pips(abs(setup.entry - setup.stop))})",
        f"TP    <code>{_price(setup.take_profit, spec)}</code>  ({pips(setup.reward_distance)})",
        f"R:R <b>1:{setup.rr:.1f}</b>  |  {setup.lots:.2f} lots  |  risk {setup.risk_amount:,.0f}",
        f"Break-even after {setup.breakeven_r:.0f}R, no partials",
        f"POI {_price(setup.poi.low, spec)}-{_price(setup.poi.high, spec)} formed {setup.poi.created_at:%Y-%m-%d %H:%M}",
        f"TP source: {escape(setup.tp_source)}",
    ]
    if forecast is not None:
        lines.append(escape(format_forecast(forecast)))
    for note in setup.notes:
        lines.append(f"<i>{escape(note)}</i>")
    return "\n".join(lines)


def format_analysis(analysis: Analysis, spec: Optional[SymbolSpec] = None, max_pois: int = 6) -> str:
    lines = [f"<b>{escape(analysis.symbol)}</b> @ {_price(analysis.price, spec)}  ({analysis.timestamp:%Y-%m-%d %H:%M} UTC)"]
    bias_bits = []
    for tf, tb in analysis.biases.items():
        bias_bits.append(f"{tf.label} {ARROWS[tb.bias]}")
    lines.append("Bias: " + "  ".join(bias_bits))
    lines.append(f"Decision: {escape(analysis.decision.reason)}")
    pois = [p for p in analysis.pois if p.status is not POIStatus.INVALIDATED]
    pois.sort(key=lambda p: abs((p.low + p.high) / 2 - analysis.price))
    if pois:
        lines.append("Nearest POIs:")
        for p in pois[:max_pois]:
            lines.append(f"  {p.timeframe.label} {ARROWS[p.direction]} {_price(p.low, spec)}-{_price(p.high, spec)} [{p.status.value}]")
    for tf, fc in analysis.forecasts.items():
        lines.append(escape(format_forecast(fc)))
    if analysis.has_valid_signal:
        lines.append("")
        lines.append(format_setup(analysis.signal.setup, analysis.signal.forecast, spec))
    elif analysis.rejections:
        lines.append("No trade:")
        for r in analysis.rejections[:6]:
            lines.append(f"  - {escape(r)}")
    return "\n".join(lines)


# ---------------------------------------------------------------- the live Telegram messages, in Dutch (14 October, Max:
# "de telegram berichten duidelijker"): one short message a market, the decision in words, only the zones the bot can trade

TF_NAMES = {"1M": "maand", "1W": "week", "1D": "dag"}
TF_SHORT = {"1M": "M", "1W": "W", "1D": "D"}
WEEKDAYS = ("ma", "di", "wo", "do", "vr", "za", "zo")


def _tf_names(labels: str) -> str:
    parts = [TF_NAMES.get(x, x) for x in labels.split("+") if x]
    return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " en " + parts[-1]


def _side(word: str) -> str:
    return "long" if word.startswith("bull") else "short"


def plain_decision(decision, emoji: bool = True) -> str:
    """The bias decision in one line for the trader: what may be traded, or why nothing may (``emoji`` False for a
    chart, whose font has no ✅ or ❌)."""
    text = _plain_decision(decision)
    return text if emoji else text[2:]


def _plain_decision(decision) -> str:
    reason = getattr(decision, "reason", "") or ""
    if decision.tradable:
        side = "long" if decision.direction is Bias.BULLISH else "short"
        combo = "+".join(tf.label for tf in (decision.matched_combo or ()))
        scalp = ", scalp" if decision.mode is TradeMode.SCALP else ""
        return f"✅ {side} toegestaan ({combo}{scalp})"
    m = re.match(r"(bullish|bearish): (\S+) against", reason)
    if m:
        verb = "staan" if "+" in m.group(2) else "staat"
        return f"❌ geen {_side(m.group(1))}: de {_tf_names(m.group(2))} {verb} ertegen"
    m = re.match(r"(bullish|bearish): (\S+) not aligned", reason)
    if m:
        verb = "meedraaien" if "+" in m.group(2) else "meedraait"
        return f"❌ geen {_side(m.group(1))}: wacht tot de {_tf_names(m.group(2))} {verb}"
    m = re.match(r"(bullish|bearish): (\S+) aligned but not a valid combination", reason)
    if m:
        way = "omhoog" if m.group(1).startswith("bull") else "omlaag"
        return f"❌ geen trade: {_tf_names(m.group(2))} wijzen {way}, maar dat is geen geldige combinatie"
    if reason.startswith("fewer than"):
        return "❌ geen trade: te weinig timeframes zijn het eens"
    return f"❌ geen trade: {reason}"


def bias_line(analysis: Analysis) -> str:
    """M ◆ · W ▼ · D ▼ · 4H ▲ · 1H ▲ (the largest timeframe first)."""
    items = sorted(analysis.biases.items(), key=lambda kv: kv[0], reverse=True)
    return " · ".join(f"{TF_SHORT.get(tf.label, tf.label)} {ARROWS[tb.bias]}" for tf, tb in items)


def zone_kind(poi) -> str:
    return "demand" if poi.direction is Bias.BULLISH else "supply"


def _distance(d: float, spec: Optional[SymbolSpec]) -> str:
    if spec is not None and spec.pip_size < 0.01:
        return f"{d / spec.pip_size:.0f} pips"
    return f"{d:,.1f}" if d < 100 else f"{d:,.0f}"


def zone_line(poi, price: float, spec: Optional[SymbolSpec] = None) -> str:
    """▲ 1H demand 1.11930-1.11969 · prijs erin / 12 pips eronder."""
    if poi.contains(price):
        where = "prijs erin"
    elif poi.low > price:
        where = f"{_distance(poi.low - price, spec)} erboven"
    else:
        where = f"{_distance(price - poi.high, spec)} eronder"
    return f"{ARROWS[poi.direction]} {poi.timeframe.label} {zone_kind(poi)} {_price(poi.low, spec)}–{_price(poi.high, spec)} · {where}"


WAITS = (
    (re.compile(r"waiting for confirmation on (\S+)"), lambda m: f"wacht op een balance shift op de {m.group(1)}"),
    (re.compile(r"outside the entry windows"), lambda m: "buiten de handelstijden (09-11 en 13-17)"),
    (re.compile(r"news blackout"), lambda m: "nieuws: even geen nieuwe trades"),
    (re.compile(r"price is not inside a (bullish|bearish) POI"),
     lambda m: f"prijs zit (nog) niet in een {'demand' if m.group(1) == 'bullish' else 'supply'}-zone"),
)


def plain_wait(analysis: Analysis) -> Optional[str]:
    """What a tradable decision waits for, from the engine's first matching refusal (None when nothing matches)."""
    for text in analysis.rejections:
        for pattern, say in WAITS:
            m = pattern.search(text)
            if m:
                return say(m)
    return None


def format_briefing(analysis: Analysis, spec: Optional[SymbolSpec], zones: Iterable, when: str = "", kind: str = "ochtendcheck",
                    extra: Iterable[str] = ()) -> str:
    """The morning (or midday) message of one market: price, the bias per timeframe, the decision in words, the zones that
    count, then the ``extra`` lines (the regime, the news, the stake, the room to the limits, what a trade needs)."""
    emoji = {"ochtendcheck": "☀️", "middagcheck": "🕐"}.get(kind, "☀️")
    head = f"{emoji} <b>{escape(analysis.symbol)}</b> · {escape(kind)}{(' ' + escape(when)) if when else ''} · {_price(analysis.price, spec)}"
    lines = [head, f"Richting: {bias_line(analysis)}", escape(plain_decision(analysis.decision))]
    if analysis.has_valid_signal:
        lines.append("🎯 er staat een setup klaar (zie het setup-bericht)")
    elif analysis.decision.tradable:
        wait = plain_wait(analysis)
        if wait:
            lines.append(f"⏳ {escape(wait)}")
    zones = list(zones)
    if zones:
        lines.append("Zones die meetellen:")
        lines += [escape(zone_line(p, analysis.price, spec)) for p in zones]
    else:
        lines.append("Geen verse zones in de buurt.")
    lines += [escape(line) for line in extra if line]
    return "\n".join(lines)


# the engine's refusals worth a message while a zone is in play (a near miss), in Dutch: "shift" ones mean a balance shift
# was seen and the trade refused on its numbers, "zone" ones mean the zone itself does not qualify; the wait-class refusals
# (no shift yet, a spent zone already left off the chart, outside the windows) stay silent
NEAR_MISSES = (
    ("shift", re.compile(r"R:R ([\d.]+) below minimum ([\d.]+) \(target (.+)\)"),
     lambda m: f"R:R 1:{float(m.group(1)):.1f} onder het minimum 1:{float(m.group(2)):.1f} (doel: {m.group(3)})"),
    ("shift", re.compile(r"no opposite liquidity or unmitigated balance block to target"),
     lambda m: "geen doel te vinden (geen liquiditeit of balance block tegenover)"),
    ("shift", re.compile(r"lies (\d+)% of the zone's height inside it \(max (\d+)%\)"),
     lambda m: f"de instap ligt te diep in de zone ({m.group(1)}% van de hoogte, max {m.group(2)}%)"),
    ("shift", re.compile(r"stop of ([\d.]+) pips too wide"),
     lambda m: f"de stop van {float(m.group(1)):.1f} pips is te wijd voor de kleinste lotgrootte"),
    ("shift", re.compile(r"a climax candle \(body ([\d.]+) ATR14"), lambda m: f"de shift-kaars is een climax-kaars ({m.group(1)} ATR14)"),
    ("shift", re.compile(r"stop ([\d.]+) ATR14 of the (\S+) \(min ([\d.]+)\)"),
     lambda m: f"de stop is te klein ({m.group(1)} ATR14 van de {m.group(2)}, min {m.group(3)})"),
    ("shift", re.compile(r"the shift closed (\d+) min after the touch \(min (\d+) min\)"),
     lambda m: f"de shift kwam te snel na het raken ({m.group(1)} min, min {m.group(2)})"),
    ("shift", re.compile(r"on the wrong side of the New York day open ([\d.]+)"),
     lambda m: f"de instap ligt aan de verkeerde kant van de New York-dagopen ({m.group(1)})"),
    ("shift", re.compile(r"news blackout"), lambda m: "nieuws-blackout: geen instap rond het nieuws"),
    ("zone", re.compile(r"visit #(\d+) - only the first return is traded"),
     lambda m: f"dit is bezoek #{m.group(1)} aan de zone; alleen het eerste bezoek wordt verhandeld"),
    ("zone", re.compile(r"first touched (\d+) h ago \(max ([\d.]+) h\)"),
     lambda m: f"het bezoek is te oud ({m.group(1)} h, max {m.group(2)} h)"),
)
SILENT = re.compile(r"waiting for confirmation|no active visit|invalidated on|already traded on visit|touched \d+ h after it formed|"
                    r"outside the entry windows|^diagnostic:")


def classify_near_miss(reason: str) -> Optional[Tuple[str, str]]:
    """The engine's refusal of a zone as ``(key, text)``: the key names the rules that refused (for the once-per-four-hours
    throttle, so a new R:R number is not a new message), the text says it in Dutch. ``build_setup`` joins several reasons
    with "; ": each is translated and all are named. None when it is no near miss: nothing has happened yet, or a refusal
    this table does not know (a zone too old, a zone inside a larger one, missing data: the engine's business, not news)."""
    if SILENT.search(reason):
        return None
    keys, texts, kinds = [], [], set()
    for part in reason.split("; "):
        for index, (kind, pattern, say) in enumerate(NEAR_MISSES):
            m = pattern.search(part)
            if m:
                keys.append(str(index)); texts.append(say(m)); kinds.add(kind)
                break
    if not texts:
        return None
    head = "shift gezien, maar " if "shift" in kinds else "geen trade: "
    return "+".join(keys), head + "; ".join(texts)


def plain_near_miss(reason: str) -> Optional[str]:
    """The engine's refusal of a zone in Dutch, or None when it is no near miss."""
    found = classify_near_miss(reason)
    return found[1] if found else None


def format_near_miss(symbol: str, poi, text: str, spec: Optional[SymbolSpec] = None) -> str:
    return (f"⚠️ <b>{escape(symbol)}</b> · {poi.timeframe.label} {zone_kind(poi)} {_price(poi.low, spec)}–{_price(poi.high, spec)}\n"
            f"{escape(text)}")


def format_approach(symbol: str, poi, price: float, spec: Optional[SymbolSpec] = None, confirm_tfs: Iterable = ()) -> str:
    tfs = "/".join(tf.label for tf in confirm_tfs) or "lagere timeframe"
    return (f"🔎 <b>{escape(symbol)}</b> nadert de {escape(zone_line(poi, price, spec))}\n"
            f"zodra de prijs erin zit: wachten op een balance shift op de {tfs}")


def format_touch(analysis: Analysis, poi, spec: Optional[SymbolSpec], confirm_tfs: Iterable = ()) -> str:
    """Price entered a zone the bias allows: which one, the decision, and what the entry waits for."""
    d = spec.price_decimals if spec else 5
    tfs = "/".join(tf.label for tf in confirm_tfs) or "lagere timeframe"
    return (f"👀 <b>{escape(analysis.symbol)}</b> zit in de {poi.timeframe.label} {zone_kind(poi)} "
            f"{poi.low:.{d}f}–{poi.high:.{d}f}\n{escape(plain_decision(analysis.decision))}\n"
            f"⏳ wacht op een balance shift op de {tfs}")


def format_setup_nl(setup: TradeSetup, spec: Optional[SymbolSpec] = None) -> str:
    """A setup in short: side, zone and confirmation, entry/stop/target, R:R, size and risk."""
    side = "BUY" if setup.direction.value > 0 else "SELL"
    plain = "long" if setup.direction.value > 0 else "short"
    pips = (lambda x: f"{x / spec.pip_size:.1f} pips") if spec else (lambda x: f"{x:.5g}")
    formed = f" ({setup.poi.created_at:%d-%m %H:%M})" if setup.poi.created_at is not None else ""
    lines = [
        f"🎯 <b>{escape(setup.symbol)} {side}</b> ({plain}) · {setup.poi.timeframe.label}-zone · "
        f"{setup.confirmation.type.value} op {setup.confirmation.timeframe.label}",
        f"Instap <code>{_price(setup.entry, spec)}</code> · stop <code>{_price(setup.stop, spec)}</code> "
        f"({pips(abs(setup.entry - setup.stop))}) · doel <code>{_price(setup.take_profit, spec)}</code> "
        f"({pips(setup.reward_distance)})",
        f"R:R <b>1:{setup.rr:.1f}</b> · {setup.lots:.2f} lots · risico {setup.risk_amount:,.0f}",
        f"Break-even na {setup.breakeven_r:.0f}R · zone {_price(setup.poi.low, spec)}–{_price(setup.poi.high, spec)}{formed}",
        f"Doel op: {escape(setup.tp_source)}",
    ]
    for note in setup.notes:
        lines.append(f"<i>{escape(note)}</i>")
    return "\n".join(lines)
