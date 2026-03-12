import os
import torch
import torchaudio
import numpy as np
import soundfile as sf
from qwen_tts import Qwen3TTSModel, Qwen3TTSTokenizer

# Standard monkey-patch for torchaudio since torchcodec is broken on this system
def sf_load(uri, frame_offset=0, num_frames=-1, normalize=True, channels_first=True, **kwargs):
    data, samplerate = sf.read(
        uri, 
        start=frame_offset, 
        frames=num_frames if num_frames != -1 else -1, 
        always_2d=True,
        dtype='float32'
    )
    tensor = torch.from_numpy(data)
    if channels_first:
        tensor = tensor.t()
    return tensor, samplerate

def sf_save(uri, src, sample_rate, channels_first=True, **kwargs):
    if torch.is_tensor(src):
        data = src.cpu().numpy()
    else:
        data = src
    if channels_first and data.ndim > 1:
        data = data.T
    sf.write(uri, data, sample_rate)

torchaudio.load = sf_load
torchaudio.save = sf_save

class Qwen3TTSService:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_id = 'Qwen/Qwen3-TTS-12Hz-0.6B-Base'
        print(f"Initializing Qwen3-TTS on {self.device}...")
        
        # Load model using specialized Qwen3TTSModel class
        # This handles the custom architecture correctly
        self.model = Qwen3TTSModel.from_pretrained(
            self.model_id, 
            dtype=torch.bfloat16 if self.device == "cuda" else torch.float32,
            device_map='auto' if self.device == "cuda" else None
        )
        
        print("Qwen3-TTS model loaded successfully.")

    def _map_parameters_to_instruction(self, params: dict) -> str:
        """Maps slider values and emotion to a natural language instruction."""
        speed = params.get("speed", 0.5)
        pitch = params.get("pitch", 0.5)
        energy = params.get("energy", 0.5)
        emotion = params.get("emotion", "Professional")
        intensity = params.get("intensity", 0.5)
        
        inst = f"Speak in a {emotion.lower()} tone. "
        
        if speed > 0.7: inst += "Speak quickly. "
        elif speed < 0.3: inst += "Speak slowly. "
        
        if pitch > 0.7: inst += "Use a high-pitched voice. "
        elif pitch < 0.3: inst += "Use a deep, low-pitched voice. "
        
        if energy > 0.7: inst += "Be very energetic and loud. "
        elif energy < 0.3: inst += "Speak softly and calmly. "
        
        if intensity > 0.7: inst += f"The {emotion.lower()} emotion should be very intense. "
        
        return inst.strip()

    def generate_cloned_speech(self, text: str, reference_wav: str, output_path: str):
        """Generates speech cloning the reference voice."""
        print(f"Cloning voice from: {reference_wav}")
        try:
            # Fix: parameter name is ref_audio, not speaker_audio
            # Fix: x_vector_only_mode=True is required if no transcription (ref_text) is provided
            wavs, sr = self.model.generate_voice_clone(
                text=text,
                ref_audio=reference_wav,
                x_vector_only_mode=True,
                do_sample=True
            )
            # Take the first sample from the batch
            audio = torch.from_numpy(wavs[0])
            if audio.ndim == 1:
                audio = audio.unsqueeze(0)
                
            torchaudio.save(output_path, audio, sr)
            print(f"Generated cloned speech to {output_path}")
        except Exception as e:
            print(f"Error in cloning: {e}")
            raise

    def generate_ai_voice(self, text: str, params: dict, output_path: str):
        """Generates speech based on AI voice parameters (instructions)."""
        instruction = self._map_parameters_to_instruction(params)
        print(f"Generating AI Voice with instruction: {instruction}")
        
        try:
            # Check model compatibility
            model_type = getattr(self.model.model, "tts_model_type", "base")
            
            if model_type == "base":
                # Base model doesn't support 'instruct' or 'custom_voice' naturally.
                # Fallback: Use a default reference voice and perform cloning.
                # Look for a default reference in the uploads or profiles directory.
                default_ref = os.path.join("uploads", "NV_reference.wav")
                if not os.path.exists(default_ref):
                    # Fallback to any file in uploads if default is missing
                    refs = [f for f in os.listdir("uploads") if f.endswith(".wav")]
                    if refs:
                        default_ref = os.path.join("uploads", refs[0])
                    else:
                        raise ValueError("No reference voice available for Base model fallback. Please upload a voice first.")
                
                print(f"Base model detected. Using {default_ref} as fallback reference for AI Voice Studio.")
                wavs, sr = self.model.generate_voice_clone(
                    text=text,
                    ref_audio=default_ref,
                    x_vector_only_mode=True,
                    do_sample=True
                )
            elif model_type == "voice_design":
                wavs, sr = self.model.generate_voice_design(
                    text=text,
                    instruct=instruction,
                    do_sample=True
                )
            else: # custom_voice or other
                # Try to get a valid speaker
                supported_speakers = self.model.get_supported_speakers()
                speaker = supported_speakers[0] if supported_speakers else "female"
                
                wavs, sr = self.model.generate_custom_voice(
                    text=text,
                    speaker=speaker,
                    instruct=instruction,
                    do_sample=True
                )
                
            # Take the first sample from the batch
            audio = torch.from_numpy(wavs[0])
            if audio.ndim == 1:
                audio = audio.unsqueeze(0)
                
            torchaudio.save(output_path, audio, sr)
            print(f"Generated AI voice to {output_path}")
        except Exception as e:
            print(f"Error in AI Voice generation: {e}")
            raise
