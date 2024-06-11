# app.py
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# 预定义的词汇列表
words = [
    "apple", "application pandas", "banana", "band", "bar", "base", "cat", "caterpillar",
    "dog", "dolphin", "elephant", "eagle", "fish", "frog"
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get('q', '')
    suggestions = [word for word in words if word.startswith(query)]
    return jsonify(suggestions)

if __name__ == '__main__':
    app.run(debug=True)
