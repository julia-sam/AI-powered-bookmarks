import React, { useEffect, useState } from 'react';
import axios from 'axios';
import Plot from 'react-plotly.js';

function App() {
  // ─── State ─────────────────────────────────────────────
  const [entries, setEntries]       = useState([]);   // all saved entries
  const [results, setResults]       = useState([]);   // search results
  const [query, setQuery]           = useState('');   // search text
  const [summaries, setSummaries]   = useState({});   // id → summary text

  // ─── Load recent entries on mount ────────────────────
  useEffect(() => {
    axios.get('/entries')
      .then(res => setEntries(res.data))
      .catch(err => console.error(err));
  }, []);

  // ─── Handlers ─────────────────────────────────────────
  const handleSearch = () => {
    if (!query.trim()) {
      setResults([]);
      return;
    }
    axios.get('/search', { params: { q: query } })
      .then(res => setResults(res.data))
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
  const displayList = results.length > 0 ? results : entries;
  const isSearchMode = results.length > 0;

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
        {isSearchMode && (
          <button
            onClick={() => { setResults([]); setQuery(''); }}
            style={{ marginLeft: '0.5rem', padding: '0.5rem 1rem' }}
          >
            Clear
          </button>
        )}
      </div>

      {/* ─── List of Entries / Results ──────────────── */}
      <h2>{isSearchMode ? 'Search Results' : 'Recent Entries'}</h2>
      <ul>
        {displayList.map(entry => (
          <li key={entry.id} style={{ marginBottom: '1rem' }}>
            <strong>{entry.page_title}</strong> – {entry.content} <br/>
            <em>{entry.page_url}</em> – {new Date(entry.timestamp).toLocaleString()}
            {isSearchMode && typeof entry.score === 'number' && (
              <span> (score: {entry.score.toFixed(2)})</span>
            )}
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
