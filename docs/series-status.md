# Series status file

Each series repo (P2 to P6) publishes its verification status in a standard file, so P1 can generate status instead of editing it by hand. P1's [`data/series.csv`](../data/series.csv) stays the source of truth for which VEs each repo owns. A status file may report on those VEs only.

## `series-status.json`

The file is `series-status.json` at the root of each series repo. Example, for P2:

```json
{
  "p_id": "P2",
  "repo": "uas-sec-p2-verified-boot",
  "p1_commit": "a16601ef75eaf1d8bf26e14caa4707647005ae86",
  "ves": [
    {"ve_id": "VE-07", "status": "partly evidenced", "evidence": ["https://github.com/samyoon727ca/uas-sec-p2-verified-boot/blob/<40-hex-sha>/evidence/ve07/summary.md"]},
    {"ve_id": "VE-08", "status": "planned", "evidence": []}
  ]
}
```

| Field | Rule |
|---|---|
| `p_id` | The repo's `p_id` in `series.csv` (`P2`) |
| `repo` | The repo name, without the owner, exactly as in that `series.csv` row |
| `p1_commit` | Full 40-character lowercase SHA of the P1 commit the repo traces to |
| `ves` | List of objects, one per VE, each with the three fields below |
| `ves[].ve_id` | A VE that `series.csv` allocates to this `p_id` |
| `ves[].status` | `planned`, `in progress`, `partly evidenced` or `evidenced` |
| `ves[].evidence` | List of evidence URLs, may be empty. Each is a GitHub URL pinned to a full commit SHA: `https://github.com/<owner>/<repo>/blob/<sha>/<path>` (or `tree/`) |

Every VE allocated to the repo should appear once. An allocated VE missing from the file is a warning, not an error.

## Checking a file

```sh
python tools/check_series_status.py path/to/series-status.json [more files...]
```

The checker reads local files only; it does not fetch from GitHub. It exits 1 if any file:

- has a `p_id` that is not a row in `series.csv`, or a `repo` that does not match that row;
- claims a VE that the row does not list (for example, P6 claiming VE-07, which is P2's);
- uses an unknown `ve_id` or `status`;
- links evidence not pinned to a full commit SHA;
- has a `p1_commit` that is not 40 hex characters.

## README header

Each series repo carries this header near the top of its README. Copy it and fill in the placeholders. Keep the VEs and the P1 commit the same as in `series-status.json`.

```markdown
> **P#** of the [UAS security series](https://github.com/samyoon727ca/uas-sec-p1-architecture).
>
> - **VEs:** VE-##, VE-## ([allocation](https://github.com/samyoon727ca/uas-sec-p1-architecture/blob/<p1-sha>/data/series.csv))
> - **P1 commit:** [`<p1-sha-7>`](https://github.com/samyoon727ca/uas-sec-p1-architecture/commit/<p1-sha>)
> - **Status:** [`series-status.json`](series-status.json)
```
