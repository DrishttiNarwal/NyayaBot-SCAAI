import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { FaMicrophone, FaPaperPlane } from "react-icons/fa";
import "./Chat.css";

function Chat({ chatHistory, setChatHistory, setSummary }) {
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

  // Scroll to latest message
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleChat = async () => {
    if (!query.trim()) return;

    const userMessage = query;
    setMessages((prev) => [...prev, { type: "user", text: userMessage }]);
    
    // Add user message to chat history
    setChatHistory((prev) => [...prev, { role: "user", content: userMessage }]);
    
    setQuery("");
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userMessage, state: selectedState }),
      });

      const data = await res.json();
      const botResponse = data.response;
      
      setMessages((prev) => [...prev, { type: "bot", text: botResponse }]);
      
      // Add bot response to chat history
      setChatHistory((prev) => [...prev, { role: "bot", content: botResponse }]);
      
    } catch (err) {
      const errorMessage = "NyayaBot couldn't respond. Please try again.";
      setMessages((prev) => [...prev, { type: "bot", text: errorMessage }]);
      
      // Add error message to chat history
      setChatHistory((prev) => [...prev, { role: "bot", content: errorMessage }]);
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

  const handleSummarize = async () => {
    if (chatHistory.length === 0) {
      alert("No chat history to summarize. Please have a conversation first.");
      return;
    }
    
    // Show loading state and navigate immediately
    setSummary("Loading summary...");
    navigate("/summarize");
    
    try {
      const res = await fetch("http://localhost:8000/summarize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chat_history: chatHistory }),
      });
      
      const data = await res.json();
      setSummary(data.summary);
      
    } catch (err) {
      setSummary("Failed to generate summary. Please try again.");
      console.error("Summarization error:", err);
    }
  };

  // Render clickable links
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
    <div className="chat-layout">
      {/* Sidebar for state selection */}
      <aside className="sidebar">
        <h3 className="sidebar-title">Select Your State</h3>
        <select
          value={selectedState}
          onChange={(e) => setSelectedState(e.target.value)}
          className="state-dropdown full-width"
          size={10} // show multiple states at once
        >
          {states.map((state) => (
            <option key={state} value={state}>
              {state.replace(/-/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
            </option>
          ))}
        </select>
      </aside>

      {/* Main chat section */}
      <div className="chat-main">
        {/* Header */}
        <div className="chat-header">
          <h2>NyayaBot</h2>
          <p className="chat-subtext">
            Your trusted assistant for simplified government scheme information
          </p>
        </div>

        {/* Chat Window */}
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

        {/* Input Row */}
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

        {/* Summarize Button */}
        <button className="chat-button summarize" onClick={handleSummarize}>
          Summarize Chat
        </button>

        {/* Disclaimer */}
        <div className="chat-disclaimer">
          <p>
            <strong>Disclaimer:</strong> NyayaBot provides simplified information and may not always be fully 
            accurate. Please refer to the provided official government website links and contact details for 
            complete information.
          </p>
        </div>
      </div>
    </div>
  );
}

export default Chat;
