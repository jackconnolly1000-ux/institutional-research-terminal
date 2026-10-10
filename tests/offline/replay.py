"""Run the app on live SEC and Yahoo data, with Claude's answers replayed from a saved real run. No Anthropic calls.

Use it to check the interface on real output without paying again. The saved answers must come from the same
filings and the same comparison code, or their source and paragraph IDs won't line up (they'd be rejected and shown
as rejected). Answers are read from ~/Stock Project/data/raw/ai_responses/{TICKER}_*.json, newest first.

Run from app/ (needs SEC_CONTACT_EMAIL in .streamlit/secrets.toml, like the real app):
    .venv/bin/streamlit run tests/offline/replay.py -- app.py
"""
import glob
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import anthropic

SAVED = Path(__file__).resolve().parents[3] / "data" / "raw" / "ai_responses"


def _saved(ticker):
    files = sorted(f for f in glob.glob(str(SAVED / f"{ticker}_2*.json")) if "rechecked" not in f)
    if not files:
        raise SystemExit(f"No saved answer for {ticker} in {SAVED}")
    return json.load(open(files[-1]))


class _Messages:
    def create(self, **kw):
        ticker = kw["messages"][0]["content"].split("(", 1)[1].split(")", 1)[0]
        raw = _saved(ticker)["raw"]
        return SimpleNamespace(stop_reason=raw["stop_reason"], usage=SimpleNamespace(**raw["usage"]),
                               content=[SimpleNamespace(type="tool_use", input=raw["tool_input"])])

    def count_tokens(self, **kw):   # same rough count as the offline mocks; the saved runs sent all input anyway
        return SimpleNamespace(input_tokens=(len(kw["messages"][0]["content"]) + len(json.dumps(kw["tools"]))) // 4)


class ReplayAnthropic:
    def __init__(self, *a, **kw):
        self.messages = _Messages()

    def with_options(self, **kw):
        return self


anthropic.Anthropic = ReplayAnthropic
app_path = Path(sys.argv[1] if len(sys.argv) > 1 else "app.py").resolve()
sys.path.insert(0, str(app_path.parent))
exec(compile(app_path.read_text(), str(app_path), "exec"), {"__name__": "__main__", "__file__": str(app_path)})
