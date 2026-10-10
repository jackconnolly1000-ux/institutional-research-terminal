"""Render the app with the stand-in network in tests/offline/mocks.py.

Run from the app/ folder:
    MOCK_DELAY=3 streamlit run tests/offline/run_offline.py -- app.py

No Anthropic calls are made, even if .streamlit/secrets.toml holds your real key:
the Anthropic client class is replaced before app.py runs, and this script stops if that fails.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import mocks  # noqa: E402

mocks.install()
import anthropic  # noqa: E402

if anthropic.Anthropic is not mocks.FakeAnthropic:
    raise SystemExit("Mock install failed; refusing to run app.py with a real Anthropic client.")

app_path = Path(sys.argv[1] if len(sys.argv) > 1 else "app.py").resolve()
sys.path.insert(0, str(app_path.parent))  # so app.py can import theme.py, ui.py, charts.py
exec(compile(app_path.read_text(), str(app_path), "exec"), {"__name__": "__main__", "__file__": str(app_path)})
