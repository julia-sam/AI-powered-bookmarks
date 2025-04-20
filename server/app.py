from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from flask_cors import CORS
from dotenv import load_dotenv
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.schema import Document

load_dotenv()
embeddings_model = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))

INDEX_DIR = "faiss_index"
vector_store = None

if os.path.isdir(INDEX_DIR):
    vector_store = FAISS.load_local(INDEX_DIR, embeddings_model, allow_dangerous_deserialization=True)

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///knowledge.db'
db = SQLAlchemy(app)

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    page_url = db.Column(db.String(500))
    page_title = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/save_entry', methods=['POST'])
def save_entry():
    data = request.get_json()
    entry = Entry(
        content   = data['content'],
        page_url  = data['page_url'],
        page_title= data['page_title'],
        timestamp = datetime.fromisoformat(data['timestamp'])
    )
    db.session.add(entry)
    db.session.commit()

    # 1) Generate embedding and persist in DB
    emb = embeddings_model.embed_query(entry.content)
    entry.embedding = emb
    db.session.commit()

    # 2) Wrap it in a LangChain Document
    doc = Document(page_content=entry.content, metadata={"id": entry.id})

    global vector_store
    if vector_store is None:
        # first document ever → create the index
        vector_store = FAISS.from_documents([doc], embeddings_model)
    else:
        # subsequent docs → just add
        vector_store.add_documents([doc])

    # 3) Save to disk so we can reload next time
    vector_store.save_local(INDEX_DIR)

    return jsonify({"status":"success","id":entry.id}), 200

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

    # 1) Run semantic search with scores
    results = vector_store.similarity_search_with_score(q, k=5)

    # 2) Lookup full entries in the DB
    out = []
    for doc, score in results:
        eid = int(doc.metadata['id'])
        e = Entry.query.get(eid)
        out.append({
            "id": e.id,
            "content": e.content,
            "page_url": e.page_url,
            "page_title": e.page_title,
            "score": float(score)  # Convert score to a standard float
        })

    return jsonify(out), 200


if __name__ == '__main__':
    if not os.path.exists('knowledge.db'):
        with app.app_context():  
            db.create_all()    
    app.run(debug=True, port=5000)
