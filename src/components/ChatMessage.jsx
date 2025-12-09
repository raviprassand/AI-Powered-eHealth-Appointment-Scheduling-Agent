// src/components/ChatMessage.jsx
import React from 'react';
import FormattedResponse from './FormattedResponse';

const ChatMessage = ({ role, content, formattedResponse, isProcessing, timestamp }) => {
  const isUser = role === 'user';
  
  const formatTime = (dateObj) => {
    if (!dateObj) return '';
    return new Date(dateObj).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Logic: If we successfully detect a table in the content, we want to hide the raw text
  // so we don't show the same information twice.
  const shouldHideRawText = () => {
    if (formattedResponse) return true;
    if (content && content.includes('|') && content.split('\n').filter(l => l.includes('|')).length > 2) {
      return true;
    }
    return false;
  };

  return (
    <div className={`chat-message ${isUser ? 'user-message' : 'assistant-message'}`}>
      <div className="avatar">
        {isUser ? 'Dr' : <i className="fa-solid fa-user-doctor"></i>}
      </div>
      
      <div className="message-wrapper">
        <div className="message-content">
          
          {/* 1. Show Text (Only if it's NOT a table) */}
          {!shouldHideRawText() && (
            <div className="text-content">
              {content}
            </div>
          )}

          {/* 1b. If it IS a table, show a small intro text instead of the big ugly table text */}
          {shouldHideRawText() && !isUser && (
             <div className="text-content" style={{marginBottom: '10px'}}>
               Here are the requested patient records:
             </div>
          )}

          {/* 2. Render the Table (Pass BOTH structured data and text content) */}
          <FormattedResponse 
            formattedResponse={formattedResponse} 
            content={content} 
          />

          {/* 3. Processing Dots */}
          {isProcessing && (
             <div className="processing-indicator">
               <span className="dot"></span><span className="dot"></span><span className="dot"></span>
             </div>
          )}
        </div>
        
        <div className="message-timestamp">
          {formatTime(timestamp)}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;