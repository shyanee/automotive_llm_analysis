import os
from datetime import datetime
from pathlib import Path
import markdown

class ReportBuilder:
    """
    Builds professional HTML reports with embedded visualizations.
    Supports multiple output formats (HTML, PDF via weasyprint).
    """
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def build_html_report(
        self, 
        narrative: str, 
        plots: dict, 
        metadata: dict = None,
        output_filename: str = "report.html"
    ) -> str:
        """
        Combines LLM narrative with Plotly visualizations into a single HTML report.
        
        Args:
            narrative: Markdown-formatted text from LLM
            plots: Dict of {plot_name: html_string} from Plotly
            metadata: Optional metadata (generation time, model, etc.)
            output_filename: Output file name
            
        Returns:
            Path to generated report
        """
        # Convert markdown to HTML
        narrative_html = markdown.markdown(
            narrative, 
            extensions=['extra', 'codehilite', 'tables']
        )
        
        # Build metadata section
        meta_html = self._build_metadata_section(metadata)
        
        # Build plots section
        plots_html = self._build_plots_section(plots)
        
        # Combine everything
        full_html = self._build_full_html(
            meta_html, 
            narrative_html, 
            plots_html
        )
        
        # Save
        output_path = self.output_dir / output_filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_html)
        
        return str(output_path)
    
    def _build_metadata_section(self, metadata: dict = None) -> str:
        """Generates metadata banner at top of report."""
        if not metadata:
            metadata = {}
        
        generation_time = metadata.get(
            'generation_time', 
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        model = metadata.get('model', 'Unknown')
        data_source = metadata.get('data_source', 'Unknown')
        
        return f"""
        <div class="metadata">
            <p><strong>Report Generated:</strong> {generation_time}</p>
            <p><strong>AI Model:</strong> {model}</p>
            <p><strong>Data Source:</strong> {data_source}</p>
        </div>
        """
    
    def _build_plots_section(self, plots: dict) -> str:
        """Embeds all Plotly plots with proper spacing."""
        plots_html = '<div class="visualizations">\n<h2>📊 Data Visualizations</h2>\n'
        
        for plot_name, plot_html in plots.items():
            plots_html += f'<div class="plot-container">\n{plot_html}\n</div>\n'
        
        plots_html += '</div>\n'
        return plots_html
    
    def _build_full_html(self, meta_html: str, narrative_html: str, plots_html: str) -> str:
        """Assembles complete HTML document with styling."""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Automated Business Intelligence Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-radius: 8px;
        }}
        
        h1 {{
            color: #1a73e8;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 3px solid #1a73e8;
        }}
        
        h2 {{
            color: #34495e;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        
        h3 {{
            color: #555;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        
        .metadata {{
            background: #e8f4f8;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 30px;
            border-left: 4px solid #1a73e8;
        }}
        
        .metadata p {{
            margin: 5px 0;
            font-size: 0.95em;
        }}
        
        .narrative {{
            margin-bottom: 40px;
        }}
        
        .visualizations {{
            margin-top: 40px;
        }}
        
        .plot-container {{
            margin: 30px 0;
            padding: 20px;
            background: #fafafa;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        
        th, td {{
            padding: 12px;
            text-align: left;
            border: 1px solid #ddd;
        }}
        
        th {{
            background-color: #1a73e8;
            color: white;
        }}
        
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        
        ul, ol {{
            margin-left: 20px;
            margin-bottom: 15px;
        }}
        
        li {{
            margin-bottom: 8px;
        }}
        
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .container {{
                box-shadow: none;
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚗 Automated Business Intelligence Report</h1>
        
        {meta_html}
        
        <div class="narrative">
            {narrative_html}
        </div>
        
        {plots_html}
        
        <footer style="margin-top: 60px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #777; font-size: 0.9em;">
            <p>This report was automatically generated using AI-powered analysis.</p>
        </footer>
    </div>
</body>
</html>
        """
    
    def save_markdown(self, narrative: str, output_filename: str = "report.md") -> str:
        """Saves raw markdown for version control or alternative rendering."""
        output_path = self.output_dir / output_filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(narrative)
        return str(output_path)