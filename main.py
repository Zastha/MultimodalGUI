import threading
import subprocess
import os
import time
from datetime import datetime

python_interpreter = "python.exe"
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
output_folder_path = os.path.join("csv_output", timestamp)

def run_GUI():
    subprocess.run([python_interpreter, "GUI.py", output_folder_path])

def run_eeg_recorder():
    subprocess.run([python_interpreter, "EEGSaver.py", output_folder_path])

# Crear carpeta si no existe
os.makedirs(output_folder_path, exist_ok=True)

# Crear hilos para cada script
threadEEG = threading.Thread(target=run_eeg_recorder)

# Iniciar los hilos para EEG
threadEEG.start()


# Ejecutar la GUI
run_GUI()

# Esperar a que los hilos de EEG terminen
threadEEG.join()

print("Todos los procesos han terminado.")
