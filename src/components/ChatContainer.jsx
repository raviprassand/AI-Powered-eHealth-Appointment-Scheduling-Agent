// src/components/ChatContainer.jsx
import React, { useState, useRef, useEffect } from 'react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import AudioPlayer from './AudioPlayer';
import { sendMessage } from '../api/chat';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
const BACKEND_URL = API_BASE_URL.replace('/api/v1', '');

const ChatContainer = ({ patientId = null }) => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [currentAudio, setCurrentAudio] = useState(null);
  const [currentPatientId, setCurrentPatientId] = useState(patientId);
  
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (patientId !== currentPatientId) {
      setCurrentPatientId(patientId);
      setMessages([]); 
      setCurrentAudio(null);
    }
  }, [patientId, currentPatientId]);

  const handleSendMessage = async (text) => {
    if (!text.trim()) return;
    
    setMessages(prev => [...prev, { 
      role: 'user', 
      content: text,
      timestamp: new Date()
    }]);
    
    setLoading(true);
    
    try {
      const response = await sendMessage(text, currentPatientId);
      
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: response.message,
        formattedResponse: response.formatted_response,
        timestamp: new Date()
      }]);
      
      if (response.audio_url) {
        setTimeout(() => {
          setCurrentAudio(`${BACKEND_URL}${response.audio_url}`);
        }, 500);
      }
    } catch (error) {
      console.error('Error getting response:', error);
      let errorMessage = 'Sorry, I encountered an error processing your request.';
      setMessages(prev => [...prev, { role: 'assistant', content: errorMessage, timestamp: new Date() }]);
    } finally {
      setLoading(false);
    }
  };

  const handleVoiceInput = async (audioBlob) => {
    setMessages(prev => [...prev, { 
      role: 'user', 
      content: '🎤 Voice message...',
      isProcessing: true,
      timestamp: new Date()
    }]);
    
    setLoading(true);
    
    try {
      // Simulate transcription for now (or hook up real STT here)
      const transcription = "This is a simulated voice message"; 
      
      setMessages(prev => prev.map((msg, i) => 
        i === prev.length - 1 ? { ...msg, content: transcription, isProcessing: false } : msg
      ));
      
      const response = await sendMessage(transcription, currentPatientId);
      
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
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      {/* 1. Header */}
      <div className="chat-header">
        Health Informatics AI
      </div>

      {/* 2. Messages Area */}
      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="chat-empty-state" style={{ textAlign: 'center', marginTop: '40px' }}>
            {/* UPDATED: Generic Title */}
            <h1 style={{ color: '#0056b3' }}>Health Informatics AI</h1>
            <p>Select a common query or type your own below.</p>
            
            <div style={{ marginTop: '30px' }}>
              <button className="suggestion-btn" onClick={() => handleSendMessage("Show me treatment history")}>
                <i className="fa-solid fa-notes-medical" style={{marginRight: '10px', color: '#0056b3'}}></i>
                Show me treatment history
              </button>
              
              <button className="suggestion-btn" onClick={() => handleSendMessage("What are the pathology results?")}>
                <i className="fa-solid fa-microscope" style={{marginRight: '10px', color: '#0056b3'}}></i>
                What are the pathology results?
              </button>
              
              {/* REMOVED: The third button is gone now */}
            </div>
          </div>
        ) : (
          <>
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
              <div className="chat-message assistant-message">
                <div className="avatar">AI</div>
                <div className="message-content">
                  <div className="spinner"></div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* 3. Footer (Input & Audio) */}
      <div className="chat-footer">
        {currentAudio && (
          <div className="audio-player-wrapper" style={{ marginBottom: '15px' }}>
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
  );
};

export default ChatContainer;