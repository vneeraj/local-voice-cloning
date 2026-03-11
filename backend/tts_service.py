import os
import torch
import torchaudio
import soundfile as sf
import numpy as np
from TTS.api import TTS

# PyTorch 2.6+ changed torch.load default to weights_only=True, which breaks TTS.
# We monkey patch torch.load to always bypass it.
_original_load = torch.load
def safe_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_load(*args, **kwargs)
torch.load = safe_load

# OPTION 3: Bypass torchaudio's broken torchcodec dependency by monkey-patching it with soundfile
def sf_load(uri, frame_offset=0, num_frames=-1, normalize=True, channels_first=True, **kwargs):
    # soundfile.read returns (data, samplerate)
    # data is [time, channel] by default
    # If num_frames is -1, read all frames
    data, samplerate = sf.read(
        uri, 
        start=frame_offset, 
        frames=num_frames if num_frames != -1 else -1, 
        always_2d=True,
        dtype='float32'
    )
    
    # If not normalize, we would usually want int16 but torchaudio.load 
    # typically handles normalization if normalize=True. Let's force float32.
    tensor = torch.from_numpy(data)
    if channels_first:
        tensor = tensor.t()
    
    if not normalize:
        # If torchaudio expects unnormalized (which is rare for its load func),
        # we would need to scale it back, but usually normalize=True is default.
        pass

    return tensor, samplerate

def sf_save(uri, src, sample_rate, channels_first=True, **kwargs):
    if torch.is_tensor(src):
        data = src.cpu().numpy()
    else:
        data = src
    if channels_first and data.ndim > 1:
        data = data.T
    sf.write(uri, data, sample_rate)

# Apply the patches
torchaudio.load = sf_load
torchaudio.save = sf_save

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
