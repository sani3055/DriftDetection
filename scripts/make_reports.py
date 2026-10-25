"""Generate summary tables and figures only from saved result files."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.reporting.make_figures import make_figures  # noqa: E402
from src.reporting.summaries import write_summaries  # noqa: E402


def main() -> None:
    write_summaries(ROOT / "data" / "benchmark" / "adaptation_results.csv", ROOT / "results")
    make_figures(ROOT)
    print("Reports and figures generated from saved artifacts")


if __name__ == "__main__":
    main()

