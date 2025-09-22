import React, { useState, useRef } from 'react';
import { recordAudio } from '../services/audioService';

const ChatInput = ({ onSendMessage, disabled }) => {
  const [message, setMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const inputRef = useRef(null);
  const audioServiceRef = useRef(recordAudio());
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message);
      setMessage('');
    }
  };

  const handleVoiceClick = async () => {
    if (message.trim()) {
      // If there's text, act as send button
      handleSubmit({ preventDefault: () => {} });
    } else if (!isRecording) {
      // Start recording
      const started = await audioServiceRef.current.start();
      if (started) {
        setIsRecording(true);
      }
    } else {
      // Stop recording and process
      setIsRecording(false);
      setIsProcessing(true);
      
      try {
        // Get audio blob and transcribe
        const audioBlob = await audioServiceRef.current.stop();
        if (audioBlob) {
          const transcript = await audioServiceRef.current.transcribe(audioBlob);
          
          if (transcript && transcript.trim()) {
            console.log("Transcribed:", transcript);
            setMessage(transcript);
            
            // Auto-send after a small delay to let the user see what was transcribed
            setTimeout(() => {
              onSendMessage(transcript);
              setMessage('');
            }, 1000);
          } else {
            console.warn("No transcript received or empty transcript");
          }
        }
      } catch (error) {
        console.error("Error processing audio:", error);
      } finally {
        setIsProcessing(false);
      }
    }
  };

  const handleKeyDown = (e) => {
    // Submit on Enter (without shift for newline)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className={`chat-input-container ${message.trim() ? 'input-active' : ''}`}>
      <form className="chat-input-form" onSubmit={handleSubmit}>
        <textarea
          ref={inputRef}
          className="chat-input"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            isProcessing ? "Transcribing audio..." : 
            isRecording ? "Recording audio..." : 
            "Message the assistant..."
          }
          disabled={disabled || isRecording || isProcessing}
          rows={1}
        />
        <div className="input-button-container">
          <button 
            type="button" 
            onClick={handleVoiceClick}
            disabled={disabled || isProcessing}
            className={`input-button ${isRecording ? 'recording' : ''} ${isProcessing ? 'processing' : ''}`}
            aria-label={
              message.trim() ? "Send message" : 
              isRecording ? "Stop recording" : 
              isProcessing ? "Processing..." : 
              "Start recording"
            }
          >
            {message.trim() ? (
              <svg className="icon send-arrow" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
              </svg>
            ) : isProcessing ? (
              <div className="spinner"></div>
            ) : isRecording ? (
              <svg className="icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8z"/>
                <path d="M9 9h6v6H9z"/>
              </svg>
            ) : (
              <svg className="icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
                <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
              </svg>
            )}
          </button>
        </div>
      </form>
      {isRecording && (
        <div className="recording-indicator">
          <span className="recording-dot"></span>
          <span>Recording...</span>
        </div>
      )}
      {isProcessing && (
        <div className="processing-indicator">
          <span className="processing-dot"></span>
          <span>Transcribing with Gemini...</span>
        </div>
      )}
    </div>
  );
};

export default ChatInput;