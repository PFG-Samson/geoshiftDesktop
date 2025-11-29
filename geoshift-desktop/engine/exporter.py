import os
from jinja2 import Template
import datetime

def export_report(data, output_path):
    """
    Exports a simple HTML report for change detection.
    data: dict containing analysis results and metadata.
    """
    template_str = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Geoshift Change Detection Report</title>
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
        <h1>Change Detection Report</h1>
        <p><strong>Date:</strong> {{ timestamp }}</p>
        <p><strong>Analysis Type:</strong> {{ analysis_type }}</p>
        
        <h2>Images</h2>
        <div class="metric"><span class="label">Image A (Before):</span> {{ image_a }}</div>
        <div class="metric"><span class="label">Image B (After):</span> {{ image_b }}</div>
        
        <h2>Results</h2>
        <div class="metric"><span class="label">Change Detected:</span> {{ "%.2f"|format(change_percentage) }}%</div>
        
        <div class="images">
            <div class="img-box">
                <h3>Before</h3>
                <img src="file://{{ preview_a }}" alt="Before">
            </div>
            <div class="img-box">
                <h3>After</h3>
                <img src="file://{{ preview_b }}" alt="After">
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        template = Template(template_str)
        html_content = template.render(
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            analysis_type=data.get('analysis_type', 'Unknown'),
            image_a=data.get('image_a', 'Unknown'),
            image_b=data.get('image_b', 'Unknown'),
            change_percentage=data.get('change_percentage', 0),
            preview_a=data.get('preview_a', ''),
            preview_b=data.get('preview_b', '')
        )
        
        with open(output_path, 'w') as f:
            f.write(html_content)
            
        return True
    except Exception as e:
        print(f"Error exporting report: {e}")
        return False
