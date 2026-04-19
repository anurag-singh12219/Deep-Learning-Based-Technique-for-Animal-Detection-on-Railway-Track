import os
import sys
import time
import cv2
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.detection_backend import detect_and_annotate, OUTPUT_IMAGE_DIR, OUTPUT_VIDEO_DIR

# Runtime state for interactive video control
video_paused = False
video_stop_requested = False
video_next_requested = False
video_detection_running = False

app = None
status_label = None
display_label = None
video_controls_row = None
pause_btn = None
stop_btn = None
next_btn = None


def set_status(text, color="#0f172a"):
    if status_label and status_label.winfo_exists():
        status_label.config(text=text, fg=color)


def set_video_controls_state(running=False, paused=False):
    if pause_btn and pause_btn.winfo_exists():
        pause_btn.config(state=("normal" if running else "disabled"), text=("Resume" if paused else "Pause"))
    if stop_btn and stop_btn.winfo_exists():
        stop_btn.config(state=("normal" if running else "disabled"))
    if next_btn and next_btn.winfo_exists():
        next_btn.config(state=("normal" if running else "disabled"))


def show_video_controls(show=False):
    if video_controls_row and video_controls_row.winfo_exists():
        if show:
            if status_label and status_label.winfo_exists():
                video_controls_row.pack(pady=(6, 8), before=status_label)
            else:
                video_controls_row.pack(pady=(6, 8))
        else:
            video_controls_row.pack_forget()


def process_video(file_path, on_video_start=None):
    """
    Process a video file, detect animals in each frame, and show the video with annotations.
    Save annotated frames in the output directory.
    """
    global video_paused, video_stop_requested, video_detection_running

    cap = cv2.VideoCapture(file_path)
    detected_animals_set = set()
    frame_count = 0
    first_frame_started = False
    video_name = os.path.splitext(os.path.basename(file_path))[0]

    video_detection_running = True
    video_paused = False
    video_stop_requested = False

    while cap.isOpened():
        if video_stop_requested:
            break

        if video_paused:
            app.update_idletasks()
            app.update()
            time.sleep(0.05)
            continue

        ret, frame = cap.read()
        if not ret:
            break

        if not first_frame_started:
            first_frame_started = True
            if on_video_start:
                on_video_start()
            set_status("Video detection is running...", "#0f766e")

        frame_count += 1
        filename = f"{video_name}_frame_{frame_count}.jpg"

        annotated_frame, detected_animals = detect_and_annotate(
            frame,
            filename=filename,
            save_dir=OUTPUT_VIDEO_DIR
        )

        for animal in detected_animals:
            if animal not in detected_animals_set:
                detected_animals_set.add(animal)

        annotated_frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(annotated_frame_rgb)
        img_tk = ImageTk.PhotoImage(img_pil)

        display_label.config(image=img_tk)
        display_label.image = img_tk
        app.update_idletasks()
        app.update()

        time.sleep(1 / 30.0)

    cap.release()
    stopped_by_user = video_stop_requested
    video_detection_running = False
    show_video_controls(show=False)
    set_video_controls_state(running=False)
    return detected_animals_set, stopped_by_user


