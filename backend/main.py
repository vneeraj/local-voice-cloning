from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import uuid
from tts_service import XTTSv2Service
from typing import Optional
import subprocess
import imageio_ffmpeg

# Get the static ffmpeg binary path
ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

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
        
    # Now sanitize and standard-convert it to PCM WAV using ffmpeg directly
    final_wav_path = os.path.join(UPLOAD_DIR, f"{file_id}_ref.wav")
    try:
        import logging
        logging.error(f"Executing ffmpeg: {ffmpeg_exe}")
        logging.error(f"Exists: {os.path.exists(ffmpeg_exe)}")
        cmd = [
            ffmpeg_exe,
            "-y",
            "-i", raw_file_path,
            "-ar", "22050",
            "-ac", "1",
            "-sample_fmt", "s16",
            final_wav_path
        ]
        logging.error(f"Cmd: {cmd}")
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)
        raise HTTPException(status_code=500, detail=f"Failed to process audio format: (make sure it's valid audio). Error: {err_msg}")
    except Exception as e:
        import traceback
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to process audio format. Error: {str(e)}")
        
    return {"status": "success", "reference_id": file_id, "file_path": final_wav_path}

@app.post("/upload_youtube")
async def upload_youtube(url: str = Form(...)):
    """Ingest reference audio from a YouTube video link."""
    file_id = str(uuid.uuid4())
    raw_file_template = os.path.join(UPLOAD_DIR, f"{file_id}_raw.%(ext)s")
    
    try:
        import yt_dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': raw_file_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # The postprocessor will output a .wav file.
            # We can find it by looking for file_id.
    except Exception as e:
        import traceback
        import logging
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to download from YouTube. Error: {str(e)}")

    # Locate the extracted wav file
    downloaded_wav = None
    for filename in os.listdir(UPLOAD_DIR):
        if filename.startswith(f"{file_id}_raw") and filename.endswith(".wav"):
            downloaded_wav = os.path.join(UPLOAD_DIR, filename)
            break
            
    if not downloaded_wav:
        raise HTTPException(status_code=500, detail="Failed to locate downloaded YouTube audio.")

    # Now standardize it using ffmpeg
    final_wav_path = os.path.join(UPLOAD_DIR, f"{file_id}_ref.wav")
    try:
        cmd: list[str] = [
            str(ffmpeg_exe),
            "-y",
            "-i", str(downloaded_wav),
            "-ar", "22050",
            "-ac", "1",
            "-sample_fmt", "s16",
            final_wav_path
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)
        raise HTTPException(status_code=500, detail=f"Failed to process YouTube audio: {err_msg}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process YouTube audio. Error: {str(e)}")
        
    return {"status": "success", "reference_id": file_id, "file_path": final_wav_path}

@app.post("/generate")
async def generate_speech(
    text: str = Form(...),
    reference_id: str = Form(...)
):
    """Generate speech using the uploaded reference voice."""
    
    # Find the processed reference file (the _ref.wav version)
    reference_path = os.path.join(UPLOAD_DIR, f"{reference_id}_ref.wav")
    if not os.path.exists(reference_path):
        # Fallback: look for any file with this reference_id
        reference_path = None
        for filename in os.listdir(UPLOAD_DIR):
            if filename.startswith(reference_id) and filename.endswith("_ref.wav"):
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
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
