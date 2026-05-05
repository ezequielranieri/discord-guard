"""PDF report generation for discord-guard."""

from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from guard.models.risk import AccountRiskReport, RiskLevel


class PDFReportGenerator:
    """Generates a security report in PDF format."""

    def generate(self, report: AccountRiskReport, output_path: str) -> str:
        """Generates the PDF report.

        Args:
            report: The risk report to export.
            output_path: The file path to save the report.

        Returns:
            The path to the generated file.
        """
        path = Path(output_path)
        doc = SimpleDocTemplate(str(path), pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        elements.append(Paragraph("discord-guard Security Report", styles["Title"]))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
        elements.append(Spacer(1, 20))

        # Account Details
        elements.append(Paragraph("Account Information", styles["Heading2"]))
        elements.append(Paragraph(f"Username: {report.username}", styles["Normal"]))
        elements.append(Paragraph(f"User ID: {report.user_id}", styles["Normal"]))
        elements.append(Spacer(1, 10))

        # Overall Score
        score_color = colors.green
        if report.overall_level == RiskLevel.CRITICAL:
            score_color = colors.red
        elif report.overall_level == RiskLevel.WARNING:
            score_color = colors.orange

        score_style = ParagraphStyle(
            "ScoreStyle",
            parent=styles["Heading1"],
            textColor=score_color,
            alignment=1, # Center
        )
        elements.append(Paragraph(f"Overall Risk Score: {report.overall_score}/100", score_style))
        elements.append(Paragraph(f"Level: {report.overall_level.upper()}", score_style))
        elements.append(Spacer(1, 20))

        # Risk Details Table
        if report.risks:
            elements.append(Paragraph("Identified Risks", styles["Heading2"]))
            data = [["Category", "Level", "Description", "Recommendation"]]
            for risk in report.risks:
                data.append([
                    risk.category,
                    risk.level.upper(),
                    Paragraph(risk.description, styles["Normal"]),
                    Paragraph(risk.recommendation, styles["Normal"])
                ])

            table = Table(data, colWidths=[80, 70, 160, 160])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph("✅ No security risks detected.", styles["Normal"]))

        # Build PDF
        doc.build(elements)
        return str(path.absolute())
