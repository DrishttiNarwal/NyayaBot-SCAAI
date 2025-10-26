import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { FaMicrophone, FaPaperPlane } from "react-icons/fa";
import "./Chat.css";

function Chat({ chatHistory, setChatHistory, setSummary }) {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedState, setSelectedState] = useState("telangana");
  const [detailsShown, setDetailsShown] = useState(false);
  const chatEndRef = useRef(null);
  const navigate = useNavigate();
  const [listening, setListening] = useState(false);
  const socketRef = useRef(null);


  const states = [
    "andhra-pradesh", "arunachal-pradesh", "assam", "bihar", "chhattisgarh",
    "goa", "gujarat", "haryana", "himachal-pradesh", "jharkhand", "karnataka",
    "kerala", "madhya-pradesh", "maharashtra", "manipur", "meghalaya", "mizoram",
    "nagaland", "odisha", "punjab", "rajasthan", "sikkim", "tamil-nadu",
    "telangana", "tripura", "uttar-pradesh", "uttarakhand", "west-bengal"
  ];

  const stateDetails = {
    "andhra-pradesh": {
      name: "Andhra Pradesh",
      website: "http://www.ap.gov.in/",
      address: "AP Secretariat, Velagapudi, Amaravati - 522238",
      email: "cs@ap.gov.in",
    },
    "arunachal-pradesh": {
      name: "Arunachal Pradesh",
      website: "http://www.arunachalpradesh.gov.in/",
      address: "CM's Office, 6th Floor, Block -2, Itanagar – 791111",
      email: "cmoffice-arn@gov.in",
    },
    "assam": {
      name: "Assam",
      website: "https://assam.gov.in/",
      address: "CM Secretariat, Janata Bhawan, Dispur, Guwahati - 781006",
      email: "cm@assam.gov.in",
    },
    "bihar": {
      name: "Bihar",
      website: "http://state.bihar.gov.in/",
      address: "Main Secretariat, Patna, Bihar - 800015",
      email: "cs-bihar@nic.in",
    },
    "chhattisgarh": {
      name: "Chhattisgarh",
      website: "http://cgstate.gov.in/",
      address: "Mahanadi Bhawan, Mantralaya, Naya Raipur, Atal Nagar, Raipur",
      email: "cs-cg@nic.in",
    },
    "goa": {
      name: "Goa",
      website: "https://www.goa.gov.in/",
      address: "Secretariat, Porvorim, Bardez, Goa - 403521",
      email: "cs-goa@nic.in",
    },
    "gujarat": {
      name: "Gujarat",
      website: "https://gujaratindia.gov.in/",
      address: "Swarnim Sankul, Sachivalay, Sector 10, Gandhinagar",
      email: "cs-guj@nic.in",
    },
    "haryana": {
      name: "Haryana",
      website: "http://www.haryana.gov.in/",
      address: "Haryana Civil Secretariat, Sector-1, Chandigarh",
      email: "cs@hry.nic.in",
    },
    "himachal-pradesh": {
      name: "Himachal Pradesh",
      website: "https://himachal.gov.in/",
      address: "H.P. Secretariat, Shimla - 171002",
      email: "cs-hp@nic.in",
    },
    "jharkhand": {
      name: "Jharkhand",
      website: "http://www.jharkhand.gov.in/",
      address: "Project Building, Dhurwa, Ranchi - 834004",
      email: "cs-jharkhand@nic.in",
    },
    "karnataka": {
      name: "Karnataka",
      website: "https://www.karnataka.gov.in/",
      address: "Room No. 320, 3rd floor, Vidhana Soudha, Bengaluru - 560001",
      email: "cs@karnataka.gov.in",
    },
    "kerala": {
      name: "Kerala",
      website: "https://kerala.gov.in/",
      address: "Government Secretariat, Thiruvananthapuram - 695001",
      email: "chiefsecy@kerala.gov.in",
    },
    "madhya-pradesh": {
      name: "Madhya Pradesh",
      website: "http://www.mp.gov.in/",
      address: "Mantralaya, Vallabh Bhawan, Bhopal - 462004",
      email: "cs@mp.gov.in",
    },
    "maharashtra": {
      name: "Maharashtra",
      website: "https://www.maharashtra.gov.in/",
      address: "Mantralaya, Madam Cama Road, Mumbai - 400032",
      email: "chiefsecretary@maharashtra.gov.in",
    },
    "manipur": {
      name: "Manipur",
      website: "https://www.manipur.gov.in/",
      address: "South Block, Old Secretariat, Imphal - 795001",
      email: "cs-manipur@nic.in",
    },
    "meghalaya": {
      name: "Meghalaya",
      website: "http://meghalaya.gov.in/",
      address: "Main Secretariat Building, Rilang Building, Shillong - 793001",
      email: "cso-meg@nic.in",
    },
    "mizoram": {
      name: "Mizoram",
      website: "https://mizoram.gov.in/",
      address: "New Secretariat Complex, Khatla, Aizawl - 796001",
      email: "cs-mizoram@nic.in",
    },
    "nagaland": {
      name: "Nagaland",
      website: "https://www.nagaland.gov.in/",
      address: "Civil Secretariat, Kohima - 797004",
      email: "csnagaland@nagaland.gov.in",
    },
    "odisha": {
      name: "Odisha",
      website: "https://odisha.gov.in/",
      address: "Lok Seva Bhawan, Sachivalaya Marg, Bhubaneswar - 751001",
      email: "csori@nic.in",
    },
    "punjab": {
      name: "Punjab",
      website: "http://punjab.gov.in/",
      address: "Punjab Civil Secretariat, Sector 1, Chandigarh",
      email: "cs@punjab.gov.in",
    },
    "rajasthan": {
      name: "Rajasthan",
      website: "https://rajasthan.gov.in/",
      address: "Secretariat, Janpath, Jaipur - 302005",
      email: "cs@rajasthan.gov.in",
    },
    "sikkim": {
      name: "Sikkim",
      website: "https://www.sikkim.gov.in/",
      address: "Tashiling Secretariat, Gangtok - 737101",
      email: "cs-sikkim@nic.in",
    },
    "tamil-nadu": {
      name: "Tamil Nadu",
      website: "https://www.tn.gov.in/",
      address: "Secretariat, Fort St. George, Chennai - 600009",
      email: "cs@tn.gov.in",
    },
    "telangana": {
      name: "Telangana",
      website: "https://www.telangana.gov.in/",
      address: "Dr. B. R. Ambedkar Telangana State Secretariat, Hyderabad",
      email: "cs@telangana.gov.in",
    },
    "tripura": {
      name: "Tripura",
      website: "https://tripura.gov.in/",
      address: "New Secretariat Complex, P.O. Secretariat, Agartala - 799010",
      email: "cs-tripura@nic.in",
    },
    "uttar-pradesh": {
      name: "Uttar Pradesh",
      website: "http://up.gov.in/",
      address: "Lok Bhawan, Vidhan Sabha Marg, Lucknow - 226001",
      email: "csup@nic.in",
    },
    "uttarakhand": {
      name: "Uttarakhand",
      website: "https://uk.gov.in/",
      address: "4 Subhash Road, Uttarakhand Secretariat, Dehradun - 248001",
      email: "cs-uttarakhand@nic.in",
    },
    "west-bengal": {
      name: "West Bengal",
      website: "https://wb.gov.in/",
      address: "Nabanna, 325, Sarat Chatterjee Road, Howrah - 711102",
      email: "cs-westbengal@nic.in",
    }
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    setDetailsShown(false); // Reset when state changes
  }, [selectedState]);

  const handleChat = async (messageText) => {
    const userMessage = messageText || query;
    if (!userMessage.trim()) return;

    setMessages((prev) => [...prev, { type: "user", text: userMessage }]);
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
      setChatHistory((prev) => [...prev, { role: "bot", content: botResponse }]);

      if (!detailsShown && stateDetails[selectedState]) {
        const details = stateDetails[selectedState];
        const detailsMessage = `
State: ${details.name}
Website: ${details.website}
Address: ${details.address}
Email: ${details.email}
        `;
        setMessages((prev) => [...prev, { type: "bot", text: detailsMessage }]);
        setChatHistory((prev) => [...prev, { role: "bot", content: detailsMessage }]);
        setDetailsShown(true);
      }
    } catch (err) {
      const errorMessage = "NyayaBot couldn't respond. Please try again.";
      setMessages((prev) => [...prev, { type: "bot", text: errorMessage }]);
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
    if (listening) {
      if (socketRef.current) {
        socketRef.current.close();
      }
      return;
    }

    setListening(true);
    const ws = new WebSocket(`ws://localhost:8000/ws/voice-command`);
    socketRef.current = ws;

    ws.onopen = () => console.log('WebSocket connection opened for voice');

    ws.onmessage = (event) => {
      const message = event.data;
      if (message.startsWith("You said:")) {
        const spokenText = message.substring(9).trim();
        handleChat(spokenText);
      } else if (message.startsWith("Error:")) {
        console.error("Voice recognition error:", message);
        alert(message);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket connection closed for voice');
      setListening(false);
      socketRef.current = null;
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setListening(false);
      socketRef.current = null;
    };
  };

  const handleSummarize = async () => {
    if (chatHistory.length === 0) {
      alert("No chat history to summarize.");
      return;
    }
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
      setSummary("Failed to generate summary.");
      console.error(err);
    }
  };

  const renderText = (text) => {
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    return text.split(urlRegex).map((part, i) =>
      urlRegex.test(part) ? (
        <a key={i} href={part} target="_blank" rel="noopener noreferrer" className="chat-link">
          {part}
        </a>
      ) : part
    );
  };

  return (
    <div className="chat-layout">
      <aside className="sidebar">
        <h3 className="sidebar-title">Select Your State</h3>
        <select
          value={selectedState}
          onChange={(e) => setSelectedState(e.target.value)}
          className="state-dropdown full-width"
          size={10}
        >
          {states.map((state) => (
            <option key={state} value={state}>
              {state.replace(/-/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
            </option>
          ))}
        </select>
      </aside>

      <div className="chat-main">
        <div className="chat-header">
          <h2>NyayaBot</h2>
          <p className="chat-subtext">
            Your trusted assistant for simplified government scheme information
          </p>
        </div>

        <div className="chat-window">
          {messages.map((msg, idx) => (
            <div key={idx} className={`chat-bubble ${msg.type === "user" ? "user-bubble" : "bot-bubble"}`}>
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
            <button className={`icon-button voice ${listening ? 'listening' : ''}`} onClick={handleVoiceClick}><FaMicrophone /></button>
            <button className="icon-button send" onClick={handleChat} disabled={loading}><FaPaperPlane /></button>
          </div>
        </div>

        <button className="chat-button summarize" onClick={handleSummarize}>Summarize Chat</button>

        <div className="chat-disclaimer">
          <p><strong>Disclaimer:</strong> NyayaBot provides simplified information and may not always be fully accurate. Please refer to official government websites for latest and complete information.</p>
        </div>
      </div>
    </div>
  );
}

export default Chat;
