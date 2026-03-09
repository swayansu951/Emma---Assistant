import ollama
from abilities.functions import AIAssistantClass
import re
import json 
import os
from datetime import datetime
from pathlib import Path
from Research.router import LRAG
from Research.local_RAG import LocalRag
from Research.pdf_reader import PDFREADER

# 1. Define the AI DNA
SYSTEM_PROMPT = {"normal assistant":"""
you are a helpfull assistant, do tasks under user's supervision, do whatever boss(user) orders, maintain a safety boundary, do not run anything by yourself, double ask every task when boss orders to do, respect your boss's every words.
make a preview about the work the user told to do, and remember the apps or file you have opened and when boss says to close or delete recall the name and use that.
use tools when boss orders you to do, never run anything by yourself, always ask before doing anything, if boss says to do something and you don't know how to do it, say "I don't know how to do that, boss. Can you please guide me?" and wait for instructions.
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
- 'Of course, boss Opening Netflix {"tool":"OPEN_APP","args":{"app":"Netflix"}}'
- 'Right away!'
- 'let me search that for you boss {"tool":"SEARCH_WEBSITE","args":{"query":"how to integrate web access?"}}'

Available capabilities:

- To open app : {"tool" : "OPEN_APP", "args" : {"app":"app_name"}}
- To open camera : {"tool" : "CAMERA", "args" : {}}
- To open chrome : {"tool" : "CHROME", "args" : {}}
- To open chrome : {"tool" : "OPEN_WEBSITE", "args" : {"url":"google.com"}}
- To search a website : {"tool":"SEARCH_WEBSITE", "args" : {"query":"python asyncio"}}
- To close a app : {"tool" : "CLOSE_APP", "args" : {"app":"app_name"}}
- To play music : {"tool" : "PLAY_MUSIC", "args" : {"query":"music name"}}
- To show all app running : {"tool" : "APP_RUNNING", "args": {}}
- To pause music : {"tool" : "PAUSE_MUSIC", "args": {}}
- To save important notes : {"tool" : "SAVE_NOTES", "args" : {"notes" : "I have to change my PC desk."}}
- To send message : {"tool" : "WRITE_MESSAGE", "args" : {"app" : "whatsapp" , "contact" : "rahul", "text" : "hello, how are you?"}}
- To read important notes : {"tool" : "READ_NOTES", "args" : {}}
- To clear conversation : {"tool" : "CLEAR_CONVERSATION", "args" : {}}
                 

                 
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
        chat_data = {"normal assistant":[]}
        if os.path.exists(filename):
            try:
                with open(filename, 'r',encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        chat_data = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"chat history corrupt : {e}")
        
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
    
def clear_conversation(file_path = "./chat_history.json"):
    with open(file_path, 'w') as f:
        json.dump([],f)
        print("conversation has been cleared.")

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
            "SAVE_NOTES" : lambda args : self.assistant.important_notes(args.get("notes")) if isinstance(args, dict) else args,
            "READ_NOTES" : lambda args : self.assistant.read_notes(),
            "WRITE_MESSAGE" : lambda args : self.assistant.write_text(args.get("app"),
                                                                      args.get("contact"),
                                                                      args.get("text")),
            "CLEAR_CONVERSATION" : lambda args : clear_conversation()

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
    

    def normal_assistant(self, user_input: str):

        self.messages.append({'role': 'user', 'content': user_input})
        
        # Generate response from Ollama
        try:
            response = ollama.chat(model='llama3-abliterated:latest', messages=self.messages,stream=True,options={"num_thread":4,"keep_alive":"2m"}) 
            # ai_response = response['message']['content']
            full_response = ""
            sentence_buffer = ""
            try:
                if "clear chat" in user_input.lower():
                    clear_conversation()
                    print("Done!")
            except Exception as e:
                print(f"Error : {e}")

            for chunk in response:
                content = chunk['message']['content']
                full_response += content
                sentence_buffer += content

                if any(p in content for p in [".","!","?","*","\n"]):
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
    def extract_last(self,text :str):
        end = text.rfind('}')
        depth =0 
        for i in range(end,-1,-1):
            if text[i] == '}':
                depth +=1
            elif text[i] == '{':
                depth -=1
                if depth == 0:
                    return text[i:end+1]
    def _handle_commands(self,ai_response : str):
        
        lines: list[str] = [l.strip() for l in ai_response.strip().splitlines() if l.strip()]
        
        if not lines: return
        
        json_text = self.extract_last(ai_response)
        if not json_text:
            return None    
     
        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError as e: 
            print (f"JSON parse error : {e}")
            print(f"raw JSON text: {json_text}")
            return 

        tool = payload.get("tool")
        args = payload.get("args", {})
        handler = self.command_registry.get(tool)

        if not handler : return

        try: 
            handler(args)
        except Exception as e:
            print(f"Error : {e}")
            return
        if tool == "OPEN_APP":
            app = args.get("app")
            if app:
                self.runtime_status["opened_app"].append(app)

        elif tool == "OPEN_WEBSITE":
            url = args.get("url")
            if url:
                self.runtime_status["opened_url"].append(url)
        elif tool == "CLOSE_APP":
            app = args.get("app")
            if app in self.runtime_status["opened_app"]:
                self.runtime_status["opened_app"].remove(app)
       
        print(f"\n{'Emma'}: {ai_response}")
               
    def shutdown(self):
        save_chat(self.messages,"normal assistant")
