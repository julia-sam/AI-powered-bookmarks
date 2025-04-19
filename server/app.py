from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from flask_cors import CORS

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
        content=data.get('content', ''),
        page_url=data.get('page_url', ''),
        page_title=data.get('page_title', ''),
        timestamp=datetime.fromisoformat(data.get('timestamp'))
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify({"status": "success", "id": entry.id}), 200

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

if __name__ == '__main__':
    if not os.path.exists('knowledge.db'):
        with app.app_context():  
            db.create_all()    
    app.run(debug=True, port=5000)
