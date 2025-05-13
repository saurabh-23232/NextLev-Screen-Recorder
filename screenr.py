import numpy as np
import cv2
import pyautogui
import threading
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import ImageGrab, Image, ImageTk
import sys
import os

def resource_path(relative_path):
    """ Get absolute path to resource for dev and PyInstaller """
    try:
        base_path = sys._MEIPASS  # Folder where PyInstaller extracts files
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)




# Global variables to control video recording
is_recording = False
is_paused = False
frame_rate = 24.0
resolution = (1920, 1080)
output_file = "screencapture.mp4"
codec = cv2.VideoWriter_fourcc(*"mp4v")
out = None
video_thread = None
recording_region = None  




# Function to allow the user to select the screen area to record
def select_recording_area():
    import tkinter as tk

    coords = []
    rect = None

    def on_mouse_down(event):
        nonlocal rect
        coords.clear()
        coords.append((event.x, event.y))
        rect = canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="yellow", width=4)

    def on_mouse_drag(event):
        if rect:
            canvas.coords(rect, coords[0][0], coords[0][1], event.x, event.y)
        

    def on_mouse_up(event):
        coords.append((event.x, event.y))
        root.quit()

    root = tk.Tk()
    root.attributes("-alpha", 0.3)
    root.attributes("-fullscreen", True)
    root.attributes("-topmost", True)
    root.config(cursor="cross")


    canvas = tk.Canvas(root, bg='grey')
    canvas.pack(fill="both", expand=True)

    root.bind("<ButtonPress-1>", on_mouse_down)
    root.bind("<B1-Motion>", on_mouse_drag)
    root.bind("<ButtonRelease-1>", on_mouse_up)

    root.mainloop()
    root.destroy()

    if len(coords) == 2:
        x1, y1 = coords[0]
        x2, y2 = coords[1]
        return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
    return None



def select_video_path():
    global output_file
    output_file = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")])
    if not output_file:  # If user cancels, set a default path
        output_file = "screencapture.mp4"


# Function to start screen recording
def start_recording():
    global is_recording, is_paused, out, video_thread
    select_video_path()

    if not output_file:  # If no path is selected, do not proceed
        messagebox.showerror("Error", "No path selected for video file.")
        return 
    is_recording = True
    is_paused = False
    
    global recording_region

    recording_region = select_recording_area()
    if not recording_region:
        messagebox.showwarning("Cancelled", "No area selected for recording.")
        return


    update_status("Recording Started", "red")
    start_button.config(state="disabled", fg="white",  cursor="circle")  # Disable and set to grey
    stop_button.config(state="normal", bg="red", fg="white", cursor="arrow")  # Active stop button with red background
    capture_button.config(state="normal", bg="lightblue", fg="black")  # Active capture button
    start_button.master.iconify()
    show_blurred_overlay(recording_region)


# Function to stop screen recording
def stop_recording():
    global is_recording, out, video_thread
    is_recording = False
    if out:
        out.release()

    video_thread.join()  # Ensure video thread has finished
    update_status("Recording Stopped", "green")

    start_button.config(state="normal", bg="green", fg="white")  # Enable and set to green
    stop_button.config(state="disabled", bg="white", fg="white", cursor="circle")  # Disable and set to grey
    capture_button.config(state="normal", bg="lightblue", fg="black")  # Enable capture button

# Function to pause/resume screen recording
def toggle_pause_resume():
    global is_paused
    is_paused = not is_paused
    if is_paused:
        update_status("Recording Paused", "orange")
    else:
        update_status("Recording Resumed", "red")

# Function to capture screenshot
def capture_screenshot(window):
    # Hide the main window during screenshot selection
    window.iconify()
    window.update_idletasks()

    choice = messagebox.askquestion("Screenshot Options", "Do you want to capture the full screen?\n\nClick 'Yes' for full screen.\nClick 'No' to select a region.")

    if choice == 'yes':
        screenshot = pyautogui.screenshot()
    else:
        # Let user select region
        region = select_recording_area()
        if not region:
            messagebox.showwarning("Cancelled", "No area selected.")
            window.deiconify()
            return

        left, top, right, bottom = region
        screenshot = pyautogui.screenshot(region=(left, top, right - left, bottom - top))

    # Ask where to save the screenshot
    screenshot_path = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
    )

    if screenshot_path:
        screenshot.save(screenshot_path)
        messagebox.showinfo("Screenshot Saved", f"Saved to:\n{screenshot_path}")
    else:
        messagebox.showwarning("Cancelled", "Screenshot not saved.")

    window.deiconify()


def start_recording_thread():
    global is_recording, is_paused, out, video_thread, recording_region

    is_recording = True
    is_paused = False

    screen_width, screen_height = pyautogui.size()
    out = cv2.VideoWriter(output_file, codec, frame_rate, (screen_width, screen_height))

    video_thread = threading.Thread(target=record_video)
    video_thread.start()

    update_status("Recording Started", "red")
    start_button.config(state="disabled", fg="white", cursor="circle")
    stop_button.config(state="normal", bg="red", fg="white")
    capture_button.config(state="normal", bg="lightblue", fg="black")


# Function to update the GUI status label
def update_status(text, color):
    status_label.config(text=text, fg=color, bg="snow3")


