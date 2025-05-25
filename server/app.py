import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "True"

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_cors import CORS
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain.embeddings import SentenceTransformerEmbeddings

hf_embeddings = SentenceTransformerEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

INDEX_DIR = "faiss_index"
vector_store = None
if os.path.isdir(INDEX_DIR):
    vector_store = FAISS.load_local(
        INDEX_DIR, hf_embeddings, allow_dangerous_deserialization=True
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
    db.session.add(entry); db.session.commit()

    doc = Document(page_content=entry.content, metadata={"id": entry.id})
    global vector_store
    if vector_store is None:
        vector_store = FAISS.from_documents([doc], hf_embeddings)
    else:
        vector_store.add_documents([doc])
    vector_store.save_local(INDEX_DIR)
    return jsonify({"status":"success","id":entry.id})

@app.route('/entries', methods=['GET'])
def get_entries():
    entries = Entry.query.all()
    return jsonify([
        {
            "id":        e.id,
            "content":   e.content,
            "page_url":  e.page_url,
            "page_title":e.page_title,
            "timestamp": e.timestamp.isoformat()
        }
        for e in entries
    ]), 200

@app.route('/search', methods=['GET'])
def search_entries():
    q = request.args.get('q','')
    if not q: return jsonify([]), 200
    results = vector_store.similarity_search_with_score(q, k=5)
    out = []
    for doc, score in results:
        e = Entry.query.get(int(doc.metadata['id']))
        out.append({**{"id":e.id, "content":e.content, "page_url":e.page_url, "page_title":e.page_title}, "score":float(score)})
    return jsonify(out), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not os.path.isdir(INDEX_DIR) and Entry.query.count()>0:
            docs = [Document(page_content=e.content, metadata={"id":e.id}) for e in Entry.query.all()]
            vs = FAISS.from_documents(docs, hf_embeddings)
            vs.save_local(INDEX_DIR)
    app.run(debug=True, port=5000)
