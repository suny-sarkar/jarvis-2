import speech_recognition as sr
import eel
import time
from engine.speaker import speak
from engine.features import OpenCommand, PlayYoutube, findContact, whatsApp, ask_gemini  # Import inside function
def takecommand():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print('Listening...')
        eel.DisplayMessage('Listening...')
        r.pause_threshold = 1
        r.adjust_for_ambient_noise(source)

        try:
            audio = r.listen(source, timeout=12, phrase_time_limit=20)
            print('Recognizing...')
            eel.DisplayMessage('Recognizing...')
            query = r.recognize_google(audio, language='en-in')
            print(f"User said: {query}")
            eel.DisplayMessage(query)
            time.sleep(1)
        except Exception as e:
            print(f"Error recognizing speech: {e}")
            eel.DisplayMessage("Sorry, I didn't catch that.")
            return ""

        return query.lower()

@eel.expose
def allCommands(message=1):

    if message == 1:
        query = takecommand()
        print(query)
        eel.senderText(query)
    else:
        query = message.lower()
        eel.senderText(query)
    if not query:
        speak("Please say that again.")
        return

    try:
        if "open" in query:
            OpenCommand(query)

        elif "on youtube" in query:
            PlayYoutube(query)

        elif "send message" in query or "phone call" in query or "video call" in query:
            flag = ""
            contact_no, name = findContact(query)
            if contact_no != 0:
                if "send message" in query:
                    flag = 'message'
                    speak("What message should I send?")
                    message_content = takecommand()
                    whatsApp(contact_no, message_content, flag, name)
                elif "phone call" in query:
                    flag = 'call'
                    whatsApp(contact_no, "", flag, name)
                else:
                    flag = 'video call'
                    whatsApp(contact_no, "", flag, name)
        else:
            # Fallback to Gemini if no system command matched
            answer = ask_gemini(query)
            eel.receiverText(answer)

    except Exception as e:
        print(f"Error in allCommands: {e}")
        eel.DisplayMessage("An error occurred while processing your command.")
    
    eel.ShowHood()
