// src/components/ChatMessage.jsx
import React from 'react';
import FormattedResponse from './FormattedResponse';
import './ChatMessage.css';

const ChatMessage = ({ role, content, formattedResponse, isProcessing, timestamp }) => {
  const formatTime = (date) => {
    if (!date) return '';
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false 
    });
  };

  return (
    <div className={`message-wrapper ${role}`}>
      <div className={`message-content ${role}`}>
        {isProcessing ? (
          <div className="processing-message">
            <span>🎤 Processing voice...</span>
          </div>
        ) : (
          <div className="message-body">
            {formattedResponse ? (
              <FormattedResponse response={formattedResponse} />
            ) : (
              <div className="message-text">{content}</div>
            )}
          </div>
        )}
        <div className="message-timestamp">
          {formatTime(timestamp)}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;