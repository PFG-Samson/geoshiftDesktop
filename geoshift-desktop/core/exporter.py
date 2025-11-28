import os
from jinja2 import Template
import datetime

def export_report(data, output_path):
    """
    Exports a simple HTML report.
    data: dict containing analysis results and metadata.
    """
    template_str = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Geoshift Water Analysis Report</title>
        <style>
            body { font-family: sans-serif; margin: 20px; }
            h1 { color: #2c3e50; }
            .metric { margin-bottom: 10px; }
            .label { font-weight: bold; }
            .images { display: flex; gap: 20px; margin-top: 20px; }
            .img-box { border: 1px solid #ccc; padding: 10px; }
            img { max-width: 400px; }
        </style>
    </head>
    <body>
        <h1>Water Analysis Report</h1>
        <p><strong>Date:</strong> {{ timestamp }}</p>
        <p><strong>File:</strong> {{ filename }}</p>
        
        <h2>Results</h2>
        <div class="metric"><span class="label">Total Water Area:</span> {{ "%.2f"|format(area_ha) }} ha</div>
        <div class="metric"><span class="label">Coverage:</span> {{ "%.2f"|format(percent_coverage) }}%</div>
        
        <h2>Metadata</h2>
        <div class="metric"><span class="label">Dimensions:</span> {{ width }} x {{ height }}</div>
        <div class="metric"><span class="label">CRS:</span> {{ crs }}</div>
        
        <div class="images">
            <div class="img-box">
                <h3>Original Image</h3>
                <img src="file://{{ preview_path }}" alt="Original">
            </div>
            <!-- Mask image could be added here if saved -->
        </div>
    </body>
    </html>
    """
    
    try:
        template = Template(template_str)
        html_content = template.render(
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            filename=os.path.basename(data.get('path', 'Unknown')),
            area_ha=data.get('area_ha', 0),
            percent_coverage=data.get('percent_coverage', 0),
            width=data.get('width', 0),
            height=data.get('height', 0),
            crs=str(data.get('crs', 'Unknown')),
            preview_path=data.get('preview_path', '')
        )
        
        with open(output_path, 'w') as f:
            f.write(html_content)
            
        return True
    except Exception as e:
        print(f"Error exporting report: {e}")
        return False
