## AI-Powered Bookmarks

### Overview
This project is a web-based dashboard for managing and visualizing saved bookmarks, integrated with a Chrome extension. It uses AI-powered categorization and a vector store to search and filter.

### Features
- Chrome Extension Integration: Right-click on selected text or images to save them directly to the knowledge base.
- Automatic Categorization: Entries are categorized using a zero-shot classification model (facebook/bart-large-mnli).
- Search Functionality: Search entries using semantic similarity.
- Category Filtering: Filter entries by category using dynamic buttons.

### Usage
#### Saving an Entry via Chrome Extension:
1. Highlight text or right-click on an image in Chrome.
2. Select Save to Knowledge Base from the context menu.
3. The selected content will be sent to the backend and saved in the knowledge base.

<img src="https://github.com/julia-sam/AI-powered-bookmarks/blob/master/bookmarking-system.png?raw=true" width="600" height="600">

### Technologies Used
- Backend: Flask, SQLAlchemy, FAISS, Hugging Face Transformers
- Frontend: React, Axios
- Database: SQLite
- Chrome Extension: JavaScript, Chrome APIs
