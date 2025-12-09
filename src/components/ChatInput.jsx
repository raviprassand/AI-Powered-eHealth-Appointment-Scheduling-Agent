// src/components/ChatInput.jsx
import React, { useState } from 'react';

const ChatInput = ({ onSendMessage, onVoiceInput, disabled }) => {
  const [text, setText] = useState('');
  const [isRecording, setIsRecording] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (text.trim() && !disabled) {
      onSendMessage(text);
      setText('');
    }
  };

  const handleMicClick = (e) => {
    e.preventDefault(); // Prevent form submission
    
    if (text.trim()) {
      // If there is text, this button acts as SEND
      handleSubmit(e);
    } else {
      // If no text, this button acts as RECORD
      if (!isRecording) {
        startRecording();
      } else {
        stopRecording();
      }
    }
  };

  const startRecording = () => {
    setIsRecording(true);
    // In a real app, you would start the MediaRecorder here
    console.log("Started recording...");
  };

  const stopRecording = () => {
    setIsRecording(false);
    // In a real app, you would get the blob here and pass it up
    onVoiceInput(new Blob()); 
  };

  return (
    <div className="chat-input-container">
      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          type="text"
          className="chat-input"
          placeholder="Message the assistant..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={disabled}
        />
        
        <div className="input-button-container">
          <button 
            type="button"
            className={`input-button ${isRecording ? 'recording' : ''}`}
            onClick={handleMicClick}
            disabled={disabled}
          >
            {/* Logic: Show Arrow if typing, Show Mic if empty */}
            {text.trim() ? (
              // Send Arrow Icon
              <svg viewBox="0 0 24 24" className="send-arrow" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 2L11 13" />
                <path d="M22 2L15 22L11 13L2 9L22 2Z" />
              </svg>
            ) : (
              // Microphone Icon
              isRecording ? (
                // Stop Icon (Square)
                <div style={{ width: '12px', height: '12px', background: 'white', borderRadius: '2px' }} />
              ) : (
                // Mic Icon
                <svg viewBox="0 0 24 24" className="icon" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                  <line x1="12" y1="19" x2="12" y2="23" />
                  <line x1="8" y1="23" x2="16" y2="23" />
                </svg>
              )
            )}
          </button>
        </div>
      </form>
      
      {isRecording && (
        <div className="recording-indicator">
          <div className="recording-dot"></div>
          Listening...
        </div>
      )}
    </div>
  );
};

export default ChatInput;