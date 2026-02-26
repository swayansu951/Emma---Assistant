import sounddevice as sd
import queue
import threading
from kokoro_onnx import Kokoro

class TTSEngine:
    def __init__(self, model="kokoro-v1.0.int8.onnx", voice_path="voices-v1.0.bin"):
        self.kokoro = Kokoro(model, voice_path)
        self.text_queue = queue.Queue()
        self.audio_queue = queue.Queue() # New: Queue for pre-calculated audio
        
        # Start both the Generator and the Player threads
        threading.Thread(target=self._generation_worker, daemon=True).start()
        threading.Thread(target=self._playback_worker, daemon=True).start()

    def _generation_worker(self):
        """Pre-calculates audio while the speaker is busy"""
        while True:
            text = self.text_queue.get()
            if text is None: break
            
            # CPU calculates the next sentence NOW
            samples, sample_rate = self.kokoro.create(text, voice="af_heart", speed=1.0, lang='en-us')
            self.audio_queue.put((samples, sample_rate))
            self.text_queue.task_done()

    def _playback_worker(self):
        """Plays audio chunks back-to-back with zero gap"""
        while True:
            samples, sample_rate = self.audio_queue.get()
            sd.play(samples, sample_rate)
            sd.wait() # Only waits for playback, not calculation!
            self.audio_queue.task_done()

    def speak(self, text):
        if isinstance(text, str) and text.strip():
            self.text_queue.put(text)
