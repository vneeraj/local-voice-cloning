import os
import torch
import torchaudio
import soundfile as sf
from qwen_tts_service import Qwen3TTSService

def verify():
    print("Starting verification of Qwen3TTSService...")
    service = Qwen3TTSService()
    
    text = "This is a verification test of the voice cloning service."
    
    # 1. Test Cloned Speech
    uploads = [f for f in os.listdir("uploads") if f.endswith(".wav")]
    if uploads:
        ref_wav = os.path.join("uploads", uploads[0])
        output_clone = "verify_clone.wav"
        print(f"Testing generate_cloned_speech with {ref_wav}...")
        try:
            service.generate_cloned_speech(text, ref_wav, output_clone)
            print(f"SUCCESS: Generated {output_clone}")
        except Exception as e:
            print(f"FAILED: generate_cloned_speech: {e}")
    else:
        print("SKIP: No reference files in 'uploads' to test cloning.")
        
    # 2. Test AI Voice Studio
    output_ai = "verify_ai.wav"
    params = {
        "pitch": 0.8,
        "speed": 0.3,
        "energy": 0.7,
        "emotion": "Energetic",
        "intensity": 0.9
    }
    print("Testing generate_ai_voice...")
    try:
        service.generate_ai_voice(text, params, output_ai)
        print(f"SUCCESS: Generated {output_ai}")
    except Exception as e:
        print(f"FAILED: generate_ai_voice: {e}")

if __name__ == "__main__":
    verify()
