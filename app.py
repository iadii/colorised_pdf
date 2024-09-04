from flask import Flask, render_template, request, send_file
import fitz  # PyMuPDF
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_heading(text, font_size):
    """Determine if the text is a heading based on font size."""
    return font_size > 15  # Adjust this threshold based on your document

def expand_bbox(bbox, margin=2):
    """Expand the bounding box by a given margin."""
    return fitz.Rect(bbox[0] - margin, bbox[1] - margin, bbox[2] + margin, bbox[3] + margin)

def convert_pdf(input_pdf, output_pdf):
    # Open the input PDF
    pdf_document = fitz.open(input_pdf)
    
    # Define the new background color (RGB normalized)
    background_color = (47/255, 45/255, 46/255)  # Converted to normalized RGB values

    # Iterate over each page
    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        text_instances = page.get_text("dict")['blocks']

        # Fill page background with the new color
        page_rect = page.rect
        page.draw_rect(page_rect, color=background_color, fill=background_color)
        
        # Iterate over text instances
        for block in text_instances:
            if 'lines' in block:
                for line in block['lines']:
                    for span in line['spans']:
                        font_size = span['size']
                        text = span['text']
                        bbox = expand_bbox(span['bbox'], margin=2)  # Add some margin
                        
                        # Determine if it's a heading
                        if is_heading(text, font_size):
                            text_color = (1, 0, 1)  # Pink (RGB normalized)
                        else:
                            text_color = (0.7, 1, 1)  # Light aqua (RGB normalized)
                        
                        # Insert text with the determined color
                        page.insert_text(bbox.tl, text, fontsize=font_size, color=text_color)

    # Save the output PDF
    pdf_document.save(output_pdf)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if the file part is present
        if 'file' not in request.files:
            return "No file part"
        
        file = request.files['file']

        # Check if a file is selected and if it has an allowed extension
        if file.filename == '' or not allowed_file(file.filename):
            return "Invalid file type. Only PDFs are allowed."

        # Save the uploaded file
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)

        # Convert the PDF
        output_filename = f"colored_{filename}"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        convert_pdf(input_path, output_path)

        # Provide the user with the download link
        return send_file(output_path, as_attachment=True)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