def show_processing_popup(message):
    """
    Show a non-blocking popup while detection is running.
    """
    popup = tk.Toplevel(app)
    popup.title("Detection Starting")
    popup.geometry("380x140")
    popup.resizable(False, False)
    popup.transient(app)
    popup.protocol("WM_DELETE_WINDOW", lambda: None)
    popup.configure(bg="#e0f2fe")

    tk.Label(
        popup,
        text=message,
        font=("Segoe UI", 12, "bold"),
        bg="#e0f2fe",
        fg="#0f172a"
    ).pack(expand=True, pady=25)
    popup.update_idletasks()

    x = app.winfo_x() + (app.winfo_width() // 2) - (popup.winfo_width() // 2)
    y = app.winfo_y() + (app.winfo_height() // 2) - (popup.winfo_height() // 2)
    popup.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    return popup


def toggle_pause_video():
    global video_paused
    if not video_detection_running:
        return
    video_paused = not video_paused
    set_video_controls_state(running=True, paused=video_paused)
    if video_paused:
        set_status("Video paused. You can resume or stop.", "#b45309")
    else:
        set_status("Video detection resumed...", "#0f766e")


def stop_video_detection():
    global video_stop_requested, video_next_requested
    if not video_detection_running:
        return
    video_stop_requested = True
    video_next_requested = False
    set_status("Stopping video detection...", "#b91c1c")


def start_next_detection():
    global video_stop_requested, video_next_requested
    if video_detection_running:
        video_next_requested = True
        video_stop_requested = True
        set_status("Preparing next detection...", "#1d4ed8")
    else:
        open_file()


def open_file():
    """
    Open a file dialog to select an image or video file and process it.
    Save annotated images in the output directory.
    """
    file_path = filedialog.askopenfilename(
        title="Select an Image or Video",
        filetypes=(("All files", "*.*"),
                   ("Image files", "*.png;*.jpg;*.jpeg;*.bmp"),
                   ("Video files", "*.mp4;*.avi;*.mov"))
    )
    if file_path:
        global video_next_requested, video_stop_requested, video_paused

        processing_popup = None
        try:
            result_title = None
            result_message = None
            video_next_requested = False
            video_stop_requested = False
            video_paused = False

            show_video_controls(show=False)
            set_video_controls_state(running=False)
            set_status("File selected. Initializing detection...", "#1d4ed8")
            display_label.config(image="")
            display_label.image = None

            processing_popup = show_processing_popup("Detection started... Please wait.")
            app.update_idletasks()
            app.update()

            if file_path.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
                filename = os.path.basename(file_path)
                annotated_img, detected_animals = detect_and_annotate(
                    cv2.imread(file_path),
                    filename=filename,
                    save_dir=OUTPUT_IMAGE_DIR
                )
                annotated_img_rgb = cv2.cvtColor(annotated_img, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(annotated_img_rgb)
                img_tk = ImageTk.PhotoImage(img_pil)

                display_label.config(image=img_tk)
                display_label.image = img_tk

                if processing_popup and processing_popup.winfo_exists():
                    processing_popup.destroy()
                    processing_popup = None

                show_video_controls(show=False)
                set_status("Image detection completed.", "#14532d")

                if detected_animals:
                    detected_animals_str = ", ".join(detected_animals)
                    result_title = "Animals Detected"
                    result_message = f"Detected animals: {detected_animals_str}\\nPush notifications sent!"
                else:
                    result_title = "No Animals Detected"
                    result_message = "No animals detected near the railway track."

            elif file_path.lower().endswith((".mp4", ".avi", ".mov")):
                def on_video_start():
                    nonlocal processing_popup
                    if processing_popup and processing_popup.winfo_exists():
                        processing_popup.destroy()
                        processing_popup = None
                    show_video_controls(show=True)
                    set_video_controls_state(running=True, paused=False)

                detected_animals, stopped_by_user = process_video(file_path, on_video_start=on_video_start)

                if stopped_by_user and video_next_requested:
                    set_status("Ready for next detection.", "#1d4ed8")
                    video_next_requested = False
                    open_file()
                    return

                if stopped_by_user:
                    result_title = "Detection Stopped"
                    result_message = "Video detection was stopped by user."
                    set_status("Video detection stopped.", "#991b1b")
                elif detected_animals:
                    detected_animals_str = ", ".join(detected_animals)
                    result_title = "Animals Detected"
                    result_message = f"Animals detected in video: {detected_animals_str}\\nPush notifications sent!"
                    set_status("Video detection completed.", "#14532d")
                else:
                    result_title = "No Animals Detected"
                    result_message = "No animals detected in the video near the railway track."
                    set_status("Video detection completed.", "#14532d")
            else:
                result_title = "Unsupported File"
                result_message = "Please choose a valid image or video file."
                set_status("Unsupported file selected.", "#991b1b")

            if processing_popup and processing_popup.winfo_exists():
                processing_popup.destroy()

            if result_title and result_message:
                messagebox.showinfo(result_title, result_message)

            next_step_popup()
        except Exception as e:
            if processing_popup and processing_popup.winfo_exists():
                processing_popup.destroy()
            show_video_controls(show=False)
            set_video_controls_state(running=False)
            set_status("Detection failed. Please try again.", "#991b1b")
            messagebox.showerror("Error", f"Failed to process the file: {e}")


def next_step_popup():
    result = messagebox.askquestion("Next Step", "Do you want to perform the next detection?")
    if result == "yes":
        open_file()
    else:
        app.quit()


def main_gui():
    global status_label, display_label, video_controls_row, pause_btn, stop_btn, next_btn

    main_frame = tk.Frame(app, bg="#ffffff")
    main_frame.pack(fill="both", expand=True)

    content_card = tk.Frame(main_frame, bg="#ffffff", bd=0, highlightthickness=1, highlightbackground="#bae6fd")
    content_card.pack(padx=0, pady=0, fill="both", expand=True)

    tk.Frame(content_card, bg="#ffffff", height=8).pack(fill="x")

    tk.Label(content_card, text="Smart Animal Detection Console", font=("Segoe UI", 22, "bold"), bg="#ffffff", fg="#0f172a").pack(pady=(18, 4))
    tk.Label(content_card, text="Upload image or video and control detection flow in real time", font=("Segoe UI", 11), bg="#ffffff", fg="#334155").pack(pady=(0, 14))

    controls_row = tk.Frame(content_card, bg="#ffffff")
    controls_row.pack(pady=8)

    tk.Button(
        controls_row,
        text="Choose File",
        command=open_file,
        font=("Segoe UI", 12, "bold"),
        bg="#2563eb",
        fg="white",
        activebackground="#1d4ed8",
        activeforeground="white",
        bd=0,
        padx=14,
        pady=8
    ).grid(row=0, column=0, padx=6)

    video_controls_row = tk.Frame(content_card, bg="#ffffff")

    pause_btn = tk.Button(
        video_controls_row,
        text="Pause",
        command=toggle_pause_video,
        font=("Segoe UI", 11, "bold"),
        bg="#f59e0b",
        fg="white",
        activebackground="#d97706",
        activeforeground="white",
        bd=0,
        padx=12,
        pady=8,
        state="disabled"
    )
    pause_btn.grid(row=0, column=0, padx=6)

    stop_btn = tk.Button(
        video_controls_row,
        text="Stop",
        command=stop_video_detection,
        font=("Segoe UI", 11, "bold"),
        bg="#dc2626",
        fg="white",
        activebackground="#b91c1c",
        activeforeground="white",
        bd=0,
        padx=12,
        pady=8,
        state="disabled"
    )
    stop_btn.grid(row=0, column=1, padx=6)

    next_btn = tk.Button(
        video_controls_row,
        text="Next Detection",
        command=start_next_detection,
        font=("Segoe UI", 11, "bold"),
        bg="#7c3aed",
        fg="white",
        activebackground="#6d28d9",
        activeforeground="white",
        bd=0,
        padx=12,
        pady=8,
        state="disabled"
    )
    next_btn.grid(row=0, column=2, padx=6)

    show_video_controls(show=False)

    status_label = tk.Label(content_card, text="Ready. Choose a file to start detection.", font=("Segoe UI", 11, "bold"), bg="#ffffff", fg="#0f172a")
    status_label.pack(pady=(8, 12))

    preview_card = tk.Frame(content_card, bg="#f8fafc", highlightthickness=1, highlightbackground="#cbd5e1")
    preview_card.pack(padx=20, pady=(0, 20), fill="both", expand=True)

    display_label = tk.Label(preview_card, bg="#f8fafc")
    display_label.pack(padx=10, pady=10, fill="both", expand=True)


def run_app():
    global app

    app = tk.Tk()
    app.title("Animal Detection on Railway Track")
    app.geometry("1100x720")
    app.minsize(980, 640)
    app.configure(bg="#ffffff")

    splash_frame = tk.Frame(app, bg="#ffffff")
    splash_frame.pack(fill="both", expand=True)

    splash_card = tk.Frame(splash_frame, bg="#ffffff", bd=0, highlightthickness=1, highlightbackground="#bae6fd")
    splash_card.pack(padx=0, pady=0, fill="both", expand=True)

    header_strip = tk.Frame(splash_card, bg="#ffffff", height=10)
    header_strip.pack(fill="x")

    try:
        splash_img = Image.open("logo.jpg").resize((320, 130))
        splash_img_tk = ImageTk.PhotoImage(splash_img)
        tk.Label(splash_card, image=splash_img_tk, bg="#ffffff").pack(pady=16)
    except Exception:
        tk.Label(splash_card, text="RAILWAY SAFETY DETECTION", font=("Segoe UI", 20, "bold"), bg="#ffffff", fg="#0f172a").pack(pady=20)

    tk.Label(splash_card, text="Deep Learning Based Technique for Animal Detection on Railway Track", font=("Segoe UI", 21, "bold"), bg="#ffffff", fg="#0f172a", wraplength=950, justify="center").pack(pady=8)
    tk.Label(splash_card, text="Greater Noida Institute Of Technology (Engg. Inst.)\\nApproved by AICTE & Affiliated by AKTU (Lucknow)", font=("Segoe UI", 13), bg="#ffffff", fg="#0f766e").pack(pady=4)
    tk.Label(splash_card, text="Department Of CSE (AI & ML)", font=("Segoe UI", 13, "bold"), bg="#ffffff", fg="#1e293b").pack(pady=4)
    tk.Label(splash_card, text="HOD: Dr. Jai Shankar Prasad", font=("Segoe UI", 12, "italic"), bg="#ffffff", fg="#334155").pack(pady=8)

    team_frame = tk.Frame(splash_card, bg="#ffffff")
    team_frame.pack(pady=10)
    tk.Label(team_frame, text="Members: Anshuman Tripathi | Anurag Singh | Apurv Mishra | Arunabh Bhardwaj", font=("Segoe UI", 12), bg="#ffffff", fg="#1e293b").grid(row=0, column=0, padx=5)
    tk.Label(team_frame, text="Guides: Arun Kumar Rai | Amrish Dubey", font=("Segoe UI", 12, "italic"), bg="#ffffff", fg="#1d4ed8").grid(row=1, column=0, padx=5)

    tk.Button(
        splash_card,
        text="Start Detection",
        command=lambda: [splash_frame.destroy(), main_gui()],
        font=("Segoe UI", 14, "bold"),
        bg="#0f766e",
        fg="white",
        activebackground="#115e59",
        activeforeground="white",
        width=22,
        bd=0,
        padx=10,
        pady=8
    ).pack(pady=24)

    app.mainloop()
