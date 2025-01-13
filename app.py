from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import spacy
import openai
import re

app = Flask(__name__)
CORS(app)

openai.api_key = "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"
nlp = spacy.load("en_core_web_sm")

def generate_summary(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # Use the correct model name
        messages=[
            {"role": "system", "content": "Summarize the given text in 100 words."},
            {"role": "user", "content": text}
        ]
    )
    print(response.choices[0].message['content'])
    return response['choices'][0]['message']['content']

def retrieve_URL_links(text):
    try:
        # OpenAI prompt for extracting URLs and their reasons
        prompt = (
            "Extract all URLs from the following text, together with the reason for their inclusion:\n\n"
            f"{text}\n\n"
            "Provide the results in this format:\n"
            "- [title], URL: [URL]"
        )
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Use the appropriate model
            messages=[
                {"role": "system", "content": "You are an assistant that extracts URLs and their corresponding title from text."},
                {"role": "user", "content": prompt}
            ]
        )
        # Return the AI's response as the extracted information
        result = response['choices'][0]['message']['content']
        print(f"Extracted URL links:\n{result}")
        return result
    except Exception as e:
        print(f"Error in retrieve_URL_links: {e}")
        return "An error occurred while extracting URLs."

def retrieve_important_claims(text):
    try:
        # OpenAI prompt for extracting top 5 important claims with numbers or achievements
        prompt = (
            "From the following text, identify the top 5 most important claims or pieces of information, "
            "especially those with numbers or achievements that can be visualized. Provide the results in this format:\n\n"
            "- [Claim 1]\n- [Claim 2]\n...\n\n"
            f"{text}"
        )
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Use the appropriate model
            messages=[
                {"role": "system", "content": "You are an assistant that identifies important claims with numbers or achievements from text."},
                {"role": "user", "content": prompt}
            ]
        )
        # Return the AI's response as the extracted claims
        result = response['choices'][0]['message']['content']
        print(f"Extracted Claims:\n{result}")
        return result
    except Exception as e:
        print(f"Error in retrieve_important_claims: {e}")
        return "An error occurred while extracting claims."


def process_report(report):
    doc = nlp(report)
    numbers = [ent.text for ent in doc.ents if ent.label_ == "CARDINAL" and re.match(r'^\d+$', ent.text)]
    dates = [ent.text for ent in doc.ents if ent.label_ == "DATE"]
    key_phrases = [
        sent.text.strip() for sent in doc.sents
        if any(keyword in sent.text.lower() for keyword in ["increase", "decrease", "revenue", "sales", "%"])
    ]
    return {"numbers": numbers, "dates": dates, "key_phrases": key_phrases}

@app.route('/generate_visuals', methods=['POST'])
def generate_visuals():
    try:
        data = request.json
        pdf_name = data.get('pdf_name', 'Unknown File')  # Extract the PDF name
        pdf_content = data.get('pdf_content', '')  # Extract the PDF content

        print(f"Received PDF Name: {pdf_name}")
        print(f"Received PDF Content (truncated): {pdf_content[:100]}...")  # Print first 100 characters
        if not data:
            return jsonify({"error": "No data received"}), 400

        report = data.get("report", "")

        print(f"Received report: {report}")  # Debugging log

        # Summarize and process
        summary = generate_summary(pdf_content)
        print(f"Generated summary: {summary}")  # Debugging log

        extracted_data = process_report(report)

        extracted_urls = retrieve_URL_links(pdf_content)
        print(f"Retrieved URL links: {extracted_urls}")  # Debugging log

        # Visual configurations
        visuals = [
            {
                "id": "info",
                "type": "text-box",
                "title": "PDF Information",
                "details": f"PDF Name: {pdf_name}",
                "size": {"columns": 4, "rows": 1}  # Stack vertically
            },
            {
                "id": "urls",
                "type": "text-box",
                "title": "Associated URLs",
                "details": extracted_urls,  # Display URLs and reasons
                "size": {"columns": 4, "rows": 1},  # Stack vertically below "Info"
            },
            {
                "id": "summary",
                "type": "text-box",
                "title": "Summary",
                "details": summary,
                "size": {"columns": 8, "rows": 2}  # Positioned to the right
            },
            {
                "id": "chart1",
                "type": "pie",
                "title": "Key Insights Distribution",
                "data": [{"value": 30, "name": "Category A"}, {"value": 70, "name": "Category B"}],
                "title": "Key Insights Distribution",
                "description": "This pie chart shows the distribution of key insights across different categories.",
                "size": {"columns": 4, "rows": 4}
            },
            {
                "id": "chart2",
                "type": "line",
                "title": "Dates in Report",
                "data": {"categories": extracted_data["dates"], "values": [10] * len(extracted_data["dates"])},
                "title": "Dates in Report",
                "description": "This line chart illustrates the trends of values over the months of January, February, and March.",
                "size": {"columns": 5, "rows": 4}
            },
            {
                "id": "chart3",
                "type": "bar",
                "title": "Numbers Mentioned in Report",
                "data": {"categories": extracted_data["numbers"], "values": [int(num.strip('%')) if '%' in num else int(num) for num in extracted_data["numbers"]]},
                "title": "Numbers Mentioned in Report",
                "description": "This bar chart shows the numbers mentioned in the report.",
                "size": {"columns": 5, "rows": 4}
            },
            {
                "id": "map1",
                "type": "map",
                "title": "Geographical Distribution",
                "description": "This map shows various locations with their respective values.",
                "zoom": 10,   #Optional zoom level
                "data": [
                    { "name": "Clementi", "latitude": 1.3151, "longitude": 103.7707, "value": 100 },
                    { "name": "Tampines", "latitude": 1.3521, "longitude": 103.943, "value": 200 },
                    { "name": "Jurong", "latitude": 1.333, "longitude": 103.706, "value": 150 }
                ],
                "size": { "columns":4, "rows": 4 }
            }

        ]
        return jsonify(visuals)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/')
def index():
    return render_template("grid_with_charts.html")

if __name__ == '__main__':
    app.run(debug=True)
