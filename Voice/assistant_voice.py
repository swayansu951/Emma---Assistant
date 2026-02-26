import pyaudio
import sounddevice as sd
import queue
import threading
from kokoro_onnx import Kokoro
import numpy as np


class TTSEngine:
    def __init__(self, model="kokoro-v1.0.int8.onnx", voice_path="voices-v1.0.bin"):
        self.kokoro = Kokoro(model, voice_path)
        self.text_queue = queue.Queue()
        self.audio_queue = queue.Queue() # New: Queue for pre-calculated audio
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paFloat32,
                                  channels=1,
                                  rate=24000,
                                  output=True)
        
        # Start both the Generator and the Player threads
        
        threading.Thread(target=self._playback_worker, daemon=True).start()
        threading.Thread(target=self._generate_worker, daemon=True).start()

    def _generate_worker(self):
        while True:
            text = self.text_queue.get()
            if text is None: break

            if not isinstance(text,str):
                text = str(text)
            try:
                samples, _ = self.kokoro.create(text, voice='af_heart', speed=1.0, lang='en-us')
                audio_np = np.asarray(samples,dtype=np.float32)
                self.audio_queue.put(audio_np)
            except Exception as e:
                print(f"Generation error: {e}")    
            self.text_queue.task_done()

    def _playback_worker(self):
        """Plays audio chunks back-to-back with zero gap"""
        while True:
            audio_data = self.audio_queue.get()
            if audio_data is None: break
            try:
                sd.play(audio_data,samplerate=24000, blocking=True)
            except Exception as e:
                print(f"error : {e}")
                
            self.audio_queue.task_done()
            
    def speak(self, text):
        if isinstance(text, str) and text.strip():
            self.text_queue.put(text)