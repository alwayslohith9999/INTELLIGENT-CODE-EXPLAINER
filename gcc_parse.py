"""Parse GCC diagnostic output into structured records (authoritative line/column)."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Diagnostic:
    line: int
    column: int | None
    severity: str  # "error", "warning", "note"
    message: str
    raw_line: str


# Anchor from the right so paths may contain ':' (e.g. Windows drive or odd filenames).
_TAIL_RE = re.compile(
    r":(?P<line>\d+):(?P<col>\d+):\s*"
    r"(?P<sev>error|warning|fatal error|note):\s*"
    r"(?P<msg>.+)$",
    re.IGNORECASE | re.DOTALL,
)


def parse_gcc_output(stderr_text: str) -> list[Diagnostic]:
    """Extract one diagnostic per primary line (file:line:col: severity: message)."""
    out: list[Diagnostic] = []
    for raw in stderr_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = _TAIL_RE.search(line)
        if not m:
            continue
        try:
            ln = int(m.group("line"))
            col = int(m.group("col"))
        except ValueError:
            continue
        sev = m.group("sev").lower()
        if "fatal" in sev:
            sev = "error"
        elif sev == "note":
            sev = "note"
        elif sev == "warning":
            sev = "warning"
        else:
            sev = "error"
        msg = m.group("msg").strip()
        out.append(
            Diagnostic(
                line=ln,
                column=col,
                severity=sev,
                message=msg,
                raw_line=line,
            )
        )
    return out


def diagnostics_to_prompt_block(diagnostics: list[Diagnostic]) -> str:
    lines = []
    for d in diagnostics:
        col = f":{d.column}" if d.column is not None else ""
        lines.append(f"Line {d.line}{col} [{d.severity}]: {d.message}")
    return "\n".join(lines) if lines else "(no structured diagnostics parsed)"
