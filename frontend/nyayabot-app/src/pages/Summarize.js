import React from "react";
import "./Summarize.css";

function Summarize({ summary }) {
  // Function to render markdown text with bold formatting
  const renderMarkdown = (text) => {
    if (!text) return null;
    
    // Split text by **bold** patterns and render accordingly
    const parts = text.split(/(\*\*.*?\*\*)/g);
    
    return parts.map((part, index) => {
      // Check if this part is bold (starts and ends with **)
      if (part.startsWith('**') && part.endsWith('**')) {
        const boldText = part.slice(2, -2); // Remove ** from start and end
        return <strong key={index} className="highlight-text">{boldText}</strong>;
      }
      
      // Handle line breaks
      return part.split('\\n').map((line, lineIndex) => (
        <span key={`${index}-${lineIndex}`}>
          {line}
          {lineIndex < part.split('\\n').length - 1 && <br />}
        </span>
      ));
    });
  };

  return (
    <div className="summarize-container">
      <div className="summarize-header">
        <h2>Chat Summary</h2>
        <p className="summarize-subtext">
          Here's a summary of your conversation with NyayaBot.
        </p>
      </div>

      {summary ? (
        <div className="summary-box">
          <h3>Conversation Summary</h3>
          <div className="summary-content">
            {renderMarkdown(summary)}
          </div>
        </div>
      ) : (
        <div className="summary-box empty">
          <p>No summary available yet. Please have a conversation with NyayaBot and click "Summarize Chat".</p>
        </div>
      )}
    </div>
  );
}

export default Summarize;