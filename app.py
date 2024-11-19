import tkinter as tk
from tkinter import *
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import cv2
import datetime
import os
import logging
from ultralytics import YOLO
import time
import playsound  # Cross-platform library for playing sounds

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load YOLO model
model = YOLO('train8/best.pt')

# Main Window Setup
window = tk.Tk()
window.title("Dress Code Detection")
window.geometry("1470x1000")
window.configure()

# Video Capture Setup
cap = cv2.VideoCapture(0)

# Set camera properties for performance and aspect ratio (960x540 for 16:9)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 540)

# Initialize variables
frame_count = 0
cooldown_time = 1 
last_capture_time = 0  
captured_frames = []  
cap = None

# Create directories for saved images
if not os.path.exists("captures"):
    os.makedirs("captures")

# Create tabbed interface
notebook = ttk.Notebook(window)
main_tab = Frame(notebook)
records_tab = Frame(notebook)
notebook.add(main_tab, text="Live Detections")
notebook.place(x=0, y=0, width=1470, height=1000)

# Detection Show Area
de_title = tk.Label(main_tab, text="", font=("Arial", 15, "bold"), bg="white", fg="black")
de_title.place(x=20, y=50, width=960, height=30)

# Video Capture Area
video_frame = Frame(main_tab)
video_frame.place(x=20, y=80, width=960, height=540)  
video_label = Label(video_frame)
video_label.pack()

# Detections Label
detections_title = tk.Label(main_tab, text="Detections", font=("Arial", 15, "bold"), bg="dark slate gray", fg="white")
detections_title.place(x=20, y=640)
detections_label = tk.Label(main_tab, text="", font=("Arial", 14), bg="dark slate gray", fg="white")
detections_label.place(x=20, y=660)

# Violations display on the right
violations_frame = tk.Frame(main_tab, width=300, height=1000)
violations_frame.place(x=1000, y=50)

# Buttons for controls
def start_live_stream():
    global cap
    if cap:
        cap.release()
    cap = cv2.VideoCapture(0)
    update_frame()

def stop_video():
    global cap
    if cap:
        cap.release()
    video_label.configure(image="default.jpg")


start_button = tk.Button(main_tab, text="Start Streaming", command=start_live_stream)
start_button.place(x=20, y=10)
stop_button = tk.Button(main_tab, text="Stop Video", command=stop_video)
stop_button.place(x=200, y=10)

# Function to play alarm
def play_alarm():
    playsound.playsound("alarm1.wav")

# Function to update video feed and YOLO detections
def update_frame():
    global frame_count, last_capture_time, cap
    if not cap:
        return

    ret, frame = cap.read()
    if not ret:
        logging.error("Failed to capture video frame.")
        return

    frame_count += 1

    # Resize frame to match display dimensions
    frame = cv2.resize(frame, (960, 540))  # Updated dimensions

    # Process every frame
    if frame_count % 1 == 0:
        results = model(frame, conf=0.6)
        detections_label.config(text="")

        for detection in results[0].boxes:
            x1, y1, x2, y2 = map(int, detection.xyxy[0])
            label = model.names[int(detection.cls[0])]
            conf = detection.conf[0]

            # Draw bounding box and label
            label_bg_color = (0, 0, 255) if 'NotAllowed' in label else (0, 100, 0)  # Background color for the label
            color = (0, 0, 255) if 'NotAllowed' in label else (0, 100, 0)  # Box color
            font_scale = 0.5
            font_thickness = 2

            # Draw the bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # Prepare label background
            label_text = f"{label} ({conf:.2f})"
            (label_width, label_height), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness)
            label_x2 = x1 + label_width + 10
            label_y2 = y1 - label_height - 10

            # Draw label background rectangle
            cv2.rectangle(frame, (x1, y1), (label_x2, label_y2), label_bg_color, -1)

            # Add text on top of the label background
            cv2.putText(
                frame, 
                label_text, 
                (x1 + 5, y1 - 5),  # Add slight padding inside the background
                cv2.FONT_HERSHEY_SIMPLEX, 
                font_scale, 
                (255, 255, 255),  # White text for contrast
                font_thickness
            )

            # Update the Tkinter label for detections
            detections_label.config(text=detections_label.cget("text") + f"\n{label_text}")

            # Handle "NotAllowed" detections
            if "NotAllowed" in label:
                current_time = time.time()
                if current_time - last_capture_time > cooldown_time:
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    play_alarm()  # Play alarm sound
                    display_violation(frame, timestamp)
                    last_capture_time = current_time  # Update last capture time

            # Update detections title
            if "NotAllowed" in label:
                de_title.config(text="Dress Code Not Allowed", bg="red", fg="white")
            else:
                de_title.config(text="Dress Code Allowed", bg="green", fg="white")

    # Update video frame in Tkinter
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(frame)
    imgtk = ImageTk.PhotoImage(image=img)
    video_label.imgtk = imgtk
    video_label.configure(image=imgtk)

    # Schedule next frame update
    video_label.after(10, update_frame)

# Function to display recent violations
def display_violation(frame, timestamp):
    global captured_frames
    thumbnail = cv2.resize(frame, (300, 169))
    thumbnail = cv2.cvtColor(thumbnail, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(thumbnail)
    thumbnail1 = cv2.resize(frame, (960, 540))
    thumbnail1= cv2.cvtColor(thumbnail1, cv2.COLOR_BGR2RGB)
    img1 = Image.fromarray(thumbnail1)
    imgtk = ImageTk.PhotoImage(image=img)

    # Update captured frames list (keep last 4)
    captured_frames.append((imgtk, timestamp))
    if len(captured_frames) > 3:
        captured_frames.pop(0)

    # Clear and update violations frame
    for widget in violations_frame.winfo_children():
        widget.destroy()
    for imgtk, timestamp in captured_frames:
        frame_container = tk.Frame(violations_frame)
        frame_container.pack(pady=5)
        tk.Label(frame_container, text=timestamp).pack()
        image_label = tk.Label(frame_container, image=imgtk)
        image_label.image = imgtk  # Prevent garbage collection
        image_label.pack()

    # Save the image with timestamp
    img1.save(f"captures/{timestamp}.png")

# Cleanup on closing the app
def on_closing():
    logging.info("Closing the app and releasing resources.")
    if cap:
        cap.release()
    cv2.destroyAllWindows()
    window.destroy()

window.protocol("WM_DELETE_WINDOW", on_closing)

# Default image setup for video frame
def show_default_image():
    default_img = Image.open("default.jpg")
    default_img = default_img.resize((960, 540), Image.LANCZOS)  # Match new display size
    imgtk = ImageTk.PhotoImage(image=default_img)
    video_label.imgtk = imgtk
    video_label.configure(image=imgtk)

# Start Tkinter main loop
show_default_image()
window.mainloop()
