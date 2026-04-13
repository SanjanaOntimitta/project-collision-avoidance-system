from flask import Flask, render_template, request
import json
from sentence_transformers import SentenceTransformer, util

app = Flask(__name__)

# Load model
model = SentenceTransformer('all-MiniLM-L6-v2')

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

    # Top 5 results
    top_results = results[:5]

    return render_template('index.html', results=top_results)

if __name__ == '__main__':
    app.run(debug=True)