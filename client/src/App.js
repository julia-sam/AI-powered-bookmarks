import React, { useEffect, useState } from 'react';
import axios from 'axios';
import bookmarkIcon from './bookmark.png'; 

function App() {
  // ─── State ─────────────────────────────────────────────
  const [entries, setEntries]       = useState([]);   // all saved entries
  const [filteredEntries, setFilteredEntries] = useState([]); // entries filtered by category
  const [categories, setCategories] = useState([]);   // unique categories
  const [activeCategory, setActiveCategory] = useState('All Entries'); // currently selected category
  const [query, setQuery]           = useState('');   // search text
  const [summaries, setSummaries]   = useState({});   // id → summary text

  // ─── Load recent entries on mount ────────────────────
  useEffect(() => {
    axios.get('/entries')
      .then(res => {
        console.log("Entries with categories:", res.data); 
        setEntries(res.data);
        setFilteredEntries(res.data); // Initially show all entries
        const uniqueCategories = ['All Entries', ...new Set(res.data.map(e => e.category))];
        setCategories(uniqueCategories);
      })
      .catch(err => console.error(err));
  }, []);  

  // ─── Handlers ─────────────────────────────────────────
  const handleCategoryClick = (category) => {
    setActiveCategory(category);
    if (category === 'All Entries') {
      setFilteredEntries(entries);
    } else {
      setFilteredEntries(entries.filter(e => e.category === category));
    }
  };

  const handleSearch = () => {
    if (!query.trim()) {
      setFilteredEntries(entries);
      return;
    }
    axios.get('/search', { params: { q: query } })
      .then(res => setFilteredEntries(res.data))
      .catch(err => console.error(err));
  };

  const handleSummarize = (id, content) => {
    // avoid duplicate calls
    if (summaries[id]) return;

    axios.post('/summarize', { content })
      .then(res => {
        setSummaries(s => ({ ...s, [id]: res.data.summary }));
      })
      .catch(err => console.error(err));
  };

  // ─── Decide what to display ───────────────────────────
  const displayList = filteredEntries.length > 0 ? filteredEntries : entries;
  const isSearchMode = filteredEntries.length > 0;

  // Common layout settings
  const commonLayout = {
    width: 700,      // Fixed width
    height: 400,     // Fixed height
    margin: { l: 60, r: 30, t: 70, b: 100 },
    paper_bgcolor: '#ffffff',
    plot_bgcolor: '#f2f2f2',
    font: { family: 'Helvetica, sans-serif', size: 14, color: '#333' },
  };

  // ─── Render ────────────────────────────────────────────
  return (
    <div style={{ display: 'flex', margin: '2rem', fontFamily: 'Helvetica, sans-serif' }}>
      {/* ─── Left Sidebar ───────────────────────────── */}
      <div style={{ width: '250px', padding: '1rem', borderRight: '1px solid #ccc' }}>
        {/* Title with Bookmark Icon */}
        <div style={{ marginBottom: '0.5rem', display: 'flex', alignItems: 'center' }}>
          <img
            src={bookmarkIcon}
            alt="Bookmark Icon"
            style={{ width: '30px', height: '30px', marginRight: '0.5rem' }}
          />
          <h2 style={{ fontSize: '1.5rem', margin: 0 }}>My Bookmarks</h2>
        </div>
        <hr style={{ marginBottom: '1rem', border: 'none', borderTop: '1px solid lightgray' }} />
        {/* Search Bar */}
        <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center' }}>
          <span style={{ fontSize: '1.2rem', marginRight: '0.5rem' }}></span>
          <input
            type="text"
            placeholder="🔍 Search bookmarks..."
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') handleSearch(); }}
            style={{
              flex: 1,
              padding: '0.5rem',
              borderRadius: '5px',
              border: '1px solid #ccc'
            }}
          />
        </div>
        {/* Categories */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {categories.map(category => (
            <button
              key={category}
              onClick={() => handleCategoryClick(category)}
              style={{
                padding: '0.5rem 1rem',
                borderRadius: '20px',
                border: 'none',
                background: activeCategory === category
                  ? 'linear-gradient(45deg, #d8b5ff, #b3e5fc)'
                  : '#E0E0E0',
                color: activeCategory === category ? 'black' : '#333',
                cursor: 'pointer',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                transition: 'background 0.3s, color 0.3s'
              }}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      {/* ─── Main Content Area ───────────────────────── */}
      <div style={{ flex: 1, padding: '1rem' }}>
        <h2>{activeCategory}</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {filteredEntries.map(entry => (
            <div
              key={entry.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                padding: '1rem',
                border: '1px solid #ccc',
                borderRadius: '5px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
              }}
            >
              {/* Column 1: Title */}
              <div style={{ flex: 1, fontWeight: 'bold' }}>
                {entry.page_title}
              </div>
              {/* Column 2: Content & Source */}
              <div style={{ flex: 2, padding: '0 1rem' }}>
                <div>{entry.content}</div>
                <div style={{ fontSize: '0.9rem', color: '#555' }}>{entry.page_url}</div>
              </div>
              {/* Column 3: Date/Time */}
              <div style={{ flex: 1, textAlign: 'right', fontSize: '0.9rem', color: '#555' }}>
                {new Date(entry.timestamp).toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default App;
