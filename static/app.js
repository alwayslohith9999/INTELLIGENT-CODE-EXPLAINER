const codeEl = document.getElementById("code");
const btn = document.getElementById("analyze");
const statusEl = document.getElementById("status");
const badgeEl = document.getElementById("compile-badge");
const diagList = document.getElementById("diag-list");
const gccRaw = document.getElementById("gcc-raw");
const runBadgeEl = document.getElementById("run-badge");
const runMetaEl = document.getElementById("run-meta");
const runRawEl = document.getElementById("run-raw");
const aiPlaceholder = document.getElementById("ai-placeholder");
const aiSummary = document.getElementById("ai-summary");
const aiRuntimeSummary = document.getElementById("ai-runtime-summary");
const aiIssues = document.getElementById("ai-issues");

function setLoading(loading) {
  btn.disabled = loading;
  statusEl.textContent = loading ? "Compiling and running…" : "";
}

function sevClass(sev) {
  if (sev === "warning") return "sev-warning";
  if (sev === "note") return "sev-note";
  return "sev-error";
}

function renderRun(data) {
  const run = data.run || {};
  runBadgeEl.classList.remove("hidden");
  runRawEl.classList.remove("hidden");
  runBadgeEl.classList.remove("ok", "fail", "neutral");
  runMetaEl.textContent = "";

  const sec =
    run.timeout_sec != null
      ? `Timeout: ${run.timeout_sec}s`
      : "";

  if (run.skipped_reason === "disabled_by_env") {
    runBadgeEl.textContent = "Run: skipped (C_SKIP_RUN)";
    runBadgeEl.classList.add("neutral");
    runMetaEl.textContent = sec;
    runRawEl.textContent = "";
    return;
  }
  if (run.skipped_reason === "compile_failed") {
    runBadgeEl.textContent = "Run: skipped (compile failed)";
    runBadgeEl.classList.add("neutral");
    runMetaEl.textContent = sec;
    runRawEl.textContent = "";
    return;
  }
  if (run.skipped_reason === "executable_missing") {
    runBadgeEl.textContent = "Run: skipped (no executable produced)";
    runBadgeEl.classList.add("fail");
    runMetaEl.textContent = sec;
    runRawEl.textContent = "";
    return;
  }
  if (run.skipped_reason === "run_error") {
    runBadgeEl.textContent = "Run: failed to start";
    runBadgeEl.classList.add("fail");
    runMetaEl.textContent = [run.error || "", sec].filter(Boolean).join(" · ");
    runRawEl.textContent = "";
    return;
  }

  if (run.timed_out) {
    runBadgeEl.textContent = "Run: timed out";
    runBadgeEl.classList.add("fail");
    runMetaEl.textContent = sec;
  } else if (run.executed && run.exit_code === 0) {
    runBadgeEl.textContent = "Run: success (exit code 0)";
    runBadgeEl.classList.add("ok");
    runMetaEl.textContent = sec;
  } else if (run.executed) {
    runBadgeEl.textContent = `Run: exited with code ${run.exit_code}`;
    runBadgeEl.classList.add("fail");
    runMetaEl.textContent = sec;
  } else {
    runBadgeEl.textContent = "Run: not executed";
    runBadgeEl.classList.add("neutral");
    runMetaEl.textContent = sec;
  }

  const chunks = [];
  if (run.stdout) chunks.push("--- stdout ---\n" + run.stdout);
  if (run.stderr) chunks.push("--- stderr ---\n" + run.stderr);
  runRawEl.textContent = chunks.join("\n\n") || "(no stdout/stderr)";
}

function render(data) {
  badgeEl.classList.remove("hidden");
  badgeEl.textContent = data.compile_success ? "Compile: success" : "Compile: failed";
  badgeEl.classList.toggle("ok", data.compile_success);
  badgeEl.classList.toggle("fail", !data.compile_success);

  renderRun(data);

  diagList.innerHTML = "";
  if (!data.diagnostics || data.diagnostics.length === 0) {
    const li = document.createElement("li");
    li.textContent = data.compile_success
      ? "No structured diagnostics (clean build)."
      : "No line:column lines parsed. See raw compiler output below.";
    diagList.appendChild(li);
  } else {
    for (const d of data.diagnostics) {
      const li = document.createElement("li");
      const meta = document.createElement("div");
      meta.className = `meta ${sevClass(d.severity)}`;
      meta.textContent = `Line ${d.line}, column ${d.column} — ${d.severity}`;
      const msg = document.createElement("div");
      msg.textContent = d.message;
      li.appendChild(meta);
      li.appendChild(msg);
      diagList.appendChild(li);
    }
  }

  gccRaw.classList.remove("hidden");
  gccRaw.textContent = data.gcc_output || "(empty)";

  aiIssues.innerHTML = "";
  aiSummary.classList.add("hidden");
  aiRuntimeSummary.classList.add("hidden");
  aiPlaceholder.classList.remove("hidden");

  if (!data.ai_configured) {
    aiPlaceholder.textContent =
      "Explainer is disabled. GCC diagnostics above are still authoritative.";
    return;
  }

  const ai = data.ai;
  if (!ai) {
    aiPlaceholder.textContent = "AI did not return a response.";
    return;
  }
  if (ai.error) {
    aiPlaceholder.textContent = ai.error;
    return;
  }

  aiPlaceholder.classList.add("hidden");
  if (ai.summary) {
    aiSummary.classList.remove("hidden");
    aiSummary.textContent = ai.summary;
  }
  if (ai.runtime_summary) {
    aiRuntimeSummary.classList.remove("hidden");
    aiRuntimeSummary.textContent = ai.runtime_summary;
  }
  const issues = Array.isArray(ai.issues) ? ai.issues : [];
  for (const issue of issues) {
    const li = document.createElement("li");
    const line = document.createElement("div");
    line.className = "line";
    line.textContent =
      issue.line != null
        ? `Line ${issue.line}`
        : "Runtime / general (no GCC line)";
    li.appendChild(line);
    const parts = [
      ["Explanation", issue.plain_explanation],
      ["Likely cause", issue.likely_cause],
      ["Suggested fix", issue.suggested_fix],
    ];
    for (const [label, text] of parts) {
      if (!text) continue;
      const p = document.createElement("p");
      p.innerHTML = `<strong>${label}:</strong> ${escapeHtml(String(text))}`;
      li.appendChild(p);
    }
    aiIssues.appendChild(li);
  }
}

function escapeHtml(s) {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

btn.addEventListener("click", async () => {
  const code = codeEl.value;
  setLoading(true);
  try {
    const r = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code }),
    });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) {
      const d = data.detail;
      statusEl.textContent =
        typeof d === "string"
          ? d
          : Array.isArray(d)
            ? d.map((x) => x.msg || JSON.stringify(x)).join("; ")
            : JSON.stringify(d || r.statusText);
      return;
    }
    render(data);
  } catch (e) {
    statusEl.textContent = String(e.message || e);
  } finally {
    setLoading(false);
  }
});
