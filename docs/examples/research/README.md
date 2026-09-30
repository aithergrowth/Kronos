# Research records awaiting sufficient evidence

These files are **not regression fixtures**. Read `../../ASTRA_TASKS.md`, Part 3,
for the coverage gap and attribution rules. Four records have inspected images;
two are caption-only source locators. No complete OHLC export exists.

The production example loader only scans `docs/examples/*.yaml` and requires a
matching CSV. Keeping these files in this subdirectory prevents unsupported
annotations from producing apparent passing tests. Do not move them to the
parent directory until symbol/feed, POI timeframe, UTC interval and the actual
shown expectations are verified.

Student plans criticized by Dorus are explicitly labeled. Their readable price
labels remain under `student_plan_not_dorus_expectations`, never under `expect`.
No tolerance, sweep, break, zone, entry time or candle series is fabricated.

Each `.yaml` has a same-name `.md` handoff instead of a candle CSV. This records
the evidence gap; it is not a claim that the brief's candle-data fallback is
already complete. `source_coverage.yaml` records access, scope and image hashes.
