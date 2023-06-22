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
import noisereduce as nr
import librosa
import soundfile as sf
import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
import requests
from bs4 import BeautifulSoup
from collections import Counter


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
##    "Has the child had a seizure or a brain (neurological problem) problem?"
##    "Does the child have cancer, leukemia, AIDS, or any other immune system problem",
##    "Has the child taken cortisone, prednisone, other steroids, or anticancer drugs, like chemotherapy or radiotherapy in the past three months",
##    "Has the child received blood transfusion or blood products, or been given a medicine called immune (gamma) globulin in the past year",
##    "Is the young adult pregnant or is there a possibility of pregnancy in the next month",
##    "Has the child received any vaccinations in the past four weeks",
##    "Does the child / young adult have a past history of Guillain-Barré syndrome / has a chronic illness / has a bleeding disorder",
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
        filename = f"question_{question_index}.mp3"  # Use a unique filename for each question
        tts.save(filename)

        # play the question
        playsound(filename)

        response_entry.insert('1.0', 'Start speaking...')

        # record the patient's response
        r = sr.Recognizer()
        with sr.Microphone() as source:
            # adjust for ambient noise
            r.adjust_for_ambient_noise(source, duration=1)
            audio = r.listen(source, timeout=self.timeout)

        # save the audio to a file
        with open("response.wav", "wb") as file:
            file.write(audio.get_wav_data())

        # load the audio file
        audio = AudioSegment.from_wav("response.wav")

        # normalize the audio file
        audio = normalize(audio)

        # save the cleaned audio file
        audio.export("cleaned_response.wav", format="wav")

        # try recognizing the speech in the cleaned audio
        with sr.AudioFile("cleaned_response.wav") as source:
            audio = r.record(source)
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
        response_filename = f"response_{question_index}.mp3"  # Use a unique filename for each response
        tts.save(response_filename)

        # play the question
        playsound(response_filename)

        # delete the question file to avoid permission issues
        if os.path.exists(filename):
            os.remove(filename)
        if os.path.exists(response_filename):
            os.remove(response_filename)
        if os.path.exists("response.wav"):
            os.remove("response.wav")
        if os.path.exists("cleaned_response.wav"):
            os.remove("cleaned_response.wav")

    def process_responses(self):
        category_keywords = self.scrape_symptom_keywords()

        results = []
        for question, response in self.responses.items():
            category = self.categorize_response(response, category_keywords)
            results.append((question, response, category))

        return results

    def scrape_symptom_keywords(self):
        # Define the URLs of the webpages for each category
        category_urls = {
            1: "https://www.mayoclinic.org/diseases-conditions/heart-attack/symptoms-causes/syc-20373106",
            2: "https://www.webmd.com/asthma/guide/asthma-symptoms",
            3: "https://www.mayoclinic.org/diseases-conditions/anaphylaxis/symptoms-causes/syc-20351468",
            4: "https://www.mayoclinic.org/diseases-conditions/broken-bones/symptoms-causes/syc-20353674",
            5: "https://www.mayoclinic.org/diseases-conditions/common-cold/symptoms-causes/syc-20351605",
        }
        # Create an empty dictionary to hold the symptom keywords for each category
        category_keywords = {}

        # Scrape symptom keywords for each category
        for category, url in category_urls.items():
            # Send a GET request to the webpage
            response = requests.get(url)

            # Parse the HTML content of the page with BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            print(soup)

            # Find all instances of a certain HTML element that contains the symptoms
            symptom_elements = soup.find_all('div', class_='symptom')
            print(symptom_elements)

            # Create an empty list to hold the symptom keywords
            symptoms = []

            # Extract the text content of each symptom element and add it to the list
            for element in symptom_elements:
                symptoms.append(element.text)

            # Add the list of symptom keywords to the category_keywords dictionary
            category_keywords[category] = symptoms
        print(category_keywords)
        return category_keywords

    def categorize_response(self, response, category_keywords):
        response = response.lower()

        # Categorize the response based on the presence of symptom keywords
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in response:
                    return category

        # If no keywords match, default to category 5
        return 5
    

