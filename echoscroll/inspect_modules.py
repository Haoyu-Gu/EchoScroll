"""Walk every M*/ module under echoscroll/ and emit MODULES.md.

For each module we record: files, line counts, top-level classes/functions
with docstring snippets, figures, demo command, README first lines.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "MODULES.md"


def trim_doc(s: str | None, maxlen: int = 110) -> str:
    if not s:
        return ""
    s = s.strip().splitlines()[0]
    return s if len(s) <= maxlen else s[: maxlen - 1] + "…"


def extract_symbols(py_path: Path) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Return (classes, functions) as (name, first_doc_line)."""
    try:
        tree = ast.parse(py_path.read_text(encoding="utf-8"))
    except Exception:
        return [], []
    classes, funcs = [], []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            classes.append((node.name, trim_doc(ast.get_docstring(node))))
        elif isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
            funcs.append((node.name, trim_doc(ast.get_docstring(node))))
    return classes, funcs


def line_count(p: Path) -> int:
    try:
        return sum(1 for _ in p.open(encoding="utf-8", errors="ignore"))
    except OSError:
        return 0


def first_lines(p: Path, n: int = 5) -> list[str]:
    try:
        out = []
        with p.open(encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if line.strip().startswith("#") and not out:
                    out.append(line)
                elif line.strip() and out:
                    out.append(line)
                if len(out) >= n:
                    break
        return out
    except OSError:
        return []


def render(module_dir: Path) -> str:
    L = []
    name = module_dir.name
    L.append(f"## {name}")

    readme = module_dir / "README.md"
    if readme.exists():
        # Extract a 1-2 sentence summary
        text = readme.read_text(encoding="utf-8", errors="ignore")
        # Strip code blocks, then take first non-header paragraph
        text_no_code = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        paragraphs = [p.strip() for p in text_no_code.split("\n\n") if p.strip() and not p.strip().startswith("#")]
        if paragraphs:
            blurb = re.sub(r"\s+", " ", paragraphs[0])[:280]
            L.append(f"> {blurb}")
    L.append("")

    # Files table
    py_files = sorted(p for p in module_dir.rglob("*.py") if "__pycache__" not in str(p))
    md_files = sorted(p for p in module_dir.glob("*.md"))
    req_files = sorted(p for p in module_dir.glob("requirements*.txt"))
    ts_files = sorted(p for p in module_dir.rglob("*.tsx")) + sorted(p for p in module_dir.rglob("*.ts"))
    figures = sorted((module_dir / "figures").glob("*.png")) if (module_dir / "figures").exists() else []

    L.append("**Files**")
    L.append("")
    L.append("| File | Lines | Role |")
    L.append("|---|---:|---|")
    for f in py_files + ts_files + md_files + req_files:
        rel = f.relative_to(module_dir)
        role = ""
        if f.name == "demo.py":          role = "smoke test / sample run"
        elif f.name == "viz.py":          role = "figure generator"
        elif f.name == "README.md":       role = "module doc"
        elif f.name == "requirements.txt": role = "deps"
        elif "test" in f.name:            role = "tests"
        elif f.suffix in (".tsx", ".ts"): role = "frontend source"
        else:                              role = "core"
        L.append(f"| `{rel}` | {line_count(f)} | {role} |")
    L.append("")

    # Symbols
    sym_rows = []
    for py in py_files:
        if py.name == "viz.py":  # viz functions are visualization plumbing, skip noise
            continue
        classes, funcs = extract_symbols(py)
        for c, doc in classes:
            sym_rows.append((py.relative_to(module_dir), "class", c, doc))
        for fn, doc in funcs:
            sym_rows.append((py.relative_to(module_dir), "def", fn, doc))
    if sym_rows:
        L.append("**Public API**")
        L.append("")
        L.append("| File | Kind | Name | Description |")
        L.append("|---|---|---|---|")
        for f, kind, name_, doc in sym_rows:
            L.append(f"| `{f}` | `{kind}` | `{name_}` | {doc or '—'} |")
        L.append("")

    # Figures
    if figures:
        L.append("**Figures**")
        L.append("")
        for fig in figures:
            sz = fig.stat().st_size
            L.append(f"- `figures/{fig.name}` ({sz / 1024:.0f} KB)")
        L.append("")

    # Demo command
    if (module_dir / "demo.py").exists():
        L.append("**Run**")
        L.append("")
        L.append("```bash")
        L.append(f"cd echoscroll/{module_dir.name}")
        L.append("pip install -r requirements.txt")
        L.append("python demo.py")
        if (module_dir / "viz.py").exists():
            L.append("python viz.py   # regenerate figures")
        L.append("```")
        L.append("")
    elif module_dir.name == "M8_frontend_backend":
        L.append("**Run**")
        L.append("")
        L.append("```bash")
        L.append("# backend")
        L.append("cd echoscroll/M8_frontend_backend/backend")
        L.append("pip install -r requirements.txt")
        L.append("uvicorn main:app --reload")
        L.append("")
        L.append("# frontend (separate shell)")
        L.append("cd echoscroll/M8_frontend_backend/frontend")
        L.append("npm install && npm run dev")
        L.append("```")
        L.append("")

    return "\n".join(L)


def main() -> None:
    modules = sorted(p for p in ROOT.iterdir() if p.is_dir() and p.name.startswith("M") and p.name[1].isdigit())
    total_py = 0
    total_lines = 0
    total_figs = 0
    for m in modules:
        for py in m.rglob("*.py"):
            if "__pycache__" in str(py):
                continue
            total_py += 1
            total_lines += line_count(py)
        figs = (m / "figures")
        if figs.exists():
            total_figs += len(list(figs.glob("*.png")))

    out_lines = [
        "# EchoScroll · Module Tracker",
        "",
        "> Auto-generated by `inspect_modules.py`. Per-module file inventory, public API,",
        "> figures, and run commands.",
        "",
        f"**Aggregate**: {len(modules)} modules · {total_py} Python files · {total_lines:,} lines · {total_figs} figures",
        "",
        "## Quick index",
        "",
        "| Module | Lines | Figures | Headline |",
        "|---|---:|---:|---|",
    ]

    for m in modules:
        py_lines = 0
        for py in m.rglob("*.py"):
            if "__pycache__" in str(py):
                continue
            py_lines += line_count(py)
        figs = list((m / "figures").glob("*.png")) if (m / "figures").exists() else []
        readme = m / "README.md"
        head = ""
        if readme.exists():
            text = readme.read_text(encoding="utf-8", errors="ignore")
            text_no_code = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
            paragraphs = [p.strip() for p in text_no_code.split("\n\n") if p.strip() and not p.strip().startswith("#")]
            if paragraphs:
                head = re.sub(r"\s+", " ", paragraphs[0])[:120]
        out_lines.append(f"| [{m.name}](#{m.name.lower().replace('_', '-')}) | {py_lines:,} | {len(figs)} | {head} |")

    out_lines.append("")
    out_lines.append("---")
    out_lines.append("")

    for m in modules:
        out_lines.append(render(m))
        out_lines.append("---")
        out_lines.append("")

    OUT.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
