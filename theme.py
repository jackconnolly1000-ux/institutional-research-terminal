"""Design tokens for the SEC Filing Research Terminal.

The one place colors are defined. ui.py turns these into CSS variables, charts.py uses them
in Plotly, and .streamlit/config.toml repeats the five base colors (TOML can't import Python).

Semantic colors are named by MEANING, not by hue. Use them only when the color carries meaning:
    POSITIVE  price up (chart candles)
    NEGATIVE  price down, errors and failures
    CAUTION   notice cards for incomplete answers and partial results
    INFO      SEC filing markers on the chart, links
    ACCENT    interactive: primary button, selected state
Everything else (metrics, body text, cards) stays neutral. Margins and P/E get no color:
a number isn't good or bad on its own. AI judgments such as impact get no color either; they are plain text.

Each semantic color has two shades:
    *_SOLID  fills, borders, candles, a notice card's left edge
    *_TEXT   text on dark backgrounds; every one is at least 4.5:1 against SURFACE and against
             its own 16% tint (WCAG AA for normal text). Contrast values checked Oct 10, 2026.
Color never carries meaning alone, and labels are plain text: the app draws no pills or badges.
"""

# Neutral surfaces and text
BG = "#131722"            # page background
SURFACE = "#1e222d"       # cards, metric tiles
SURFACE_HOVER = "#262b38"
BORDER = "#2a2e39"
BORDER_STRONG = "#454b5a"  # outline of an expanded finding row, so it reads as one container
TEXT = "#d1d4dc"          # body text: 10.7:1 on SURFACE
TEXT_STRONG = "#f8fafc"   # headings, key numbers
TEXT_MUTED = "#9598a1"    # labels, sources, captions: 5.5:1 on SURFACE (the old #787b86 was 3.8:1)

# Semantic: solid shade / text shade
POSITIVE_SOLID, POSITIVE_TEXT = "#089981", "#26c6a5"
NEGATIVE_SOLID, NEGATIVE_TEXT = "#f23645", "#ff6b75"
CAUTION_SOLID, CAUTION_TEXT = "#f0b429", "#f5c451"
INFO_SOLID, INFO_TEXT = "#2962ff", "#7aa2ff"
ACCENT = "#2962ff"        # white text on it: 4.9:1

# Identity colors for the debt and liquidity reviews. They say WHICH quantity a mark is, never whether it is good
# or bad, so they avoid green/red. Used only for cash and baseline borrowing: their bars in "How did borrowing and
# cash change?" and a matching swatch beside the same headline figures. Text stays in text tokens.
# Validated Oct 17, 2026 with the dataviz six checks (all pairs, dark mode) on BG and SURFACE: CVD ΔE 26.8,
# normal-vision ΔE 31.8, both >= 3:1 against the surface. The chart also labels each panel, so color is never alone.
SERIES_CASH = "#3987e5"        # cash and cash equivalents
SERIES_BORROWING = "#d95926"   # baseline borrowing (carrying value, excludes leases)

# Chart series that carry no meaning get hues outside the semantic set (no green/red/amber/blue)
SERIES_SMA_FAST = "#a78bfa"   # 50-day moving average
SERIES_SMA_SLOW = "#b2b5be"   # 200-day moving average (drawn dotted, so it differs by more than color)

FONT_STACK = ('-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, '
              '"Apple Color Emoji", "Segoe UI Emoji"')

# Change labels come from code (compare.py), not the model. Only "new" carries color; the rest are context.
TREND_CHIP = {"NEW": ("info", "No close match in the prior 10-K"), "CHANGED": ("neutral", "Changed since the prior 10-K"),
              "REMOVED": ("neutral", "Removed since the prior 10-K"), "QUARTERLY_UPDATE": ("neutral", "Updated in a 10-Q"),
              "NOT_COMPARED": ("neutral", "No annual comparison")}
