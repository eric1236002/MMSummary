import React, { useState } from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import axios from 'axios';

import InputSection from './components/InputSection';
import SettingsSection from './pages/SettingsSection';
import ResultSection from './components/ResultSection';
import HistoryPage from './pages/HistoryPage';
import './App.css';

function App() {
  const [text, setText] = useState("");
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);
  const [settings, setSettings] = useState({
    model: "google/gemma-3-27b-it:free",
    chunk_size_1: 16000,
    chunk_size_2: 8000,
    token_max: 16000,
    temperature: 0.0,
    map: "map"
  });

  const location = useLocation();

  const handleTextChange = (newText) => {
    setText(newText);
  };

  const handleSummarize = async () => {
    if (!text) return;
    setLoading(true);
    try {
      const response = await axios.post("http://127.0.0.1:8001/summarize", {
        text: text,
        model: settings.model,
        chunk_size_1: settings.chunk_size_1,
        chunk_size_2: settings.chunk_size_2,
        token_max: settings.token_max,
        temperature: settings.temperature,
        use_map: settings.map === "map"
      });
      setSummary(response.data.summary);
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
          <Link to="/" className={`nav-button ${location.pathname === '/' ? 'active' : ''}`}>摘要工具 </Link>
          <Link to="/settings" className={`nav-button ${location.pathname === '/settings' ? 'active' : ''}`}>偏好設定</Link>
          <Link to="/history" className={`nav-button ${location.pathname === '/history' ? 'active' : ''}`}>歷史紀錄</Link>
        </nav>
      </header>

      <main>
        <Routes>
          <Route path="/" element={
            <div className="summary-grid">
              <div className="left-panel">
                <div className="section">
                  <InputSection onTextLoad={handleTextChange} />
                  <div style={{ marginTop: '2rem' }}>
                    <button
                      className="action-button"
                      onClick={handleSummarize}
                      disabled={loading || !text}
                    >
                      {loading ? "處理中..." : "開始摘要內容"}
                    </button>
                  </div>
                </div>
              </div>
              <div className="right-panel">
                <ResultSection content={summary} loading={loading} />
              </div>
            </div>
          } />

          <Route path="/settings" element={
            <div className="centered-view">
              <SettingsSection settings={settings} onChange={setSettings} />
            </div>
          } />

          <Route path="/history" element={
            <div className="centered-view">
              <HistoryPage />
            </div>
          } />
        </Routes>
      </main>
    </div>
  );
}

export default App;
