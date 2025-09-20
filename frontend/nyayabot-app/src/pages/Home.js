import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import './Home.css';

function Home() {
  const navigate = useNavigate();

  return (
    <div className="home-wrapper">
      {/* Hero */}
      <section className="hero">
        <div className="hero-text">
          <h1>Legal Guidance, Simplified.</h1>
          <p>NyayaBot delivers precise legal and welfare insights tailored to your region, age, and profile.</p>
          <button className="cta-btn" onClick={() => navigate('/chat')}>Start Chatting</button>
        </div>
      </section>

      {/* Services */}
      <section className="services" id="services">
        <div className="service-card card-left">
          <h3>Explore Schemes</h3>
          <p>Access government schemes that are relevant to you. Precision without noise.</p>
        </div>
        <div className="service-card card-center">
          <h3>Legal Queries</h3>
          <p>Receive straightforward answers to legal questions in a language you understand.</p>
        </div>
        <div className="service-card card-right">
          <h3>Personalized Help</h3>
          <p>Smart recommendations based on age, gender, and your state for maximum relevance.</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        &copy; 2025 NyayaBot. All rights reserved.
      </footer>
    </div>
  );
}

export default Home;
