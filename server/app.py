import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "True"
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_cors import CORS
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import List
from langchain.embeddings.base import Embeddings
import torch
torch.set_num_threads(1)
torch.set_num_interop_threads(1)

# 1) Define your generator first
tokenizer = AutoTokenizer.from_pretrained("microsoft/phi-3-mini-4k-instruct")
model     = AutoModelForCausalLM.from_pretrained("microsoft/phi-3-mini-4k-instruct")
model.config.output_hidden_states = True

def generate_embeddings(text: str) -> List[float]:
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    outputs = model(**inputs)
    last_hidden = outputs.hidden_states[-1]          # (1, seq_len, d)
    emb = last_hidden.mean(dim=1)                   # (1, d)
    return emb.detach().cpu().numpy().flatten().tolist()

# 2) Wrap it in an Embeddings subclass
class TransformerEmbeddings(Embeddings):
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [generate_embeddings(t) for t in texts]
    def embed_query(self, text: str) -> List[float]:
        return generate_embeddings(text)

hf_embeddings = TransformerEmbeddings()

# 3) Load (or will be None if no index folder)
INDEX_DIR = "faiss_index"
vector_store = None
if os.path.isdir(INDEX_DIR):
    vector_store = FAISS.load_local(
        INDEX_DIR, 
        hf_embeddings, 
        allow_dangerous_deserialization=True
    )

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///knowledge.db'
db = SQLAlchemy(app)

class Entry(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    content   = db.Column(db.Text)
    page_url  = db.Column(db.String(500))
    page_title= db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/save_entry', methods=['POST'])
def save_entry():
    data = request.get_json()
    entry = Entry(
        content    = data['content'],
        page_url   = data['page_url'],
        page_title = data['page_title'],
        timestamp  = datetime.fromisoformat(data['timestamp'])
    )
    db.session.add(entry)
    db.session.commit()

    doc = Document(page_content=entry.content, metadata={"id": entry.id})
    global vector_store
    if vector_store is None:
        # first ever → creates a new index with hf_embeddings
        vector_store = FAISS.from_documents([doc], hf_embeddings)
    else:
        vector_store.add_documents([doc])
    vector_store.save_local(INDEX_DIR)

    return jsonify({"status":"success","id": entry.id})

@app.route('/entries', methods=['GET'])
def get_entries():
    entries = Entry.query.all()
    results = []
    for e in entries:
        results.append({
            "id": e.id,
            "content": e.content,
            "page_url": e.page_url,
            "page_title": e.page_title,
            "timestamp": e.timestamp.isoformat()
        })
    return jsonify(results), 200

@app.route('/search', methods=['GET'])
def search_entries():
    q = request.args.get('q', '')
    if not q:
        return jsonify([]), 200

    # Debug: Check query
    print(f"Search query: {q}")

    # 1) Run semantic search with scores
    try:
        results = vector_store.similarity_search_with_score(q, k=5)
    except Exception as e:
        return jsonify({"error": f"Search failed: {str(e)}"}), 500

    # Debug: Check results
    print(f"Search results: {results}")

    # 2) Lookup full entries in the DB
    out = []
    for item in results:
        if isinstance(item, tuple) and len(item) == 2:
            doc, score = item
            eid = int(doc.metadata['id'])
            e = Entry.query.get(eid)
            if e:
                out.append({
                    "id": e.id,
                    "content": e.content,
                    "page_url": e.page_url,
                    "page_title": e.page_title,
                    "score": float(score)
                })
        else:
            return jsonify({"error": "Unexpected result format"}), 500

    return jsonify(out), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # if there’s no index folder but there are saved entries in DB
        if not os.path.isdir(INDEX_DIR) and Entry.query.count() > 0:
            all_docs = [ Document(page_content=e.content, metadata={"id":e.id})
                         for e in Entry.query.all() ]
            print("🔄 Rebuilding FAISS index from existing DB entries…")
            vector_store = FAISS.from_documents(all_docs, hf_embeddings)
            vector_store.save_local(INDEX_DIR)
            print("🔄 Done rebuilding.")
    app.run(debug=True, port=5000)
