from src.workflows.free_format_workflow import FreeFormatWorkflow
from src.workflows.url_workflow import URLWorkflow
from src.workflows.image_workflow import ImageWorkflow
from src.workflows.pdf_workflow import PDFWorkflow
from src.utils.sheet_client import SheetClient

class WorkflowOrchestrator:
    def __init__(self, event_schema):
        """Initialize the workflow orchestrator"""
        self.event_schema = event_schema
        self.free_format_workflow = FreeFormatWorkflow(event_schema)
        self.url_workflow = URLWorkflow(event_schema)
        self.image_workflow = ImageWorkflow(event_schema)
        self.pdf_workflow = PDFWorkflow(event_schema)

        # Initialize sheet client
        self.sheet_client = SheetClient()

        # Keep track of processed URLs to avoid duplicate processing
        self.processed_urls = set()
        self.processed_images = set()

        # Initialize the target event record
        self.target_event_record = {field: '' for field in event_schema.keys()}

    def run(self, free_format_text, image_data, pdf_data):
        """Run all workflows and aggregate results"""
        # Queue for pending media sources
        media_sources_queue = []

        # Add initial media sources to the queue
        if free_format_text:
            media_sources_queue.append(('free_format', free_format_text))

        if image_data:
            media_sources_queue.append(('image', image_data))

        if pdf_data:
            media_sources_queue.append(('pdf', pdf_data))

        # Process media sources until the queue is empty
        while media_sources_queue:
            source_type, source_data = media_sources_queue.pop(0)

            # Process the current media source
            if source_type == 'free_format':
                if source_data and source_data.startswith(('http://', 'https://')) and ' ' not in source_data:
                    source_event_record, new_sources = self.url_workflow.process(source_data)
                else:
                    source_event_record, new_sources = self.free_format_workflow.process(source_data)
            elif source_type == 'url':
                # Skip if already processed
                if source_data in self.processed_urls:
                    continue
                self.processed_urls.add(source_data)

                source_event_record, new_sources = self.url_workflow.process(source_data)
            elif source_type == 'image':
                # For image URLs, skip if already processed
                if isinstance(source_data, str) and source_data in self.processed_images:
                    continue
                if isinstance(source_data, str):
                    self.processed_images.add(source_data)

                source_event_record, new_sources = self.image_workflow.process(source_data)
            elif source_type == 'pdf':
                source_event_record, new_sources = self.pdf_workflow.process(source_data)
            else:
                continue

            # Validate and aggregate info into target event record
            self._validate_and_aggregate(source_event_record)

            # Add new sources to the queue
            for new_source_type, new_source_data in new_sources:
                media_sources_queue.append((new_source_type, new_source_data))

        # Write the final event record to the sheet
        self.sheet_client.append_event_record(self.target_event_record)

        return self.target_event_record

    def _validate_and_aggregate(self, source_event_record):
        """Validate source event record against target and aggregate info"""
        for field, value in source_event_record.items():
            # Skip empty values
            if not value:
                continue

            # Get current target value
            target_value = self.target_event_record.get(field, '')

            # Determine field format
            field_format = self.event_schema.get(field, {}).get('format', 'free_text')

            # Validate and aggregate based on field format
            if not target_value:
                # If target is empty, just use the source value
                self.target_event_record[field] = value
            elif value == target_value:
                # If values are identical, they are validated
                pass
            elif field_format in ['date', 'time', 'day_of_week', 'event_type']:
                # For strict formats, flag conflicts
                if field == 'Error':
                    # Append to error field
                    self.target_event_record[field] += f", Conflicting {field}: {target_value} vs {value}"
                else:
                    # Add to error field
                    if 'Error' not in self.target_event_record:
                        self.target_event_record['Error'] = ''
                    if self.target_event_record['Error']:
                        self.target_event_record['Error'] += ', '
                    self.target_event_record['Error'] += f"Conflicting {field}: {target_value} vs {value}"

                    # Keep the original value for now
                    print(f"Conflicting values for {field}: {target_value} vs {value}")
            elif field_format == 'sdg_list':
                # For SDG list, combine unique values
                target_list = target_value.split(', ') if isinstance(target_value, str) else target_value
                source_list = value.split(', ') if isinstance(value, str) else value
                combined_values = set(target_list + source_list)
                self.target_event_record[field] = ', '.join([v for v in combined_values if v])
            elif field_format == 'url':
                # For URLs, keep both if they're different
                if value not in target_value:
                    if target_value:
                        self.target_event_record[field] = f"{target_value}, {value}"
                    else:
                        self.target_event_record[field] = value
            else:  # free_text and other formats
                # For free text, concatenate if they're different
                if value not in target_value:
                    if target_value:
                        self.target_event_record[field] = f"{target_value}\n{value}"
                    else:
                        self.target_event_record[field] = value
