from typing import Dict, Any, List

from .engine import engine
from .models import GraphCreateRequest


# ---------- Tools (nodes) ----------

def extract_functions_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node 1: Extract functions from Python code (very simple heuristic).
    """
    code: str = state.get("code", "")
    lines = code.splitlines()

    functions: List[str] = []
    current_fn_lines: List[str] = []
    inside_fn = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("def "):
            if current_fn_lines:
                functions.append("\n".join(current_fn_lines))
                current_fn_lines = []
            inside_fn = True
        if inside_fn:
            current_fn_lines.append(line)

    if current_fn_lines:
        functions.append("\n".join(current_fn_lines))

    state["functions"] = functions
    state["function_count"] = len(functions)
    return state


def check_complexity_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node 2: Check a very simple "complexity" = number of lines per function.
    """
    functions: List[str] = state.get("functions", [])
    complexities = [fn.count("\n") + 1 for fn in functions] if functions else []
    avg_complexity = sum(complexities) / len(complexities) if complexities else 0.0

    state["complexities"] = complexities
    state["avg_complexity"] = avg_complexity
    return state


def style_check_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node 3: Simple style checks:
    - Long lines (> 79 chars)
    - Tabs instead of spaces
    - Trailing spaces
    """
    code: str = state.get("code", "")
    lines = code.splitlines()

    warnings: List[str] = []
    long_lines = 0
    tab_lines = 0
    trailing_space_lines = 0

    for i, line in enumerate(lines, start=1):
        if len(line) > 79:
            long_lines += 1
        if "\t" in line:
            tab_lines += 1
        if line.rstrip() != line:
            trailing_space_lines += 1

    if long_lines:
        warnings.append(f"{long_lines} lines are longer than 79 characters.")
    if tab_lines:
        warnings.append(f"{tab_lines} lines use tabs instead of spaces.")
    if trailing_space_lines:
        warnings.append(f"{trailing_space_lines} lines have trailing spaces.")

    state["style_warnings"] = warnings
    state["style_warning_count"] = len(warnings)
    return state


def comment_quality_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node 4: Check how many comments there are.
    """
    code: str = state.get("code", "")
    lines = code.splitlines()

    comment_lines = 0
    code_lines = 0

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            comment_lines += 1
        else:
            code_lines += 1

    ratio = (comment_lines / code_lines) if code_lines else 0.0

    comments_feedback: List[str] = []
    if code_lines > 0:
        if ratio < 0.05:
            comments_feedback.append(
                "Very few comments relative to code; consider explaining complex logic."
            )
        elif ratio > 0.4:
            comments_feedback.append(
                "A lot of comments; make sure they add value and are up to date."
            )

    state["comment_lines"] = comment_lines
    state["code_lines"] = code_lines
    state["comment_ratio"] = ratio
    state["comment_feedback"] = comments_feedback
    return state


def docstring_check_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node 5: Very naive docstring check for each extracted function.
    """
    functions: List[str] = state.get("functions", [])
    docstring_missing_for: List[str] = []

    for fn in functions:
        lines = fn.splitlines()
        if not lines:
            continue

        header = lines[0].strip()
        fn_name = header.split("(")[0].replace("def", "").strip() or "<unknown>"

        # Look for triple-quoted string in the next few lines
        has_doc = False
        for line in lines[1:4]:
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                has_doc = True
                break

        if not has_doc:
            docstring_missing_for.append(fn_name)

    state["missing_docstrings"] = docstring_missing_for
    return state


def detect_issues_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node 6: Detect basic issues using naive rules.
    """
    code: str = state.get("code", "")
    issues: List[str] = []

    if "print(" in code:
        issues.append("Uses print() statements; consider logging instead.")
    if "TODO" in code:
        issues.append("Contains TODO comments; consider resolving them.")
    if "global " in code:
        issues.append("Uses global variables; this can reduce code clarity.")
    if "except:" in code or "except Exception:" in code:
        issues.append("Catches broad exceptions; consider catching specific ones.")

    state["issues"] = issues
    state["issue_count"] = len(issues)
    return state


