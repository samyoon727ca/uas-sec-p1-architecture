# Series status snapshots

One `<repo>.json` per series repo (P2 to P6), named after the `repo` column of [`../series.csv`](../series.csv). Each is a copy of that repo's `series-status.json`, in the format in [`docs/series-status.md`](../../docs/series-status.md), and must pass `tools/check_series_status.py`.

A scheduled workflow fills this folder; don't add or edit snapshots by hand. `tools/render_views.py` reads them to generate the series table in the [README](../../README.md#verification-evidence). It checks each snapshot first and fails on an invalid one. For a repo with no snapshot, or a VE missing from its snapshot, the table falls back to the `status` and `evidence` columns of [`../verification.csv`](../verification.csv).
