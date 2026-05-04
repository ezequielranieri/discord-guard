"""JSON report generation for discord-guard."""

import json
from pathlib import Path
from guard.models.risk import AccountRiskReport


class JSONReportGenerator:
    """Generates a security report in JSON format."""

    def generate(self, report: AccountRiskReport, output_path: str) -> str:
        """Generates the JSON report.

        Args:
            report: The risk report to export.
            output_path: The file path to save the report.

        Returns:
            The path to the generated file.
        """
        path = Path(output_path)
        data = report.model_dump(mode="json")
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        return str(path.absolute())
