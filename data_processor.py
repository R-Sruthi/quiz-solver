import pandas as pd
import PyPDF2
import json
import io
import logging
from typing import Dict, Any, List
import base64

logger = logging.getLogger(__name__)

class DataProcessor:
    """Handles processing of various file types and data formats"""
    
    async def process_files(self, file_contents: Dict[str, bytes]) -> Dict[str, Any]:
        """Process multiple files and return structured data"""
        results = {}
        
        for url, content in file_contents.items():
            try:
                file_type = self.detect_file_type(url)
                
                if file_type == 'pdf':
                    results[url] = self.process_pdf(content)
                elif file_type == 'csv':
                    results[url] = self.process_csv(content)
                elif file_type == 'xlsx':
                    results[url] = self.process_excel(content)
                elif file_type == 'json':
                    results[url] = self.process_json(content)
                elif file_type == 'txt':
                    results[url] = self.process_text(content)
                else:
                    results[url] = {"error": "Unknown file type"}
                    
            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
                results[url] = {"error": str(e)}
        
        return results
    
    def detect_file_type(self, url: str) -> str:
        """Detect file type from URL"""
        url_lower = url.lower()
        
        if '.pdf' in url_lower:
            return 'pdf'
        elif '.csv' in url_lower:
            return 'csv'
        elif '.xlsx' in url_lower or '.xls' in url_lower:
            return 'xlsx'
        elif '.json' in url_lower:
            return 'json'
        elif '.txt' in url_lower:
            return 'txt'
        
        return 'unknown'
    
    def process_pdf(self, content: bytes) -> Dict[str, Any]:
        """Extract text and tables from PDF"""
        try:
            pdf_file = io.BytesIO(content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            pages = []
            for page_num, page in enumerate(pdf_reader.pages, 1):
                text = page.extract_text()
                pages.append({
                    "page": page_num,
                    "text": text
                })
            
            return {
                "type": "pdf",
                "num_pages": len(pdf_reader.pages),
                "pages": pages
            }
        except Exception as e:
            logger.error(f"PDF processing error: {e}")
            return {"error": str(e)}
    
    def process_csv(self, content: bytes) -> Dict[str, Any]:
        """Process CSV file and return structured data"""
        try:
            df = pd.read_csv(io.BytesIO(content))
            
            return {
                "type": "csv",
                "shape": df.shape,
                "columns": df.columns.tolist(),
                "head": df.head(10).to_dict(orient='records'),
                "summary": {
                    "numeric_columns": df.select_dtypes(include=['number']).columns.tolist(),
                    "statistics": df.describe().to_dict() if not df.empty else {}
                },
                "data": df.to_dict(orient='records')  # Full data for analysis
            }
        except Exception as e:
            logger.error(f"CSV processing error: {e}")
            return {"error": str(e)}
    
    def process_excel(self, content: bytes) -> Dict[str, Any]:
        """Process Excel file"""
        try:
            excel_file = io.BytesIO(content)
            sheets = pd.read_excel(excel_file, sheet_name=None)
            
            result = {
                "type": "excel",
                "sheets": {}
            }
            
            for sheet_name, df in sheets.items():
                result["sheets"][sheet_name] = {
                    "shape": df.shape,
                    "columns": df.columns.tolist(),
                    "head": df.head(10).to_dict(orient='records'),
                    "data": df.to_dict(orient='records')
                }
            
            return result
        except Exception as e:
            logger.error(f"Excel processing error: {e}")
            return {"error": str(e)}
    
    def process_json(self, content: bytes) -> Dict[str, Any]:
        """Process JSON file"""
        try:
            data = json.loads(content.decode('utf-8'))
            return {
                "type": "json",
                "data": data
            }
        except Exception as e:
            logger.error(f"JSON processing error: {e}")
            return {"error": str(e)}
    
    def process_text(self, content: bytes) -> Dict[str, Any]:
        """Process text file"""
        try:
            text = content.decode('utf-8')
            return {
                "type": "text",
                "content": text,
                "lines": len(text.split('\n'))
            }
        except Exception as e:
            logger.error(f"Text processing error: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def create_visualization(data: pd.DataFrame, chart_type: str = "bar") -> str:
        """Create a visualization and return as base64 data URI"""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            if chart_type == "bar":
                data.plot(kind='bar', ax=ax)
            elif chart_type == "line":
                data.plot(kind='line', ax=ax)
            elif chart_type == "scatter":
                data.plot(kind='scatter', ax=ax)
            else:
                data.plot(ax=ax)
            
            plt.tight_layout()
            
            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close(fig)
            
            return f"data:image/png;base64,{image_base64}"
            
        except Exception as e:
            logger.error(f"Visualization error: {e}")
            return None