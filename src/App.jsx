// App.jsx
import React from 'react';
import { BrowserRouter, Routes, Route, useParams } from 'react-router-dom';
import ChatContainer from './components/ChatContainer';
import './styles/main.css';

// Wrapper component to extract patient ID from URL
function ChatWithPatient() {
  const { patientId } = useParams();
  return <ChatContainer patientId={patientId} />;
}

function App() {
  return (
    <div className="app">
      <BrowserRouter>
        <Routes>
          <Route path="/patient/:patientId" element={<ChatWithPatient />} />
          <Route path="/" element={<ChatContainer />} /> {/* No patientId prop - will use backend default */}
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;