import ollama
from abilities.functions import AIAssistantClass
import re
import json 
import os
from datetime import datetime
from pathlib import Path

# 1. Define the AI DNA
SYSTEM_PROMPT = {"normal assistant":"""
you are an assistant, do tasks under user's supervision, do whatever boss(user) orders, maintain a safety boundary, do not run anything by yourself, double ask every task when boss orders to do, respect your boss's every words.
make a preview about the work the user told to do, and remember the apps or file you have opened and when boss says to close or delete recall the name and use that.
You must output at most one tool command per reply.
Never combine multiple commands in a single answer.
double ask every task when boss orders to do
When you want to use a tool, output ONLY a JSON object
on a single line at the end of your reply.

Format:

{"tool":"TOOL_NAME","args":{...}}

Rules:
- Output at most one tool call
- Do not wrap it in markdown
- Do not explain the JSON
- Normal text must come before the JSON
                 
Examples: 
- 'Of course, boss Opening Netflix'
- 'Right away!'
- 'let me search that for you boss'

Available capabilities:

OPEN_APP -> {"tool":"OPEN_APP","args":{"app":"notepad"}}
CAMERA -> {"tool":"CAMERA","args":{}}
CHROME -> {"tool":"CHROME","args":{}}
OPEN_WEBSITE -> {"tool":"OPEN_WEBSITE","args":{"url":"google.com"}}
SEARCH_WEBSITE -> {"tool":"SEARCH_WEBSITE","args":{"query":"python asyncio"}}
CLOSE_APP -> {"tool" : "CLOSE_APP", "args" : {"app":"chrome"}}
PLAY_MUSIC -> {"tool" : "PLAY_MUSIC", "args" : {"query":"music name"}}
APP_RUNNING -> {"tool" : "APP_RUNNING", "args": {}}
PAUSE_MUSIC -> {"tool" : "PAUSE_MUSIC", "args": {}}
SAVE_NOTES -> {"tool" : "SAVE_NOTES", "args" : {"notes" : "I have to change my PC desk."}}
WRITE_MESSAGE -> {"tool" : "WRITE_MESSAGE", "args" : {"app" : "whatsapp" , "contact" : "rahul", "text" : "hello, how are you?"}}
                 

                 
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
        
        if assistant_type not in chat_data:
            chat_data[assistant_type] = []

        # Add current session
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

        self.runtime_status = {
            "opened_app" : [],
            "opened_url" : []
        }
        # tools
        self.assistant = AIAssistantClass()
        self.command_registry = {
            "OPEN_APP": lambda args : self.assistant.app_opener(args.get("app")),
            "CAMERA": lambda args : self.assistant.open_camera(),
            "CHROME": lambda args : self.assistant.open_google(),
            "OPEN_WEBSITE" : lambda args : self.assistant.open_website(args.get("url")),
            "SEARCH_WEBSITE" : lambda args : self.assistant.search_web(args.get("query")),
            "CLOSE_APP": lambda args: self.assistant.close_apps(args.get("app")),
            "PLAY_MUSIC" : lambda args : self.assistant.play_youtube_music(args.get("query")),
            "APP_RUNNING": lambda args : self.assistant.list_running_apps(),
            "PAUSE_MUSIC": lambda args: self.assistant.pause_song(),
            "SAVE_NOTES" : lambda args : self.assistant.important_notes(args.get("notes")),
            "WRITE_MESSAGE" : lambda args : self.assistant.write_text(args.get("app"),
                                                                      args.get("contact"),
                                                                      args.get("text"))
        }
        # load memory
        history = load_chat_history("normal assistant")

        if history:
            # load last session
            self.messages = history[-1]["messages"][-20:]
        else:
            self.messages = [
                {"role": "system", "content": SYSTEM_PROMPT["normal assistant"]}
            ]
        
    def start_ai(self, user_input: str):

        self.messages.append({'role': 'user', 'content': user_input})
        
        # Generate response from Ollama
        try:
            response = ollama.chat(model='llama3-abliterated:latest', messages=self.messages,stream=True,options={"num_thread":4,"keep_alive":"2m"}) 
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
    def _handle_commands(self,ai_response : str):
        
        lines: list[str] = [l.strip() for l in ai_response.strip().splitlines() if l.strip()]
        
        if not lines: return

        last = lines[-1]
        if not last.startswith('{'): return
        
        try:
            payload = json.loads(last)
        except Exception as e: print (f"error : {e}")
        
        tool = payload.get("tool")
        args = payload.get("args", {})
        handler = self.command_registry.get(tool)

        if not handler : return

        try: 
            handler(args)
        except Exception as e:
            print(f"Error : {e}")
            return

       
        print(f"\n{'Emma'}: {ai_response}")
               
    def shutdown(self):
        save_chat(self.messages,"normal assistant")
