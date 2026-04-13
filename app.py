<<<<<<< HEAD
from flask import Flask, render_template, request
import json
from sentence_transformers import SentenceTransformer, util
=======
from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import json
import PyPDF2
>>>>>>> 94d3936f69ec706972a35cdca183044544c34f9e

app = Flask(__name__)

model = SentenceTransformer('all-MiniLM-L6-v2')
THRESHOLD = 0.7

<<<<<<< HEAD
# Load dataset
with open('data/projects.json') as f:
    projects = json.load(f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check', methods=['POST'])
def check():
    user_title = request.form['title']
    user_abstract = request.form['abstract']

    user_text = user_title + " " + user_abstract

    results = []

    for project in projects:
        db_text = project['title'] + " " + project['abstract']

        score = util.cos_sim(
            model.encode(user_text),
            model.encode(db_text)
        )

        results.append({
            "title": project['title'],
            "score": float(score)
        })

    # Sort by similarity
    results.sort(key=lambda x: x['score'], reverse=True)
=======
with open("projects.json") as f:
    projects = json.load(f)

def extract_text(file):
    text = ""
    if file and file.filename != "":
        if file.filename.endswith(".txt"):
            text = file.read().decode("utf-8")
        elif file.filename.endswith(".pdf"):
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                if page.extract_text():
                    text += page.extract_text()
    return text

def get_status(score):
    percent = score * 100
    if percent > 85:
        return "⚠️ High Similarity"
    elif percent >= 70:
        return "⚡ Moderate Similarity"
    else:
        return "✅ Low Similarity"

@app.route("/check", methods=["POST"])
def check():
    text = request.form.get("text", "").strip()
    file = request.files.get("file")

    abstract = extract_text(file)

    if not text and not abstract:
        return jsonify({"results": []})

    combined = " ".join([t for t in [text, abstract] if t])

    user_embedding = model.encode([combined])

    stored_texts = [
        p["title"] + " " + p["abstract"] for p in projects
    ]

    stored_embeddings = model.encode(stored_texts)

    similarities = cosine_similarity(user_embedding, stored_embeddings)[0]

    results = []

    for i, score in enumerate(similarities):
        if score >= THRESHOLD:
            results.append({
                "title": projects[i]["title"],
                "similarity": round(score * 100, 2),
                "status": get_status(score)
            })

    results = sorted(results, key=lambda x: x["similarity"], reverse=True)

    return jsonify({"results": results})
>>>>>>> 94d3936f69ec706972a35cdca183044544c34f9e

    # Top 5 results
    top_results = results[:5]

    return render_template('index.html', results=top_results)

if __name__ == '__main__':
    app.run(debug=True)