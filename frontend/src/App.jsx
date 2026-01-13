import React, { useState } from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import axios from 'axios';

import InputSection from './components/InputSection';
import SettingsSection from './pages/SettingsSection';
import ResultSection from './components/ResultSection';
import HistoryPage from './pages/HistoryPage';
import { translations } from './translations';
import './App.css';

function App() {
  const [text, setText] = useState("");
  const [result, setResult] = useState({ summary: "", processing_time: 0 });
  const [loading, setLoading] = useState(false);
  const [settings, setSettings] = useState({
    model: "google/gemma-3-27b-it:free",
    chunk_size_1: 16000,
    chunk_size_2: 8000,
    token_max: 16000,
    temperature: 0.0,
    strategy: "map",
    test_mode: false,
    map_temple: "", // read from temple dir
    reduce_temple: "", // read from temple
    reduce_temperature: 0.0,
    language: "en"
  });

  const location = useLocation();
  const t = translations[settings.language] || translations.en;

  const handleTextChange = (newText) => {
    setText(newText);
  };

  const handleSummarize = async () => {
    if (!text) return;
    setLoading(true);
    try {
      const languageMap = {
        "zh": "Traditional Chinese",
        "en": "English"
      };
      const targetLanguage = languageMap[settings.language] || "Traditional Chinese";

      const response = await axios.post("/api/summarize", {
        text: text,
        model: settings.model,
        chunk_size_1: settings.chunk_size_1,
        chunk_size_2: settings.chunk_size_2,
        token_max: settings.token_max,
        temperature: settings.temperature,
        use_map: settings.strategy === "map",
        reduce_temple: settings.reduce_temple,
        map_temple: settings.map_temple,
        reduce_temperature: settings.reduce_temperature,
        test_mode: settings.test_mode,
        language: targetLanguage
      });
      setResult({
        summary: response.data.summary,
        processing_time: response.data.processing_time
      });
      setText("");
      setLoading(false);
    } catch (err) {
      console.error(err);
      alert("API Error: " + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header>
        <h1>MMSummary</h1>
        <nav className="navbar">
          <Link to="/" className={`nav-button ${location.pathname === '/' ? 'active' : ''}`}>{t.nav_tool} </Link>
          <Link to="/settings" className={`nav-button ${location.pathname === '/settings' ? 'active' : ''}`}>{t.nav_settings}</Link>
          <Link to="/history" className={`nav-button ${location.pathname === '/history' ? 'active' : ''}`}>{t.nav_history}</Link>
        </nav>
      </header>

      <main>
        <Routes>
          <Route path="/" element={
            <div className="summary-grid">
              <div className="left-panel">
                <div className="section">
                  <InputSection onTextLoad={handleTextChange} t={t} />
                  <div style={{ marginTop: '2rem' }}>
                    <button
                      className="action-button"
                      onClick={handleSummarize}
                      disabled={loading || !text}
                    >
                      {loading ? t.processing : t.startSummarize}
                    </button>
                  </div>
                </div>
              </div>
              <div className="right-panel">
                <ResultSection result={result} loading={loading} t={t} />
              </div>
            </div>
          } />

          <Route path="/settings" element={
            <div className="centered-view">
              <SettingsSection settings={settings} onChange={setSettings} t={t} />
            </div>
          } />

          <Route path="/history" element={
            <div className="centered-view">
              <HistoryPage t={t} />
            </div>
          } />
        </Routes>
      </main>
    </div>
  );
}

export default App;
