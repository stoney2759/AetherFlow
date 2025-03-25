# tools/filesystem_tool.py
import os
import json
import logging
from .base_tool import BaseTool

class FileSystemTool(BaseTool):
    """Tool for reading and writing files."""
    
    def __init__(self, name="filesystem", config=None):
        super().__init__(name, config or {})
        self.logger = logging.getLogger(self.__class__.__name__)
        self.output_dir = config.get("output_dir", "output")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def run(self, operation, file_path, content=None, mode="utf-8"):
        """
        Perform file system operations.
        
        Args:
            operation (str): "read", "write", "append", or "list"
            file_path (str): Path to the file
            content (str, optional): Content to write (for write/append)
            mode (str): Encoding mode
            
        Returns:
            dict: Operation result
        """
        try:
            # Ensure the path is safe
            if ".." in file_path:
                raise ValueError("Path traversal not allowed")
                
            # Ensure path is within output directory for write operations
            if operation in ["write", "append"]:
                if not file_path.startswith(self.output_dir):
                    file_path = os.path.join(self.output_dir, file_path)
                
                # Ensure directory exists
                directory = os.path.dirname(file_path)
                if directory and not os.path.exists(directory):
                    os.makedirs(directory, exist_ok=True)
            
            # Perform the requested operation
            if operation == "read":
                with open(file_path, "r", encoding=mode) as f:
                    return {"content": f.read(), "file_path": file_path}
                    
            elif operation == "write":
                with open(file_path, "w", encoding=mode) as f:
                    f.write(content)
                return {"success": True, "file_path": file_path}
                
            elif operation == "append":
                with open(file_path, "a", encoding=mode) as f:
                    f.write(content)
                return {"success": True, "file_path": file_path}
                
            elif operation == "list":
                if os.path.isdir(file_path):
                    return {"files": os.listdir(file_path), "directory": file_path}
                else:
                    return {"error": "Not a directory", "path": file_path}
                    
            else:
                return {"error": f"Unknown operation: {operation}"}
                
        except Exception as e:
            self.logger.error(f"❌ File operation failed: {e}")
            return {"error": str(e), "file_path": file_path}