from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import uuid
from tts_service import XTTSv2Service
from typing import Optional
from pydub import AudioSegment
import imageio_ffmpeg as ffmpeg

# Configure pydub to use the static ffmpeg binary
AudioSegment.converter = ffmpeg.get_ffmpeg_exe()

app = FastAPI(title="Local Voice Cloning API")

# Setup CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories for temp files
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Initialize TTS Service
tts_service = XTTSv2Service()

@app.post("/upload_reference")
async def upload_reference(audio: UploadFile = File(...)):
    """Upload a reference audio file for voice cloning."""
    if not audio.filename.endswith((".wav", ".mp3", ".ogg", ".flac")):
        raise HTTPException(status_code=400, detail="Unsupported audio format")
    
    # Save the file with a unique ID securely
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(audio.filename)[1]
    raw_file_path = os.path.join(UPLOAD_DIR, f"{file_id}_raw{ext}")
    
    # Save the raw uploaded file first
    with open(raw_file_path, "wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)
        
    # Now sanitize and standard-convert it to PCM WAV using pydub
    final_wav_path = os.path.join(UPLOAD_DIR, f"{file_id}_ref.wav")
    try:
        audio_segment = AudioSegment.from_file(raw_file_path)
        # Force 16-bit PCM, mono, 22050Hz (Standard clean audio for Coqui)
        audio_segment = audio_segment.set_frame_rate(22050).set_channels(1).set_sample_width(2)
        audio_segment.export(final_wav_path, format="wav")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process audio format: (make sure it's valid audio). Error: {str(e)}")
        
    return {"status": "success", "reference_id": file_id, "file_path": final_wav_path}

@app.post("/generate")
async def generate_speech(
    text: str = Form(...),
    reference_id: str = Form(...)
):
    """Generate speech using the uploaded reference voice."""
    
    # Find the reference file
    reference_path = None
    for filename in os.listdir(UPLOAD_DIR):
        if filename.startswith(reference_id):
            reference_path = os.path.join(UPLOAD_DIR, filename)
            break
            
    if not reference_path:
        raise HTTPException(status_code=404, detail="Reference voice not found")
        
    # Output file
    output_id = str(uuid.uuid4())
    output_path = os.path.join(OUTPUT_DIR, f"{output_id}.wav")
    
    try:
        # Generate the audio blockingly (in production you'd use a background task or queue)
        tts_service.generate_speech(
            text=text,
            speaker_wav=reference_path,
            language="en",
            output_path=output_path
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    return FileResponse(
        path=output_path, 
        media_type="audio/wav",
        filename=f"generated_{output_id}.wav"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
