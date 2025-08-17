from src.scrapers.pdf_processor import PDFProcessor
from src.utils.llm_client import LLMClient

class PDFWorkflow:
    def __init__(self, event_schema):
        """Initialize the PDF workflow"""
        self.event_schema = event_schema
        self.pdf_processor = PDFProcessor()
        self.llm_client = LLMClient()

    def process(self, pdf_data):
        """Process a PDF file"""
        # Skip empty PDF data
        if not pdf_data:
            return {}, []

        # Extract text from PDF
        if isinstance(pdf_data, dict) and pdf_data.get('type') == 'file':  # PDF file
            pdf_text = self.pdf_processor.process_pdf_file(pdf_data.get('path', ''))
            original_name = pdf_data.get('original_name', '')
        else:
            return {}, []

        # Skip if no text was extracted
        if not pdf_text:
            return {}, []

        # Extract event information from text
        event_record = self.llm_client.extract_event_info(pdf_text, self.event_schema)

        # Add original file name to event record if any information was found
        if event_record and any(event_record.values()) and original_name:
            if 'לינקים נוספים' in event_record:
                if original_name not in event_record['לינקים נוספים']:
                    if event_record['לינקים נוספים']:
                        event_record['לינקים נוספים'] += f", PDF: {original_name}"
                    else:
                        event_record['לינקים נוספים'] = f"PDF: {original_name}"
            else:
                event_record['לינקים נוספים'] = f"PDF: {original_name}"

        # Find URLs in the PDF text
        urls = self.llm_client.find_urls_in_text(pdf_text)

        # Prepare new sources to process
        new_sources = [('url', url) for url in urls]

        return event_record, new_sources
