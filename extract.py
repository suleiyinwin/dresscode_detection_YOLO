import os
import cv2
from yt_dlp import YoutubeDL

# URL of the YouTube video
url = "" #Path to youtube link
video_filename = "dubaimall.mp4"

# yt-dlp options for downloading the best video quality without audio
ydl_opts = {
    'format': 'bestvideo',  
    'outtmpl': video_filename,
}

# Download the video using yt-dlp
with YoutubeDL(ydl_opts) as ydl:
    ydl.download([url])

# Continue with frame extraction using OpenCV
output_folder = "" #Path to output folder
os.makedirs(output_folder, exist_ok=True)

video = cv2.VideoCapture(video_filename)

# Get frames per second (FPS) and set the interval for frame extraction
fps = video.get(cv2.CAP_PROP_FPS)
frame_interval = int(fps) 
frame_id = 0
saved_frame_count = 0

# Extract frames from the video
while True:
    success, frame = video.read()
    if not success:
        break
    if frame_id % frame_interval == 0:
        frame_path = os.path.join(output_folder, f"dubai_frame_{saved_frame_count:04d}.jpg") 
        cv2.imwrite(frame_path, frame)
        saved_frame_count += 1
    frame_id += 1

# Release the video object and optionally remove the video file
video.release()
os.remove(video_filename)  
