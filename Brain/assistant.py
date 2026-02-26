import ollama
from abilities.functions import AIAssistantClass
import re
import json 
import os
from datetime import datetime
from pathlib import Path

# 1. Define the AI DNA
SYSTEM_PROMPT = {"normal assistant":"""
you are an assistant, having all contol over users computer but under user's supervision, do whatever when boss(user) orders, maintain a safety boundary, double ask everything if boss tries to delete or open, respect your boss's every words.
make a preview about the work the user told to do, and remember the apps or file you have opened and when boss says to close or delete recall the name and use that.

Examples: 
- 'Of course, boss [EXECUTE_APP:netflix] Opening Netflix'
- 'Right away! [PLAY_MUSIC:Taylor Swift] '
- 'let me search that for you boss [SEARCH_WEB:best restaurants nearby]'

Additional capabilities:
- To read files: [READ_FILE:path]
- To write files: [WRITE_FILE:path:content]
- To execute code: [EXEC_CODE:language:code]
- To play music: [PLAY_MUSIC:song/artist name]
- To search web: [SEARCH_WEB:search query]
- To open website: [OPEN_WEBSITE:url]
- To show all apps on desktop: [SHOW_ALL_APPS:]
- To close apps: [CLOSE_APP: app_name]
- To send text message: [WRITE_TEXT: app_name, contact, text]
- To execute apps: [OPEN_APP:app_name]
- To open camera: [CAMERA:]
- To show all running apps: [APP_RUNNING:]
- To pause music palying: [PAUSE_MUSIC:]

if boss(user) tells you to send some message or email and tells you to mention yourself then do: [Emma] i am boss's assitant....
"""}

chat_folder = "chat_logs"
if not os.path.exists(chat_folder):
    os.makedirs(chat_folder)
def save_chat(messages, assistant_type, filename=None):
    """Save chat history to file, organized by assistant type"""
    try:
        # Default filename with proper path
        if filename is None:
            filename = os.path.join(chat_folder, "chat_history.json")
        
        # Load existing chat history if it exists
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                chat_data = json.load(f)
        else:
            chat_data = {"normal assistant": []}
        
        # Add current session with timestamp
        chat_session = {
            "timestamp": datetime.now().isoformat(),
            "messages": messages
        }
        chat_data[assistant_type].append(chat_session)
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(chat_data, f, indent=2)
            
        print(f"Chat saved for {assistant_type} to {filename}")
        return True
    except Exception as e:
        print(f"Failed to save chat: {e}")
        return False

def load_chat_history(assistant_type, filename=None):
    """Load previous chat history for assistant """
    try:
        # Default filename with proper path
        if filename is None:
            filename = os.path.join(chat_folder, "chat_history.json")
            
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                chat_data = json.load(f)
            return chat_data.get(assistant_type, [])
        return []
    except Exception as e:
        print(f"Failed to load chat history: {e}")
        return []
    
