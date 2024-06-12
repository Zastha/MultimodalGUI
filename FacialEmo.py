import cv2
import pandas as pd
import time
from fer import FER
import datetime
import os
import sys
import threading

class faceRec:
    stop_event = threading.Event()

    @staticmethod
    def detectEmo(folder_path):
        # Initialize the emotion detector
        detector = FER(mtcnn=True)

        # Start the webcam video capture
        cap = cv2.VideoCapture(0)

        # Lists to store emotion data and timestamps
        emotions_list = []
        timestamps = []

        start_time = datetime.datetime.now()

        while not faceRec.stop_event.is_set():
            # Capture frame-by-frame
            ret, frame = cap.read()
            if not ret:
                break

            # Analyze the frame for emotions
            result = detector.detect_emotions(frame)

            # If emotions are detected, save the results
            if result:
                emotions = result[0]['emotions']
                current_time = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S.%f')[:-3]  # Formato con milisegundos
                timestamps.append(current_time)
                emotions_list.append(emotions)

                # Get the dominant emotion
                dominant_emotion = max(emotions, key=emotions.get)

                # Draw a rectangle around the face and label the dominant emotion
                (x, y, w, h) = result[0]['box']
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.putText(frame, dominant_emotion, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

            # Display the resulting frame
            # cv2.imshow('Real-time Emotion Detection', frame)

            # Press 'q' to exit the video
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Release the capture and close all windows
        cap.release()
        cv2.destroyAllWindows()

        # Save the emotion data to a pandas DataFrame and then to a CSV file
        df = pd.DataFrame(emotions_list)
        df.insert(0, 'timestamp', timestamps)  # Insert the timestamps as the first column
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Create the folder if it does not exist
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        csv_path = os.path.join(folder_path, f'real_time_emotion_detection_{timestamp}.csv')
        df.to_csv(csv_path, index=False)
        print(f"Results saved to {csv_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python FacialEmo.py <output_folder_path>")
        sys.exit(1)

    output_folder_path = sys.argv[1]
    faceRec.detectEmo(output_folder_path)
