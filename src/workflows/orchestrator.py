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

        # Track URL depth for hard-limiting crawling depth
        self.url_depths = {}

        # Initialize the target event record
        self.target_event_record = {field: '' for field in event_schema.keys()}

    def run(self, free_format_text, image_data, pdf_data):
        """Run all workflows and aggregate results"""
        # Queue for pending media sources
        media_sources_queue = []

        # Add initial media sources to the queue
        if free_format_text:
            media_sources_queue.append(('free_format', free_format_text, 0))

        if image_data:
            media_sources_queue.append(('image', image_data, 0))

        if pdf_data:
            media_sources_queue.append(('pdf', pdf_data, 0))

        # Process media sources until the queue is empty
        while media_sources_queue:
            source_type, source_data, current_depth = media_sources_queue.pop(0)

            # Log the processing of each media source
            source_identifier = source_data if isinstance(source_data, str) else f"{source_type} data"
            print(f"Processing {source_type} source: {source_identifier} (depth {current_depth})")

            # Process the current media source
            if source_type == 'free_format':
                if source_data and source_data.startswith(('http://', 'https://')) and ' ' not in source_data:
                    # Handle URL in free format text as depth 0
                    self.url_depths[source_data] = 0
                    source_event_record, new_sources = self.url_workflow.process(source_data)
                else:
                    source_event_record, new_sources = self.free_format_workflow.process(source_data)
            elif source_type == 'url':
                # Skip if already processed
                if source_data in self.processed_urls:
                    continue
                self.processed_urls.add(source_data)

                # Store the URL depth
                self.url_depths[source_data] = current_depth

                # Process URL for event info, but don't retrieve new URLs if at depth 1
                if current_depth < 1:
                    source_event_record, new_sources = self.url_workflow.process(source_data)
                else:
                    # At depth 1, only extract event info, don't gather new sources
                    scrape_result = self.url_workflow.url_scraper.scrape(source_data)
                    scraped_text = scrape_result.get('scraped_text', '')
                    source_event_record = self.url_workflow.llm_client.extract_event_info(scraped_text, self.event_schema)

                    # Add current URL to event record
                    if source_event_record and any(source_event_record.values()):
                        if 'לינקים נוספים' in source_event_record:
                            if source_data not in source_event_record['לינקים נוספים']:
                                if source_event_record['לינקים נוספים']:
                                    source_event_record['לינקים נוספים'] += f", {source_data}"
                                else:
                                    source_event_record['לינקים נוספים'] = source_data
                        else:
                            source_event_record['לינקים נוספים'] = source_data

                    new_sources = []
            elif source_type == 'image':
                # For image URLs, skip if already processed
                if isinstance(source_data, str) and source_data in self.processed_images:
                    continue
                if isinstance(source_data, str):
                    self.processed_images.add(source_data)

                # Process image for event info
                source_event_record, new_sources = self.image_workflow.process(source_data)
            elif source_type == 'pdf':
                source_event_record, new_sources = self.pdf_workflow.process(source_data)
            else:
                continue

            # Validate and aggregate info into target event record
            self._validate_and_aggregate(source_event_record)

            # Add new sources to the queue with depth tracking
            for new_source_type, new_source_data in new_sources:
                # Calculate new depth for URL sources
                new_depth = current_depth
                if new_source_type == 'url':
                    new_depth = current_depth + 1

                    # Skip if depth would exceed 1
                    if new_depth > 1:
                        continue

                # Add to queue with depth information
                media_sources_queue.append((new_source_type, new_source_data, new_depth))

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

            # Log the field being processed
            print(f"Validating field '{field}': New value = '{value}', Current value = '{target_value}'")

            # Determine field format
            field_format = self.event_schema.get(field, {}).get('format', 'free_text')

            # Validate and aggregate based on field format
            if not target_value:
                # If target is empty, just use the source value
                self.target_event_record[field] = value
                print(f"  ADDED NEW: Field '{field}' was empty, setting to '{value}'")
            elif value == target_value:
                # If values are identical, they are validated
                print(f"  VALIDATED: Value for '{field}' is identical to existing value")
                pass
            elif field_format in ['date', 'time', 'day_of_week', 'event_type']:
                # For strict formats, flag conflicts
                print(f"  CONFLICT: Strict field '{field}' has conflicting values: '{target_value}' vs '{value}'")
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
                    print(f"  KEEPING ORIGINAL: Using '{target_value}' for field '{field}'")
            elif field_format == 'sdg_list':
                # For SDG list, combine unique values
                target_list = target_value.split(', ') if isinstance(target_value, str) else target_value
                source_list = value.split(', ') if isinstance(value, str) else value
                combined_values = set(target_list + source_list)
                self.target_event_record[field] = ', '.join([v for v in combined_values if v])
                print(f"  MERGED LIST: For field '{field}', combined values from '{target_value}' and '{value}'")
                print(f"    RESULT: '{self.target_event_record[field]}'")
            elif field_format == 'url':
                # For URLs, keep both if they're different
                # Convert value to string if it's a list
                url_value = ', '.join(value) if isinstance(value, list) else value
                if url_value not in target_value:
                    if target_value:
                        self.target_event_record[field] = f"{target_value}, {url_value}"
                        print(f"  APPENDED URL: For field '{field}', added '{url_value}' to existing URLs")
                    else:
                        self.target_event_record[field] = url_value
                        print(f"  ADDED URL: For field '{field}', set URL to '{url_value}'")
                else:
                    print(f"  DUPLICATE URL: URL '{url_value}' already exists in field '{field}'")
            else:  # free_text and other formats
                # For free text, concatenate if they're different
                if value not in target_value:
                    if target_value:
                        self.target_event_record[field] = f"{target_value}\n{value}"
                        print(f"  CONCATENATED: For field '{field}', added new content")
                    else:
                        self.target_event_record[field] = value
                        print(f"  ADDED TEXT: For field '{field}', set text value")
                else:
                    print(f"  DUPLICATE TEXT: Content already exists in field '{field}'")
