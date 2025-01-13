import openai

# Set your OpenAI API key
openai.api_key = "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"

def generate_summary(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Change to "gpt-4" if available
            messages=[
                {"role": "system", "content": "Answer the question."},
                {"role": "user", "content": text}
            ]
        )
        return response['choices'][0]['message']['content']
    except openai.error.OpenAIError as e:
        return f"An error occurred: {e}"

# Test the function
if __name__ == "__main__":
    test_text = "What is love~"
    summary = generate_summary(test_text)
    print("Summary:", summary)
