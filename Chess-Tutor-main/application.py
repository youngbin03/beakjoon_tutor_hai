import openai
import re
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
import easyocr
from PIL import Image
import io
import numpy as np

load_dotenv()

application = Flask(__name__)

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

reader = easyocr.Reader(['ko'])

@application.route("/")
def index():
    return render_template('index.html')

def extract_text_from_image(image):
    image_stream = io.BytesIO(image)
    image = Image.open(image_stream).convert('RGB')
    image_np = np.array(image)
    result = reader.readtext(image_np, detail=0)
    return " ".join(result)

@application.route('/gpt4', methods=['GET', 'POST'])
def gpt4():
    user_input = request.form.get('user_input')
    uploaded_image = request.files.get('image_upload')

    if not user_input and not uploaded_image:
        return jsonify({"error": "No user input or image provided."}), 400

    if uploaded_image:
        extracted_text = extract_text_from_image(uploaded_image.read())
        user_input = f"{user_input}\n{extracted_text}" if user_input else extracted_text

    system_message = {
        "role": "system",
        "content": (
            "You are a programming tutor. "
            "Always include a code example in your responses. "
            "The code examples should be simple, easy to understand, and include comments that explain each step."
        )
    }
    user_message = {"role": "user", "content": user_input}

    messages = [system_message, user_message]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            max_tokens=500,
            temperature=0.7,
        )
        content = response['choices'][0]['message']['content']

        language_patterns = {
            "python": r'```python(.*?)```',
            "cpp": r'```cpp(.*?)```',
            "c": r'```c(.*?)```',
            "java": r'```java(.*?)```',
            "javascript": r'```javascript(.*?)```',
            "ruby": r'```ruby(.*?)```'
        }

        code = None
        language_type = None

        for lang, pattern in language_patterns.items():
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                code = match.group(1).strip()
                content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL).strip()
                language_type = lang
                break

        if not code:
            code = "No code found in the response."
            language_type = "text"

        response_data = {
            "python_code": code,
            "description": content,
            "type": language_type,
        }
        return jsonify(response_data)

    except openai.OpenAIError as e:
        return jsonify({"error": f"OpenAI error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5001, debug=True)
