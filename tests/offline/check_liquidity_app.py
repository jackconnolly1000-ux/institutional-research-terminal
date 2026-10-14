"""Run the complete saved-pilot view and the existing sample with all network calls disabled."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(ROOT))
os.environ["MOCK_NO_NETWORK"] = "1"
os.environ["SEC_CONTACT_EMAIL"] = "offline-test@example.com"
import mocks  # noqa: E402
mocks.install()
from streamlit.testing.v1 import AppTest  # noqa: E402

app = AppTest.from_file(str(ROOT / "app.py"))
app.secrets["ANTHROPIC_API_KEY"] = "offline-placeholder"
app.run(timeout=30)
assert not app.exception and not app.error
assert not app.tabs
app.session_state["liquidity_pilot_open"] = True
app.run(timeout=30)
assert not app.exception and not app.error
text = "\n".join(m.value for m in app.markdown)
assert all(value in text for value in ("54,908M", "125,337M", "19,895M", "Financing changes after June 30"))
next(b for b in app.button if b.label == "View saved sample").click().run(timeout=30)
assert not app.exception and not app.error
assert any("Saved sample. Analysis run" in m.value for m in app.markdown)
print("Saved liquidity pilot and existing sample passed with all network calls disabled.")
