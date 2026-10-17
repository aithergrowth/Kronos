# Source chart records awaiting complete data

These are **not regression fixtures**. Read `../../ASTRA_TASKS.md`, Part 3.
There are five Dorus-authored chart records, two student-chart critiques, and three
caption-only research leads. No complete OHLC export or five complete cases exist.

The example loader scans only `docs/examples/*.yaml` and requires a matching CSV.
This subdirectory prevents partial records from producing apparent passing tests.
All records omit `expect`. Gold preserves its intermediate drawing states and the
corrected 02:40 entry/stop/distance/RR labels. The corrected target-price label and
chart timezone remain obscured; those fields remain omitted from trade assertions. See the
[focused follow-up](../../DORUS_FOCUSED_AUDIT.md).

Keep this directory outside the test-fixture scan until POI timeframe, feed, UTC
interval, real candles and actual shown expectations are verified. Student price
annotations are not Dorus’s approved trade expectations. Selected crosshair dates,
alert levels, live quotes and drawing endpoints are not silently labeled as orders.

Each example YAML has a same-name Markdown handoff with source, available public-post screenshots, known metadata
and missing data. [Exact retrieval requests](RETRIEVAL_REQUESTS.md) now specify
seven dataset requests across six source cases. Their date windows are explicitly
researcher-selected padding, not claimed chart-event dates. Metadata handoff,
actual candle export and validated regression fixture are separate states.
Missing unshown entry/SL/TP fields do not by themselves prohibit a metadata
handoff; source attribution, POI classification and coverage must still be honest.
`source_coverage.yaml` records scope and asset hashes;
`course_caption_audit.yaml` is a coverage manifest, not an example fixture.

Raw academy screenshots are excluded from the PR; source lesson timestamps support
the corresponding readings. This follows an automatic approval review restriction
on uploading potentially private raw source images.
