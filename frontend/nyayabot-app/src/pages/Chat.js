import React, { useState, useEffect, useRef } from "react";
import "./Chat.css";

function Chat() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedState, setSelectedState] = useState("telangana"); // Default state
  const chatEndRef = useRef(null);

  const states = [
    "andhra-pradesh", "arunachal-pradesh", "assam", "bihar", "chhattisgarh",
    "goa", "gujarat", "haryana", "himachal-pradesh", "jharkhand", "karnataka",
    "kerala", "madhya-pradesh", "maharashtra", "manipur", "meghalaya", "mizoram",
    "nagaland", "odisha", "punjab", "rajasthan", "sikkim", "tamil-nadu",
    "telangana", "tripura", "uttar-pradesh", "uttarakhand", "west-bengal"
  ];

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleChat = async () => {
    if (!query.trim()) return;

    setMessages((prev) => [...prev, { type: "user", text: query }]);
    setQuery("");
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query,
          state: selectedState,
        }),
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
        <button className="chat-button" onClick={handleChat} disabled={loading}>
          {loading ? "..." : "Send"}
        </button>
        <button className="chat-button reset" onClick={() => setMessages([])}>
          Clear
        </button>
      </div>
    </div>
  );
}

export default Chat;
