# Examples from Dorus's material - the format that turns into tests

Every example is two files with the same name:

- `<name>.csv` - the candles of the **POI timeframe**, columns
  `timestamp,open,high,low,close,volume` (timestamp = candle open, UTC,
  `2026-03-04 08:00` style). At least 60 candles before the sweep and enough
  after the break to show the return into the zone. Volume may be 0.
  Optional: `<name>_ltf.csv` with the confirmation-timeframe candles around
  the entry.
- `<name>.yaml` - the annotations (copy `example_template.yaml`).

`python -m pytest tests/trader/test_examples.py` then checks, for every
example, that the code finds the same sweep, the same break, the same zone
and, when given, the same stop and target. A failing example is exactly what
we want: it shows where the code's reading differs from Dorus's.

## Brief for Astra

While going through the videos and the Skool material, collect two things.

**1. Definitions, in Dorus's own words** (quote + video title + timestamp), for
each of these terms: liquidity (which highs/lows count: swing points, equal
highs/lows, previous day/week/month, session highs/lows), sweep, balance /
balance block, protected zone / POI, break of structure (BOS), break of market
structure (BMS), confirmation, invalidation, target, premium/discount if he
uses it, scalp vs intraday vs swing. Put them in `docs/ASTRA_TASKS.md` under
the matching question.

**2. Worked examples** - at least five, ideally ten, covering: a monthly or
weekly POI, a daily POI, a 4H POI, a 1H POI, one scalp-only situation, one
example that looked valid but Dorus rejected (and why). For each, the two
files above. Prices and times must come from the chart, not from memory; if a
video shows the chart without a timestamp, note the approximate date and
Claude will pull the candles from TradingView.

Also record every rule he states that is **not** in our rule set (session
filters, news rules, maximum trades per day, anything about partials or
trailing). Those go under "New rules" in `docs/ASTRA_TASKS.md`.
