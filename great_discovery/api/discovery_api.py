
from flask import Flask, request, jsonify

app = Flask(__name__)

questions = []

@app.route("/new_question", methods=["POST"])
def new_question():
    q = request.json.get("question")
    questions.append(q)
    return jsonify({"status": "stored", "question": q})

@app.route("/questions")
def list_questions():
    return jsonify(questions)
