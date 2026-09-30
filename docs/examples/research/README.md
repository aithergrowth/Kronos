# Source chart records awaiting complete data

These are **not regression fixtures**. Read `../../ASTRA_TASKS.md`, Part 3.
There are five Dorus-authored chart records, two student-chart critiques, and two
caption-only research leads. No complete OHLC export or five complete cases exist.

The example loader scans only `docs/examples/*.yaml` and requires a matching CSV.
This subdirectory prevents partial records from producing apparent passing tests.
Gold has a partial `expect` containing only readable position-tool prices, explicitly
separated from verified execution. All other records omit `expect`.

Keep this directory outside the test-fixture scan until POI timeframe, feed, UTC
interval, real candles and actual shown expectations are verified. Student price
annotations are not Dorus’s approved trade expectations. Selected crosshair dates,
alert levels, live quotes and drawing endpoints are not silently labeled as orders.

Each YAML has a same-name Markdown handoff with source, available public-post screenshots, known metadata
and missing data. The CSV fallback remains incomplete where exact date ranges or
feed details cannot be read. `source_coverage.yaml` records scope and asset hashes.

Raw academy screenshots are excluded from the PR; source lesson timestamps support
the corresponding readings. This follows an automatic approval review restriction
on uploading potentially private raw source images.
