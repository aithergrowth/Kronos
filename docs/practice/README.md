# Practice material

## Journal template

`journal_template.csv` has the same columns as the backtest ledger, so a replay trade written by hand can be laid next to
what the code did at the same moment. One row per trade; a refused setup gets a row too, with `result_r` empty and the
reason in `notes`. Times in UTC or with the time zone named in `notes`.

## Blind charts: judge the code's trades

`eurusd_blind/` holds 20 EURUSD trades of the frozen phase 2 run (`docs/backtests/phase2/EURUSD_5m_pure.csv`), drawn with
`trade-charts --blind`: zone, X, B, P, entry, stop and target are shown, the outcome is not. The exercise: for each chart,
write down whether you would take the trade under Dorus's rules and why, before opening `answers.csv`, which lists the
result per chart. The point is not to guess the outcome but to judge the reading: zone, confirmation, stop, target.

Regenerate with:

    python -m kronos_trader --config config/dorus_pure.yaml trade-charts --symbol EURUSD --data-dir data/histdata \
        --trades docs/backtests/phase2/EURUSD_5m_pure.csv --out docs/practice/eurusd_blind --max 20 --zones 1 --blind --kronos off
