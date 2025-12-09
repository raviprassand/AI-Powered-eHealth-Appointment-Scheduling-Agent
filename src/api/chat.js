// src/api/chat.js
const API_BASE_URL = "http://localhost:8000/api/v1";

export async function sendMessage(message, patientId = null) {
  try {
    console.log("Sending request to:", `${API_BASE_URL}/chat/send`);

    const response = await fetch(`${API_BASE_URL}/chat/send`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: message,
        patient_id: patientId,
      }),
    });

    if (!response.ok) {
      throw new Error(`Server responded with ${response.status}`);
    }

    const data = await response.json();
    console.log("✅ API Response:", data);
    return data;

  } catch (error) {
    console.error("❌ Error in sendMessage:", error);
    throw error;
  }
}