def suggest_improvements_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node 7: Suggest improvements and compute a quality score.
    """
    suggestions: List[str] = []

    issues: List[str] = state.get("issues", [])
    avg_complexity: float = float(state.get("avg_complexity", 0.0))
    style_warnings: List[str] = state.get("style_warnings", [])
    comment_feedback: List[str] = state.get("comment_feedback", [])
    missing_docstrings: List[str] = state.get("missing_docstrings", [])

    # Base quality score starts at 1.0 and we subtract penalties.
    quality_score = 1.0

    # Penalize for issues
    quality_score -= 0.07 * len(issues)

    # Penalize for style warnings
    quality_score -= 0.03 * len(style_warnings)

    # Penalize for missing docstrings
    quality_score -= 0.02 * len(missing_docstrings)

    # Penalize for high complexity
    if avg_complexity > 30:
        quality_score -= 0.3
        suggestions.append(
            "Functions are quite long; consider splitting them into smaller ones."
        )
    elif avg_complexity > 15:
        quality_score -= 0.15
        suggestions.append(
            "Average function length is moderate; consider refactoring large ones."
        )

    # Suggestions based on issues
    if any("print()" in issue or "print(" in issue for issue in issues):
        suggestions.append("Replace print() with a configurable logger.")
    if any("TODO" in issue for issue in issues):
        suggestions.append("Resolve TODOs or convert them into tracked tickets.")
    if any("global" in issue.lower() for issue in issues):
        suggestions.append("Avoid global variables; pass data as parameters instead.")
    if any("exceptions" in issue.lower() for issue in issues):
        suggestions.append("Catch specific exception types instead of broad ones.")

    # Suggestions based on style warnings
    suggestions.extend(style_warnings)

    # Suggestions based on comments/docstrings
    suggestions.extend(comment_feedback)
    if missing_docstrings:
        suggestions.append(
            f"Add docstrings for functions: {', '.join(missing_docstrings)}."
        )

    # Clamp quality between 0 and 1
    quality_score = max(0.0, min(1.0, quality_score))

    state["suggestions"] = suggestions
    state["quality_score"] = quality_score
    return state


def quality_loop_tool(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node 8: Loop until 'quality_score >= threshold'.

    - If quality is good enough, stop.
    - Else, loop back to 'suggest_improvements'.
    """
    quality_score: float = float(state.get("quality_score", 0.0))
    threshold: float = float(state.get("quality_threshold", 0.8))

    if quality_score >= threshold:
        state["approved"] = True
        state["_stop"] = True  # Tell engine to stop
    else:
        state["approved"] = False
        # Loop back to 'suggest_improvements'
        state["_next_node"] = "suggest_improvements"

    return state


# ---------- Register tools in the engine ----------

engine.register_tool("extract_functions", extract_functions_tool)
engine.register_tool("check_complexity", check_complexity_tool)
engine.register_tool("style_check", style_check_tool)
engine.register_tool("comment_quality", comment_quality_tool)
engine.register_tool("docstring_check", docstring_check_tool)
engine.register_tool("detect_issues", detect_issues_tool)
engine.register_tool("suggest_improvements", suggest_improvements_tool)
engine.register_tool("quality_check", quality_loop_tool)


# ---------- Create an example graph on startup ----------

def create_default_code_review_graph() -> str:
    """
    Creates the example workflow for Option A:

    1. Extract functions
    2. Check complexity
    3. Style check
    4. Comment quality
    5. Docstring check
    6. Detect basic issues
    7. Suggest improvements
    8. Loop until quality_score >= threshold
    """
    request = GraphCreateRequest(
        nodes=[
            "extract_functions",
            "check_complexity",
            "style_check",
            "comment_quality",
            "docstring_check",
            "detect_issues",
            "suggest_improvements",
            "quality_check",
        ],
        edges={
            "extract_functions": "check_complexity",
            "check_complexity": "style_check",
            "style_check": "comment_quality",
            "comment_quality": "docstring_check",
            "docstring_check": "detect_issues",
            "detect_issues": "suggest_improvements",
            "suggest_improvements": "quality_check",
            # "quality_check" has no static next node, it uses _next_node / _stop
            "quality_check": None,
        },
        start_node="extract_functions",
    )
    graph_id = engine.create_graph(request)
    return graph_id


DEFAULT_GRAPH_ID = create_default_code_review_graph()
