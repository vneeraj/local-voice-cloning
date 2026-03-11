import torch
from TTS.api import TTS
import os

# PyTorch 2.6+ changed torch.load default to weights_only=True, which breaks TTS.
_original_load = torch.load
def safe_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_load(*args, **kwargs)
torch.load = safe_load

print("Initializing TTS...")
try:
    os.environ["COQUI_TOS_AGREED"] = "1"
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    print("TTS initialized successfully.")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tts.to(device)
    print(f"Moved to {device}.")
except Exception as e:
    print(f"Error: {e}")
