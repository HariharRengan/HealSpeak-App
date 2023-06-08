import os
import speech_recognition as sr
from pydub import AudioSegment
from pydub.effects import normalize
from gtts import gTTS
from playsoundLocal import playsound
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

questions = [
    "Does the child have any allergies to medicines, food, or any vaccine?",
    "Has the child had a serious reaction to a vaccine in the past?"
]

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
        tts = gTTS(text=question, lang='en', tld='co.in')
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
            response = r.recognize_google(audio, language='en-US', show_all=False)
            self.responses[question] = response
        except sr.UnknownValueError:
            self.responses[question] = "Google Speech Recognition could not understand audio"
        except sr.RequestError as e:
            self.responses[question] = f"Error: {e}"

        response_entry.delete('1.0', tk.END)
        response_entry.insert('1.0', self.responses[question])
        response_entry.update()

        # convert the question to speech
        tts = gTTS(text=self.responses[question], lang='en', tld='co.in')
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



# Create the main window
window = tk.Tk()
window.title("Triage System")

# Create a label to display the current question
question_label = ttk.Label(window, text='Enter name:', font=("Arial", 16))
question_label.pack(pady=20)

# Create an entry field to display and edit the user's response
response_label = ttk.Label(window, text="Your Response:", font=("Arial", 14))
response_label.pack(pady=5)

class ResponseEntry(tk.Text):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(font=("Arial", 12), wrap=tk.WORD)

response_entry = ResponseEntry(window, width=50, height=10)
response_entry.pack()

# Create a button to start/continue the triage process
start_button = ttk.Button(window, text="Start/Next Question", command=start_triage, style="TButton", padding=(10, 5))
start_button.pack()

# Set the window size and center it on the screen
window.geometry("1000x500")
window.eval('tk::PlaceWindow %s center' % window.winfo_toplevel())

# Configure ttk style
style = ttk.Style(window)
style.configure("TButton", font=("Arial", 14))

# Start the GUI event loop
window.mainloop()
