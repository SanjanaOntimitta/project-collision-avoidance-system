from flask import Flask, request, render_template
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from pymongo import MongoClient

app = Flask(__name__)

# Load model
model = SentenceTransformer('all-MiniLM-L6-v2')

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["projectDB"]
collection = db["projects"]

THRESHOLD = 0.8

def get_similarity(input_text, db_texts):
    input_embedding = model.encode([input_text])
    db_embeddings = model.encode(db_texts)
    return cosine_similarity(input_embedding, db_embeddings)[0]

@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    warning = None

    if request.method == "POST":
        title = request.form["title"]
        abstract = request.form["abstract"]
        description = request.form["description"]

        input_text = abstract + " " + description

        projects = list(collection.find())

        if projects:
            db_texts = [p["abstract"] + " " + p["description"] for p in projects]
            scores = get_similarity(input_text, db_texts)

            for i, score in enumerate(scores):
                results.append({
                    "title": projects[i]["title"],
                    "score": round(float(score), 2)
                })

                if score > THRESHOLD:
                    warning = "⚠️ Similar project exists!"

        # Save project
        collection.insert_one({
            "title": title,
            "abstract": abstract,
            "description": description
        })

    return render_template("index.html", results=results, warning=warning)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)