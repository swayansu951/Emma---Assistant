from AppOpener import open
import os
import json
from pathlib import Path
# import psutil
import webbrowser
import urllib.parse
import pyautogui
import time
from datetime import datetime
import subprocess
from pycaw.pycaw import AudioUtilities
# import winreg   ## going to be implemented on future
from pywinauto import findwindows, Desktop
# import winapps ## going to be implemented on future
# import hashlib

# path = "C:/Users/swaya/Desktop/"
desktop_app = Path.home()/ "Desktop"
# all_apps = os.listdir(path)
apps = [app for app in desktop_app.iterdir() if app.is_file()]
opened_app = []
important_folder = "important_docs"

class AIAssistantClass:
    def app_opener(self,app_name):
            try:
                cmdd = f'PowerShell -Command "explorer.exe shell:AppsFolder\\$( (Get-StartApps | Where-Object {{$_.Name -like \'{app_name}*\'}}).AppID )"'
                full_path = os.path.join(apps, app_name)
                opened = False
                cmd = f'PowerShell -Command "Get-StartApps | Where-Object {{$_.Name -like \'*{app_name}*\'}}"'
                result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                if app_name.endswith('.lnk'):
                    if os.path.exists(full_path):
                        print("Success! File found.")
                        os.startfile(full_path)
                        print("file opened by startfile\n")
                        opened =True
                        opened_app.append(app_name)
                    else:
                        opened = False
                        print(f"{app_name} does not end with .lnk")
                    
                # If stdout has content, the app is present
                elif opened == False:
                    if result.stdout.strip():
                        os.system(f"start {app_name.lower()}:")
                        print("file opened using os.system\n")
                        opened =True
                        opened_app.append(app_name)
                        return True
                    else:
                        try:
                            subprocess.Popen(cmdd, shell=True)
                            print(f" Launching {app_name} via AppID.    ..")
                        except Exception as e:
                            print(f" Failed: {e}")
                        return True
                
                else:
                    print("not such directory")
                    print(apps)
                    for f in apps:
                        if app_name.lower() in f.lower():
                            print(f"did you mean: {f}?")
                            return True
            except Exception as e:
                print(f"oops...somethings gone wrong: {e}")
                 
    def open_camera(self):
        os.system("start microsoft.windows.camera:")
        return True
    
    def open_google(self):
        """Open Google in default browser"""
        try:
            webbrowser.open("https://www.google.com")
            return "Google opened successfully"
        except Exception as e:
            return f"Error opening Google: {str(e)}"
    def play_youtube_music(self, query):
        """Search and play music on YouTube Music"""
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://music.youtube.com/search?q={encoded_query}"
            webbrowser.open(url)
            return f"Playing '{query}' on YouTube Music"
        except Exception as e:
            return f"Error playing music: {str(e)}"
        
    # def play_youtube_music(self, query):
    #     """Search and play music on YouTube Music"""
    #     try:
    #         encoded_query = urllib.parse.quote(query)
    #         url = f"https://music.youtube.com/search?q={encoded_query}"
    #         webbrowser.open(url)
    #         return f"Playing '{query}' on YouTube Music"
    #     except Exception as e:
    #         return f"Error playing music: {str(e)}"
        
    def open_netflix(self, query):
        """Search and play movie on Netflix"""
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"C://Program Files (x86)//Microsoft//Edge//Application{encoded_query}"
            webbrowser.open(url)
            return f"Playing '{query}' on Netflix"
        except Exception as e:
            return f"Error playing music: {str(e)}"
        
    def open_website(self, url):
        """Open any website"""
        try:
            if not url.startswith("http"):
                url = "https://" + url
            webbrowser.open(url)
            return f"Opened {url}"
        except Exception as e:
            return f"Error opening website: {str(e)}"
    
    def search_web(self, query, engine="Bing"):
        """Search the web using specified search engine"""
        try:
            encoded_query = urllib.parse.quote(query)
            engines = {
                "google": f"https://www.google.com/search?q={encoded_query}",
                "bing": f"https://www.bing.com/search?q={encoded_query}",
                "duckduckgo": f"https://duckduckgo.com/?q={encoded_query}"
            }
            url = engines.get(engine.lower(), engines["bing"])
            webbrowser.open(url)
            return f"Searched '{query}' on {engine}"
        except Exception as e:
            return f"Error searching: {str(e)}"

    def all_appications(self):
        try:
            desktop_app = Path.home()/ "Desktop"
            apps = [app for app in desktop_app.iterdir() if app.is_file()]
            print(f"you might search apps from your desktop {apps}")
        except Exception as e:
            return f" error : {e}"
    
    def pause_song(self, timeout =5):
        start = time.time()

        print("song pause\n")

        while time.time() - start < timeout:
        
            audio_playing = False
            sessions = AudioUtilities.GetAllSessions()
            for session in sessions:
                if session.State == 1:
                    pyautogui.press('playpause')
                    audio_playing =True
                    return "music paused"
                
            time.sleep(0.5)
        return "no active audio session found"

    def important_notes(self,notes,filename=None):
        new_note = {"time":datetime.now().strftime("%H:%M %y-%m-%d"),
                    "notes":notes}
        try:
            if not os.path.exists(important_folder):
                os.makedirs(important_folder)
            if filename is None:
                filename = os.path.join(important_folder,"important.json")
            if os.path.exists(filename):
                with open(filename, 'r+', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        data=[]
                    if not isinstance(data,list):
                        data =[]
                    data.append(new_note)
                    
                    f.seek(0)
                    json.dump(data,f,indent=2)

        except Exception as e:
            return f"error : {e}"
    def close_search(self):
        close=False
        try:
            pyautogui.hotkey('ctrl','w')
            close =True
            return None
        except Exception as e:
            close =False
            return f"error : {e}"
    
    # def system_details(self):
    #     try:
    #         os.system()

    def list_running_apps(self):
    # Fetch all top-level windows from the desktop
        windows = Desktop(backend="uia").windows()
        
        print(f"{'INDEX':<10} {'WINDOW TITLE'}")
        print("-" * 40)
        
        active_apps = []
        for i, win in enumerate(windows):
            title = win.window_text()
            # Filter out windows with no title (usually background services)
            if title:
                print(f"{i:<10} {title}")
                active_apps.append(title)
                
        return active_apps
    def close_apps(self,name):
        elements = findwindows.find_elements(backend="uia", top_level_only=True)
        
        # 2. Filter titles that match our search and aren't empty
        matches = []
        for el in elements:
            title = el.name
            if title and name.lower() in title.lower():
                matches.append(title)


        try:
            blacklist = ["taskbar", "program manager", "start", "desktop"]
            
            # 3. Get the list of titles that match what the user typed
            titles = matches
            
            if not titles:
                print(f"No running app found matching '{name}'")
                return False

            found_and_closed = False
            for title in titles and title in opened_app:
                # 4. Final check against blacklist
                if title.lower() not in blacklist:
                    print(f"Attempting to close: {title}")
                    # 5. Use the EXACT title found in the list for taskkill
                    subprocess.call(f'taskkill /F /FI "WINDOWTITLE eq {title}" /T', shell=True)
                    opened_app.remove(name)
                    found_and_closed = True
        
            if found_and_closed:
                print(f"Cleanup of '{name}' complete.")
                return True
                
        except Exception as e:
            print(f"Error occurred: {e}")
        return False                

    def write_text(self, app_name:str, contact:str, text:str):
        """
        Opens a specific app and sends a message to a contact.

        Args:
            app_name: The name of the application (e.g., 'WhatsApp').
            contact: The name of the person to search for.
            text: The message content to send.
        """
        # slam mouse to left to exit the ongoing code...(safety)
        try:
            pyautogui.FAILSAFE = True
            os.system(f"start {app_name.lower()}:")
            time.sleep(7)

            pyautogui.hotkey('ctrl', 'f')
            time.sleep(1)     

            pyautogui.write(contact)
            time.sleep(2)
            
            pyautogui.press('enter')
            time.sleep(2)
            
            pyautogui.write(text.title())
            time.sleep(5)
            
            pyautogui.press('enter')
            time.sleep(2)
            return f"Message sent to {contact} via {app_name}"
        except Exception as e:
            return f"Error sending message: {e}"
    
    def apps_opened(self):
        print(opened_app)
        return 
        # os.system(f"taskkill /F /IM {app_name}.exe /T")
        # print("completely closed the app :)")
 
# if __name__ == "__main__":
#     action = input("whats the act: ")
#     user = input("enter the name of the file you want to open: ").strip()
#     target = input("enter the person to send message: ")
#     text =input("enter the message: ")
#     opener = AIAssistantClass()
#     if action == 'open':
#         print(opener.write_text(user,target,text))