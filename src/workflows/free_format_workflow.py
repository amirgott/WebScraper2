from src.utils.llm_client import GenaiLLMClient


class FreeFormatWorkflow:
    def __init__(self, event_schema, llm_client):
        """Initialize the free format workflow"""
        self.event_schema = event_schema
        self.llm_client = llm_client

    def process(self, text, existing_event_record=None):
        """Process free format text"""
        # Skip empty text
        if not text:
            return {}, []

        # Extract event information
        event_record = self.llm_client.extract_event_info(text, self.event_schema, existing_event_record)

        # Find URLs in the text
        urls = self.llm_client.find_urls_in_text(text)

        # Prepare new sources to process
        new_sources = [('url', url) for url in urls]

        return event_record, new_sources
