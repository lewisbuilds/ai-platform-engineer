"""Unit tests for markdown report rendering."""

from ai_container_intelligence.models.report import create_analysis_report
from ai_container_intelligence.reporting.markdown_report import render_markdown_report


def test_render_markdown_report_contains_title() -> None:
    """Ensure report renderer includes top-level title."""
    internal_report = create_analysis_report("AI Container Intelligence Report", [])
    markdown = render_markdown_report(internal_report)
    assert "AI Container Intelligence Report" in markdown.content
    assert "Total findings: 0" in markdown.content
