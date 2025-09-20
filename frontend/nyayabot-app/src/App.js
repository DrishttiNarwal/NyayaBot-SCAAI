import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Chat from './pages/Chat';
import Contact from './pages/Contact';
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
            <Link to="/Summarize">Summarize</Link>
            <Link to="/Contact">Contact</Link>
          </nav>
        </header>

        <main className="content">
          <Routes>
            <Route path="/" element={<Home />} />
            {/* Add other routes below */}
            <Route path="/chat" element={<Chat />} />
            <Route path="/summarize" element={<Summarize />} />
            <Route path="/contact" element={<Contact />} />
            {/* Add /services if you want */}
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
