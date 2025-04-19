import React, { useEffect, useState } from 'react';
import axios from 'axios';
import Plot from 'react-plotly.js';

function App() {
  const [entries, setEntries] = useState([]);

  useEffect(() => {
    axios.get('http://localhost:5000/entries')
      .then((res) => setEntries(res.data))
      .catch((err) => console.error(err));
  }, []);

  // Example chart data
  // Let's count how many times a domain appears
  const domainCount = entries.reduce((acc, entry) => {
    try {
      const urlObj = new URL(entry.page_url);
      const domain = urlObj.hostname;
      acc[domain] = acc[domain] ? acc[domain] + 1 : 1;
    } catch (e) {
      // skip invalid URLs
    }
    return acc;
  }, {});

  const domains = Object.keys(domainCount);
  const counts = Object.values(domainCount);

  return (
    <div style={{ margin: '2rem' }}>
      <h1>Embed Anywhere Dashboard</h1>
      <h2>Recent Entries</h2>
      <ul>
        {entries.map((entry) => (
          <li key={entry.id}>
            <strong>{entry.page_title}</strong> - {entry.content} <br />
            <em>{entry.page_url}</em> - {new Date(entry.timestamp).toLocaleString()}
          </li>
        ))}
      </ul>

      <h2>Domain Frequency</h2>
      <Plot
        data={[
          {
            x: domains,
            y: counts,
            type: 'bar'
          }
        ]}
        layout={{ title: 'Saved Entries by Domain', xaxis: { automargin: true } }}
        style={{ width: '100%', maxWidth: '600px' }}
      />
    </div>
  );
}

export default App;
