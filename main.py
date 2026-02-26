import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import sounddevice as sd
import soundfile as sf
import numpy as np
import scipy.io.wavfile as wav
from Ear.assistant_ear import STTEngine
from Voice.assistant_voice import TTSEngine
from Brain.assistant import ASSISTANT,load_chat_history ,save_chat
import random
import soundfile as sf
import sounddevice as sd
# from abilitites.explicit_functions import AIAssistantClass

def play_random_filler():
    try:
        filler_files = ["assets/fillers/hmmm.wav", "assets/fillers/thinking.wav", "assets/fillers/ok.wav"]
        choice = random.choice(filler_files)
        data, fs = sf.read(choice)
        sd.play(data, fs)
    except Exception as e:
        print(f"filler error: {e}")

def main():
    ear = STTEngine()
    voice = TTSEngine()
    brain = ASSISTANT()
    print("*"*8, "Assistant ACtivated", "*"*8)
    while True:
        cmd = input("Press ENTER to speak (type q + ENTER to quit): ").strip().lower()
        
        if cmd == "q":
                print("Shutting down...")
                brain.shutdown()
                break
        try:
            print("listening now....")
            fs = 16000
            duration= 7
            recording = sd.rec(int(duration * fs),samplerate=fs,channels=1, dtype ='float32')
            sd.wait()
            
            #load the audio file
            audio_file = "record.wav"
            wav.write(audio_file,fs,recording)
          
            # ear
            user_text = ear.transcibe(audio_file)
            if user_text:
                # brain
                print(f"you : {user_text}")
               
                if "bye" in user_text.lower():
                    print("Emma: catch you soon boss.. ")
                    voice.speak("catch you soon boss!")   
                    break 

                play_random_filler()
                
                print("Emma : ",end="",flush=True)
                
                response = brain.start_ai(user_text)
                for sentence in response:
                    print(sentence, end=" ", flush=True)
                    voice.speak(sentence)

        except KeyboardInterrupt:
            print("\nclosing the task..")
            brain.shutdown()
            break

if __name__ == "__main__":
    main()