def record_video():
    global is_recording, is_paused, out, recording_region
    import time

    left, top, right, bottom = recording_region
    region_width, region_height = right - left, bottom - top

    out = cv2.VideoWriter(output_file, codec, frame_rate, (region_width, region_height))

    frame_interval = 1.0 / frame_rate
    last_time = time.time()

    while is_recording:
        current_time = time.time()
        if not is_paused and (current_time - last_time) >= frame_interval:
            try:
                # Capture screen region
                img = ImageGrab.grab(bbox=(left, top, right, bottom))
                frame = np.array(img)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                # Draw semi-transparent grey circle around the mouse pointer
                mouse_x, mouse_y = pyautogui.position()
                if left <= mouse_x < right and top <= mouse_y < bottom:
                    overlay = frame.copy()
                    cursor_pos = (mouse_x - left, mouse_y - top)
                    radius = 10
                    color = (128, 128, 128)  # Grey color in BGR
                    alpha = 0.5  # Transparency level

                    cv2.circle(overlay, cursor_pos, radius, color, -1)  # Filled circle
                    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)  # Blend overlay

                # Write frame to output video
                out.write(frame)
                last_time = current_time

            except Exception as e:
                print("Error capturing frame:", e)

        # Prevent CPU overload
        time.sleep(0.001)



# Function to create a button with hover effects
def create_button(parent, text, command, color, hover_color, **kwargs):
    button = tk.Button(parent, text=text, command=command, **kwargs)
    
    # Set initial background and foreground colors
    button.config(bg=color, fg="white", relief="flat", font=("Helvetica", 12, "bold"))
    
    # Add hover effect
    button.bind("<Enter>", lambda event: button.config(bg=hover_color))
    button.bind("<Leave>", lambda event: button.config(bg=color))
    
    return button

def show_blurred_overlay(selected_region):
    global stop_btn, stop_drag_area

    from PIL import ImageTk, Image

    left, top, right, bottom = selected_region
    screen = ImageGrab.grab()
    screen_np = np.array(screen)
    screen_np = cv2.cvtColor(screen_np, cv2.COLOR_BGR2RGB)

    # Blur entire screen
    blurred = cv2.GaussianBlur(screen_np, (51, 51), 0)
    blurred[top:bottom, left:right] = (0, 0, 0)

    image = Image.fromarray(blurred)
    overlay_img = ImageTk.PhotoImage(image)

    overlay = tk.Toplevel()
    overlay.attributes("-fullscreen", True)
    overlay.attributes("-topmost", True)
    overlay.wm_attributes("-transparentcolor", "black")
    overlay.overrideredirect(True)

    label = tk.Label(overlay, image=overlay_img, bg="black")
    label.image = overlay_img
    label.pack()

    # Main stop button
    stop_btn = tk.Button(
        overlay,
        text="   Stop Recording",
        font=("Helvetica", 14, "bold"),
        bg="red", fg="white", cursor="hand2",
        command=lambda: stop_overlay_and_recording(overlay)
    )

    stop_btn_width = 200
    stop_btn_height = 40
    btn_x = overlay.winfo_screenwidth() // 2 - stop_btn_width // 2
    btn_y = overlay.winfo_screenheight() - 100

    stop_btn.place(x=btn_x, y=btn_y, width=stop_btn_width, height=stop_btn_height)

    # Drag area on the left side (e.g., 30px wide)
    stop_drag_area = tk.Frame(overlay, bg="", cursor="fleur")
    drag_width = 30
    stop_drag_area.place(x=btn_x, y=btn_y, width=drag_width, height=stop_btn_height)

    # Track drag state
    def on_drag_start(event):
        stop_drag_area.startX = event.x
        stop_drag_area.startY = event.y

    def on_drag_motion(event):
        dx = event.x - stop_drag_area.startX
        dy = event.y - stop_drag_area.startY
        new_x = stop_btn.winfo_x() + dx
        new_y = stop_btn.winfo_y() + dy
        stop_btn.place(x=new_x, y=new_y)
        stop_drag_area.place(x=new_x, y=new_y)

    stop_drag_area.bind("<Button-1>", on_drag_start)
    stop_drag_area.bind("<B1-Motion>", on_drag_motion)

    start_recording_thread()
    overlay.mainloop()



def stop_overlay_and_recording(overlay_window):
    stop_recording()  # stops the actual screen recording
    overlay_window.destroy()  # close the blur overlay

# Function to create the Tkinter window (GUI)
def create_gui():
    window = tk.Tk()
    window.title("NextLev Screen Recorder")
    window.geometry("400x350")
    icon_path = resource_path("icon.ico")
    window.iconbitmap(icon_path)
    window.resizable(False, False)

    # Set a gradient background (using a canvas widget)
    canvas = tk.Canvas(window, width=400, height=300, bg="snow3", highlightthickness=0)
    canvas.pack(fill="both", expand=True)


    # Create the buttons and labels
    global start_button, stop_button, capture_button, status_label

    start_button = create_button(window, "Start Recording", start_recording, "RoyalBlue3", "SpringGreen2")
    start_button.place(x=120, y=20, width=160, height=40)

    stop_button = create_button(window, "Stop Recording", stop_recording, "DeepSkyBlue3", "salmon1")
    stop_button.place(x=120, y=80, width=160, height=40)
    stop_button.config(state="disabled")  # Initially disable stop button

    resume_button = create_button(window, "Pause/Resume", toggle_pause_resume, "RoyalBlue2", "CadetBlue4")
    resume_button.place(x=120, y=140, width=160, height=40)

    # capture_button = create_button(window, "Capture Screenshot", capture_screenshot, "goldenrod", "lime green")
    capture_button = create_button(window, "Capture Screenshot", lambda: capture_screenshot(window), "goldenrod", "lime green")

    capture_button.place(x=120, y=200, width=160, height=40)

    # Status label - initially empty
    status_label = tk.Label(window, text="", fg="green", font=("Helvetica", 14), bg="snow3")
    status_label.place(x=100, y=250, width=190, height=40)

    window.mainloop()

# Main function to launch the program
if __name__ == "__main__":
    create_gui()