class ASSISTANT:
    def __init__(self):

        # tools
        self.assistant = AIAssistantClass()

        # load memory
        history = load_chat_history("normal assistant")

        if history:
            # load last session
            self.messages = history[-1]["messages"]
        else:
            self.messages = [
                {"role": "system", "content": SYSTEM_PROMPT["normal assistant"]}
            ]
        
    def start_ai(self, user_input: str):

        self.messages.append({'role': 'user', 'content': user_input})
        
        # Generate response from Ollama
        try:
            response = ollama.chat(model='llama3-abliterated:latest', messages=self.messages,stream=True,options={"num_thread":4}) # lama get stoped after completing the task
            # ai_response = response['message']['content']
            full_response = ""
            sentence_buffer = ""

            for chunk in response:
                content = chunk['message']['content']
                full_response += content
                sentence_buffer += content

                if any(p in content for p in [".","!","?","\n"]):
                    text_to_speak = re.sub(r'\[.*?\]', '', sentence_buffer).strip()

                    if text_to_speak:
                        yield str(text_to_speak)
                    sentence_buffer= ""

            if sentence_buffer.strip():
                finral_text = re.sub(r'\[.*?\]', '', sentence_buffer).strip()
                if finral_text:
                    yield finral_text

            self.messages.append({'role': 'assistant', 'content': full_response})
            self._handle_commands(full_response)
        
        except Exception as e :
            print(f"Brain stoped: {e}")
            yield "sorry boss my brain got stalled :("

            # Check for and execute system commands
    def _handle_commands(self,ai_response):
        action_feedback = ""

        # Handle all command types for both assistants
        if "[PLAY_MUSIC:" in ai_response:
            match = re.search(r'\[PLAY_MUSIC:(.*?)\]', ai_response)
            if match: action_feedback = self.assistant.play_youtube_music(match.group(1))
        
        elif "[SEARCH_WEB:" in ai_response:
            match = re.search(r'\[SEARCH_WEB:(.*?)\]', ai_response)
            if match: self.assistant.search_web(match.group(1))
        
        elif "[OPEN_WEBSITE:" in ai_response:
            match = re.search(r'\[OPEN_WEBSITE:(.*?)\]', ai_response)
            if match: self.assistant.open_website(match.group(1)) 
                
        elif "[OPEN_APP:" in ai_response:
            match = re.search(r'\[OPEN_APP:(.*?)\]', ai_response)
            if match: self.assistant.app_opener(match.group(1))
            
        elif "[READ_FILE:" in ai_response:
            match = re.search(r'\[READ_FILE:(.*?)\]', ai_response)
            if match: self.assistant.read_system_file(match.group(1))
                
        elif "[WRITE_FILE:" in ai_response:
            match = re.search(r'\[WRITE_FILE:(.*?):(.*?)\]', ai_response)
            if match: self.assistant.write_system_file(match.group(1), match.group(2))
            
        elif "[EXEC_CODE:" in ai_response:
            match = re.search(r'\[EXEC_CODE:(.*?):(.*?)\]', ai_response)
            if match: self.assistant.execute_code(match.group(1), match.group(2))

        elif "[CLOSE_APP:" in ai_response:
            match = re.search(r'\[CLOSE_APP:(.*?)\]', ai_response)
            if match: self.assistant.close_apps(match.group(1))
                
        elif "[SHOW_ALL_APPS:" in ai_response:
            match = re.search(r'\[SHOW_ALL_APPS:(.*?)\]',ai_response)
            if match: self.assistant.all_appications()
                
        elif "[WRITE_TEXT:" in ai_response:
            match = re.search(r'\[WRITE_TEXT:(.*?)\]',ai_response)
            if match: 
                params = match.group(1)
                parts = [p.strip() for p in params.split(',')]
                if len(parts) >= 3: 
                    self.assistant.write_text(parts[0], parts[1],','.join(parts[2:]))
                                                              
                else: 
                    print("Invalid WRITE_TEXT format. Expected: [WRITE_TEXT:app,contact,text]")
                       
        elif "[APP_RUNNING:" in ai_response:
            match = re.search(r'\[APP_RUNNING:(.*?)\]',ai_response)
            if match: self.assistant.list_running_apps()

        elif "[PAUSE_MUSIC:" in ai_response:
            action_feedback = self.assistant.pause_song()
            print(action_feedback)

        elif "[CAMERA:" in ai_response:
            action_feedback = self.assistant.open_camera()
            print(action_feedback)
        elif "[BROWSER]" in ai_response:
            action_feedback = self.assistant.open_google()
            print(action_feedback)
        elif "[NOTEPAD]" in ai_response:
            action_feedback = self.assistant.app_opener("notepad")
            print(action_feedback)
        elif "[CALC]" in ai_response:
            action_feedback = self.assistant.app_opener("calc")
            print(action_feedback)
        elif "[BATTERY]" in ai_response:
            action_feedback = "Battery check not implemented in this version"
            print(action_feedback)
        print(f"\n{'Emma'}: {ai_response}")
        if action_feedback:
            print(f"--- System: {action_feedback} ---")
            
   
    def shutdown(self):
        save_chat(self.messages,"normal assistant")
