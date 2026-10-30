# Independent synthetic CloudTrail replay protocol

Declared before inspecting model outcomes on this source. The independently
authored Opsbreak Trailhunt repository describes an MIT-licensed, generated
CloudTrail sample with seven days of benign background followed by three
simulated incidents. The repository is a research-support source, not an
independent production environment or an event-level labelled gold standard.

Acquire a bounded repository archive at a pinned public commit as inert data.
Do not run the generator, detection rules, scripts or attack code. Parse only
the committed sample CloudTrail JSON gzip files, validate counts and timestamps,
and retain no raw access-key identifiers or response payloads. Record the source
licence, commit, archive hash and input counts. Confirm sample timestamps match
the source's documented dates before analysing.

Run all twenty frozen v4 main seed-42 models without target retraining or
threshold adjustment. Construct actor histories strictly from preceding sampled
events, cold at the start of this different synthetic account, keeping all
timestamp ties together. Do not warm these actor states using the other corpus.

Use records before 8 September 2026 00:00 UTC as the source-described synthetic
benign background. Report its event alert fraction and separately the fraction
after a 24-hour cold-start warm-up. This is an empirical alarm rate under a
synthetic generator, not a production false-positive rate. Verify that all
source model training timestamps precede these records.

Predeclare three incident-start windows from the generator documentation:
8 September 03:12 UTC, 9 September 01:47 UTC and 9 September 14:02 UTC, each
extending fifteen minutes. Record events and alerts in each. An alert somewhere
in a mixed window may be due to benign activity and is not confirmed attack
detection, so report window alert coverage only, not event-level attack recall.
The three windows share one synthetic environment and are not independent sites.
Fail rather than infer missing incident labels, silently change windows or select
a favourable model after viewing these outcomes.
