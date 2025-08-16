import os
import time
import subprocess
import sqlite3
import struct
import webbrowser
import eel
import pyautogui
import pyaudio
import pvporcupine
import pywhatkit as kit
import pygetwindow as gw
from playsound import playsound  # type: ignore
from engine.helper import extract_yt_term, remove_words
from engine.speaker import speak
import google.generativeai as genai 
from dotenv import load_dotenv

con = sqlite3.connect("jarvis.db")
cursor = con.cursor()

@eel.expose
def playAssistantSound():
    music_dir = "www\\assets\\audio\\start_sound.mp3"
    playsound(music_dir)

def OpenCommand(query):
    query = query.replace("jarvis", "").replace("open", "").lower().strip()

    if query != "":
        try:
            cursor.execute('SELECT path FROM sys_command WHERE name IN (?)', (query,))
            results = cursor.fetchall()
            if results:
                speak("Opening " + query)
                os.startfile(results[0][0])
                return

            cursor.execute('SELECT url FROM web_command WHERE name IN (?)', (query,))
            results = cursor.fetchall()
            if results:
                speak("Opening " + query)
                webbrowser.open(results[0][0])
                return

            speak("Opening " + query)
            os.system('start ' + query)
        except Exception as e:
            speak("Something went wrong")
            print(f"OpenCommand error: {e}")

def PlayYoutube(query):
    search_term = extract_yt_term(query)
    if search_term:
        speak("Playing " + search_term + " on YouTube")
        kit.playonyt(search_term)
    else:
        speak("Sorry, I couldn't understand")

def hotword():
    porcupine = None
    paud = None
    audio_stream = None
    try:
        porcupine = pvporcupine.create(keywords=["jarvis", "alexa"])
        paud = pyaudio.PyAudio()
        audio_stream = paud.open(rate=porcupine.sample_rate, channels=1, format=pyaudio.paInt16, input=True, frames_per_buffer=porcupine.frame_length)

        while True:
            keyword = audio_stream.read(porcupine.frame_length)
            keyword = struct.unpack_from("h" * porcupine.frame_length, keyword)
            keyword_index = porcupine.process(keyword)

            if keyword_index >= 0:
                print("Hotword detected")
                pyautogui.hotkey("win", "j")
                time.sleep(2)

    except Exception as e:
        print(f"Hotword detection error: {e}")
    finally:
        if porcupine:
            porcupine.delete()
        if audio_stream:
            audio_stream.close()
        if paud:
            paud.terminate()

def findContact(query):
    words_to_remove = ['jarvis', 'make', 'a', 'to', 'phone', 'call', 'send', 'message', 'whatsapp', 'video']
    query = remove_words(query, words_to_remove).strip().lower()

    try:
        cursor.execute("SELECT mobile_no FROM contacts WHERE LOWER(name) LIKE ? OR LOWER(name) LIKE ?",
                       ('%' + query + '%', query + '%'))
        results = cursor.fetchall()
        if results:
            mobile_number_str = str(results[0][0])
            if not mobile_number_str.startswith('+91'):
                mobile_number_str = '+91' + mobile_number_str
            return mobile_number_str, query
        else:
            speak('Contact not found in database')
            return 0, 0
    except Exception as e:
        speak('Database error occurred')
        print(f"findContact error: {e}")
        return 0, 0

def whatsApp(mobile_no, message, flag, name):
    try:
        if flag == 'message':
            speak(f"Sending message to {name}")
            encoded_message = message.replace(' ', '%20')
            whatsapp_url = f"whatsapp://send?phone={mobile_no}&text={encoded_message}"
            subprocess.run(f'start "" "{whatsapp_url}"', shell=True)
            time.sleep(5)

            try:
                window = gw.getWindowsWithTitle('WhatsApp')[0]
                window.activate()
                time.sleep(1)
            except:
                speak("Could not focus WhatsApp window")
                return

            pyautogui.press('enter')
            speak(f"Message sent to {name}")

        elif flag == 'call':
            whatsApp_call(mobile_no, name, call_type="audio")

        elif flag == 'video call':
            whatsApp_call(mobile_no, name, call_type="video")

    except Exception as e:
        speak(f"Failed WhatsApp operation: {e}")
        print(f"whatsApp error: {e}")

def whatsApp_call(mobile_no, name, call_type="audio"):
    speak(f"Calling {name} on WhatsApp")
    whatsapp_url = f"whatsapp://send?phone={mobile_no}"
    subprocess.run(f'start "" "{whatsapp_url}"', shell=True)
    time.sleep(5)

    try:
        window = gw.getWindowsWithTitle('WhatsApp')[0]
        window.activate()
        time.sleep(1)
    except:
        speak("Could not focus WhatsApp window")
        return

    button_image = f"engine/{call_type}_call.png"
    print(f"Looking for {call_type} call button using image: {button_image}")

    for _ in range(3):
        button_location = pyautogui.locateCenterOnScreen(button_image, confidence=0.8)
        if button_location:
            pyautogui.moveTo(button_location)
            pyautogui.click()
            speak(f"{call_type.capitalize()} call started")
            return
        time.sleep(2)

    speak(f"Could not find {call_type} call button on screen")


def click_button(image_path, confidence=0.8, attempts=3, delay=2):
    for _ in range(attempts):
        button_location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
        if button_location:
            pyautogui.moveTo(button_location)
            pyautogui.click()
            print(f"Clicked on {image_path}")
            return True
        time.sleep(delay)
    print(f"Could not find {image_path}")
    return False


load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("⚠️ Gemini API Key not found. Please check your .env file.")

@eel.expose
def ask_gemini(query: str):
    """Send query to Gemini and get response"""
    try:
        if not GEMINI_API_KEY:
            speak("Gemini API key not configured")
            return "Gemini API key not found"

        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(query)

        if response and response.text:
            answer = response.text
            speak(answer)   # Make Jarvis speak the answer
            return answer
        else:
            speak("Sorry, I didn't get any response")
            return "No response from Gemini"

    except Exception as e:
        error_message = f"Gemini chat error: {e}"
        print(error_message)
        speak("Something went wrong while connecting to Gemini")
        return error_message