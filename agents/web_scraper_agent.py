# agents/web_scraper_agent.py
import json
import logging
import os
from agents.agent_core import AgentCore

class WebScraperAgent(AgentCore):
    """Agent specialized in web scraping and information extraction.
    
    @agent_metadata{"description": "Specializes in web scraping and information extraction", "capabilities": ["web scraping", "html parsing", "data extraction", "content analysis", "landing page creation"]}
    """
    
    def __init__(self, llm_client, config=None):
        super().__init__(llm_client, config)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("🛠️ WebScraperAgent initialized.")
        
        # Initialize tools
        self.get_tool("web_scraper")
        self.get_tool("data_extractor")
        self.get_tool("html_generator")
        self.get_tool("filesystem")
    
    def think(self, task):
        """Analyzes the task and determines the execution strategy."""
        self.logger.info(f"🤔 Analyzing task: {task}")
        
        thinking_prompt = f"""
        Analyze this web scraping task:
        
        {task}
        
        What is the best strategy to complete it? Consider:
        1. What URL needs to be scraped?
        2. What specific information needs to be extracted?
        3. How should the data be formatted and presented?
        4. Are there any specific requirements for the output?
        
        Provide a step-by-step plan.
        """
        
        plan = self.llm_client.generate_response(thinking_prompt)
        return plan
    
    def act(self, task):
        """Scrapes a webpage and creates a landing page or extracts information."""
        self.logger.info(f"🌐 Web scraping task: {task}")
        
        # First, think about how to approach the task
        plan = self.think(task)
        
        # Extract URL from task
        url_prompt = f"Extract just the URL from this task: {task}"
        url = self.llm_client.generate_response(url_prompt).strip()
        
        if not url.startswith("http"):
            self.logger.error("No valid URL found in task")
            return "Error: No valid URL found in the task."
        
        try:
            # 1. Use WebScraperTool to get the content
            self.logger.info(f"Scraping URL: {url}")
            scraper_tool = self.tools.get("web_scraper")
            if not scraper_tool:
                return "Error: WebScraperTool not available"
                
            scraped_data = scraper_tool.run(url=url)
            
            # 2. Use DataExtractorTool to extract structured information
            self.logger.info("Extracting information from scraped content")
            extractor_tool = self.tools.get("data_extractor")
            if not extractor_tool:
                return "Error: DataExtractorTool not available"
                
            # Create extraction schema based on task
            schema_prompt = f"""
            Based on this task, what information should be extracted from the webpage?
            
            {task}
            
            Generate a JSON schema with key-value pairs where keys are the data points to extract
            and values are brief descriptions of what to look for. Return just the JSON.
            """
            
            extraction_schema_json = self.llm_client.generate_response(schema_prompt)
            
            try:
                extraction_schema = json.loads(extraction_schema_json)
            except json.JSONDecodeError:
                self.logger.warning("Failed to parse extraction schema, using default")
                extraction_schema = {
                    "title": "Main title or heading of the page",
                    "description": "Main description or summary",
                    "content": "Primary content of interest",
                    "categories": "Categories or topics",
                    "key_points": "Important points or highlights"
                }
            
            # Extract the data
            extracted_data = extractor_tool.run(
                scraped_data.get("full_text", ""), 
                extraction_schema=extraction_schema,
                llm_extraction=True
            )
            
            # 3. Check if task is just extraction or needs a landing page
            if "landing page" in task.lower() or "webpage" in task.lower() or "website" in task.lower():
                # Create a landing page
                self.logger.info("Generating landing page from extracted data")
                html_tool = self.tools.get("html_generator")
                if not html_tool:
                    return "Error: HTMLGeneratorTool not available"
                    
                # Determine theme preference from task
                theme = "light"
                if "dark" in task.lower():
                    theme = "dark"
                elif "colorful" in task.lower():
                    theme = "colorful"
                
                # Generate HTML
                html_content = html_tool.run(
                    extracted_data,
                    theme=theme,
                    llm_generation=True
                )
                
                # Save the HTML file
                fs_tool = self.tools.get("filesystem")
                if not fs_tool:
                    return "Error: FileSystemTool not available"
                    
                # Create a filename based on the URL
                page_title = extracted_data.get("title", "landing_page").lower()
                page_title = ''.join(c if c.isalnum() else '_' for c in page_title)
                filename = f"output/{page_title}.html"
                
                save_result = fs_tool.run("write", filename, html_content)
                
                if save_result.get("success"):
                    # Return the path and a summary
                    return {
                        "output": {
                            "summary": f"Successfully created a landing page based on {url}",
                            "result": f"Landing page saved to: {save_result.get('file_path')}"
                        },
                        "extracted_data": extracted_data,
                        "artifacts": [
                            {
                                "name": "Landing Page",
                                "description": f"Created from data scraped from {url}",
                                "filename": save_result.get('file_path'),
                                "type": "html"
                            }
                        ]
                    }
                else:
                    return f"Error saving the landing page: {save_result.get('error')}"
            else:
                # Just return the extracted data
                return {
                    "output": {
                        "summary": f"Successfully extracted information from {url}",
                        "result": json.dumps(extracted_data, indent=2)
                    },
                    "extracted_data": extracted_data
                }
                
        except Exception as e:
            self.logger.error(f"Error during web scraping task: {e}")
            return f"Error: {str(e)}"