import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import base64
import tempfile
from werkzeug.utils import secure_filename

from src.workflows.orchestrator import WorkflowOrchestrator
from src.utils.config import load_event_schema

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Load event schema
event_schema = load_event_schema()

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/api-check')
def api_check():
    """A simple endpoint to check if the API is accessible"""
    return jsonify({
        'status': 'ok',
        'message': 'API is accessible',
        'endpoints': {
            'run_scrape': '/run_scrape (POST)'
        }
    })

@app.route('/run_scrape', methods=['POST'])
def run_scrape():
    """Endpoint to run the scraping process"""
    try:
        # Get input data from request
        app.logger.info(f"Form data received: {request.form.keys()}")
        free_format_text = request.form.get('free_format_text', '')
        app.logger.info(f"Free format text: {free_format_text[:100] if free_format_text else 'None'}")  # Log first 100 chars

        # Handle image if provided
        image_data = None
        if 'image' in request.files and request.files['image'].filename:
            image_file = request.files['image']
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                image_file.save(temp_file.name)
                image_path = temp_file.name
            image_data = {'type': 'file', 'path': image_path}
        elif 'image_base64' in request.form and request.form['image_base64']:
            # Handle base64 encoded image (for clipboard paste)
            base64_data = request.form['image_base64'].split(',')[1] if ',' in request.form['image_base64'] else request.form['image_base64']
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                temp_file.write(base64.b64decode(base64_data))
                image_path = temp_file.name
            image_data = {'type': 'file', 'path': image_path}

        # Handle PDF if provided
        pdf_data = None
        if 'pdf_file' in request.files and request.files['pdf_file'].filename:
            pdf_file = request.files['pdf_file']
            filename = secure_filename(pdf_file.filename)
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                pdf_file.save(temp_file.name)
                pdf_path = temp_file.name
            pdf_data = {'type': 'file', 'path': pdf_path, 'original_name': filename}

        # Initialize orchestrator and run workflows
        orchestrator = WorkflowOrchestrator(event_schema)
        result = orchestrator.run(free_format_text, image_data, pdf_data)

        # Clean up temporary files
        if image_data and os.path.exists(image_data['path']):
            os.unlink(image_data['path'])
        if pdf_data and os.path.exists(pdf_data['path']):
            os.unlink(pdf_data['path'])

        return jsonify({
            'success': True,
            'message': 'Scraping completed successfully',
            'result': result
        })

    except Exception as e:
        app.logger.error(f"Error in run_scrape: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
