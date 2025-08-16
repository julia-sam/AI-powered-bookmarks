import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "True"

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_cors import CORS
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain.embeddings import SentenceTransformerEmbeddings
from flask_migrate import Migrate
from transformers import pipeline  

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
migrate = Migrate(app, db)

class Entry(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    content   = db.Column(db.Text)
    page_url  = db.Column(db.String(500))
    page_title= db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    category  = db.Column(db.String(100), default='Uncategorized')
    image_url = db.Column(db.String(500))

category_model = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

@app.route('/save_entry', methods=['POST'])
def save_entry():
    data = request.get_json()
    
    candidate_labels = ["Technology", "Health", "Finance", "Education", "Entertainment", "Politics", "Sports", "Science", "Travel", "Lifestyle"]
    prediction = category_model(data['content'], candidate_labels=candidate_labels)
    predicted_category = prediction['labels'][0]
    
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

    entries = Entry.query.all()
    docs = [
        Document(page_content=e.content, metadata={"id": e.id})
        for e in entries
    ]
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
        }
        for e in entries
    ]), 200

@app.route('/search', methods=['GET'])
def search_entries():
    q = request.args.get('q','')
    if not q: return jsonify([]), 200
    results = vector_store.similarity_search_with_score(q, k=2)
    out = []
    for doc, score in results:
        e = Entry.query.get(int(doc.metadata['id']))
        out.append({**{"id":e.id, "content":e.content, "page_url":e.page_url, "page_title":e.page_title}, "score":float(score)})
    return jsonify(out), 200

@app.route('/entries/<int:entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    entry = Entry.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()

    # Update vector store after deletion
    entries = Entry.query.all()
    if entries:
        docs = [
            Document(page_content=e.content, metadata={"id": e.id})
            for e in entries
        ]
        global vector_store
        vector_store = FAISS.from_documents(docs, hf_embeddings)
        vector_store.save_local(INDEX_DIR)

    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  
      
        entries = Entry.query.all()
        
        if entries:  
            docs = [
                Document(page_content=e.content, metadata={"id": e.id})
                for e in entries
            ]
            vector_store = FAISS.from_documents(docs, hf_embeddings)
            vector_store.save_local(INDEX_DIR)
        else:
            print("No entries found in the database. Vector store not created.")
    
    app.run(debug=True, port=5000)
