// src/components/ChatContainer.jsx - Updated
import React, { useState, useRef, useEffect } from 'react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import AudioPlayer from './AudioPlayer';
import { sendMessage } from '../api/chat';
import './ChatContainer.css';

// Add this at the top after imports
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
const BACKEND_URL = API_BASE_URL.replace('/api/v1', ''); // Gets base backend URL



const ChatContainer = ({ patientId = null }) => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [currentAudio, setCurrentAudio] = useState(null);
  const [currentPatientId, setCurrentPatientId] = useState(patientId);
  
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (patientId !== currentPatientId) {
      setCurrentPatientId(patientId);
      setMessages([]); // Clear chat history when patient changes
      setCurrentAudio(null); // Clear any playing audio
    }
  }, [patientId, currentPatientId]);

  const handleSendMessage = async (text) => {
    if (!text.trim()) return;
    
    // Add user message with timestamp
    setMessages(prev => [...prev, { 
      role: 'user', 
      content: text,
      timestamp: new Date()
    }]);
    
    setLoading(true);
    
    try {
      // Send to API and get response
      const response = await sendMessage(text, currentPatientId);
      
      // Add assistant message
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: response.message,
        formattedResponse: response.formatted_response,
        timestamp: new Date()
      }]);
      
      // Set audio URL for playback if available
      if (response.audio_url) {
        setTimeout(() => {
          setCurrentAudio(`${BACKEND_URL}${response.audio_url}`);
        }, 500);
      }
    } catch (error) {
      console.error('Error getting response:', error);
      
      let errorMessage = 'Sorry, I encountered an error processing your request.';
      
      if (error.code === 'ECONNABORTED') {
        errorMessage = '⏰ Request timed out. Please try again with a shorter query.';
      } else if (error.response) {
        // Server responded with error status
        errorMessage = `Server error: ${error.response.status}. Please try again.`;
      } else if (error.request) {
        // Network error
        errorMessage = '🌐 Network error. Please check your connection and try again.';
      }
      
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: errorMessage,
        timestamp: new Date()
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleVoiceInput = async (audioBlob) => {
    // Add voice message UI indicator
    setMessages(prev => [...prev, { 
      role: 'user', 
      content: '🎤 Voice message...',
      isProcessing: true,
      timestamp: new Date()
    }]);
    
    setLoading(true);
    
    try {
      const transcription = "This is a simulated voice message";
      
      // Update the message with the transcription
      setMessages(prev => prev.map((msg, i) => 
        i === prev.length - 1 ? { ...msg, content: transcription, isProcessing: false } : msg
      ));
      
      // Now process like a regular message
      const response = await sendMessage(transcription,currentPatientId);
      
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: response.message,
        formattedResponse: response.formatted_response,
        timestamp: new Date()
      }]);
      
      if (response.audio_url) {
        setTimeout(() => {
          setCurrentAudio(`${BACKEND_URL}${response.audio_url}`);
        }, 1000);
      }
    } catch (error) {
      console.error('Error processing voice input:', error);
      setMessages(prev => prev.map((msg, i) => 
        i === prev.length - 1 ? { ...msg, content: "Voice processing failed", isProcessing: false } : msg
      ));
    } finally {
      setLoading(false);
    }
  };

  // Handle prompt card clicks
  const handlePromptClick = (promptText) => {
    handleSendMessage(promptText);
  };

  return (
    <div className="chatgpt-container">
      {/* Main chat area */}
      <div className="chat-main">
        {messages.length === 0 ? (
          // Initial empty state
          <div className="chat-empty-state">
            <div className="empty-state-content">
              <h1>Health Informatics AI</h1>
              <p>Ask me about patient data and medical information</p>
              <div className="example-prompts">
                <div 
                  className="prompt-card"
                  onClick={() => handlePromptClick("Show me treatment history")}
                >
                  <span>Show me treatment history</span>
                </div>
                <div 
                  className="prompt-card"
                  onClick={() => handlePromptClick("What are the pathology results?")}
                >
                  <span>What are the pathology results?</span>
                </div>
                <div 
                  className="prompt-card"
                  onClick={() => handlePromptClick("Get patient registration details")}
                >
                  <span>Get patient registration details</span>
                </div>
              </div>
            </div>
          </div>
        ) : (
          // Messages area
          <div className="chat-messages-area">
            <div className="messages-container">
              {messages.map((msg, index) => (
                <ChatMessage 
                  key={index}
                  role={msg.role}
                  content={msg.content}
                  formattedResponse={msg.formattedResponse}
                  isProcessing={msg.isProcessing}
                  timestamp={msg.timestamp}
                />
              ))}
              {loading && (
                <div className="message-wrapper assistant">
                  <div className="message-content assistant">
                    <div className="typing-indicator">
                      <div className="typing-dot"></div>
                      <div className="typing-dot"></div>
                      <div className="typing-dot"></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>
        )}
      </div>
      
      {/* Fixed input area */}
      <div className="chat-input-area">
        <div className="input-container">
          {currentAudio && (
            <div className="audio-player-wrapper">
              <AudioPlayer src={currentAudio} autoPlay={true} />
            </div>
          )}
          <ChatInput 
            onSendMessage={handleSendMessage} 
            onVoiceInput={handleVoiceInput}
            disabled={loading} 
          />
        </div>
      </div>
    </div>
  );
};

export default ChatContainer;