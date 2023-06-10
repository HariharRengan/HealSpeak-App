import os
import speech_recognition as sr
from pydub import AudioSegment
from pydub.effects import normalize
from gtts import gTTS
from playsound import playsound
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import json
from translate import Translator
import ttkthemes as ttkt


# Load settings from file
with open('settings.txt', 'r') as f:
    settings = json.load(f)
lang = settings['lang']
speed = settings['speed']

languages = {
    'af': 'Afrikaans',
    'ar': 'Arabic',
    'bg': 'Bulgarian',
    'bn': 'Bengali',
    'bs': 'Bosnian',
    'ca': 'Catalan',
    'cs': 'Czech',
    'da': 'Danish',
    'de': 'German',
    'el': 'Greek',
    'en': 'English',
    'es': 'Spanish',
    'et': 'Estonian',
    'fi': 'Finnish',
    'fr': 'French',
    'gu': 'Gujarati',
    'hi': 'Hindi',
    'hr': 'Croatian',
    'hu': 'Hungarian',
    'id': 'Indonesian'
}

speeds = {
    '0.5': 'Slow',
    '1.0': 'Normal',
    '1.5': 'Fast'
}

questions = [
    "Does the child have any allergies to medicines, food, or any vaccine?",
    "Has the child had a serious reaction to a vaccine in the past?",
]

# Translate questions
def translate_questions(lang):
    translator = Translator(to_lang=lang)
    return [translator.translate(q) for q in questions]

questions = translate_questions(lang)

class TriageSystem:
    def __init__(self, timeout=30):
        self.timeout = timeout
        self.questions = questions
        self.responses = {}

    def ask_question(self, question_index):
        response_entry.delete('1.0', tk.END)
        
        question = self.questions[question_index]
        question_label.configure(text=question)
        question_label.update()

        # convert the question to speech
        tts = gTTS(text=question, lang=lang)
        tts.save("question.mp3")

        # play the question
        playsound("question.mp3")

        response_entry.insert('1.0', 'Start speaking...')

        # record the patient's response
        r = sr.Recognizer()
        with sr.Microphone() as source:
            # adjust for ambient noise
            r.adjust_for_ambient_noise(source, duration=1)
            audio = r.listen(source, timeout=self.timeout)

        # try recognizing the speech in the audio
        try:
            # use the 'default' language model and show all results
            response = r.recognize_google(audio, language=lang, show_all=False)
            self.responses[question] = response
        except sr.UnknownValueError:
            self.responses[question] = "Google Speech Recognition could not understand audio"
        except sr.RequestError as e:
            self.responses[question] = f"Error: {e}"

        response_entry.delete('1.0', tk.END)
        response_entry.insert('1.0', self.responses[question])
        response_entry.update()

        # convert the question to speech
        tts = gTTS(text=self.responses[question], lang=lang)
        tts.save("response.mp3")

        # play the question
        playsound("response.mp3")

        # delete the question file to avoid permission issues
        if os.path.exists("question.mp3"):
            os.remove("question.mp3")
        if os.path.exists("response.mp3"):
            os.remove("response.mp3")

# Global variables
triage_system = TriageSystem(timeout=60)
question_index = 0

def start_triage():
    global question_index
    
    response_entry.configure(height=10)
    response_entry.update()

    if question_index == len(triage_system.questions) - 1:
        start_button.configure(text='Finish triage')

    elif question_index >= len(triage_system.questions):
        messagebox.showinfo("Triage Complete", "Triage process completed.")
        print(triage_system.responses)
        window.destroy()
        return

    question_label.configure(text=triage_system.questions[question_index])
    triage_system.ask_question(question_index)
    question_index += 1
    response_entry.delete('1.0', tk.END)
    response_entry.insert('1.0', triage_system.responses[triage_system.questions[question_index-1]])

def show_settings():
    setting = tk.Tk()
    setting.title("Settings")

    lang_label = ttk.Label(setting, text='Language:', font=("Arial", 14))
    lang_label.pack(pady=5)

    lang_var = tk.StringVar(setting)
    lang_var.set(languages[lang])  # set default value

    lang_dropdown = ttk.OptionMenu(setting, lang_var, *languages.values())
    lang_dropdown.pack()

    speed_label = ttk.Label(setting, text='Speed:', font=("Arial", 14))
    speed_label.pack(pady=5)

    speed_var = tk.StringVar(setting)
    speed_var.set(speeds[str(speed)])  # set default value

    speed_dropdown = ttk.OptionMenu(setting, speed_var, *speeds.values())
    speed_dropdown.pack()

    def apply_settings():
        global lang, speed
        lang = list(languages.keys())[list(languages.values()).index(lang_var.get())]
        speed = float(list(speeds.keys())[list(speeds.values()).index(speed_var.get())])
        # Translate questions
        global questions
        questions = translate_questions(lang)
        # Save settings to file
        with open('settings.txt', 'w') as f:
            json.dump({'lang': lang, 'speed': speed}, f)
        setting.destroy()

    apply_button = ttk.Button(setting, text="Apply", command=apply_settings, style="TButton", padding=(10, 5))
    apply_button.pack()


# Create the main window
window = ttkt.ThemedTk()
window.set_theme("yaru")  # yaru, plastik
window.title("Triage System")

# Set the background color of the window to turquoise
window.configure(background='turquoise')

# Create a style
style = ttk.Style()

# Set the background color of the TButton to turquoise and the foreground color to red
style.configure("TButton", background='turquoise', foreground='red', font=("Arial", 18))

# Set the background color of the TLabel to turquoise and the foreground color to red
style.configure("TLabel", background='turquoise', foreground='red')

# Create a label to display the current question with a larger border, larger font, and yellow background
question_label = ttk.Label(window, text='Enter name:', font=("Arial", 18), relief="solid", borderwidth=4, background='yellow')
question_label.pack(pady=20, padx=20)  # Add some padding to create space around the label

# Create an entry field to display and edit the user's response with a larger border, larger font, and yellow background
response_label = ttk.Label(window, text="Your Response:", font=("Arial", 18), relief="solid", borderwidth=4, background='yellow')
response_label.pack(pady=5, padx=20)  # Add some padding to create space around the label

class ResponseEntry(tk.Text):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(font=("Arial", 18), wrap=tk.WORD, bg='turquoise', fg='red')

response_entry = ResponseEntry(window, width=50, height=1)
response_entry.pack(pady=10)  # Add some padding to create space between the text box and the buttons

# Create a button to start/continue the triage process with increased padding
start_button = ttk.Button(window, text="Start/Next Question", command=start_triage, style="TButton", padding=(20, 10))
start_button.pack(pady=10)  # Add some padding to create space between the text box and the buttons

settings_button = ttk.Button(window, text="Settings", command=show_settings, style="TButton", padding=(20, 10))
settings_button.pack(pady=10)  # Add some padding to create space between the text box and the buttons

# Set the window size and center it on the screen
window.geometry("1000x500")
window.eval('tk::PlaceWindow %s center' % window.winfo_toplevel())

# Start the GUI event loop
window.mainloop()

