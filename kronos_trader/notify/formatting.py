"""Human-readable (Telegram HTML) rendering of analyses, setups and forecasts."""
from __future__ import annotations

from html import escape
from typing import Optional

from ..config import SymbolSpec
from ..core.types import Analysis, Bias, ForecastSummary, POIStatus, TradeSetup

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
