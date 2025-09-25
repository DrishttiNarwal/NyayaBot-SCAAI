import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { FaMicrophone, FaPaperPlane } from "react-icons/fa";
import "./Chat.css";

function Chat() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedState, setSelectedState] = useState("telangana");
  const chatEndRef = useRef(null);
  const navigate = useNavigate();

  const states = [
    "andhra-pradesh", "arunachal-pradesh", "assam", "bihar", "chhattisgarh",
    "goa", "gujarat", "haryana", "himachal-pradesh", "jharkhand", "karnataka",
    "kerala", "madhya-pradesh", "maharashtra", "manipur", "meghalaya", "mizoram",
    "nagaland", "odisha", "punjab", "rajasthan", "sikkim", "tamil-nadu",
    "telangana", "tripura", "uttar-pradesh", "uttarakhand", "west-bengal"
  ];

  // Scroll to the latest message whenever messages update
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Optional: Detect Hindi based on Devanagari characters (for logging/UI)
  const detectLanguage = (text) => {
    const hindiRegex = /[\u0900-\u097F]/;
    return hindiRegex.test(text) ? "hi" : "en";
  };

  const handleChat = async () => {
    if (!query.trim()) return;

    // Add user message
    setMessages((prev) => [...prev, { type: "user", text: query }]);
    setQuery("");
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query, state: selectedState }), // lang removed, backend auto-detects
      });

      const data = await res.json();
      setMessages((prev) => [...prev, { type: "bot", text: data.response }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { type: "bot", text: "NyayaBot couldn't respond. Please try again." },
      ]);
    }

    setLoading(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleChat();
    }
  };

  const handleVoiceClick = () => {
    alert("Voice input feature coming soon!");
  };

  // Render text with clickable links
  const renderText = (text) => {
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    return text.split(urlRegex).map((part, i) =>
      urlRegex.test(part) ? (
        <a key={i} href={part} target="_blank" rel="noopener noreferrer" className="chat-link">
          {part}
        </a>
      ) : (
        part
      )
    );
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>NyayaBot</h2>
        <p className="chat-subtext">
          Your trusted assistant for simplified government scheme information
        </p>
      </div>

      <div className="chat-controls">
        <label htmlFor="state">Select your state: </label>
        <select
          id="state"
          value={selectedState}
          onChange={(e) => setSelectedState(e.target.value)}
          className="state-dropdown"
        >
          {states.map((state) => (
            <option key={state} value={state}>
              {state.replace(/-/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
            </option>
          ))}
        </select>
      </div>

      <div className="chat-window">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`chat-bubble ${msg.type === "user" ? "user-bubble" : "bot-bubble"}`}
          >
            {renderText(msg.text)}
          </div>
        ))}
        {loading && (
          <div className="chat-bubble bot-bubble">
            <div className="typing-dots">
              <span></span><span></span><span></span>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      <div className="chat-input-row">
        <textarea
          className="chat-textarea"
          placeholder="Ask your question..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyPress}
        />
        <div className="input-icons">
          <button className="icon-button voice" onClick={handleVoiceClick}>
            <FaMicrophone />
          </button>
          <button className="icon-button send" onClick={handleChat} disabled={loading}>
            <FaPaperPlane />
          </button>
        </div>
      </div>

      <button className="chat-button summarize" onClick={() => navigate("/summarize")}>
        Summarize Chat
      </button>
    </div>
  );
}

export default Chat;
