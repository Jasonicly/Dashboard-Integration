from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import openai
import re

app = Flask(__name__)
CORS(app)

openai.api_key = "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"  # Replace with your OpenAI API key

def generate_summary(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Summarize the given text in 100 words."},
                {"role": "user", "content": text}
            ]
        )
        summary = response['choices'][0]['message']['content']
        print(f"Generated Summary: {summary}")
        return summary
    except Exception as e:
        print(f"Error in generate_summary: {e}")
        return "An error occurred while generating the summary."

def retrieve_URL_links(text):
    try:
        prompt = (
            "Extract all URLs from the following text, together with the reason for their inclusion:\n\n"
            f"{text}\n\n"
            "Provide the results in this format:\n"
            "- [title], URL: [URL]"
        )
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an assistant that extracts URLs and their corresponding title from text."},
                {"role": "user", "content": prompt}
            ]
        )
        urls = response['choices'][0]['message']['content']
        print(f"Extracted URL Links: {urls}")
        return urls
    except Exception as e:
        print(f"Error in retrieve_URL_links: {e}")
        return "An error occurred while extracting URLs."

def retrieve_important_claims(text, limit=5):
    try:
        prompt = (
            "From the following text, identify the most important claims or pieces of information, "
            "especially those with numbers or significant achievements that can be visualized in a dashboard, or locations that can be plotted on a map. "
            f"Limit the claims up to the top {limit}. Provide the results in this format:\n\n"
            "- [Claim 1]\n- [Claim 2]\n...\n\n"
            f"{text}"
        )
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an assistant that identifies important claims and achievements from text."},
                {"role": "user", "content": prompt}
            ]
        )
        claims = response['choices'][0]['message']['content'].split("\n")
        claims = [claim.strip() for claim in claims if claim.strip()]
        print(f"Extracted Claims: {claims}")
        return claims[:limit]
    except Exception as e:
        print(f"Error in retrieve_important_claims: {e}")
        return ["An error occurred while extracting claims."]

def data_assignment(claim):
    try:
        prompt = (
            f"Based on the following claim, decide the best visualization type, short form title, and provide the necessary data "
            f"for visualization using templates (pie, bar, line). "
            f"For text-based claims without numerical data, use the text-box template. "
            f"The response format should be:\n\n"
            f"Visualization Type: [Type]\n"
            f"Title: [Generated Title]\n"
            f"Data:\n"
            f"- For Pie: [{{'name': 'Category A', 'value': 30}}, {{'name': 'Category B', 'value': 70}}]\n"
            f"- For Bar or Line: {{'categories': ['Category A', 'Category B'], 'values': [30, 70]}}\n"
            f"- For Text-Box: {{'title': 'Title for the Claim', 'content': 'Claim content goes here'}}\n\n"
            f"Claim: {claim}"
        )
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an assistant that assigns visualization types, generates titles, and provides data based on claims."},
                {"role": "user", "content": prompt}
            ]
        )
        result = response['choices'][0]['message']['content']
        print(f"Raw Data Assignment Response for Claim '{claim}':\n{result}")  # Log raw response for debugging

        # Parse visualization type, title, and data
        vis_type_match = re.search(r"Visualization Type: (\w+)", result)
        title_match = re.search(r"Title: \[([^\]]+)\]", result)
        vis_data_match = re.search(r"Data:\s*({.+})", result, re.DOTALL)  # Look for JSON-like structures

        if vis_type_match and title_match and vis_data_match:
            vis_type = vis_type_match.group(1).strip().lower()
            title = title_match.group(1).strip()
            raw_data = vis_data_match.group(1).strip()

            if vis_type == "text-box":
                try:
                    text_data = eval(raw_data)  # Convert JSON-like string to Python dict
                    if isinstance(text_data, dict) and "title" in text_data and "content" in text_data:
                        return {
                            "type": "text-box",
                            "title": text_data["title"],
                            "content": text_data["content"]
                        }
                except Exception as e:
                    print(f"Error parsing text-box data: {e}")

            elif vis_type == "pie":
                try:
                    data = eval(raw_data)  # Convert to Python
                    if isinstance(data, list):
                        return {"type": "pie", "title": title, "data": data}
                except Exception as e:
                    print(f"Error parsing pie chart data: {e}")

            elif vis_type in ["bar", "line"]:
                try:
                    data = eval(raw_data)
                    if isinstance(data, dict) and "categories" in data and "values" in data:
                        return {"type": vis_type, "title": title, "data": data}
                except Exception as e:
                    print(f"Error parsing bar/line chart data: {e}")

        # Log invalid format before fallback
        print(f"Invalid response format from OpenAI:\n{result}")
        raise ValueError("Invalid response format from OpenAI.")

    except Exception as e:
        print(f"Error in data_assignment: {e}")
        return {
            "type": "text-box",
            "title": "Unparsed Claim",
            "content": f"An error occurred while processing the claim: {claim}"
        }


@app.route('/generate_visuals', methods=['POST'])
def generate_visuals():
    try:
        data = request.json
        pdf_name = data.get('pdf_name', 'Unknown File')
        pdf_content = data.get('pdf_content', '')

        print(f"Received PDF Name: {pdf_name}")
        print(f"Received PDF Content Length: {len(pdf_content)}")

        if not pdf_content.strip():
            return jsonify({"error": "No PDF content provided."}), 400

        # Generate summary
        summary = generate_summary(pdf_content)

        # Extract claims
        claims = retrieve_important_claims(pdf_content)

        # Extract URL links
        extracted_urls = retrieve_URL_links(pdf_content)

        # Assign visualization for each claim
        dynamic_visuals = []
        for claim in claims:
            visualization = data_assignment(claim)  # Get visualization data for each claim
            if isinstance(visualization, dict) and "type" in visualization and "data" in visualization:
                visual_config = {
                    "id": f"vis_{len(dynamic_visuals) + 1}",
                    "type": visualization["type"],
                    "title": visualization["title"],  # Use the title from the visualization
                    "data": visualization["data"],
                    "description": claim,
                    "size": {"columns": 4, "rows": 4}  # Example size, adjust as needed
                }
                dynamic_visuals.append(visual_config)

        # Add summary and URL visuals
        dynamic_visuals.insert(0, {
            "id": "info",
            "type": "text-box",
            "title": "PDF Information",
            "details": f"PDF Name: {pdf_name}",
            "size": {"columns": 4, "rows": 2}
        })
        dynamic_visuals.insert(1, {
            "id": "urls",
            "type": "text-box",
            "title": "Extracted URLs",
            "details": extracted_urls,
            "size": {"columns": 4, "rows": 2}
        })
        dynamic_visuals.insert(2, {
            "id": "summary",
            "type": "text-box",
            "title": "Summary",
            "details": summary,
            "size": {"columns": 8, "rows": 2}
        })

        return jsonify(dynamic_visuals)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    return render_template("grid_with_charts.html")

if __name__ == '__main__':
    app.run(debug=True)