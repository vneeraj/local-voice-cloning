import os
import torch
import torchaudio
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

def test():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_id = 'Qwen/Qwen3-TTS-12Hz-0.6B-Base'
    print(f"Testing Qwen3-TTS on {device}...")
    
    try:
        model = Qwen3TTSModel.from_pretrained(
            model_id, 
            dtype=torch.bfloat16 if device == "cuda" else torch.float32,
            device_map='auto' if device == "cuda" else None
        )
        print("Model loaded.")
        
        text = "Hello, this is a test of the emergency broadcast system."
        instruction = "Speak in a professional tone."
        
        print("Starting generation (voice design)...")
        wavs, sr = model.generate_voice_design(
            text=text,
            instruct=instruction,
            do_sample=True
        )
        print(f"Generation complete. sr={sr}, wavs type={type(wavs)}")
        
        audio = torch.from_numpy(wavs[0])
        if audio.ndim == 1:
            audio = audio.unsqueeze(0)
            
        torchaudio.save("test_output_design.wav", audio, sr)
        print("Saved test_output_design.wav")
        
        # Test cloning if we have a reference file
        # (Assuming we might have one from previous runs)
        ref_files = [f for f in os.listdir("uploads") if f.endswith(".wav")]
        if ref_files:
            ref_path = os.path.join("uploads", ref_files[0])
            print(f"Starting generation (voice clone) with {ref_path} ...")
            wavs, sr = model.generate_voice_clone(
                text=text,
                ref_audio=ref_path,
                do_sample=True
            )
            print(f"Cloning complete. sr={sr}")
            audio = torch.from_numpy(wavs[0])
            if audio.ndim == 1:
                audio = audio.unsqueeze(0)
            torchaudio.save("test_output_clone.wav", audio, sr)
            print("Saved test_output_clone.wav")
        else:
            print("No reference files found in 'uploads', skipping clone test.")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()
