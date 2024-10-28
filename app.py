import os
import pdfplumber
import requests
import markdown
from flask import Flask, request, render_template

# Initialize Flask app
app = Flask(__name__)

# Set upload folder
UPLOAD_FOLDER = 'uploads/'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to extract text from PDF
def load_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        all_text = ""
        for page in pdf.pages:
            all_text += page.extract_text() + "\n"
    return all_text

# Function to check Gemini API
def check_gemini_api(query, pdf_content):
    api_key = "AIzaSyAz9GiIJQVu_aoOiXLv0MHB36KwgzbEPqM"  # Replace with your actual API key
    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}'
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [
            {
                "parts": [
                    {"text": f"Based on the following content from a PDF: {pdf_content}\n\nAnswer this query: {query}"}
                ]
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            print(response)
            return True, response.json()  # Return success and response data
            
        else:
            
            return False, response.text  # Return failure and error message
        

    except requests.exceptions.RequestException as e:
        return False, str(e)  # Return failure and exception message

# Route for file upload form
@app.route('/')
def upload_file():
    return render_template('index.html', api_result=None, answer=None)

# Route to handle file upload and text extraction
@app.route('/uploader', methods=['POST'])
def uploader():
    if request.method == 'POST':
        file = request.files['file']
        
        if file and file.filename.endswith('.pdf'):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            pdf_text = load_pdf(file_path)
            return render_template('index.html', pdf_text=pdf_text, answer=None)  # Render PDF text for querying
        else:
            return "Please upload a valid PDF file."

# Route to handle user query and generate a response
@app.route('/query', methods=['POST'])
def query():
    user_query = request.form['query']
    pdf_content = request.form['pdf_content']
    
    # Call the Gemini API with the user query and PDF content
    is_working, response = check_gemini_api(user_query, pdf_content)
    
    if is_working:
        # Extract text from the response and convert to string
        answer_text = response['candidates'][0]['content']['parts'][0]['text']
        answer_html = markdown.markdown(answer_text)
        return render_template('index.html', answer=answer_html, pdf_text=pdf_content)  # Show the response
    
    else:
        return render_template('index.html', answer=f"Error: {response}", pdf_text=pdf_content)  # Show error

if __name__ == '__main__':
    app.run(debug=True)
