import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Chat from './pages/Chat';
import Home from './pages/Home';  
import Summarize from './pages/Summarize';

function App() {
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
            {/* Add other routes below */}
            <Route path="/chat" element={<Chat />} />
            <Route path="/summarize" element={<Summarize />} />
            {/* Add /services if you want */}
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
