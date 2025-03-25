# tools/data_extractor_tool.py
import re
import json
import logging
from .base_tool import BaseTool

class DataExtractorTool(BaseTool):
    """Tool for extracting structured data from text."""
    
    def __init__(self, name="data_extractor", config=None, llm_client=None):
        super().__init__(name, config or {})
        self.logger = logging.getLogger(self.__class__.__name__)
        self.llm_client = llm_client
    
    def run(self, text, extraction_schema=None, llm_extraction=False):
        """
        Extract structured data from text.
        
        Args:
            text (str): The text to extract data from
            extraction_schema (dict, optional): Schema defining patterns to extract
            llm_extraction (bool): Whether to use LLM for extraction
            
        Returns:
            dict: Extracted data
        """
        result = {}
        
        # Use LLM-based extraction if requested and client is available
        if llm_extraction and self.llm_client:
            prompt = f"""
            Extract structured information from the following text according to these requirements:
            
            {json.dumps(extraction_schema, indent=2) if extraction_schema else "Extract all key entities, facts, and relationships."}
            
            TEXT:
            {text[:10000]}  # Limit text to avoid token limits
            
            Return ONLY a valid JSON object with the extracted information.
            """
            
            try:
                extracted_json_text = self.llm_client.generate_response(prompt)
                # Try to parse the JSON response
                try:
                    # Find JSON in the response (in case of additional text)
                    json_match = re.search(r'(\{.*\})', extracted_json_text, re.DOTALL)
                    if json_match:
                        json_text = json_match.group(1)
                        result = json.loads(json_text)
                    else:
                        result = json.loads(extracted_json_text)
                except json.JSONDecodeError:
                    self.logger.error("❌ Failed to parse JSON from LLM response")
                    result = {"raw_extraction": extracted_json_text}
            except Exception as e:
                self.logger.error(f"❌ LLM extraction failed: {e}")
                result = {"error": str(e)}
                
        # Pattern-based extraction
        elif extraction_schema:
            for key, pattern in extraction_schema.items():
                matches = re.findall(pattern, text)
                result[key] = matches
                
        return result