import csv
import sys
from pylsl import StreamInlet, resolve_stream
import datetime
import threading
import os

class EEGRecorder:
    def __init__(self, filename, stop_signal_file):
        self.filename = filename
        self.stop_event = threading.Event()
        self.stop_signal_file = stop_signal_file

    def start_recording(self):
        # Resolver y conectar al stream LSL 'AURAPSD'
        print("Buscando el stream 'AURAPSD'...")
        streams = resolve_stream('name', 'AURA_Power')
        inlet = StreamInlet(streams[0])
        print("Conectado al stream.")

        # Configurar el archivo CSV
        with open(self.filename, mode='w', newline='') as archivo_csv:
            escritor_csv = csv.writer(archivo_csv)

            nombres_columnas = ['Time and date']

            # Generar nombres de columnas para Delta, Theta, Alpha, Beta, Gamma desde 1 hasta 8
            for i in range(1, 9):
                nombres_columnas.extend([f'Delta{i}', f'Theta{i}', f'Alpha{i}', f'Beta{i}', f'Gamma{i}'])

            # Añadir la columna 'Event'
            nombres_columnas.append('Event')

            print(nombres_columnas)

            escritor_csv.writerow(nombres_columnas)

            # Leer datos del stream y guardar en CSV
            try:
                while not self.stop_event.is_set():
                    if os.path.exists(self.stop_signal_file):
                        self.stop_event.set()
                        os.remove(self.stop_signal_file)
                        break

                    sample, timestamp = inlet.pull_sample()
                    current_time = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S.%f')[:-3]  # Formato con milisegundos
                    sample_with_time = [current_time] + sample + [0]  # Añadir la marca de tiempo y un marcador de evento
                    escritor_csv.writerow(sample_with_time)
                    print(f"Datos guardados: {sample_with_time}")
            except KeyboardInterrupt:
                print("Guardado finalizado.")

    def stop_recording(self):
        self.stop_event.set()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python EEGSaver.py <output_folder_path>")
        sys.exit(1)

    output_folder_path = sys.argv[1]
    filename = os.path.join(output_folder_path, "datos_psd2.csv")
    stop_signal_file = os.path.join(output_folder_path, "stop_signal")
    os.makedirs(output_folder_path, exist_ok=True)
    eeg_recorder = EEGRecorder(filename, stop_signal_file)
    eeg_thread = threading.Thread(target=eeg_recorder.start_recording)

    eeg_thread.start()

    try:
        while eeg_thread.is_alive():
            eeg_thread.join(1)
    except KeyboardInterrupt:
        print("Deteniendo grabación...")
        eeg_recorder.stop_recording()
        eeg_thread.join()

    print("Grabación finalizada.")
