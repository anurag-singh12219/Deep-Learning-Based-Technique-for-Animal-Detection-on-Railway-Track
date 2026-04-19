import os
import cv2
import requests
from ultralytics import YOLO

# Initialize YOLOv8 model (pre-trained on COCO dataset)
model = YOLO('yolov8x.pt')

# Pushover credentials
PUSHOVER_API_KEY = "a8qa9j5t64wzj6xcry4ofhgxtwqptk"  # Replace with your Pushover API Key
USER_KEY = "udefk276ph6jmusqth78tedg5cnmxp"  # Replace with your Pushover User Key

# Output directories for saving annotated results
OUTPUT_IMAGE_DIR = "output_images"
OUTPUT_VIDEO_DIR = "output_videos"

os.makedirs(OUTPUT_IMAGE_DIR, exist_ok=True)
os.makedirs(OUTPUT_VIDEO_DIR, exist_ok=True)


def send_push_notification(message):
    """
    Sends a push notification using Pushover.
    """
    try:
        url = "https://api.pushover.net:443/1/messages.json"
        data = {"token": PUSHOVER_API_KEY, "user": USER_KEY, "message": message}
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("Push notification sent successfully!")
        else:
            print(f"Failed to send push notification. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error sending push notification: {e}")


def detect_and_annotate(frame, filename=None, save_dir=None):
    """
    Detect animals in a frame and return the annotated frame with detected animal names.
    Save the annotated frame if a filename and save_dir are provided.
    """
    results = model(frame)
    annotated_frame = results[0].plot()

    # Get detected classes and names
    detected_classes = [model.names[int(cls)] for cls in results[0].boxes.cls]
    animals_to_alert = {"dog", "cow", "sheep", "elephant", "bear"}
    detected_animals = set(detected_classes) & animals_to_alert

    if detected_animals:
        for animal in detected_animals:
            alert_message = f"Animal detected near railway track: {animal}"
            send_push_notification(alert_message)

    # Save the annotated frame if a filename and save_dir are provided
    if filename and save_dir:
        save_path = os.path.join(save_dir, filename)
        cv2.imwrite(save_path, annotated_frame)
        print(f"Annotated frame saved at {save_path}")

    return annotated_frame, detected_animals
