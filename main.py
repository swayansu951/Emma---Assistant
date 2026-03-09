import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import sounddevice as sd
import soundfile as sf
import numpy as np
# import scipy.io.wavfile as wav
from Ear.assistant_ear import STTEngine
from Voice.assistant_voice import TTSEngine
from Brain.assistant import ASSISTANT,load_chat_history ,save_chat
import random
import soundfile as sf
import sounddevice as sd
import io
import speech_recognition as sr
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
    print("*"*10, "Assistant ACtivated", "*"*10)
    r = sr.Recognizer()
    r.energy_threshold = 230
    r.pause_threshold =0.9
    r.dynamic_energy_threshold= True
    
    while True:
        raw = input("\nPress ENTER to speak (type q + ENTER to quit): ")
        cmd = raw.strip().lower()
        user_text = ""
        if cmd == "q":
                print("Shutting down...")
                brain.shutdown()
                break
        try:
            if raw.strip():
                user_text = raw.strip()
            else:
                try:
                    with sr.Microphone(sample_rate=16000) as source:
                        print("Emma Listening..")
                        audio = r.listen(source,phrase_time_limit=None)
                        audio_stream = io.BytesIO(audio.get_wav_data())
                        # ear
                        user_text = ear.transcribe(audio_stream)
                except Exception as e :
                    print(f"Error : {e}")
                    continue

            if not user_text.strip(): 
                print("can't catch that")
                continue

            print("Processing it now....")
            sd.wait()
            print(f"you : {user_text}")
           
            if user_text:
               
                if "bye" in user_text.lower():
                    print("Emma: catch you soon boss.. ")
                    voice.speak("catch you soon boss!")  
                    save_chat(brain.messages, "normal response") 
                    break 

                # brain
                play_random_filler()
                
                print("Emma : ",end="",flush=True)
                
                response = brain.normal_assistant(user_text)
                # voice\
                spoken =False
                for sentence in response:
                    spoken = True
                    print(sentence, end=" ", flush=True)
                    voice.speak(sentence)

        except KeyboardInterrupt:
            print("\nclosing the task..")
            brain.shutdown()
            break

if __name__ == "__main__":
    main()