import React from "react";
import "./Summarize.css";

function Summarize({ summary }) {
  return (
    <div className="summarize-container">
      <div className="summarize-header">
        <h2>NyayaBot Recommendation</h2>
        <p className="summarize-subtext">
          Based on your chat interaction, here is the recommended scheme.
        </p>
      </div>

      {summary ? (
        <div className="summary-box">
          <h3>Recommended Scheme</h3>
          <p>{summary}</p>
        </div>
      ) : (
        <div className="summary-box empty">
          <p>No recommendation available yet. Interact with NyayaBot to get recommendations.</p>
        </div>
      )}
    </div>
  );
}

export default Summarize;
