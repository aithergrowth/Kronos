"""Human-readable (Telegram HTML) rendering of analyses, setups and forecasts."""
from __future__ import annotations

import re
from html import escape
from typing import Iterable, Optional

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


def format_briefing(analysis: Analysis, spec: Optional[SymbolSpec], zones: Iterable, when: str = "") -> str:
    """The morning message of one market: price, the bias per timeframe, the decision in words, the zones that count."""
    head = f"☀️ <b>{escape(analysis.symbol)}</b> · ochtendcheck{(' ' + escape(when)) if when else ''} · {_price(analysis.price, spec)}"
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
    return "\n".join(lines)


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
