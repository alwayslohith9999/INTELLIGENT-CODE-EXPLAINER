"""Local explainer: TF-IDF + linear classifier trained on synthetic GCC-like text (no cloud APIs)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from explainer_catalog import CATEGORY_EXPLANATIONS, expanded_training_pairs

BASE = Path(__file__).resolve().parent
MODEL_PATH = BASE / "models" / "gcc_explainer.joblib"

_pipeline = None


def _load_pipeline():
    global _pipeline
    if _pipeline is not None:
        return _pipeline
    if not MODEL_PATH.is_file():
        return None
    try:
        import joblib

        _pipeline = joblib.load(MODEL_PATH)
    except Exception:
        _pipeline = None
    return _pipeline


def _keyword_classify(message: str) -> str:
    """Fallback: longest matching training substring wins."""
    msg = message.strip()
    best_cat = "generic"
    best_len = -1
    for text, cat in expanded_training_pairs():
        if len(text) > best_len and text.lower() in msg.lower():
            best_cat = cat
            best_len = len(text)
    return best_cat


def classify_diagnostic_message(message: str) -> str:
    pipe = _load_pipeline()
    if pipe is not None:
        try:
            return str(pipe.predict([message])[0])
        except Exception:
            pass
    return _keyword_classify(message)


def _issue_for_line(line: int | None, category: str) -> dict[str, Any]:
    fields = CATEGORY_EXPLANATIONS.get(category) or CATEGORY_EXPLANATIONS["generic"]
    return {
        "line": line,
        "plain_explanation": fields["plain_explanation"],
        "likely_cause": fields["likely_cause"],
        "suggested_fix": fields["suggested_fix"],
    }


def _runtime_summary(runtime_text: str, runtime_meta: dict[str, Any]) -> str | None:
    if runtime_meta.get("skipped_reason") == "disabled_by_env":
        return None
    if runtime_meta.get("skipped_reason") == "compile_failed":
        return None
    if not runtime_meta.get("executed"):
        return None
    if runtime_meta.get("timed_out"):
        return "The program hit the run timeout—likely an infinite loop or blocking I/O."
    code = runtime_meta.get("exit_code")
    if code == 0:
        return "The program exited normally with status 0."
    low = (runtime_text or "").lower()
    if "segmentation fault" in low or "access violation" in low:
        return f"Nonzero exit ({code}); output suggests a crash (e.g. bad pointer or stack overflow)."
    if "aborted" in low or "abort" in low:
        return f"Nonzero exit ({code}); the runtime reported an abort/assert-style failure."
    return f"The program finished with exit code {code} (nonzero). Check stdout/stderr for details."


def explain_locally(
    *,
    source_code: str,  # reserved for future context-aware explanations
    gcc_stderr: str,
    diagnostics_json: list[dict[str, Any]],
    runtime_text: str,
    runtime_meta: dict[str, Any],
) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []

    for d in diagnostics_json:
        msg = d.get("message") or ""
        line = d.get("line")
        cat = classify_diagnostic_message(msg)
        issues.append(_issue_for_line(line, cat))

    if not issues and (gcc_stderr or "").strip():
        raw = (gcc_stderr or "")[:2000]
        # Single synthetic issue from raw text (no line/column parsed)
        cat = classify_diagnostic_message(raw)
        issues.append(_issue_for_line(None, cat))

    has_error = any((x.get("severity") or "").lower() == "error" for x in diagnostics_json)
    summary_parts = []
    if has_error:
        summary_parts.append("Compilation failed: GCC reported one or more errors.")
    elif diagnostics_json:
        summary_parts.append("GCC reported warnings or notes; review each diagnostic.")
    else:
        summary_parts.append("No structured line/column diagnostics were parsed from GCC output.")

    if runtime_meta.get("executed"):
        if runtime_meta.get("timed_out"):
            summary_parts.append("The run timed out.")
        elif runtime_meta.get("exit_code") == 0:
            summary_parts.append("The built program ran and exited with code 0.")
        else:
            summary_parts.append(
                f"The program ran and exited with code {runtime_meta.get('exit_code')}."
            )

    summary = " ".join(summary_parts) if summary_parts else "No compiler output to summarize."
    if not model_available():
        summary = (
            "[Keyword fallback — run: python train_explainer.py] " + summary
        )

    return {
        "summary": summary,
        "runtime_summary": _runtime_summary(runtime_text, runtime_meta),
        "issues": issues,
    }


def model_available() -> bool:
    return MODEL_PATH.is_file()
