# Research evidence v4: reproduction guide

This is an exploratory research release, not a claim of independent prospective validation or journal acceptance. The manuscript reports negative and mixed findings. The 60 seed/configuration cells reuse the same labelled source events.

## Contents and exclusions

The accompanying archive contains the manuscript, Python source and tests, declared protocols, aggregate and per-window experiment outputs, and a SHA-256 file inventory. It deliberately excludes raw cloud logs, actor identifiers, cloud credentials, downloaded papers, generated feature caches and fitted model files. The inherited CloudTrail CSV is not redistributed because its provenance and redistribution permissions are not established. Its separate timestamped export was available locally at `D:/Projects/CloudGuard/data/nineteenFeaturesDf.csv`; the corresponding script currently uses that path explicitly and must be adapted if the file is obtained elsewhere. Source-order sampling and missing ground truth limit the associated results.

## Environment and source data

Create a Python environment and install `requirements-journal.txt` (which includes `requirements.txt`); run from the project root. Obtain the publicly described ArielCyber Cloud Log Sampling Dataset, verify the archive hashes recorded in the output manifests, and place its `TrainOn` and `TestOn` archives under `data/external/cloud_log_sampling-main`. The label-free cache script uses `TrainOn/base_a.zip`, `TestOn/labeled_cloudtrail_a.zip`, and `TrainOn/train_labeled_a.zip`.

Example commands (Windows PowerShell):

```powershell
python -m pip install -r requirements-journal.txt
python scripts/build_causal_feature_cache.py
python scripts/run_behaviour_tie_safe_grid.py --seeds 42 17 73
python scripts/analyze_behaviour_results.py
python scripts/analyze_behaviour_seed_sensitivity.py
python -m pytest tests -q
```

These experiments can be computationally intensive. The cache is derived from the source archives and has internal code, order and source-hash checks. The grid deliberately treats an existing result manifest as a completed cached cell; the cache builder similarly refuses to overwrite an existing completed cache. To actually reproduce results, use a **fresh copy** of the package with a fresh results directory, retaining the packaged results elsewhere for comparison. Never replace the only copy of research evidence.

The matched monthly intervention and richer original-export studies also require separately obtained inherited data. The richer-export study is not an independent dataset. The public Splunk attack traces and the MIT-licensed Opsbreak synthetic sample are separate sources. Their pinned revisions and acquisition details are recorded in `docs/INDEPENDENT_CLOUD_DATA_AUDIT.md` and the output manifests. The acquisition scripts read inert data and do not run third-party attack generators; replay requires source-trained frozen models, which this archive does not redistribute and must be regenerated. A network connection and permission to obtain each source are required.

## Interpretation and checks

Start with `docs/JOURNAL_V4_PROTOCOL.md`, `docs/PRIMARY_RICH_CONTEXT_PROTOCOL.md` and `docs/INDEPENDENT_SYNTHETIC_PROTOCOL.md`. The designated test corpus was seen during earlier project work; the later protocol is not an external preregistration. Attack labels are used for evaluation and controlled contamination construction, not as online adaptation inputs. The synthetic incident windows contain both background and incident activity, so an alert anywhere in a window is not attack recall. Model seeds and sessions from one deployment are not independent organisations.

The Word file is a journal manuscript **draft**, not a submission. The archive focuses on experimental reproduction rather than promising byte-identical Word regeneration. The author must review the work, verify bibliographic details, resolve corresponding-author information and follow the chosen journal's policies. The separate 100-paper PRISMA review remains unfinished; no final inclusion count is claimed here.
