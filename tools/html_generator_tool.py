# tools/html_generator_tool.py
import logging
import json
from .base_tool import BaseTool

class HTMLGeneratorTool(BaseTool):
    """Tool for generating HTML content from structured data."""
    
    def __init__(self, name="html_generator", config=None, llm_client=None):
        super().__init__(name, config or {})
        self.logger = logging.getLogger(self.__class__.__name__)
        self.llm_client = llm_client
        
    def run(self, data, template=None, theme="light", llm_generation=False):
        """
        Generate HTML content from structured data.
        
        Args:
            data (dict): Structured data to include in the HTML
            template (str, optional): HTML template with placeholders
            theme (str): "light", "dark", or "colorful"
            llm_generation (bool): Whether to use LLM for generation
            
        Returns:
            str: Generated HTML content
        """
        if llm_generation and self.llm_client:
            prompt = f"""
            Generate a clean, professional HTML landing page using this structured data:
            
            {json.dumps(data, indent=2)}
            
            Theme: {theme}
            
            Requirements:
            - Use a responsive design (mobile-friendly)
            - Include proper semantic HTML5 tags
            - Include internal CSS styling
            - Use a clean, professional design
            - Organize content logically by topic
            - Do not use external resources or CDNs
            
            Return ONLY the complete HTML code with no explanation.
            """
            
            try:
                html_content = self.llm_client.generate_response(prompt)
                return html_content
            except Exception as e:
                self.logger.error(f"❌ LLM HTML generation failed: {e}")
                return f"<!-- Error generating HTML: {str(e)} -->"
        
        elif template:
            # Simple template-based approach
            html_content = template
            for key, value in data.items():
                placeholder = f"{{{key}}}"
                if isinstance(value, list):
                    value = ", ".join(str(item) for item in value)
                html_content = html_content.replace(placeholder, str(value))
            return html_content
            
        else:
            # Basic default template
            html = f"""<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{data.get('title', 'Generated Page')}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 0; }}
                    .container {{ width: 80%; margin: 0 auto; padding: 20px; }}
                    header {{ background-color: #{'#f4f4f4' if theme == 'light' else '#333'}; padding: 1rem; }}
                    h1, h2, h3 {{ color: #{'#333' if theme == 'light' else '#f4f4f4'}; }}
                    section {{ margin-bottom: 20px; }}
                </style>
            </head>
            <body>
                <header>
                    <div class="container">
                        <h1>{data.get('title', 'Generated Page')}</h1>
                    </div>
                </header>
                <div class="container">"""
                
            # Add sections for each key in the data
            for key, value in data.items():
                if key != 'title':  # Already used in header
                    html += f"\n<section id='{key}'>\n<h2>{key.replace('_', ' ').title()}</h2>\n"
                    
                    if isinstance(value, list):
                        html += "<ul>\n"
                        for item in value:
                            html += f"<li>{item}</li>\n"
                        html += "</ul>\n"
                    elif isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            html += f"<h3>{sub_key.replace('_', ' ').title()}</h3>\n"
                            if isinstance(sub_value, list):
                                html += "<ul>\n"
                                for item in sub_value:
                                    html += f"<li>{item}</li>\n"
                                html += "</ul>\n"
                            else:
                                html += f"<p>{sub_value}</p>\n"
                    else:
                        html += f"<p>{value}</p>\n"
                        
                    html += "</section>\n"
                    
            html += """</div>
            </body>
            </html>"""
            
            return html