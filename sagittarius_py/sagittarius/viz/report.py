"""
Lightweight report generation tool for simulation results.

Automatically generates summary reports with embedded charts, metadata,
and clear distinction between exploratory visualizations and benchmark evidence.

Reports include:
- Result summaries with key metrics
- Embedded visualization charts
- Mode version and backend metadata
- Random seeds and basis mode information
- Output grid details
- Associated manifest files
- Clear classification: EXPLORATORY vs BENCHMARK EVIDENCE

IMPORTANT: Reports strictly distinguish between exploratory visualizations
(not for calibration) and benchmark/official conclusion materials (SPEC-GOV-001).
"""

import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.figure import Figure


class ReportGenerator:
    """
    Lightweight report generator for simulation results.
    
    Generates HTML or Markdown reports with embedded charts and metadata.
    Strictly distinguishes between exploratory visualizations and benchmark evidence.
    """
    
    def __init__(
        self,
        output_dir: str = "reports",
        report_type: str = "html",
        title: str = "Simulation Results Report",
    ):
        """
        Initialize report generator.
        
        Args:
            output_dir: Directory to save reports
            report_type: 'html' or 'markdown'
            title: Report title
        """
        self.output_dir = output_dir
        self.report_type = report_type.lower()
        self.title = title
        self.sections = []
        self.metadata = {}
        
        os.makedirs(output_dir, exist_ok=True)
    
    def add_result_summary(
        self,
        result: Any,
        classification: str = "exploratory",
        custom_metrics: Optional[Dict[str, Any]] = None,
    ) -> 'ReportGenerator':
        """
        Add a result summary section to the report.
        
        Args:
            result: SimulationResult object
            classification: 'exploratory' or 'benchmark_evidence'
            custom_metrics: Additional metrics to display
            
        Returns:
            Self for method chaining
        """
        if classification not in ('exploratory', 'benchmark_evidence'):
            raise ValueError(f"Invalid classification: {classification}. Must be 'exploratory' or 'benchmark_evidence'")
        
        # Extract metadata
        summary = {
            'type': 'result_summary',
            'classification': classification,
            'artifact_id': result.manifest.get('artifact_id') if hasattr(result, 'manifest') and result.manifest else None,
            'mode_version': getattr(result, 'mode_version', None),
            'schema_version': getattr(result, 'schema_version', None),
            'backend': getattr(result, 'backend', None),
            'seed': getattr(result, 'seed', None),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        }
        
        # Extract register info
        if hasattr(result, 'register'):
            try:
                reg = result.register
                summary['register'] = {
                    'n_atoms': len(reg.positions) if hasattr(reg, 'positions') else None,
                    'basis': str(getattr(reg, 'basis', 'computational')),
                }
            except:
                pass
        
        # Extract solver config
        if hasattr(result, 'config'):
            try:
                config = result.config
                summary['solver_config'] = {
                    'method': getattr(config, 'method', None),
                    'dt': getattr(config, 'dt', None),
                    't_final': getattr(config, 't_final', None),
                }
            except:
                pass
        
        # Add custom metrics
        if custom_metrics:
            summary['custom_metrics'] = custom_metrics
        
        # Classification disclaimer
        if classification == 'exploratory':
            summary['disclaimer'] = "⚠️ EXPLORATORY VISUALIZATION - Not for hardware calibration or performance evidence"
        else:
            summary['disclaimer'] = "✅ BENCHMARK EVIDENCE - Bound to controlled standard artifacts per SPEC-GOV-001"
        
        self.sections.append(summary)
        return self
    
    def add_chart(
        self,
        fig: Figure,
        title: str,
        description: str = "",
        classification: str = "exploratory",
        chart_metadata: Optional[Dict[str, Any]] = None,
    ) -> 'ReportGenerator':
        """
        Add a chart section to the report.
        
        Args:
            fig: Matplotlib figure
            title: Chart title
            description: Chart description
            classification: 'exploratory' or 'benchmark_evidence'
            chart_metadata: Additional chart metadata
            
        Returns:
            Self for method chaining
        """
        if classification not in ('exploratory', 'benchmark_evidence'):
            raise ValueError(f"Invalid classification: {classification}")
        
        # Save chart
        chart_filename = f"chart_{len(self.sections)}.png"
        chart_path = os.path.join(self.output_dir, chart_filename)
        fig.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
        
        chart_section = {
            'type': 'chart',
            'title': title,
            'description': description,
            'classification': classification,
            'filename': chart_filename,
            'metadata': chart_metadata or {},
        }
        
        if classification == 'exploratory':
            chart_section['disclaimer'] = "⚠️ EXPLORATORY - Not for calibration"
        else:
            chart_section['disclaimer'] = "✅ BENCHMARK EVIDENCE"
        
        self.sections.append(chart_section)
        return self
    
    def add_manifest_link(
        self,
        manifest_path: str,
        description: str = "",
    ) -> 'ReportGenerator':
        """
        Add a link to associated manifest file.
        
        Args:
            manifest_path: Path to manifest JSON file
            description: Description of the manifest
            
        Returns:
            Self for method chaining
        """
        self.sections.append({
            'type': 'manifest_link',
            'path': manifest_path,
            'description': description,
        })
        return self
    
    def generate(self, output_filename: Optional[str] = None) -> str:
        """
        Generate the final report.
        
        Args:
            output_filename: Output filename (auto-generated if None)
            
        Returns:
            Path to generated report file
        """
        if output_filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            ext = 'html' if self.report_type == 'html' else 'md'
            output_filename = f"report_{timestamp}.{ext}"
        
        output_path = os.path.join(self.output_dir, output_filename)
        
        if self.report_type == 'html':
            self._generate_html(output_path)
        else:
            self._generate_markdown(output_path)
        
        return output_path
    
    def _generate_html(self, output_path: str):
        """Generate HTML report."""
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #bdc3c7; background: #f8f9fa; }}
        .exploratory {{ border-left-color: #e74c3c; background: #fdf2f2; }}
        .benchmark {{ border-left-color: #27ae60; background: #f2fdf5; }}
        .disclaimer {{ padding: 10px; margin: 10px 0; border-radius: 4px; font-weight: bold; }}
        .disclaimer.exploratory {{ background: #ffebee; color: #c62828; }}
        .disclaimer.benchmark {{ background: #e8f5e9; color: #2e7d32; }}
        .metadata {{ font-size: 0.9em; color: #666; }}
        .chart {{ max-width: 100%; height: auto; margin: 10px 0; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #3498db; color: white; }}
    </style>
</head>
<body>
    <h1>{self.title}</h1>
    <p class="metadata">Generated: {datetime.utcnow().isoformat()}Z</p>
"""
        
        for i, section in enumerate(self.sections):
            if section['type'] == 'result_summary':
                html_content += self._render_result_summary_html(section, i)
            elif section['type'] == 'chart':
                html_content += self._render_chart_html(section, i)
            elif section['type'] == 'manifest_link':
                html_content += self._render_manifest_link_html(section, i)
        
        html_content += """
</body>
</html>"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _render_result_summary_html(self, section: Dict, index: int) -> str:
        """Render result summary as HTML."""
        classification_class = 'benchmark' if section['classification'] == 'benchmark_evidence' else 'exploratory'
        
        html = f"""
    <div class="section {classification_class}">
        <h2>Result Summary #{index + 1}</h2>
        <div class="disclaimer {classification_class}">{section['disclaimer']}</div>
        <table>
"""
        
        for key, value in section.items():
            if key in ('type', 'classification', 'disclaimer'):
                continue
            if isinstance(value, dict):
                html += f"            <tr><th>{key}</th><td><pre>{json.dumps(value, indent=2)}</pre></td></tr>\n"
            else:
                html += f"            <tr><th>{key}</th><td>{value}</td></tr>\n"
        
        html += """        </table>
    </div>
"""
        return html
    
    def _render_chart_html(self, section: Dict, index: int) -> str:
        """Render chart as HTML."""
        classification_class = 'benchmark' if section['classification'] == 'benchmark_evidence' else 'exploratory'
        
        html = f"""
    <div class="section {classification_class}">
        <h2>{section['title']}</h2>
        <div class="disclaimer {classification_class}">{section['disclaimer']}</div>
        <p>{section['description']}</p>
        <img src="{section['filename']}" alt="{section['title']}" class="chart">
"""
        
        if section['metadata']:
            html += f"        <div class='metadata'><strong>Metadata:</strong> {json.dumps(section['metadata'], indent=2)}</div>\n"
        
        html += """    </div>
"""
        return html
    
    def _render_manifest_link_html(self, section: Dict, index: int) -> str:
        """Render manifest link as HTML."""
        return f"""
    <div class="section">
        <h2>Associated Manifest</h2>
        <p>{section['description']}</p>
        <p><a href="{section['path']}" target="_blank">{section['path']}</a></p>
    </div>
"""
    
    def _generate_markdown(self, output_path: str):
        """Generate Markdown report."""
        md_content = f"# {self.title}\n\n"
        md_content += f"*Generated: {datetime.utcnow().isoformat()}Z*\n\n"
        md_content += "---\n\n"
        
        for i, section in enumerate(self.sections):
            if section['type'] == 'result_summary':
                md_content += self._render_result_summary_md(section, i)
            elif section['type'] == 'chart':
                md_content += self._render_chart_md(section, i)
            elif section['type'] == 'manifest_link':
                md_content += self._render_manifest_link_md(section, i)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
    
    def _render_result_summary_md(self, section: Dict, index: int) -> str:
        """Render result summary as Markdown."""
        md = f"## Result Summary #{index + 1}\n\n"
        md += f"**{section['disclaimer']}**\n\n"
        
        for key, value in section.items():
            if key in ('type', 'classification', 'disclaimer'):
                continue
            if isinstance(value, dict):
                md += f"- **{key}:**\n```json\n{json.dumps(value, indent=2)}\n```\n"
            else:
                md += f"- **{key}:** {value}\n"
        
        md += "\n---\n\n"
        return md
    
    def _render_chart_md(self, section: Dict, index: int) -> str:
        """Render chart as Markdown."""
        md = f"## {section['title']}\n\n"
        md += f"**{section['disclaimer']}**\n\n"
        md += f"{section['description']}\n\n"
        md += f"![{section['title']}]({section['filename']})\n\n"
        
        if section['metadata']:
            md += f"**Metadata:**\n```json\n{json.dumps(section['metadata'], indent=2)}\n```\n\n"
        
        md += "---\n\n"
        return md
    
    def _render_manifest_link_md(self, section: Dict, index: int) -> str:
        """Render manifest link as Markdown."""
        md = f"## Associated Manifest\n\n"
        md += f"{section['description']}\n\n"
        md += f"[{section['path']}]({section['path']})\n\n"
        md += "---\n\n"
        return md


def generate_quick_report(
    results: List[Any],
    output_dir: str = "reports",
    title: str = "Quick Simulation Report",
    classifications: Optional[List[str]] = None,
) -> str:
    """
    Quick one-liner to generate report from multiple results.
    
    Args:
        results: List of SimulationResult objects
        output_dir: Output directory
        title: Report title
        classifications: List of classifications for each result ('exploratory' or 'benchmark_evidence')
        
    Returns:
        Path to generated report
        
    Example:
        >>> report_path = generate_quick_report([result1, result2], classifications=['exploratory', 'benchmark_evidence'])
    """
    if classifications is None:
        classifications = ['exploratory'] * len(results)
    
    if len(results) != len(classifications):
        raise ValueError("results and classifications must have the same length")
    
    generator = ReportGenerator(output_dir=output_dir, title=title)
    
    for result, classification in zip(results, classifications):
        generator.add_result_summary(result, classification=classification)
    
    return generator.generate()