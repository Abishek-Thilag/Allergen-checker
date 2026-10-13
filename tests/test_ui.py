"""
Tests for core/ui.py — render_html and palette constants.

render_html() is tested without a running Streamlit instance by
monkey-patching st.markdown.
"""
import textwrap
from unittest.mock import MagicMock, patch


def _call_render_html(block: str) -> str:
    """Call render_html() and return the string that would be passed to st.markdown."""
    captured = {}

    def fake_markdown(text, **kwargs):
        captured["text"] = text

    with patch("streamlit.markdown", side_effect=fake_markdown):
        from core.ui import render_html
        render_html(block)

    return captured.get("text", "")


# ── No line should start with 4+ spaces ──────────────────────────────────────

def test_no_four_space_indent():
    html = """
        <div>
            <p>hello</p>
        </div>
    """
    result = _call_render_html(html)
    for line in result.splitlines():
        assert not line.startswith("    "), (
            f"Line starts with 4+ spaces (would render as code block): {repr(line)}"
        )


def test_no_four_space_indent_deeply_indented():
    # Simulate HTML deeply indented inside a Python function body
    html = textwrap.dedent("""
                <div style="color:red">
                    <span>test</span>
                </div>
            """)
    result = _call_render_html(html)
    for line in result.splitlines():
        assert not line.startswith("    "), repr(line)


# ── No blank lines in the output ─────────────────────────────────────────────

def test_no_consecutive_blank_lines():
    html = """
        <div>

            <p>hello</p>

        </div>
    """
    result = _call_render_html(html)
    lines = result.splitlines()
    for i in range(len(lines) - 1):
        if lines[i].strip() == "" and lines[i + 1].strip() == "":
            raise AssertionError(
                f"Consecutive blank lines at positions {i} and {i+1}"
            )


def test_leading_trailing_blank_lines_stripped():
    html = "\n\n  <div>hi</div>\n\n"
    result = _call_render_html(html)
    assert not result.startswith("\n"), "Leading blank line present"
    assert not result.endswith("\n"), "Trailing blank line present"


# ── Content is preserved ──────────────────────────────────────────────────────

def test_html_content_preserved():
    html = "<div><p>hello world</p></div>"
    result = _call_render_html(html)
    assert "hello world" in result


def test_unsafe_allow_html_passed():
    """render_html must call st.markdown with unsafe_allow_html=True."""
    calls = []

    def fake_markdown(text, **kwargs):
        calls.append(kwargs)

    with patch("streamlit.markdown", side_effect=fake_markdown):
        from core.ui import render_html
        render_html("<p>test</p>")

    assert calls, "st.markdown was never called"
    assert calls[0].get("unsafe_allow_html") is True, (
        "unsafe_allow_html was not True"
    )


def test_fstring_html_no_four_space_indent():
    """f-string HTML blocks (most common usage) must also pass the check."""
    colour = "#D2042D"
    html = f"""
        <div style="color:{colour};">
            <span>cherry</span>
        </div>
    """
    result = _call_render_html(html)
    for line in result.splitlines():
        assert not line.startswith("    "), repr(line)


# ── Palette sanity checks ─────────────────────────────────────────────────────

def test_cherry_palette_defined():
    from core.ui import CHERRY, DARK_CHERRY, DEEP_CHERRY, TINT, WHITE
    assert CHERRY == "#D20A2E", f"Expected #D20A2E, got {CHERRY}"
    assert DARK_CHERRY == "#8F0720", f"Expected #8F0720, got {DARK_CHERRY}"
    assert DEEP_CHERRY == "#5C0516", f"Expected #5C0516, got {DEEP_CHERRY}"
    assert TINT == "#FCE8EB", f"Expected #FCE8EB, got {TINT}"
    assert WHITE == "#FFFFFF"


def test_status_colours_distinct_from_cherry():
    """Status colours must be visually distinct from the cherry brand colour."""
    from core.ui import CHERRY, PRESENT_BG, MAY_BG, UNCERTAIN_BG
    assert PRESENT_BG != CHERRY, "PRESENT and brand cherry must differ"
    assert not MAY_BG.upper().startswith("#D2"), "MAY CONTAIN should not be cherry-coloured"
    assert not UNCERTAIN_BG.upper().startswith("#D2"), "UNCERTAIN should not be cherry-coloured"


def test_present_uses_deep_cherry():
    """PRESENT must use DEEP_CHERRY (#5C0516), not brand cherry."""
    from core.ui import DEEP_CHERRY, PRESENT_BG
    assert PRESENT_BG == DEEP_CHERRY, (
        f"PRESENT_BG should be DEEP_CHERRY ({DEEP_CHERRY}), got {PRESENT_BG}"
    )


def test_wcag_aa_text_on_uncertain():
    """UNCERTAIN uses dark text on amber — check it's not white (would fail contrast)."""
    from core.ui import UNCERTAIN_FG
    assert UNCERTAIN_FG.lower() != "#ffffff", (
        "White text on amber fails WCAG AA contrast"
    )


# ── Navigation page titles ────────────────────────────────────────────────────

def test_page_titles():
    """
    The four pages must have exactly these titles (capitalised, in order):
    Home, Check, History, About.

    We inspect app.py source rather than running Streamlit to keep this
    test fast and offline.
    """
    import ast
    from pathlib import Path

    source = (Path(__file__).parent.parent / "app.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    # Collect all keyword arguments named "title" in st.Page(...) calls
    titles = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        # Match st.Page(...)
        is_st_page = (
            (isinstance(func, ast.Attribute) and func.attr == "Page")
            or (isinstance(func, ast.Name) and func.id == "Page")
        )
        if not is_st_page:
            continue
        for kw in node.keywords:
            if kw.arg == "title" and isinstance(kw.value, ast.Constant):
                titles.append(kw.value.value)

    expected = ["Home", "Check", "History", "About"]
    assert titles == expected, (
        f"Page titles mismatch.\nExpected: {expected}\nGot:      {titles}"
    )


def test_url_paths_unique():
    """Each st.Page must have a unique url_path to avoid the lambda pathname clash."""
    import ast
    from pathlib import Path

    source = (Path(__file__).parent.parent / "app.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    url_paths = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        is_st_page = (
            (isinstance(func, ast.Attribute) and func.attr == "Page")
            or (isinstance(func, ast.Name) and func.id == "Page")
        )
        if not is_st_page:
            continue
        for kw in node.keywords:
            if kw.arg == "url_path" and isinstance(kw.value, ast.Constant):
                url_paths.append(kw.value.value)

    expected_paths = {"home", "check", "history", "about"}
    assert len(url_paths) == 4, f"Expected 4 url_path values, found {len(url_paths)}: {url_paths}"
    assert set(url_paths) == expected_paths, (
        f"url_path values mismatch.\nExpected: {expected_paths}\nGot: {set(url_paths)}"
    )
