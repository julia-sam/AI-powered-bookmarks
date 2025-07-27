import React, { useEffect, useState } from 'react';
import axios from 'axios';
import Plot from 'react-plotly.js';

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

  // ─── Prepare chart data ───────────────────────────────
  let chartData;
  let chartLayout;

  if (isSearchMode) {
    // Bar chart of similarity scores for search results
    const titles = displayList.map(e => e.page_title);
    const scores = displayList.map(e => e.score ?? 0);
    chartData = [{ 
      x: titles, 
      y: scores, 
      type: 'bar', 
      marker: { color: 'rgba(54, 162, 235, 0.7)', line: { color: 'rgba(54, 162, 235, 1)', width: 2 } } 
    }];
    chartLayout = {
      title: 'Search Result Similarity Scores',
      titlefont: { size: 24, color: '#333' },
      xaxis: { automargin: true, title: 'Page Titles', titlefont: { size: 16, color: '#666' } },
      yaxis: { title: 'Similarity Score', titlefont: { size: 16, color: '#666' } },
      plot_bgcolor: '#f9f9f9',
      paper_bgcolor: '#ffffff',
      font: { family: 'Arial, sans-serif', size: 14, color: '#333' },
    };
  } else {
    // Domain frequency for recent entries
    const domainCount = displayList.reduce((acc, entry) => {
      try {
        const hostname = new URL(entry.page_url).hostname;
        acc[hostname] = (acc[hostname] || 0) + 1;
      } catch {
        // skip bad URLs
      }
      return acc;
    }, {});
    const domains = Object.keys(domainCount);
    const counts  = Object.values(domainCount);
    chartData = [{ 
      x: domains, 
      y: counts, 
      type: 'bar', 
      marker: { color: 'rgba(75, 192, 192, 0.7)', line: { color: 'rgba(75, 192, 192, 1)', width: 2 } } 
    }];
    chartLayout = {
      title: 'Saved Entries by Domain',
      titlefont: { size: 24, color: '#333' },
      xaxis: { automargin: true, title: 'Domains', titlefont: { size: 16, color: '#666' } },
      yaxis: { title: 'Entry Count', titlefont: { size: 16, color: '#666' } },
      plot_bgcolor: '#f9f9f9',
      paper_bgcolor: '#ffffff',
      font: { family: 'Arial, sans-serif', size: 14, color: '#333' },
    };
  }

  // ─── Render ────────────────────────────────────────────
  return (
    <div style={{ margin: '2rem' }}>
      <h1>Embed Anywhere Dashboard</h1>

      {/* ─── Category Buttons ───────────────────────────── */}
      <div style={{ marginBottom: '1rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        {categories.map(category => (
          <button
            key={category}
            onClick={() => handleCategoryClick(category)}
            style={{
              padding: '0.5rem 1rem',
              borderRadius: '20px',
              border: 'none',
              backgroundColor: activeCategory === category ? '#007BFF' : '#E0E0E0',
              color: activeCategory === category ? '#FFF' : '#333',
              cursor: 'pointer',
              boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
              transition: 'background-color 0.3s, color 0.3s',
            }}
          >
            {category}
          </button>
        ))}
      </div>

      {/* ─── Search Bar ──────────────────────────────── */}
      <div style={{ marginBottom: '1rem' }}>
        <input
          type="text"
          placeholder="Search highlights..."
          value={query}
          onChange={e => setQuery(e.target.value)}
          style={{ padding: '0.5rem', width: '300px' }}
        />
        <button onClick={handleSearch} style={{ marginLeft: '0.5rem', padding: '0.5rem 1rem' }}>
          Search
        </button>
      </div>

      {/* ─── List of Entries ──────────────── */}
      <h2>{activeCategory}</h2>
      <ul>
        {filteredEntries.map(entry => (
          <li key={entry.id} style={{ marginBottom: '1rem' }}>
            <strong>{entry.page_title}</strong> – {entry.content} <br/>
            <em>{entry.page_url}</em> – {new Date(entry.timestamp).toLocaleString()}
            <div style={{ marginTop: '0.5rem' }}>
              <button
                onClick={() => handleSummarize(entry.id, entry.content)}
                style={{ fontSize: '0.9rem', padding: '0.3rem 0.6rem' }}
              >
                {summaries[entry.id] ? 'Summarized' : 'Summarize'}
              </button>
              {summaries[entry.id] && (
                <p style={{ marginTop: '0.3rem', fontStyle: 'italic' }}>
                  {summaries[entry.id]}
                </p>
              )}
            </div>
          </li>
        ))}
      </ul>

      {/* ─── Plotly Chart ────────────────────────────── */}
      <h2>{chartLayout.title}</h2>
      <Plot
        data={chartData}
        layout={chartLayout}
        style={{ width: '100%', maxWidth: '700px' }}
      />
    </div>
  );
}

export default App;
