# backend/app/routers/chat.py - Cleaned up version
from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
import time
import os
import asyncio
import boto3
# from google import genai
from openai import OpenAI
from app.core.config import settings
from app.models.chat import ChatRequest, ChatResponse
from app.services.database_agent import DatabaseAgent
from app.services.llm_utilities import synthesize_speech, save_audio_file, transcribe_audio
from fastapi.responses import FileResponse
# from google.genai import types
import re
import json

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize clients
# genai_client = genai.Client(api_key=settings.GOOGLE_API_KEY)
openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

polly_client = boto3.client(
    'polly',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION
)


# Audio utility functions
async def wait_for_file(file_path, max_wait=5.0, check_interval=0.1):
    """Wait for file to exist and be fully written"""
    waited = 0
    while waited < max_wait:
        if os.path.exists(file_path):
            try:
                size = os.path.getsize(file_path)
                if size > 0:
                    # Wait a bit more to ensure write is complete
                    await asyncio.sleep(0.2)
                    # Check size again to make sure it's stable
                    new_size = os.path.getsize(file_path)
                    if new_size == size:
                        return True
            except OSError:
                pass  # File might still be being written
        await asyncio.sleep(check_interval)
        waited += check_interval
    return False

async def generate_audio_response_sync(text: str, output_path: str):
    """Generate audio synchronously and wait for completion"""
    try:
        print(f"Generating audio for text of length {len(text)}")
        
        # Generate audio synchronously
        synthesized_audio = synthesize_speech(polly_client, text)
        if synthesized_audio:
            # Save the file
            save_audio_file(synthesized_audio, output_path)
            
            # Wait for file to be fully written
            if await wait_for_file(output_path):
                print(f"Audio saved successfully to {output_path}")
                return True
            else:
                print(f"Failed to confirm audio file creation: {output_path}")
                return False
        else:
            print("Failed to synthesize speech - no audio data returned")
            return False
    except Exception as e:
        print(f"Error generating audio: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def prepare_text_for_audio(formatted_response, text_response, response_length):
    """Prepare appropriate text for audio generation"""
    if formatted_response.get('type') == 'table_data':
        # For table data, use the summary for audio
        text_for_audio = formatted_response.get('summary', 'Data retrieved from database')
        if len(text_for_audio) > 400:
            text_for_audio = text_for_audio[:400] + "... View the full results for more details."
        print("Using summary for audio (table data)")
    elif response_length <= 400:
        # Short response, use the full text for audio
        text_for_audio = text_response
        print("Using full response for audio")
    else:
        # Too long, use a summary message instead
        text_for_audio = "The response is too long for audio playback. Please read the text response for details."
        print("Response too long, using summary message for audio")
    
    return text_for_audio

# backend/app/routers/chat.py - Simplified version
@router.post("/send", response_model=ChatResponse)
async def send_message(request: ChatRequest, background_tasks: BackgroundTasks):
    # Use provided patient_id or fall back to environment default
    patient_id = request.patient_id or settings.DEFAULT_PATIENT_ID
    
    print(f"🏥 Processing request for Patient ID: {patient_id} {'(from URL)' if request.patient_id else '(default)'}")
    
    start_time = time.time()
    print(f"🕐 REQUEST START: {request.message[:50]}...")
    try:
        # Step 1: Setup
        setup_start = time.time()
        # patient_id = settings.DEFAULT_PATIENT_ID
        print(f"⚡ Setup completed in {(time.time() - setup_start)*1000:.0f}ms")
        
        # Step 2: Database Agent Call
        agent_start = time.time()
        print("🔍 Starting DatabaseAgent...")
        # database_agent = DatabaseAgent(patient_id, settings.GOOGLE_API_KEY, request.message)
        database_agent = DatabaseAgent(patient_id, settings.OPENAI_API_KEY, request.message)
        
        # Get response from database agent
        text_response, html_response = database_agent.create_agent()
        agent_duration = time.time() - agent_start
        print(f"🏃 DatabaseAgent completed in {agent_duration:.2f}s")
        
        # Step 3: Response Processing
        processing_start = time.time()
        response_length = len(text_response) if text_response else 0

        # Parse the JSON response directly from database agent
        try:
            formatted_response = json.loads(text_response)
            print(f"✅ Parsed JSON response: {formatted_response.get('type')}")
        except json.JSONDecodeError:
            print("❌ Not JSON, creating fallback text response")
            formatted_response = {
                "type": "text", 
                "content": text_response,
                "html": html_response
            }

        processing_duration = time.time() - processing_start
        print(f"🛠️ Response processing completed in {processing_duration:.2f}s")

        # Generate unique ID for audio file
        session_id = str(int(time.time() * 1000000))
        audio_filename = f"temp_audio_output_{session_id}.mp3"
        os.makedirs("audio", exist_ok=True)
        audio_path = f"audio/{audio_filename}"
        print(f"Audio path: {audio_path}")
        
        # Prepare text for audio
        text_for_audio = prepare_text_for_audio(formatted_response, text_response, response_length)
        
        # Step 4: Audio Generation
        audio_start = time.time()
        audio_success = await generate_audio_response_sync(text_for_audio, audio_path)
        audio_duration = time.time() - audio_start  
        
        # Only provide audio URL if generation was successful
        audio_url = f"/api/v1/chat/audio/{audio_filename}" if audio_success else None

        # # Step 4: Audio Generation (if enabled)
        # audio_start = time.time()
        # audio_url = None  # Skip audio for now to test speed
        # audio_duration = time.time() - audio_start
        # print(f"🔊 Audio processing in {audio_duration*1000:.0f}ms (skipped)")

        response = ChatResponse(
            message=text_response,
            formatted_response=formatted_response,
            audio_url=audio_url,
            patient_id=patient_id,
        )
        
        if audio_success:
            print(f"Returning response with audio URL: {audio_url}")
        else:
            print("Returning response without audio due to generation failure")

        total_duration = time.time() - start_time
        print(f"🏁 TOTAL REQUEST TIME: {total_duration:.2f}s")
        print(f"📊 Breakdown: Agent={agent_duration:.2f}s, Processing={processing_duration*1000:.0f}ms, Audio={audio_duration*1000:.0f}ms")
        
            
        return response
    
    except Exception as e:
        print(f"Error in send_message: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Remove the greeting detection functions - no longer needed

@router.get("/audio/{filename}")
async def get_audio(filename: str):
    audio_path = f"audio/{filename}"
    print(f"Looking for audio file at {audio_path}")
    
    if not os.path.exists(audio_path):
        print(f"File not found: {audio_path}")
        # List available files in the directory for debugging
        if os.path.exists("audio"):
            files = os.listdir("audio")
            print(f"Available files in audio directory: {files}")
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    print(f"Returning audio file: {audio_path}")
    return FileResponse(audio_path, media_type="audio/mp3")

@router.post("/transcribe", response_model=dict)
async def transcribe_voice(file: UploadFile = File(...)):
    try:
        print(f"Received audio file: {file.filename}")
        
        # Generate a unique filename
        session_id = str(int(time.time() * 1000000))
        temp_audio_path = f"audio/temp_audio_input_{session_id}.wav"
        
        # Ensure audio directory exists
        os.makedirs("audio", exist_ok=True)
        
        # Save the uploaded file
        with open(temp_audio_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Transcribe using Gemini
        print(f"Transcribing audio file at: {temp_audio_path}")
        transcript = transcribe_audio(
            openai_client=openai_client,
            # gemini_client=genai_client,
            audio_path=temp_audio_path,
            # mime_type="audio/wav"
        )
        print(f"Transcription result: {transcript}")
        
        # Clean up temporary file
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        
        return {"transcript": transcript}
        
    except Exception as e:
        print(f"Error transcribing audio: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))