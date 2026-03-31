from flask import Flask, request, jsonify, send_file
import os
import re
import xml.etree.ElementTree as ET
from io import BytesIO
from datetime import datetime
import random
import string
from payment_generator import PaymentData, XMLFieldMapper, ACHNachaXMLGenerator

app = Flask(__name__)

def extract_keywords(text):
    """Extract meaningful keywords from text"""
    # Remove common words
    stop_words = {'what', 'is', 'the', 'a', 'an', 'do', 'does', 'how', 'why', 'when', 'where', 'can', 'you', 'about', 'tell', 'me', 'know', 'understand'}
    words = text.lower().split()
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    return keywords

def find_relevant_knowledge(question, knowledge_text):
    """Find the most relevant parts of knowledge base based on question"""
    question_keywords = extract_keywords(question)
    knowledge_lines = knowledge_text.split('\n')

    scored_lines = []
    for line in knowledge_lines:
        if not line.strip():
            continue
        score = sum(1 for keyword in question_keywords if keyword in line.lower())
        if score > 0:
            scored_lines.append((score, line.strip()))

    # Sort by relevance score
    scored_lines.sort(reverse=True)
    relevant_knowledge = ' '.join([line for _, line in scored_lines[:3]])  # Top 3 relevant lines
    return relevant_knowledge if relevant_knowledge else knowledge_text.strip()

def generate_response(question, knowledge):
    """Generate a natural response based on knowledge"""
    relevant = find_relevant_knowledge(question, knowledge)

    # Simple template-based response generation
    response = f"{relevant}"
    return response

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    question = data['question']
    project = data.get('project', 'general')

    # Check for bug/error/issue related questions
    if 'bug' in question.lower() or 'error' in question.lower() or 'issue' in question.lower():
        answer = f"This seems like a common issue. Please check the logs or restart the service."
    else:
        # Check the knowledge base
        try:
            with open(f'knowledge_{project}.txt', 'r') as f:
                knowledge = f.read().strip()
            if knowledge:
                # Generate a contextual response
                answer = generate_response(question, knowledge)
            else:
                answer = f"I'm sorry, I don't have specific information on that for project {project}. If you can provide more details or knowledge about this topic, it would be greatly appreciated so I can assist better in the future."
        except FileNotFoundError:
            answer = f"I'm sorry, I don't have specific information on that for project {project}. If you can provide more details or knowledge about this topic, it would be greatly appreciated so I can assist better in the future."
    return jsonify({'answer': answer})

@app.route('/submit-knowledge', methods=['POST'])
def submit_knowledge():
    data = request.get_json()
    project = data.get('project', 'general')
    knowledge = data.get('knowledge', '')

    if not knowledge:
        return jsonify({'message': 'No knowledge provided'}), 400

    # Save the knowledge to a local file (appending for simplicity)
    with open(f'knowledge_{project}.txt', 'a') as f:
        f.write(knowledge + '\n')

    return jsonify({'message': 'Knowledge submitted successfully!'})

@app.route('/generate-xml', methods=['POST'])
def generate_xml():
    """Generate ACH NACHA payment XML file"""
    try:
        form_data = request.get_json()
        file_type = form_data.get('fileType', 'ACH NACHA XML')

        if file_type == 'ACH NACHA XML':
            return generate_ach_nacha_xml(form_data)
        else:
            return jsonify({'error': f'File type {file_type} not yet implemented'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 400

def generate_ach_nacha_xml(form_data):
    """
    Generate ACH NACHA payment file XML

    Process:
    1. Extract and structure form data into PaymentData object
    2. Map fields to XML template placeholders
    3. Generate complete XML content
    4. Return as downloadable file
    """
    try:
        # Get base directory for templates
        base_path = os.path.join(os.path.dirname(__file__), '..')

        # Step 1: Convert form data to structured PaymentData object
        payment_data = PaymentData.from_form_data(form_data)

        # Log the structured data (for debugging)
        print(f"Payment Data: {payment_data.to_dict()}")

        # Step 2: Initialize XML generator with template directory
        xml_generator = ACHNachaXMLGenerator(base_path)

        # Step 3: Generate complete XML content
        xml_content = xml_generator.generate(payment_data)



        # Convert to bytes
        xml_bytes = xml_content.encode('utf-8')
        xml_io = BytesIO(xml_bytes)
        xml_io.seek(0)

        return send_file(
            xml_io,
            mimetype='application/xml',
            as_attachment=True,
            download_name='ach_nacha_payment.xml'
        )

    except FileNotFoundError as e:
        return jsonify({'error': f'Template file not found: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Error generating XML: {str(e)}'}), 400

if __name__ == '__main__':
    app.run(debug=True)
