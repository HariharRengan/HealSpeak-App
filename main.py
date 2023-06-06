import os
import speech_recognition as sr
from pydub import AudioSegment
from pydub.effects import normalize
from gtts import gTTS
from playsound import playsound

namesauce = 'name'

class Patient:
    def __init__(self, name):
        self.name = name
        self.responses = {}

class TriageSystem:
    def __init__(self, timeout=5):
        self.patients = []
        self.timeout = timeout
        self.questions = [
##            "How old are you",
##            "Is the child sick today",
            "Does the child have any allergies to medicines, food, or any vaccine",
            "Has the child had a serious reaction to a vaccine in the past",
##            "Has the child had a seizure or a brain (neurological problem) problem?"
##            "Does the child have cancer, leukemia, AIDS, or any other immune system problem",
##            "Has the child taken cortisone, prednisone, other steroids, or anticancer drugs, like chemotherapy or radiotherapy in the past three months",
##            "Has the child received blood transfusion or blood products, or been given a medicine called immune (gamma) globulin in the past year",
##            "Is the young adult pregnant or is there a possibility of pregnancy in the next month",
##            "Has the child received any vaccinations in the past four weeks",
##            "Does the child / young adult have a past history of Guillain-Barré syndrome / has a chronic illness / has a bleeding disorder",
        ]

    def add_patient(self, patient):
        self.patients.append(patient)

    def ask_questions(self, patient):
        r = sr.Recognizer()

        for question in self.questions:
            # convert the question to speech
            tts = gTTS(text=question, lang='en')
            tts.save("question.mp3")

            # wait for user confirmation before playing the question and recording the patient's response
            proceed = input("Press 'Y' to listen to the question and record the patient's response.")
            if proceed.lower() != 'y':
                continue

            # play the question
            playsound("question.mp3")

            # record the patient's response
            with sr.Microphone() as source:
                # adjust for ambient noise
                r.adjust_for_ambient_noise(source, duration=1)
                print("Listening for patient's response...")
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

    def triage(self):
        for patient in self.patients:
            self.ask_questions(patient)
            print(f"Patient {patient.name}'s responses: {patient.responses}")

triage_system = TriageSystem(timeout=5)
     
# Add some patients
triage_system.add_patient(Patient(namesauce))

# Triage the patients
triage_system.triage()
