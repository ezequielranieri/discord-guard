"""Unit tests for report generation."""

import os
import json
import pytest
from pathlib import Path
from guard.models.risk import AccountRiskReport, RiskLevel
from guard.reports.json_report import JSONReportGenerator
from guard.reports.pdf_report import PDFReportGenerator


@pytest.fixture
def mock_report():
    return AccountRiskReport(
        user_id="12345",
        username="testuser#0001",
        overall_score=70,
        overall_level=RiskLevel.CRITICAL,
        risks=[],
        authorized_apps=[],
        active_sessions=[],
        two_fa_enabled=False
    )


def test_json_report_generation(mock_report, tmp_path):
    """Tests that the JSON report is generated correctly."""
    output_file = tmp_path / "test_report.json"
    generator = JSONReportGenerator()
    
    path = generator.generate(mock_report, str(output_file))
    
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["user_id"] == "12345"
        assert data["overall_score"] == 70


def test_pdf_report_generation(mock_report, tmp_path):
    """Tests that the PDF report is generated successfully."""
    output_file = tmp_path / "test_report.pdf"
    generator = PDFReportGenerator()
    
    path = generator.generate(mock_report, str(output_file))
    
    assert os.path.exists(path)
    # Basic PDF check: file size should be > 0 and start with %PDF
    assert os.path.getsize(path) > 0
    with open(path, "rb") as f:
        assert f.read(4) == b"%PDF"
