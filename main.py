"""
Intelligent Code Error Explainer — C only.
Line/column come from GCC; a locally trained classifier (see train_explainer.py) explains diagnostics.
Falls back to keyword rules if models/gcc_explainer.joblib is missing.
After a successful compile, the built program is run once with a timeout (see C_RUN_TIMEOUT_SEC).
Run: uvicorn main:app --reload --host 127.0.0.1 --port 8000
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from gcc_parse import Diagnostic, parse_gcc_output
from local_explain import explain_locally, model_available

BASE = Path(__file__).resolve().parent
STATIC = BASE / "static"

app = FastAPI(title="C Error Explainer", version="1.0.0")


class AnalyzeBody(BaseModel):
    code: str = Field(..., min_length=1, max_length=256_000)


def _gcc_cmd() -> str:
    return os.getenv("GCC_PATH", "gcc").strip() or "gcc"


def _gcc_resolves(gcc: str) -> bool:
    g = gcc.strip().strip('"')
    if os.path.isfile(g):
        return True
    exe = g.split()[0]
    return bool(shutil.which(exe))


def _run_timeout_sec() -> float:
    raw = os.getenv("C_RUN_TIMEOUT_SEC", "5").strip() or "5"
    try:
        return max(0.5, min(120.0, float(raw)))
    except ValueError:
        return 5.0


def _skip_run() -> bool:
    return os.getenv("C_SKIP_RUN", "").strip().lower() in ("1", "true", "yes", "on")


def format_runtime_for_llm(run: dict[str, Any]) -> str:
    reason = run.get("skipped_reason")
    if reason == "disabled_by_env":
        return "Program was not run (C_SKIP_RUN is set)."
    if reason == "compile_failed":
        return "Program was not run because compilation failed."
    if reason == "executable_missing":
        return "Program was not run: executable was not produced."
    if run.get("error"):
        return f"Program run failed: {run['error']}"
    if not run.get("executed"):
        return "Program was not run."
    parts = [
        f"timed_out={run.get('timed_out', False)}",
        f"exit_code={run.get('exit_code')!r}",
        "--- stdout ---",
        run.get("stdout") or "",
        "--- stderr ---",
        run.get("stderr") or "",
    ]
    return "\n".join(parts)


def runtime_meta_compact(run: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "executed",
        "skipped_reason",
        "timed_out",
        "exit_code",
        "error",
        "timeout_sec",
    )
    return {k: run[k] for k in keys if k in run}


def compile_and_run(code: str) -> tuple[int, str, dict[str, Any]]:
    """Compile C source; if OK, run the executable under a timeout. Returns (compile_exit, compiler_text, run_info)."""
    gcc = _gcc_cmd()
    if not _gcc_resolves(gcc):
        raise HTTPException(
            status_code=503,
            detail="GCC not found. Install MinGW/MSYS2 and add gcc to PATH, or set GCC_PATH.",
        )

    run_timeout = _run_timeout_sec()
    skip = _skip_run()

    with tempfile.TemporaryDirectory(prefix="c_explainer_") as tmp:
        tdir = Path(tmp)
        src = tdir / "user.c"
        out = tdir / ("user.exe" if sys.platform == "win32" else "user")
        src.write_text(code, encoding="utf-8", newline="\n")
        try:
            p = subprocess.run(
                [
                    gcc,
                    "-std=c11",
                    "-Wall",
                    "-Wextra",
                    "-O0",
                    "-o",
                    str(out),
                    str(src),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                shell=False,
            )
        except subprocess.TimeoutExpired:
            raise HTTPException(status_code=400, detail="GCC timed out (possible infinite compile).")
        except FileNotFoundError:
            raise HTTPException(status_code=503, detail=f"Could not run compiler: {gcc}")

        err = (p.stderr or "").strip()
        out_txt = (p.stdout or "").strip()
        combined = "\n".join(x for x in (err, out_txt) if x)

        run_block: dict[str, Any] = {
            "executed": False,
            "skipped_reason": None,
            "exit_code": None,
            "timed_out": False,
            "stdout": "",
            "stderr": "",
            "error": None,
            "timeout_sec": run_timeout,
        }

        if skip:
            run_block["skipped_reason"] = "disabled_by_env"
        elif p.returncode != 0:
            run_block["skipped_reason"] = "compile_failed"
        elif not out.is_file():
            run_block["skipped_reason"] = "executable_missing"
        else:
            try:
                pr = subprocess.run(
                    [str(out)],
                    cwd=str(tdir),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=run_timeout,
                    shell=False,
                )
                run_block["executed"] = True
                run_block["exit_code"] = pr.returncode
                run_block["stdout"] = (pr.stdout or "")[:8000]
                run_block["stderr"] = (pr.stderr or "")[:8000]
            except subprocess.TimeoutExpired as te:
                run_block["executed"] = True
                run_block["timed_out"] = True
                run_block["exit_code"] = None
                run_block["stdout"] = ((te.stdout or "") or "")[:8000]
                run_block["stderr"] = ((te.stderr or "") or "")[:8000]
            except OSError as oe:
                run_block["skipped_reason"] = "run_error"
                run_block["error"] = str(oe)[:500]

        return p.returncode, combined, run_block


def diagnostics_to_json(ds: list[Diagnostic]) -> list[dict]:
    return [
        {
            "line": d.line,
            "column": d.column,
            "severity": d.severity,
            "message": d.message,
        }
        for d in ds
    ]


@app.post("/api/analyze")
async def analyze(body: AnalyzeBody):
    code = body.code
    if not code.strip():
        raise HTTPException(status_code=400, detail="Code is empty.")

    exit_code, compiler_text, run_block = compile_and_run(code)
    diagnostics = parse_gcc_output(compiler_text)

    runtime_text = format_runtime_for_llm(run_block)
    rmeta = runtime_meta_compact(run_block)

    try:
        ai_payload = explain_locally(
            source_code=code,
            gcc_stderr=compiler_text,
            diagnostics_json=diagnostics_to_json(diagnostics),
            runtime_text=runtime_text,
            runtime_meta=rmeta,
        )
    except Exception as exc:
        hint = str(exc).strip()
        if len(hint) > 500:
            hint = hint[:500] + "…"
        ai_payload = {
            "error": (
                f"Explainer failed ({type(exc).__name__}): {hint}"
                if hint
                else f"Explainer failed ({type(exc).__name__})."
            ),
        }

    run_success = bool(
        run_block.get("executed")
        and not run_block.get("timed_out")
        and run_block.get("exit_code") == 0
    )

    return {
        "language": "c",
        "compiler": _gcc_cmd(),
        "compile_success": exit_code == 0,
        "gcc_output": compiler_text,
        "diagnostics": diagnostics_to_json(diagnostics),
        "run": run_block,
        "run_success": run_success,
        "ai": ai_payload,
        "ai_configured": True,
        "local_model_loaded": model_available(),
    }


@app.get("/api/health")
def health():
    g = _gcc_cmd()
    return {"ok": True, "gcc": g, "gcc_ok": _gcc_resolves(g)}


if STATIC.is_dir():
    app.mount("/assets", StaticFiles(directory=str(STATIC)), name="assets")


@app.get("/")
def index():
    index_path = STATIC / "index.html"
    if not index_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Frontend missing. Ensure backend/static/index.html exists.",
        )
    return FileResponse(index_path)