# Global variables
triage_system = TriageSystem(timeout=60)
question_index = 0
def start_triage():
    global question_index
    
    # Save the edited response to the responses dictionary
    if question_index > 0:
        edited_response = response_entry.get('1.0', 'end-1c')  # Get the current text in the response_entry widget
        triage_system.responses[triage_system.questions[question_index-1]] = edited_response  # Save the edited response to the responses dictionary

    response_entry.configure(height=10)
    response_entry.update()

    if question_index == len(triage_system.questions) - 1:
        start_button.configure(text='Finish triage')

    elif question_index >= len(triage_system.questions):
        edited_response = response_entry.get('1.0', 'end-1c')  # Get the current text in the response_entry widget
        triage_system.responses[triage_system.questions[question_index-1]] = edited_response  # Save the edited response to the responses dictionary
        print(triage_system.responses)
        print("")
        # Process responses and print responses and categorization
        categorization = triage_system.process_responses()
        print("Responses:")
        for question, response in triage_system.responses.items():
            print(f"Question: {question}\nResponse: {response}\n")
        print(f"Categorization: {categorization}")
        print("")
        triage_info = """Categories: Triage category 1
            People who need to have treatment immediately or within two minutes are categorised as having an immediately life-threatening condition.

            People in this category are critically ill and require immediate attention. Most would have arrived in emergency department by ambulance. They would probably be suffering from a critical injury or cardiac arrest.

            Triage category 2
            People who need to have treatment within 10 minutes are categorised as having an imminently life-threatening condition.

            People in this category are suffering from a critical illness or in very severe pain. People with serious chest pains, difficulty in breathing or severe fractures are included in this category.

            Triage category 3
            People who need to have treatment within 30 minutes are categorised as having a potentially life-threatening condition.

            People in this category are suffering from severe illness, bleeding heavily from cuts, have major fractures or are severely dehydrated.

            Triage category 4
            People who need to have treatment within one hour are categorised as having a potentially serious condition.

            People in this category have less severe symptoms or injuries, such as a foreign body in the eye, sprained ankle, migraine or earache.

            Triage category 5
            People who need to have treatment within two hours are categorised as having a less urgent condition.

            People in this category have minor illnesses or symptoms that may have been present for more than a week, such as rashes or minor aches and pains."""
##        print(triage_info)

        messagebox.showinfo("Triage Complete", "Triage process completed.")
        window.destroy()
        return

    # Update the question label with the translated question
    question_label.configure(text=triage_system.questions[question_index])
    triage_system.ask_question(question_index)
    question_index += 1
    response_entry.delete('1.0', tk.END)
    response_entry.insert('1.0', triage_system.responses[triage_system.questions[question_index-1]])



def show_settings():
    setting = tk.Toplevel(window)  # Use Toplevel instead of Tk to create a new window
    setting.title("Settings")

    # Set the background color of the window to white
    setting.configure(background='white')
    setting.geometry("200x200")

    lang_label = tk.Label(setting, text='Language:', font=("Arial", 14), background='#dc3545', foreground='white')
    lang_label.pack(pady=5)

    lang_var = tk.StringVar(setting)
    lang_var.set(languages[lang])  # set default value

    lang_dropdown = ttk.OptionMenu(setting, lang_var, *languages.values())
    lang_dropdown.pack()

    speed_label = tk.Label(setting, text='Speed:', font=("Arial", 14), background='#dc3545', foreground='white')
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
        # Update the questions in the TriageSystem
        triage_system.questions = questions
        # Save settings to file
        with open('settings.txt', 'w') as f:
            json.dump({'lang': lang, 'speed': speed}, f)
        setting.destroy()

    apply_button = tk.Button(setting, text="Apply", command=apply_settings, bg='#007bff', fg='white', font=("Arial", 18), padx=10, pady=5)
    apply_button.pack()

# Create the main window
window = tk.Tk()
window.title("Triage System")

# Set the background color of the window to white
window.configure(background='white')

# Create a label to display the current question with a larger border, larger font, and red background
question_label = tk.Label(window, text='Enter name:', font=("Arial", 18), relief="solid", background='#dc3545', foreground='white', borderwidth=0, anchor='center', justify='center')
question_label.pack(pady=20, padx=20, ipadx=20, ipady=10)  # Add some padding to create space around the label and inside the label

# Create an entry field to display and edit the user's response with a larger border, larger font, and red background
response_label = tk.Label(window, text="Your Response:", font=("Arial", 18), relief="solid", background='#dc3545', foreground='white', borderwidth=0, anchor='center', justify='center')
response_label.pack(pady=5, padx=20, ipadx=20, ipady=10)  # Add some padding to create space around the label and inside the label

class ResponseEntry(tk.Text):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(font=("Arial", 18), wrap=tk.WORD, bg='azure2', fg='red')

response_entry = ResponseEntry(window, width=60, height=1)
response_entry.pack(pady=15)  # Add some padding to create space between the text box and the buttons

# Create a button to start/continue the triage process with increased padding
start_button = tk.Button(window, text="Start/Next Question", command=start_triage, bg='#007bff', fg='black', font=("Arial", 18), padx=20, pady=10)
start_button.pack(pady=10)  # Add some padding to create space between the text box and the buttons

settings_button = tk.Button(window, text="Settings", command=show_settings, bg='#6c757d', fg='black', font=("Arial", 18), padx=20, pady=10)
settings_button.pack(pady=10)  # Add some padding to create space between the text box and the buttons

# Set the window size and center it on the screen
window.geometry("1000x1000")
window.eval('tk::PlaceWindow %s center' % window.winfo_toplevel())

# Start the GUI event loop
window.mainloop()

