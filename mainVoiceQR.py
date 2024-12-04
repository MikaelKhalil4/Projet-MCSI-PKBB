from QRCodeDetection import QRDetector
#from voiceAction import AudioProcessor


def main_voice_qr():
    server_address = 'localhost'  # TODO change this when running on different machines

    qr_port = 6007
    voice_port = 6008

    #model_path = r"C:\Users\DELL\Desktop\Yassine\Projet-MCSI-PKBB\model\vosk-model-small-en-us-0.15"
    #audio_processor = AudioProcessor(model_path, server_address, voice_port)
    #audio_processor.run()

    qr_detector = QRDetector(server_address, qr_port)
    qr_detector.run()


if __name__ == "__main__":
    main_voice_qr()
