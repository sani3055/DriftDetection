# PRISMA 2020 flow accounting

The counts below are generated from the automated metadata collection package and are not a claim
that human screening has been completed.

| Stage | Count | Evidence |
|---|---:|---|
| Records retrieved across 12 searches | 2,400 | `search_log.json` |
| Unique DOI values observed | 1,898 | `collection_manifest.json` |
| Duplicate DOI observations removed | 502 | 2,400 − 1,898 |
| Records passing automated topic/year/type screen before final selection | 1,246 candidate hits | `collection_manifest.json`; candidate-hit count may include repeated DOI observations |
| Records retained for the 100-paper evidence set | 100 | `evidence_matrix_100.csv` |
| Open-access PDFs downloaded | 12 | `collection_manifest.json` |
| Records needing human title/abstract/full-text confirmation | 100 | `screening_log_100.csv` |

## Interpretation

The current package is a reproducible initial screening set. A final PRISMA flow diagram requires
separate human-screening counts, full-text retrieval counts, full-text exclusions with reasons, and
the final included-study count after two-reviewer agreement. Those values must not be invented from
the automated collector.
