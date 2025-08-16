import os
import requests
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_cors import CORS
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain_huggingface import HuggingFaceEmbeddings
from flask_migrate import Migrate

# ------------------ Embeddings ------------------
hf_embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"  # ~60MB
)

# ------------------ FAISS Index ------------------
INDEX_DIR = "faiss_index"
vector_store = None
if os.path.isdir(INDEX_DIR):
    vector_store = FAISS.load_local(
        INDEX_DIR, hf_embeddings, allow_dangerous_deserialization=True
    )

# ------------------ Flask Setup ------------------
app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///knowledge.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ------------------ Database Model ------------------
class Entry(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    content   = db.Column(db.Text)
    page_url  = db.Column(db.String(500))
    page_title= db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    category  = db.Column(db.String(100), default='Uncategorized')
    image_url = db.Column(db.String(500))


# ------------------ Hugging Face Inference API for categorization ------------------
from dotenv import load_dotenv
load_dotenv()
HF_API_TOKEN = os.getenv("HF_API_TOKEN") 
HF_API_URL   = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"

def classify_text(text):
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    candidate_labels = [
        "Movies", "TV Shows", "Documentaries", "Music", "Sports",
        "Technology", "Health", "Finance", "Education", "Politics", "Science", "Travel", "Lifestyle"
    ]
    payload = {
        "inputs": text,  # Ensure this is a string
        "parameters": {"candidate_labels": candidate_labels}  # Use `parameters` key
    }
    
    try:
        r = requests.post(HF_API_URL, headers=headers, json=payload)
        print(f"API Response Status: {r.status_code}")
        print(f"API Response: {r.text}")
        
        if r.status_code == 200:
            result = r.json()
            print("Classification result:", result)
            if result.get("scores") and result["scores"][0] > 0.2:
                return result["labels"][0]
            else:
                print("Low confidence score, defaulting to Uncategorized")
                return "Uncategorized"
        else:
            print(f"API error: {r.status_code} - {r.text}")
            return "Uncategorized"
    except Exception as e:
        print(f"Error during classification: {str(e)}")
        return "Uncategorized"



# ------------------ Routes ------------------
@app.route('/save_entry', methods=['POST'])
def save_entry():
    data = request.get_json()
    predicted_category = classify_text(data['content'])
    
    entry = Entry(
        content    = data['content'],
        page_url   = data['page_url'],
        page_title = data['page_title'],
        timestamp  = datetime.fromisoformat(data['timestamp']),
        category   = predicted_category,
        image_url  = data.get('image_url') 
    )
    db.session.add(entry)
    db.session.commit()

    # Update FAISS
    entries = Entry.query.all()
    docs = [Document(page_content=e.content, metadata={"id": e.id}) for e in entries]
    global vector_store
    vector_store = FAISS.from_documents(docs, hf_embeddings)
    vector_store.save_local(INDEX_DIR)

    return jsonify({"status": "success", "id": entry.id})


@app.route('/entries', methods=['GET'])
def get_entries():
    entries = Entry.query.all()
    return jsonify([
        {
            "id":         e.id,
            "content":    e.content,
            "page_url":   e.page_url,
            "page_title": e.page_title,
            "timestamp":  e.timestamp.isoformat(),
            "category":   e.category,
            "image_url":  e.image_url  
        } for e in entries
    ]), 200


@app.route('/search', methods=['GET'])
def search_entries():
    q = request.args.get('q','')
    if not q or not vector_store:
        return jsonify([]), 200
    results = vector_store.similarity_search_with_score(q, k=2)
    out = []
    for doc, score in results:
        e = Entry.query.get(int(doc.metadata['id']))
        out.append({
            "id": e.id,
            "content": e.content,
            "page_url": e.page_url,
            "page_title": e.page_title,
            "score": float(score)
        })
    return jsonify(out), 200


@app.route('/entries/<int:entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    entry = Entry.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()

    # Update FAISS
    entries = Entry.query.all()
    if entries:
        docs = [Document(page_content=e.content, metadata={"id": e.id}) for e in entries]
        global vector_store
        vector_store = FAISS.from_documents(docs, hf_embeddings)
        vector_store.save_local(INDEX_DIR)
    else:
        vector_store = None

    return jsonify({"status": "success"}), 200


# ------------------ Main ------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        entries = Entry.query.all()
        if entries:
            docs = [Document(page_content=e.content, metadata={"id": e.id}) for e in entries]
            vector_store = FAISS.from_documents(docs, hf_embeddings)
            vector_store.save_local(INDEX_DIR)
        else:
            print("No entries found. Vector store not created.")
    
    app.run(debug=True, port=5000)
