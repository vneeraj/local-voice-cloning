from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import uuid
import json
from tts_service import CombinedTTSService
from typing import Optional, List
from pydantic import BaseModel
import subprocess
from fastapi.staticfiles import StaticFiles
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

# Serve static files from the frontend directory
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

# Directories for temp files and profiles
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
PROFILES_DIR = "profiles"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PROFILES_DIR, exist_ok=True)

# Pydantic models for AI Voice Studio
class VoiceParameters(BaseModel):
    pitch: float
    speed: float
    energy: float
    emotion: str
    intensity: float
    gender_hint: Optional[str] = "unspecified"

class VoiceProfile(BaseModel):
    name: str
    parameters: VoiceParameters
    instruction: Optional[str] = ""

# Initialize TTS Service (Combined: Qwen3-TTS & Kokoro)
tts_service = CombinedTTSService()

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
        # Use filters to clean up the reference audio:
        # 1. Highpass at 80Hz to remove rumble
        # 2. Lowpass at 8000Hz to remove high-frequency hiss
        # 3. Loudnorm (EBU R128) to stabilize volume
        # 4. Silenceremove to trim long silent gaps
        filters = "highpass=f=80, lowpass=f=8000, loudnorm, silenceremove=stop_periods=-1:stop_duration=1:stop_threshold=-50dB"
        
        cmd = [
            ffmpeg_exe,
            "-y",
            "-i", raw_file_path,
            "-af", filters,
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
            'ffmpeg_location': ffmpeg_exe,
            'format': 'bestaudio/best',
            'outtmpl': raw_file_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
            'quiet': True,
            'no_warnings': True,
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
        # Clean and standardize using ffmpeg filters for quality
        filters = "highpass=f=80, lowpass=f=8000, loudnorm, silenceremove=stop_periods=-1:stop_duration=1:stop_threshold=-50dB"
        cmd: list[str] = [
            str(ffmpeg_exe),
            "-y",
            "-i", str(downloaded_wav),
            "-af", filters,
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
    reference_id: str = Form(...),
    engine: str = Form("qwen")
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
        # Generate the audio blockingly
        tts_service.generate_cloned_speech(
            text=text,
            reference_wav=reference_path,
            output_path=output_path,
            engine=engine
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    return FileResponse(
        path=output_path, 
        media_type="audio/wav",
        filename=f"generated_{output_id}.wav"
    )

@app.post("/generate_ai_voice")
async def generate_ai_voice(
    text: str = Form(...),
    parameters_json: str = Form(...), # JSON string containing the VoiceParameters
    engine: str = Form("qwen")
):
    """Generate speech using tuned AI voice parameters."""
    try:
        params_dict = json.loads(parameters_json)
        # Validate using Pydantic
        params = VoiceParameters(**params_dict)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters JSON: {str(e)}")

    output_id = str(uuid.uuid4())
    output_path = os.path.join(OUTPUT_DIR, f"{output_id}.wav")
    
    try:
        tts_service.generate_ai_voice(
            text=text,
            params=params.dict(),
            output_path=output_path,
            engine=engine
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    return FileResponse(
        path=output_path, 
        media_type="audio/wav",
        filename=f"ai_voice_{output_id}.wav"
    )

@app.post("/save_profile")
async def save_profile(profile: VoiceProfile):
    """Save an AI voice profile as a JSON file."""
    safe_name = "".join([c for c in profile.name if c.isalnum() or c in (' ', '_', '-')]).rstrip()
    if not safe_name:
        raise HTTPException(status_code=400, detail="Invalid profile name")
    
    file_path = os.path.join(PROFILES_DIR, f"{safe_name}.json")
    try:
        with open(file_path, "w") as f:
            json.dump(profile.dict(), f, indent=2)
        return {"status": "success", "profile_name": profile.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/list_profiles")
async def list_profiles():
    """List all saved AI voice profiles."""
    profiles = []
    for filename in os.listdir(PROFILES_DIR):
        if filename.endswith(".json"):
            try:
                with open(os.path.join(PROFILES_DIR, filename), "r") as f:
                    data = json.load(f)
                    profiles.append(data)
            except:
                pass
    return profiles

app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
