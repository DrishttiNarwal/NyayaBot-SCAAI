import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Chat from './pages/Chat';
import Home from './pages/Home';  
import Summarize from './pages/Summarize';

function App() {
  const [chatHistory, setChatHistory] = useState([]);
  const [summary, setSummary] = useState("");

  // Ping backend health endpoint once on app load
  useEffect(() => {
    fetch("http://127.0.0.1:8000/health")
      .catch(err => console.error("Backend not reachable:", err));
  }, []);

  return (
    <Router>
      <div className="main-wrapper">
        <header className="navbar">
          <h1 className="title">NyayaBot</h1>
          <nav className="nav-links">
            <Link to="/">Home</Link>
            <Link to="/Chat">Chat</Link>
            <Link to="/Summarize">Summarize</Link>
          </nav>
        </header>

        <main className="content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/chat" element={<Chat chatHistory={chatHistory} setChatHistory={setChatHistory} setSummary={setSummary} />} />
            <Route path="/summarize" element={<Summarize summary={summary} />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;