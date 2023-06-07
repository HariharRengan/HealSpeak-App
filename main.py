import os
import speech_recognition as sr
from pydub import AudioSegment
from pydub.effects import normalize
from gtts import gTTS
from playsoundLocal import playsound
import tkinter as tk
from tkinter import messagebox

class Patient:
    def __init__(self, name):
        self.name = name
        self.responses = {}

class TriageSystem:
    def __init__(self, timeout=5):
        self.patients = []
        self.timeout = timeout
        self.questions = [
            "Does the child have any allergies to medicines, food, or any vaccine",
            "Has the child had a serious reaction to a vaccine in the past",
        ]

    def add_patient(self, patient):
        self.patients.append(patient)

    def ask_questions(self, patient, question_label):
        r = sr.Recognizer()

        for question in self.questions:
            question_label.configure(text=question)

            # convert the question to speech
            tts = gTTS(text=question, lang='en')
            tts.save("question.mp3")

            # wait for user confirmation before playing the question and recording the patient's response
            proceed = messagebox.askyesno("Question", "Press 'Yes' to listen to the question and record the patient's response.")
            if not proceed:
                continue

            # play the question
            playsound("question.mp3")

            # record the patient's response
            with sr.Microphone() as source:
                # adjust for ambient noise
                r.adjust_for_ambient_noise(source, duration=1)
                question_label.configure(text="Listening for patient's response...")
                audio = r.listen(source, timeout=self.timeout)

            # try recognizing the speech in the audio
            try:
                # use the 'default' language model and show all results
                response = r.recognize_google(audio, language='en-US', show_all=False)
                patient.responses[question] = response
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand audio")
            except sr.RequestError as e:
                print("Could not request results from Google Speech Recognition service; {0}".format(e))

            # delete the question file to avoid permission issues
            if os.path.exists("question.mp3"):
                os.remove("question.mp3")

    def triage(self, question_label, name):
        patient = Patient(name)
        self.ask_questions(patient, question_label)
        print(f"Patient {patient.name}'s responses: {patient.responses}")

# Create the GUI
def start_triage():
    triage_system = TriageSystem(timeout=5)
    name = name_entry.get()

    if name:
        triage_system.triage(question_label, name)
    else:
        messagebox.showinfo("Error", "Please enter a name.")

# Create the main window
window = tk.Tk()
window.title("Triage System")

# Create a label and input field for the patient's name
name_label = tk.Label(window, text="Enter patient's name:", font=("Arial", 14))
name_label.pack(pady=10)
name_entry = tk.Entry(window, font=("Arial", 12))
name_entry.pack(pady=5)

# Create a label to display the current question
question_label = tk.Label(window, text="Question", wraplength=400, font=("Arial", 16))
question_label.pack(pady=20)

# Create a button to start the triage process
start_button = tk.Button(window, text="Start Triage", command=start_triage, font=("Arial", 14), padx=10, pady=5)
start_button.pack()

# Set the window size and center it on the screen
window.geometry("500x300")
window.eval('tk::PlaceWindow %s center' % window.winfo_toplevel())

# Start the GUI event loop
window.mainloop()
