import openai
from typing import Optional

# OpenAI Client for audio transcription
def transcribe_audio(openai_client, audio_path: str, model: str = "whisper-1", show_debug: bool = False):
    """
    Transcribe audio to text using OpenAI Whisper.
    
    Parameters:
    - openai_client: OpenAI client instance
    - audio_path: Path to the audio file
    - model: Whisper model to use (default: "whisper-1")
    - show_debug: Whether to show debug information
    
    Returns:
    - Transcribed text
    """
    try:
        with open(audio_path, "rb") as audio_file:
            transcript = openai_client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                response_format="text"
            )
        
        if show_debug:
            print(f"Transcription result: {transcript}")
        
        return transcript
    
    except Exception as e:
        print(f"Error transcribing audio with OpenAI: {str(e)}")
        return "Error: Could not transcribe audio"

def synthesize_speech(polly_client, text, voice_id="Ruth", engine="neural", output_format="mp3", text_type="text"):
    """
    Synthesize speech using Amazon Polly and return the audio stream.
    
    Parameters:
    - text: The text to convert to speech
    - voice_id: The voice to use (e.g., 'Joanna', 'Matthew')
    - engine: The engine to use ('standard', 'neural', or 'long-form')
    - output_format: The output format ('mp3', 'ogg_vorbis', or 'pcm')
    - text_type: The type of input text ('text' or 'ssml')
    
    Returns:
    - Audio stream
    """
    try:
        response = polly_client.synthesize_speech(
            Text=text,
            VoiceId=voice_id,
            Engine=engine,
            OutputFormat=output_format,
            TextType=text_type
        )
        return response['AudioStream'].read()
    except Exception as e:
        print(f"Error synthesizing speech: {str(e)}")
        return None

def save_audio_file(audio_data, file_path):
    """
    Save audio data to a file.
    
    Parameters:
    - audio_data: The audio data to save
    - file_path: The path where to save the file
    """
    if audio_data:
        if not file_path.endswith(('.mp3', '.wav', '.ogg')):
            print("Invalid file extension. Please use .mp3, .wav, or .ogg.")
            return None
        try:
            with open(file_path, 'wb') as file:
                file.write(audio_data)
            print(f"Audio saved to {file_path}")
            return True
        except Exception as e:
            print(f"Error saving audio file: {str(e)}")
            return False
    return False

# Optional: OpenAI TTS function (alternative to AWS Polly)
def synthesize_speech_openai(openai_client, text: str, voice: str = "alloy", model: str = "tts-1"):
    """
    Synthesize speech using OpenAI TTS (alternative to AWS Polly).
    
    Parameters:
    - openai_client: OpenAI client instance
    - text: The text to convert to speech
    - voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
    - model: TTS model to use (tts-1 or tts-1-hd)
    
    Returns:
    - Audio bytes
    """
    try:
        response = openai_client.audio.speech.create(
            model=model,
            voice=voice,
            input=text
        )
        return response.content
    except Exception as e:
        print(f"Error synthesizing speech with OpenAI: {str(e)}")
        return None