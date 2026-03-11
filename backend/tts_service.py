import os
import torch
from TTS.api import TTS

# PyTorch 2.6+ changed torch.load default to weights_only=True, which breaks TTS.
# We monkey patch torch.load to always bypass it.
_original_load = torch.load
def safe_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_load(*args, **kwargs)
torch.load = safe_load

class XTTSv2Service:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Initializing XTTSv2 on {self.device}...")
        
        # Agree to Coqui TOS via environment variable to suppress prompts
        os.environ["COQUI_TOS_AGREED"] = "1"
        
        # Initialize the model
        # Using tts_models/multilingual/multi-dataset/xtts_v2
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)
        print("XTTSv2 model loaded successfully.")

    def generate_speech(self, text: str, speaker_wav: str, language: str, output_path: str):
        """
        Generates speech cloning the voice from speaker_wav.
        
        Args:
            text (str): The script to synthesize.
            speaker_wav (str): Path to the reference audio (.wav format works best).
            language (str): Language code (e.g., 'en', 'es', 'fr', 'de').
            output_path (str): The path to save the resulting .wav file.
        """
        print(f"Generating speech for text: '{text}' using reference: {speaker_wav}")
        # text, speaker_wav, language, file_path are the primary expected args
        self.tts.tts_to_file(
            text=text, 
            speaker_wav=speaker_wav, 
            language=language, 
            file_path=output_path
        )
        print(f"Saved generated speech to {output_path}")
