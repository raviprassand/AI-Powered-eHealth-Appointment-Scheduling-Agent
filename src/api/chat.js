import axios from 'axios';

// For Cloud Run deployment - we'll update this with actual backend URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 
  'http://localhost:8000/api/v1'; // Default for local development

console.log('Environment:', import.meta.env.MODE);
console.log('API Base URL:', API_BASE_URL);

export const sendMessage = async (message, patientId = null) => {
  try {
    console.log('Sending request to:', `${API_BASE_URL}/chat/send`);
    console.log('Patient ID:', patientId || 'using backend default');

    const requestBody = {
      message: message
    };

    // Only include patient_id if explicitly provided
    if (patientId) {
      requestBody.patient_id = String(patientId);
    }
    
    const response = await axios.post(`${API_BASE_URL}/chat/send`, requestBody, {
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 60000 // 60 second timeout for Cloud Run
    });

    return response.data;
  } catch (error) {
    console.error('Error sending message:', error);
    console.error('Request config:', error.config);
    throw error;
  }
};