import os
import webbrowser
import pyttsx3
import datetime
import speech_recognition as sr
import requests
import cohere
import re
import subprocess
from dotenv import load_dotenv

# =======================
# Load API KEYS from .env
# =======================
load_dotenv()
WEATHER_KEY = os.getenv("WEATHER_KEY")
NEWS_KEY = os.getenv("NEWS_KEY")
COHERE_KEY = os.getenv("COHERE_KEY")

# Initialize Cohere client
co = cohere.Client(COHERE_KEY)

# =======================
# Bruno AI Assistant
# =======================
class Bruno:
    def __init__(self):
        self.conversation_history = []
        self.apps = {
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            "vscode": r"C:\Users\HP\AppData\Local\Programs\Microsoft VS Code\Code.exe",
            "youtube": r"C:\Users\HP\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe",
            "spotify": "shell:AppsFolder\\SpotifyAB.SpotifyMusic_zpdnekdrzrea0!Spotify",
            "paint": r"C:\Windows\System32\mspaint.exe",
            "instagram": "shell:AppsFolder\\Facebook.InstagramBeta_8xx8rvfyw5nnt!App",
            "linkedin": "shell:AppsFolder\\7EE7776C.LinkedInforWindows_w1wdnht996gqy!App",
            "whatsapp": "shell:AppsFolder\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App"
        }
        self.speak("Hello Aafrin! I'm Bruno, How can I help you?")

    # =======================
    # Speak (TTS)
    # =======================
    def speak(self, text):
        print(f"Bruno: {text}")
        try:
            engine = pyttsx3.init(driverName='sapi5')
            voices = engine.getProperty('voices')
            engine.setProperty('voice', voices[0].id)
            engine.setProperty('rate', 200)
            engine.setProperty('volume', 1.0)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            print(f"[TTS Error] {e}")

    # =======================
    # Listen to user
    # =======================
    def hear(self):
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        with mic as source:
            print("Listening...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)
        try:
            command = recognizer.recognize_google(audio)
            print(f"You said: {command}")
            return command
        except sr.UnknownValueError:
            self.speak("Sorry, I could not understand.")
            return ""
        except sr.RequestError:
            self.speak("Sorry, the speech service is unavailable.")
            return ""

    # =======================
    # Cohere GPT-like responses
    # =======================
    def ask_cohere(self, prompt):
        try:
            self.conversation_history.append(f"User: {prompt}")
            history_text = "\n".join(self.conversation_history[-10:])
            full_prompt = (
                f"You are Bruno, a friendly AI assistant. "
                f"User may speak any language. Please reply in English only.\n"
                f"{history_text}\nBruno:"
            )
            response = co.generate(
                model='command-xlarge',
                prompt=full_prompt,
                max_tokens=150,
                temperature=0.7,
            )
            answer = response.generations[0].text.strip()
            self.conversation_history.append(f"Bruno: {answer}")
            return answer
        except Exception as e:
            return f"Error: {e}"

    # =======================
    # Weather info
    # =======================
    def get_weather(self, command):
        match = re.search(r'weather in (.+)', command.lower())
        city = match.group(1).strip() if match else input("Please mention the city: ").strip()
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_KEY}&units=metric"
        try:
            data = requests.get(url).json()
            if data.get("cod") != 200:
                return f"Sorry, I couldn't find weather for {city}."
            weather = data["weather"][0]["description"]
            temp = data["main"]["temp"]
            return f"The weather in {city} is {temp}°C with {weather}."
        except:
            return "Sorry, I could not retrieve the weather."

    # =======================
    # News
    # =======================
    def get_news(self):
        url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_KEY}"
        try:
            data = requests.get(url).json()
            articles = data.get("articles", [])[:3]
            headlines = [f"{a['title']} - {a['source']['name']}" for a in articles]
            return "Top headlines: " + "; ".join(headlines)
        except:
            return "Sorry, I could not retrieve the news."

    # =======================
    # Handle commands
    # =======================
    def handle(self, command):
        command_lower = command.lower()

        for trigger in ["bruno ", "hey bruno ", "ok bruno "]:
            if command_lower.startswith(trigger):
                command_lower = command_lower.replace(trigger, "", 1).strip()

        if command_lower in ["exit", "quit", "bye"]:
            self.speak("Goodbye!")
            return False

        # ======= YouTube Handling =======
        elif "youtube" in command_lower:
            brave_path = self.apps.get("youtube")
            if not brave_path:
                self.speak("Brave browser path not configured.")
                return True

            query = command_lower.replace("youtube", "").strip()
            url = "https://www.youtube.com" if not query else f"https://www.youtube.com/results?search_query={query}"
            subprocess.Popen([brave_path, "--profile-directory=Default", url])
            self.speak(f"Opening YouTube{' results for ' + query if query else ''}")
            return True

        # ======= Open Apps =======
        elif command_lower.startswith("open "):
            app_name = command_lower.replace("open ", "").strip()
            app_path = self.apps.get(app_name)
            try:
                if app_path:
                    if app_path.startswith("shell:AppsFolder"):
                        os.system(f"start {app_path}")
                    else:
                        os.startfile(app_path)
                    self.speak(f"Opening {app_name}")
                else:
                    os.system(f'start "" "{app_name}"')
                    self.speak(f"Trying to open {app_name}")
            except:
                self.speak(f"Sorry, I couldn't open {app_name}")

        # ======= Google Search =======
        elif command_lower.startswith("search "):
            query = command_lower.replace("search ", "").strip()
            webbrowser.open(f"https://www.google.com/search?q={query}")
            self.speak(f"Searching for {query}")

        # ======= Weather =======
        elif "weather" in command_lower:
            self.speak(self.get_weather(command))

        # ======= News =======
        elif "news" in command_lower:
            self.speak(self.get_news())

        # ======= Time & Date =======
        elif command_lower == "time":
            now = datetime.datetime.now().strftime("%H:%M:%S")
            self.speak(f"The time is {now}")

        elif command_lower == "date":
            today = datetime.datetime.now().strftime("%A, %d %B %Y")
            self.speak(f"Today is {today}")

        # ======= General Q&A =======
        else:
            response = self.ask_cohere(command)
            self.speak(response)

        return True

# =======================
# Main Loop
# =======================
def main():
    bruno = Bruno()
    mode = input("Choose input mode - type 'voice' or 'text': ").strip().lower()
    try:
        while True:
            if mode == "voice":
                command = bruno.hear()
            else:
                command = input("You: ")
            if command and not bruno.handle(command):
                break
    except KeyboardInterrupt:
        print("\n[Interrupted]")

if __name__ == "__main__":
    main()
