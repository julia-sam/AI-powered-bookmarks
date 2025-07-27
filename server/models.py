from sqlalchemy.dialects.sqlite import JSON
from app import db

class Entry(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    content    = db.Column(db.Text)
    page_url   = db.Column(db.String(500))
    page_title = db.Column(db.String(500))
    timestamp  = db.Column(db.DateTime)
    embedding  = db.Column(JSON)
    category  = db.Column(db.String(100), default='Uncategorized')