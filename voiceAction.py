import speech_recognition as sr
import socket

def detect_fire():
    # Initialize the recognizer
    recognizer = sr.Recognizer()
    
    # Setup socket for sending commands to stk_server
    server_address = ('localhost', 6006)  # Address and port of stk_server
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Use the microphone as the source of input
    with sr.Microphone() as source:
        print("Listening for the word 'fire'... Speak clearly.")
        while True:
            try:
                # Listen to audio
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source)

                # Recognize speech using Google's speech recognition API
                
                text = recognizer.recognize_google(audio)
                
                print(f"You said: {text}")

                # Check if the word 'fire' is detected
                if "fire" in text.lower():
                    print("Alert! The word 'fire' was detected!")
                    # Send "FIRE" command to stk_server
                    sock.sendto(b"FIRE", server_address)
                    
            except sr.UnknownValueError:
                print("Could not understand audio, please speak again.")
            except sr.RequestError as e:
                print(f"Could not request results from the recognition service; {e}")
                break

if __name__ == "__main__":
    detect_fire()
