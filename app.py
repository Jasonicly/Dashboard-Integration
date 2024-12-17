from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import spacy

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load the spaCy NLP model
nlp = spacy.load("en_core_web_sm")

# Function to process a report and extract relevant data
def process_report(report):
    doc = nlp(report)

    # Extract numbers, dates, and meaningful noun phrases
    numbers = [ent.text for ent in doc.ents if ent.label_ == "CARDINAL"]
    dates = [ent.text for ent in doc.ents if ent.label_ == "DATE"]

    # Extract key phrases or sentences containing relevant keywords
    key_phrases = []
    for sent in doc.sents:
        if any(keyword in sent.text.lower() for keyword in ["increase", "decrease", "revenue", "sales", "%"]):
            key_phrases.append(sent.text.strip())

    # Aggregate extracted data
    response_data = {
        "numbers": numbers,
        "dates": dates,
        "key_phrases": key_phrases
    }
    return response_data

# Endpoint to process report and generate visual configuration
@app.route('/generate_visuals', methods=['POST'])
def generate_visuals():
    data = request.json
    report = data.get("report", "")

    # Process the report and extract key data
    extracted_data = process_report(report)

    # Map extracted data to example visualizations
    visuals = [
        {
            "id": "chart1",
            "type": "pie",
            "title": "Keyword Sentences Distribution",
            "data": [{"value": len(extracted_data["key_phrases"]), "name": "Key Insights"}],
            "size": {"columns": 4, "rows": 4}
        },
        {
            "id": "chart2",
            "type": "line",
            "title": "Dates in Report",
            "data": {"categories": extracted_data["dates"], "values": [10] * len(extracted_data["dates"])},
            "size": {"columns": 6, "rows": 4}
        },
        {
            "id": "chart3",
            "type": "bar",
            "title": "Numbers Mentioned in Report",
            "data": {"categories": extracted_data["numbers"], "values": [int(num.strip('%')) if '%' in num else int(num) for num in extracted_data["numbers"]]},
            "size": {"columns": 6, "rows": 4}
        }
    ]
    return jsonify(visuals)

# Serve the HTML page
@app.route('/')
def index():
    return render_template("grid_with_charts.html")

if __name__ == '__main__':
    app.run(debug=True)
