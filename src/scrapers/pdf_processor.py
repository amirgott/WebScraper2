import pdfplumber
import os

class PDFProcessor:
    def __init__(self):
        """Initialize the PDF processor"""
        pass

    def process_pdf_file(self, pdf_path):
        """Process a PDF file and extract text"""
        try:
            # Ensure the PDF exists
            if not os.path.exists(pdf_path):
                print(f"PDF file not found: {pdf_path}")
                return ""

            # Extract text from the PDF
            with pdfplumber.open(pdf_path) as pdf:
                text = '\n'.join([page.extract_text() or '' for page in pdf.pages])

            return text

        except Exception as e:
            print(f"Error processing PDF file {pdf_path}: {str(e)}")
            return ""
