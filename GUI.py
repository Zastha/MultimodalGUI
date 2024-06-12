import threading
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os
from datetime import datetime
import cv2
import time
from FacialEmo import faceRec
import subprocess
import sys

if len(sys.argv) != 2:
    print("Usage: python GUI.py <output_folder_path>")
    sys.exit(1)

# Define una variable global para almacenar la ruta de la carpeta
output_folder_path = sys.argv[1]

# List of videos
video_list = sorted([f for f in os.listdir("assets") if f.startswith("vid") and f.endswith(".mp4")])
first_video_duration = 10  # Duration in seconds for the first video
video_duration = 5         # Duration in seconds for other videos
neutral_video_path = os.path.join("assets", "neutral.mp4")

# Dictionary to store user data
user_data = {
    "Nombre": "",
    "Apellido": "",
    "Nacionalidad": "",
    "Edad": "",
    "Género": "",
    "Textos": [],
    "Video_Data": []
}

# Function to check if the camera is working
def check_camera():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror("Camera Error", "Camera not found or cannot be opened.")
        return False
    cap.release()
    return True

# Function to start the emotion detection thread
def start_emotion_detection():
    threading.Thread(target=faceRec.detectEmo, args=(output_folder_path,), daemon=True).start()

# Function to save user data temporarily
def save_user_data():
    user_data["Nombre"] = entry_nombre.get()
    user_data["Apellido"] = entry_apellido.get()
    user_data["Nacionalidad"] = entry_nacionalidad.get()
    user_data["Edad"] = entry_edad.get()
    user_data["Género"] = gender_var.get()

    if not all([user_data["Nombre"], user_data["Apellido"], user_data["Nacionalidad"], user_data["Edad"], user_data["Género"]]):
        messagebox.showwarning("Input Error", "All fields are required")
        return

    messagebox.showinfo("Success", "Data saved temporarily")
    
    # Check if camera is working before proceeding
    if check_camera():
        # Start emotion detection
        start_emotion_detection()

        # Close the main GUI window and continue with video playback
        root.destroy()
        play_all_videos()

# Function to save data to a CSV file at the end of the program
def save_to_csv():
    global output_folder_path
    nombre = user_data["Nombre"]
    carpeta_path = output_folder_path

    # Generate CSV file path
    csv_path = os.path.join(carpeta_path, f"{nombre}.csv")

    # Ensure directory exists
    os.makedirs(carpeta_path, exist_ok=True)

    # Personal data
    personal_data = {
        "Nombre": [user_data["Nombre"]],
        "Apellido": [user_data["Apellido"]],
        "Nacionalidad": [user_data["Nacionalidad"]],
        "Edad": [user_data["Edad"]],
        "Género": [user_data["Género"]]
    }
    df_personal_data = pd.DataFrame(personal_data)
    df_personal_data.to_csv(csv_path, index=False)

    # Video data
    if user_data["Video_Data"]:
        df_video_data = pd.DataFrame(user_data["Video_Data"])
        df_video_data.to_csv(csv_path, mode='a', header=True, index=False)

    messagebox.showinfo("Success", f"Data saved in {csv_path}")
    
    # Show thank you window
    show_thank_you_window()

# Add this function to display the thank you window
def show_thank_you_window():
    thank_you_window = tk.Toplevel()
    thank_you_window.attributes('-fullscreen', True)
    thank_you_window.configure(bg='white')

    def end_program():
        faceRec.stop_event.set()  # Detener el hilo de detección de emociones
        thank_you_window.destroy()
        subprocess.run([python_interpreter, "EEGSaver.py", "stop"])  # Assuming you have a stop command for EEG recording

    label = tk.Label(thank_you_window, text="Thank you for participating!", font=('Helvetica', 24), bg='white')
    label.pack(pady=20)

    button = tk.Button(thank_you_window, text="End", font=('Helvetica', 16), command=end_program)
    button.pack(pady=20)

    thank_you_window.mainloop()

# Function to play all videos
def play_all_videos():
    for index, video in enumerate(video_list):
        video_path = os.path.join("assets", video)
        if index == 0:
            start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            play_video(video_path)
            user_data["Video_Data"].append({
                "Video": f"Video {index+1}",
                "Start Time": start_time,
                "End Time": "",
                "sentiment_prompt": ""
            })
        else:
            # Play neutral video
            start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            play_video(neutral_video_path, video_duration)
            end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user_data["Video_Data"].append({
                "Video": f"Neutral Video {index}",
                "Start Time": start_time,
                "End Time": end_time,
                "sentiment_prompt": ""
            })

            # Play numbered video
            start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            play_video(video_path, video_duration)
            end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user_data["Video_Data"].append({
                "Video": f"Video {index+1}",
                "Start Time": start_time,
                "End Time": end_time,
                "sentiment_prompt": ""
            })

            # Get user text after each numbered video
            get_user_text(f"Video {index+1}")

    # Detener el hilo de detección de emociones al finalizar todos los videos
    faceRec.stop_event.set()
    save_to_csv()  # Guardar los datos al final de todos los videos

