// src/services/audioService.js
import RecordRTC from 'recordrtc';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
const API_URL = `${API_BASE_URL}/chat`;

export const recordAudio = () => {
  let recorder;
  let mediaStream;
  
  const start = async () => {
    try {
      // Store the stream reference directly so we can access it later
      mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      recorder = new RecordRTC(mediaStream, {
        type: 'audio',
        mimeType: 'audio/wav',
        recorderType: RecordRTC.StereoAudioRecorder,
        numberOfAudioChannels: 1,
        sampleRate: 44100,
        desiredSampRate: 16000
      });
      
      recorder.startRecording();
      return true;
    } catch (error) {
      console.error('Error starting recording:', error);
      return false;
    }
  };
  
  const stop = () => {
    return new Promise((resolve) => {
      if (!recorder) {
        resolve(null);
        return;
      }
      
      recorder.stopRecording(() => {
        const blob = recorder.getBlob();
        
        // Stop tracks using our saved mediaStream reference instead of internal recorder
        if (mediaStream) {
          try {
            mediaStream.getTracks().forEach(track => track.stop());
            console.log("Audio tracks stopped successfully");
          } catch (err) {
            console.warn("Error stopping media tracks:", err);
          }
        } else {
          console.warn("No mediaStream available to stop");
        }
        
        resolve(blob);
      });
    });
  };
  
  const transcribe = async (audioBlob) => {
    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.wav');
      
      const response = await axios.post(`${API_URL}/transcribe`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      return response.data.transcript;
    } catch (error) {
      console.error('Error transcribing audio:', error);
      throw error;
    }
  };
  
  return { start, stop, transcribe };
};