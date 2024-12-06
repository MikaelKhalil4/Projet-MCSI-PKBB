import sounddevice as sd
import queue
import sys
import json
import socket
import time
from vosk import Model, KaldiRecognizer

from Reworked import GamepadController


class VoiceActionReworked:
    def __init__(self, gamepad_controller : GamepadController, model_path = r"model\vosk-model-small-en-us-0.15", target_word="fire"):
        self.model_path = model_path
        self.target_word = target_word.lower()
        self.audio_queue = queue.Queue()
        self.running = True
        self.last_detection_time = 0
        self.detection_cooldown = 2.0  # Cooldown period in seconds
        self.gc = gamepad_controller

        # Initialize model and recognizer
        try:
            self.model = Model(model_path)
            self.recognizer = KaldiRecognizer(self.model, 16000)
        except Exception as e:
            raise Exception(f"Failed to load model: {str(e)}")


    def audio_callback(self, indata, frames, time_info, status):
        """Callback function for audio stream"""
        if status:
            print(f"Audio stream error: {status}", file=sys.stderr)
        self.audio_queue.put(bytes(indata))

    def process_audio(self):
        """Process audio data from the queue"""
        try:
            data = self.audio_queue.get(timeout=1)
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                if 'text' in result and result['text']:
                    self.check_for_target_word(result['text'], is_partial=False)
            else:
                partial = json.loads(self.recognizer.PartialResult())
                if 'partial' in partial and partial['partial']:
                    self.check_for_target_word(partial['partial'], is_partial=True)
        except queue.Empty:
            pass
        except json.JSONDecodeError:
            print("Error decoding speech recognition result", file=sys.stderr)
        except Exception as e:
            print(f"Error processing audio: {str(e)}", file=sys.stderr)

    def check_for_target_word(self, text, is_partial):
        """Check if target word is in the recognized text"""
        current_time = time.time()
        if self.target_word in text.lower():
            # Immediate detection: send command if cooldown allows
            if current_time - self.last_detection_time >= self.detection_cooldown:
                print(f"\nINSTANT DETECTION: '{self.target_word.upper()}'!")
                print(f"Recognized text: {text}")

                # Send command to server immediately
                self.send_fire_command()
                self.last_detection_time = current_time

    def send_fire_command(self):
        """Send the 'FIRE' command to the server"""
        try:
            self.gc.send_instant_command("FIRE")
        except Exception as e:
            print(f"Failed to send command: {str(e)}", file=sys.stderr)

    def run(self):
        """Main run loop"""
        try:
            stream = sd.RawInputStream(
                samplerate=16000,
                blocksize=8000,
                dtype="int16",
                channels=1,
                callback=self.audio_callback
            )

            print(f"\nListening for '{self.target_word}'...")
            print("Press Ctrl+C to stop\n")

            with stream:
                while self.running:
                    self.process_audio()

        except KeyboardInterrupt:
            self.running = False
            print("\nStopping...")
        except Exception as e:
            print(f"\nError in audio stream: {str(e)}", file=sys.stderr)
        finally:
            if 'stream' in locals():
                stream.close()
            


def main():
    try:
        # Update this path to your model location
        model_path = r"model\vosk-model-small-en-us-0.15"
        #processor = AudioProcessor(model_path)
        #processor.run()
    except Exception as e:
        print(f"Fatal error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