# Function to play video
def play_video(video_path, duration=5):
    cap = cv2.VideoCapture(video_path)
    start_time = time.time()

    # Configure window to fullscreen
    cv2.namedWindow('Video', cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty('Video', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while (time.time() - start_time) < duration:
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow('Video', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# Function to get user text in fullscreen
def get_user_text(video_name):
    input_window = tk.Toplevel()
    input_window.attributes('-fullscreen', True)
    input_window.configure(bg='white')

    # Initialize wait_var here to ensure scope
    wait_var = tk.IntVar()

    def save_input():
        user_text = text_box.get("1.0", tk.END).strip()
        if user_text:
            for video in user_data["Video_Data"]:
                if video["Video"] == video_name:
                    video["sentiment_prompt"] = user_text
                    break
        input_window.destroy()
        wait_var.set(1)

    label = tk.Label(input_window, text="Enter your text:", font=('Helvetica', 24), bg='white')
    label.pack(pady=20)

    text_box = tk.Text(input_window, font=('Helvetica', 16), wrap='word')
    text_box.pack(expand=True, fill='both', padx=20, pady=20)

    button = tk.Button(input_window, text="Save", font=('Helvetica', 16), command=save_input)
    button.pack(pady=20)

    # Bind the Escape key to close the window and set wait_var
    input_window.bind("<Escape>", lambda e: (input_window.destroy(), wait_var.set(1)))

    # Ensure wait_var is set when the window is closed
    input_window.protocol("WM_DELETE_WINDOW", lambda: (input_window.destroy(), wait_var.set(1)))

    # Wait for the input window to close
    input_window.wait_variable(wait_var)

# Function to close the application on Escape key press and save the data
def on_escape(event):
    save_to_csv()
    root.destroy()
    faceRec.stop_event.set()  # Detener el hilo de detección de emociones al cerrar la aplicación

# Create the main window
root = tk.Tk()
root.title("Survey")
root.attributes('-fullscreen', True)

# Bind the Escape key to the on_escape function
root.bind("<Escape>", on_escape)

# Custom style
style = ttk.Style()
style.configure('TLabel', font=('Helvetica', 16))
style.configure('TButton', font=('Helvetica', 16))
style.configure('Header.TLabel', font=('Helvetica', 24, 'bold'), foreground='blue')

# Frame for the title
title_frame = ttk.Frame(root)
title_frame.pack(side=tk.TOP, pady=20)
title_label = ttk.Label(title_frame, text="Multimodal Emotion Detection", style='Header.TLabel')
title_label.pack()

# Main frame
frame = ttk.Frame(root, padding="10")
frame.pack(expand=True)

# Labels and entries for user data
label_nombre = ttk.Label(frame, text="Nombre:")
label_nombre.grid(row=0, column=0, padx=10, pady=10)
entry_nombre = ttk.Entry(frame, font=('Helvetica', 16))
entry_nombre.grid(row=0, column=1, padx=10, pady=10)

label_apellido = ttk.Label(frame, text="Apellido:")
label_apellido.grid(row=0, column=2, padx=10, pady=10)
entry_apellido = ttk.Entry(frame, font=('Helvetica', 16))
entry_apellido.grid(row=0, column=3, padx=10, pady=10)

label_nacionalidad = ttk.Label(frame, text="Nacionalidad:")
label_nacionalidad.grid(row=1, column=0, padx=10, pady=10)
entry_nacionalidad = ttk.Entry(frame, font=('Helvetica', 16))
entry_nacionalidad.grid(row=1, column=1, padx=10, pady=10)

label_edad = ttk.Label(frame, text="Edad:")
label_edad.grid(row=2, column=0, padx=10, pady=10)
entry_edad = ttk.Entry(frame, font=('Helvetica', 16))
entry_edad.grid(row=2, column=1, padx=10, pady=10)

# Gender section
label_genero = ttk.Label(frame, text="Género:")
label_genero.grid(row=3, column=0, padx=10, pady=10)

gender_var = tk.StringVar()
radiobutton_male = ttk.Radiobutton(frame, text="Hombre", variable=gender_var, value="Hombre")
radiobutton_male.grid(row=3, column=1, padx=10, pady=10, sticky="w")

radiobutton_female = ttk.Radiobutton(frame, text="Mujer", variable=gender_var, value="Mujer")
radiobutton_female.grid(row=3, column=2, padx=10, pady=10, sticky="w")

# Button to save data temporarily
button_next = ttk.Button(frame, text="Next", command=save_user_data)
button_next.grid(row=4, columnspan=4, pady=20)

# Run the main loop
root.mainloop()

