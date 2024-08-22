from flask import Flask
import sys
import streamlit as st

import json
import os
from flask import Flask, render_template, request, jsonify
from openai import OpenAI

client = OpenAI(api_key="")
from openai.error import RateLimitError
import re  # 정규 표현식을 사용하기 위해 모듈 추가

application = Flask(__name__)

# CHANGE OPENAI_API_KEY -> YOUR_API_KEY
# EXAMPLE 
# openai.api_key = "sk-JUg...."

@application.route("/")
def index():
    return render_template('index.html')

@application.route('/gpt4', methods=['GET', 'POST'])
def gpt4():
    user_input = request.args.get('user_input') if request.method == 'GET' else request.form['user_input']
    messages = [{"role": "user", "content": user_input}]

    try:
        response = client.chat.completions.create(model="gpt-3.5-turbo",
        messages=messages)
        content = response.choices[0].message.content
        #code_match_p = re.search(r'```python(.*?)```', content, re.DOTALL | re.IGNORECASE)
        code_match_p = re.search(r'```python(.*?)```', content, re.IGNORECASE | re.DOTALL)
        code_match_cpp = re.search(r'```cpp(.*?)```', content, re.IGNORECASE | re.DOTALL)
        code_match_c = re.search(r'```c(.*?)```', content, re.IGNORECASE | re.DOTALL)
        code_match_java = re.search(r'```java(.*?)```', content, re.IGNORECASE | re.DOTALL)
        language_type = "python"

        if code_match_p:
            python_code = code_match_p.group(1)
            content = content.replace(code_match_p.group(0), "").strip()
            language_type = "python"
        elif code_match_c:
            python_code = code_match_c.group(1)
            content = content.replace(code_match_c.group(0), "").strip()
            language_type = "c"
        elif code_match_cpp:
            python_code = code_match_cpp.group(1)
            content = content.replace(code_match_cpp.group(0), "").strip()
            language_type = "cpp"
        elif code_match_java:
            python_code = code_match_java.group(1)
            content = content.replace(code_match_java.group(0), "").strip()
            language_type = "java"
        else:
            python_code = "No code found in the response."
            description = content

        response_data = {
            "python_code": python_code,
            "description": content,
            "type": language_type,
        }

    except RateLimitError:
        content = "The server is experiencing a high volume of requests. Please try again later."


    return jsonify(response_data)

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=int(sys.argv[1]))