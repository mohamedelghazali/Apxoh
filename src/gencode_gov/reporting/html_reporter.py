"""CSP-locked, HTML-escaped static HTML governance assessment reporter."""

from __future__ import annotations

import html
import os
import tempfile
from pathlib import Path
from typing import Any

from gencode_gov.core.errors import GovernanceError


def _atomic_safe_write(target: Path, content: str, root_anchor: Path | None = None) -> Path:
    if target.exists() and target.is_symlink():
        raise GovernanceError(f"refusing to write report through symlink: {target}")
    parent = target.parent
    if parent.exists() and parent.is_symlink():
        raise GovernanceError(f"refusing symlinked report parent directory: {parent}")
    parent.mkdir(parents=True, exist_ok=True)
    if root_anchor is not None:
        try:
            parent.resolve().relative_to(root_anchor.resolve())
        except ValueError as exc:
            raise GovernanceError(f"report path escapes project root: {target}") from exc

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=parent,
        prefix=".report-",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
        tmp = Path(handle.name)
    tmp.replace(target)
    return target


class HtmlReporter:
    """Render a JSON governance assessment dict into a zero-JS, CSP-locked HTML document."""

    def render(self, report_data: dict[str, Any]) -> str:
        esc = html.escape
        project = esc(str(report_data.get("project", report_data.get("project_name", "Project"))))
        decision = esc(str(report_data.get("decision", report_data.get("verdict", "UNKNOWN"))))
        commit = esc(str(report_data.get("commit_sha", "uncommitted")))
        score_raw = report_data.get("score", {})
        total_score = (
            esc(str(score_raw.get("total", score_raw)))
            if isinstance(score_raw, dict)
            else esc(str(score_raw))
        )

        rows: list[str] = []
        rules_list = report_data.get("rules", report_data.get("outcomes", []))
        if isinstance(rules_list, list):
            for item in rules_list:
                if not isinstance(item, dict):
                    continue
                rid = esc(str(item.get("rule_id", item.get("id", ""))))
                dom = esc(str(item.get("domain", "")))
                st = esc(str(item.get("status", "")))
                rsn = esc(str(item.get("reason", "")))
                rows.append(
                    f"<tr><td><code>{rid}</code></td><td>{dom}</td>"
                    f"<td class='st-{st.lower()}'>{st}</td><td>{rsn}</td></tr>"
                )
        rows_html = "\n".join(rows) or "<tr><td colspan='4'>No rule outcomes recorded.</td></tr>"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="Content-Security-Policy"
        content="default-src 'none'; style-src 'unsafe-inline'">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>GENCODE-GOV Assessment Report — {project}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem auto; max-width: 1080px;
            padding: 0 1rem; color: #111827; line-height: 1.5; }}
    header {{ border-bottom: 2px solid #e5e7eb; padding-bottom: 1rem; margin-bottom: 1.5rem; }}
    .meta {{ display: flex; gap: 1.5rem; flex-wrap: wrap; font-size: 0.95rem; color: #374151; }}
    .badge {{ font-weight: 700; padding: 0.15rem 0.5rem; border-radius: 4px;
              background: #f3f4f6; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; font-size: 0.9rem; }}
    th, td {{ border: 1px solid #e5e7eb; padding: 0.55rem 0.7rem; text-align: left;
              vertical-align: top; }}
    th {{ background: #f9fafb; font-weight: 600; }}
    .st-pass {{ color: #065f46; font-weight: 600; }}
    .st-fail {{ color: #991b1b; font-weight: 600; }}
    .st-blocked {{ color: #92400e; font-weight: 600; }}
  </style>
</head>
<body>
  <header>
    <h1>GENCODE-GOV Governance Assessment</h1>
    <div class="meta">
      <span>Project: <strong>{project}</strong></span>
      <span>Decision: <span class="badge">{decision}</span></span>
      <span>Score: <strong>{total_score}</strong></span>
      <span>Commit: <code>{commit}</code></span>
    </div>
  </header>
  <main>
    <h2>Rule Verification Outcomes</h2>
    <table>
      <thead>
        <tr><th>Rule ID</th><th>Domain</th><th>Status</th><th>Verification Detail</th></tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>
  </main>
</body>
</html>
"""

    def write(
        self,
        report_data: dict[str, Any],
        target: Path,
        *,
        project_root: Path | None = None,
    ) -> Path:
        rendered = self.render(report_data)
        return _atomic_safe_write(target, rendered, root_anchor=project_root)


__all__ = ["HtmlReporter", "_atomic_safe_write"]
