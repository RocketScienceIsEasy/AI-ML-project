import { useState } from 'react';
import ShinyText from './ShinyText';
import SplitText from './SplitText';
import './App.css';

const handleAnimationComplete = () => {
  console.log('All letters have animated!');
};

// Helper to convert URLs in text into clickable anchor tags
const convertLinksToAnchors = (text) => {
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  return text.replace(urlRegex, (url) => {
    return `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`;
  });
};

function App() {
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFetch = async () => {
    if (!inputValue.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("http://localhost:8000/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: inputValue }),
      });

      if (!response.ok) throw new Error('Request failed.');
      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError('Something went wrong. Try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="App"
      style={{
        minHeight: '100vh',
        minWidth: '100vw',
        width: '100vw',
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'flex-start',
        boxSizing: 'border-box',
        paddingTop: '4rem',
        paddingBottom: '2rem',
        overflowY: 'auto',
      }}
    >
      {/* Heading */}
      <div style={{
        fontSize: '4rem',
        lineHeight: '1.1',
        fontWeight: 600,
        textAlign: 'center',
        marginBottom: '2rem',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
      }}>
        <SplitText
          text="Soliloquy"
          className="font-semibold text-center"
          delay={100}
          duration={0.6}
          ease="power3.out"
          splitType="chars"
          from={{ opacity: 0, y: 40 }}
          to={{ opacity: 1, y: 0 }}
          threshold={0.1}
          rootMargin="-100px"
          textAlign="center"
          onLetterAnimationComplete={handleAnimationComplete}
        />
      </div>

      {/* Input and Button */}
      <div
        className="center-input"
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          marginBottom: '2rem'
        }}
      >
        <input
          type="text"
          value={inputValue}
          onChange={e => setInputValue(e.target.value)}
          placeholder="Enter title of book..."
        />
        <button
          className="raised-btn"
          onClick={handleFetch}
          disabled={loading}
        >
          {loading ? 'Loading...' : 'Find'}
        </button>
      </div>

      {/* Error */}
      {error && <p style={{ color: 'red', marginTop: '1rem', textAlign: 'center' }}>{error}</p>}

      {/* Results block from backend "message" */}
      {result?.message && (
        <div className="results" style={{
          background: '#e8e8e8',
          color: '#111',
          padding: '1.5rem',
          maxWidth: '900px',
          minHeight: '400px',
          whiteSpace: 'pre-wrap',
          textAlign: 'left',
          fontFamily: 'monospace',
          fontSize: '1rem',
          borderRadius: '6px',
          overflowX: 'auto',
          margin: '2rem auto'
        }}
        dangerouslySetInnerHTML={{
          __html: convertLinksToAnchors(result.message),
        }}
        />
      )}
    </div>
  );
}

export default App;
