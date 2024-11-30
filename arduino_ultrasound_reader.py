import serial
import time

def read_ultrasound_data(port, baud_rate=9600):
    try:
        # Ouverture de la connexion série
        with serial.Serial(port, baud_rate, timeout=1) as ser:
            print(f"Connexion établie sur le port {port} avec un débit de {baud_rate} bauds.")
            
            while True:
                # Lecture des données envoyées par l'Arduino
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8').strip()
                    if '#' in line:
                        # Séparer les données des deux capteurs
                        accel_data, brake_data = line.split('#')
                        print(f"Distance de l'accélérateur: {accel_data} cm")
                        print(f"Distance du frein: {brake_data} cm")
                time.sleep(0.1)

    except serial.SerialException as e:
        print(f"Erreur de connexion série : {e}")
    except KeyboardInterrupt:
        print("Arrêt du programme.")

if __name__ == "__main__":
    port = "COM3"  
    read_ultrasound_data(port)
