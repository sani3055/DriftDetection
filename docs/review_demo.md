# Streamlit review demo

The local interface replays saved held-out controlled experiments. It reads the
saved signals and validation-selected thresholds, then calls the actual diagnosis
and adaptation-policy functions. It does not retrain models, regenerate SHAP,
write research outputs, or connect to AWS. Known scenario categories enter only
the evaluation comparison, after the decision.

## Start

On this configured Windows machine, double-click `Start_Review_Demo.cmd` from the
project folder and open <http://127.0.0.1:8501>. Keep the terminal running.

Alternatively, from the project root:

```powershell
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

For a fresh setup, install the optional demo dependencies into the project virtual
environment first:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-demo.txt
```

The server binds to the local machine only and disables usage statistics. No API
key, AWS account, original large CSV, or internet connection is needed after
installation, provided the saved research files remain available.

## One-minute walkthrough

Use held-out test run 5, the default:

1. **Stable activity:** both drift magnitudes are below their limits. No update.
2. **Routine change: AWS region:** the data shifts, but the explanation magnitude
   remains below its limit. No update, even though feature alignment is high.
3. **Simulated security change: defence:** both magnitudes and alignment pass their
   limits. The coupling policy requests an update.
4. **Simulated security change: privilege:** this saved security scenario receives
   a routine-drift diagnosis. Show the missed-case warning rather than implying
   perfect detection.

The sidebar exposes all ten held-out seeds, not only a hand-picked successful
run. The main selector exposes every available scenario for the chosen run.
Each signal uses its own fixed scale across runs, with a black decision-limit
marker. Do not compare the raw scales as though they had the same units.

Expand the plain-English findings, source evidence, or real monthly plot if asked.
The monthly corpus has no verified attack labels. A scenario-level update request
is not a verified attack prediction or evidence of real-world reliability.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_review_demo.py tests/test_streamlit_demo.py -q
```

UI tests use Streamlit's official
[AppTest framework](https://docs.streamlit.io/develop/api-reference/app-testing).
They skip when the optional Streamlit dependency is absent.
