document.addEventListener('DOMContentLoaded', () => {
    const API_BASE = "http://127.0.0.1:8000";

    // UI Elements
    const recordBtn = document.getElementById('record-btn');
    const stopBtn = document.getElementById('stop-btn');
    const recordingStatus = document.getElementById('recording-status');
    const visualizer = document.getElementById('visualizer');
    const bars = document.querySelectorAll('.bar');
    
    const referencePlayerContainer = document.getElementById('reference-player-container');
    const referenceAudio = document.getElementById('reference-audio');
    
    const generateBtn = document.getElementById('generate-btn');
    const scriptInput = document.getElementById('script-input');
    const generationStatus = document.getElementById('generation-status');
    
    const loader = document.getElementById('loader');
    const resultContainer = document.getElementById('result-container');
    const resultAudio = document.getElementById('result-audio');
    const downloadBtn = document.getElementById('download-btn');

    const fileInput = document.getElementById('file-input');
    const youtubeInput = document.getElementById('youtube-input');
    const youtubeBtn = document.getElementById('youtube-btn');

    // Tab Logic
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.add('hidden'));
            
            btn.classList.add('active');
            document.getElementById(btn.dataset.target).classList.remove('hidden');
        });
    });

    // State
    let mediaRecorder;
    let audioChunks = [];
    let audioContext;
    let analyser;
    let animationId;
    let referenceId = null;

    // --- Audio Recording Logic ---
    recordBtn.addEventListener('click', async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            // Setup Visualizer
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const source = audioContext.createMediaStreamSource(stream);
            analyser = audioContext.createAnalyser();
            analyser.fftSize = 64;
            source.connect(analyser);
            
            visualizer.classList.add('active');
            updateVisualizer();

            // Setup Recorder
            // Try to use a format backend supports
            let options = { mimeType: 'audio/webm;codecs=opus' };
            if (MediaRecorder.isTypeSupported('audio/mp4')) {
                options = { mimeType: 'audio/mp4' };
            }

            mediaRecorder = new MediaRecorder(stream, options);
            audioChunks = [];

            mediaRecorder.ondataavailable = event => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                cancelAnimationFrame(animationId);
                visualizer.classList.remove('active');
                if (audioContext && audioContext.state !== 'closed') {
                    audioContext.close();
                }
                
                // Stop all tracks to release mic
                stream.getTracks().forEach(track => track.stop());

                // Reset visualizer bars
                bars.forEach(bar => bar.style.height = '10px');

                // Process audio
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' }); // Typically webm on Chrome
                
                // Set local player
                const audioUrl = URL.createObjectURL(audioBlob);
                referenceAudio.src = audioUrl;
                referencePlayerContainer.classList.remove('hidden');

                // Upload to Backend
                await uploadReferenceAudio(audioBlob);
            };

            mediaRecorder.start();
            
            // Update UI
            recordBtn.classList.add('hidden');
            stopBtn.classList.remove('hidden');
            recordingStatus.textContent = 'Recording 🔴';
            recordingStatus.style.background = 'rgba(239, 68, 68, 0.2)';
            recordingStatus.style.color = '#ef4444';

        } catch (err) {
            console.error("Error accessing mic: ", err);
            alert("Could not access microphone: " + err.message);
        }
    });

    stopBtn.addEventListener('click', () => {
        if (mediaRecorder && mediaRecorder.state === "recording") {
            mediaRecorder.stop();
            
            // Update UI
            stopBtn.classList.add('hidden');
            recordBtn.classList.remove('hidden');
            recordBtn.classList.remove('pulse');
            recordingStatus.textContent = 'Processing...';
            recordingStatus.style.background = 'rgba(255,255,255,0.1)';
            recordingStatus.style.color = '#fff';
        }
    });

    function updateVisualizer() {
        if (!analyser) return;
        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        analyser.getByteFrequencyData(dataArray);

        for (let i = 0; i < bars.length; i++) {
            // Pick a frequency bin for each bar
            const value = dataArray[i * 2 + 1]; 
            // Scale and set height (min 10px, max 50px)
            const height = Math.max(10, (value / 255) * 50);
            bars[i].style.height = `${height}px`;
        }

        animationId = requestAnimationFrame(updateVisualizer);
    }

    // --- File Upload Logic ---
    fileInput.addEventListener('change', async (e) => {
        if (e.target.files.length > 0) {
            const file = e.target.files[0];
            const audioUrl = URL.createObjectURL(file);
            referenceAudio.src = audioUrl;
            referencePlayerContainer.classList.remove('hidden');
            await uploadReferenceAudio(file);
        }
    });

    // --- YouTube Logic ---
    youtubeBtn.addEventListener('click', async () => {
        const url = youtubeInput.value.trim();
        if (!url) {
            alert("Please enter a YouTube URL");
            return;
        }

        youtubeBtn.disabled = true;
        recordingStatus.textContent = 'Downloading YouTube...';
        recordingStatus.style.background = 'rgba(245, 158, 11, 0.2)';
        recordingStatus.style.color = '#f59e0b';
        recordingStatus.className = 'status-badge';

        const formData = new FormData();
        formData.append('url', url);

        try {
            const response = await fetch(`${API_BASE}/upload_youtube`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Upload failed");
            }

            const data = await response.json();
            referenceId = data.reference_id;
            
            referencePlayerContainer.classList.add('hidden'); // We don't have local preview right away for YT
            
            recordingStatus.textContent = 'Ready ✅';
            recordingStatus.className = 'status-badge active';
            
            generationStatus.textContent = 'Ready';
            generationStatus.className = 'status-badge active';
            
            scriptInput.disabled = false;
            generateBtn.disabled = false;
            generateBtn.classList.remove('disabled');

        } catch (err) {
            console.error(err);
            alert("Error processing YouTube link: " + err.message);
            recordingStatus.textContent = 'Failed';
            recordingStatus.style.background = 'rgba(239, 68, 68, 0.2)';
            recordingStatus.style.color = '#ef4444';
        } finally {
            youtubeBtn.disabled = false;
        }
    });

    // --- Backend API Integration ---
    async function uploadReferenceAudio(blob) {
        recordingStatus.textContent = 'Uploading...';
        
        const formData = new FormData();
        // Backend expects common audio extension to save it right
        formData.append('audio', blob, 'reference.wav'); 

        try {
            const response = await fetch(`${API_BASE}/upload_reference`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Upload failed");
            }

            const data = await response.json();
            referenceId = data.reference_id;
            
            // Enable Studio
            recordingStatus.textContent = 'Ready ✅';
            recordingStatus.className = 'status-badge active';
            
            generationStatus.textContent = 'Ready';
            generationStatus.className = 'status-badge active';
            
            scriptInput.disabled = false;
            generateBtn.disabled = false;
            generateBtn.classList.remove('disabled');

        } catch (err) {
            console.error(err);
            alert("Error uploading reference voice: " + err.message);
            recordingStatus.textContent = 'Failed';
            recordingStatus.style.background = 'rgba(239, 68, 68, 0.2)';
            recordingStatus.style.color = '#ef4444';
        }
    }

    generateBtn.addEventListener('click', async () => {
        const text = scriptInput.value.trim();
        if (!text) {
            alert("Please enter a script to generate.");
            return;
        }

        // Show loading state
        generateBtn.disabled = true;
        generateBtn.classList.add('disabled');
        scriptInput.disabled = true;
        loader.classList.remove('hidden');
        resultContainer.classList.add('hidden');
        generationStatus.textContent = 'Synthesizing...';
        generationStatus.className = 'status-badge';
        generationStatus.style.background = 'rgba(245, 158, 11, 0.2)';
        generationStatus.style.color = '#f59e0b';

        const formData = new FormData();
        formData.append('text', text);
        formData.append('reference_id', referenceId);

        try {
            const response = await fetch(`${API_BASE}/generate`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Generation failed");
            }

            // The response is the binary audio file
            const audioBlob = await response.blob();
            const audioUrl = URL.createObjectURL(audioBlob);

            // Update UI
            resultAudio.src = audioUrl;
            
            // Setup download button
            downloadBtn.href = audioUrl;
            downloadBtn.download = `voiceover_${referenceId.substring(0,6)}.wav`;

            resultContainer.classList.remove('hidden');
            generationStatus.textContent = 'Complete ✅';
            generationStatus.className = 'status-badge active';

        } catch (err) {
            console.error(err);
            alert("Error generating voiceover: " + err.message);
            generationStatus.textContent = 'Failed';
            generationStatus.className = 'status-badge';
            generationStatus.style.background = 'rgba(239, 68, 68, 0.2)';
            generationStatus.style.color = '#ef4444';
        } finally {
            // Restore UI state
            generateBtn.disabled = false;
            generateBtn.classList.remove('disabled');
            scriptInput.disabled = false;
            loader.classList.add('hidden');
        }
    });
});
