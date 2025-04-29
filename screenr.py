import numpy as np
import cv2
import pyautogui
import threading
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import ImageGrab, Image, ImageTk




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
        rect = canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="red", width=2)

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

    canvas = tk.Canvas(root, bg='gray')
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

# Calculate width and height from selected area
    left, top, right, bottom = recording_region
    region_width, region_height = right - left, bottom - top

    out = cv2.VideoWriter(output_file, codec, frame_rate, (region_width, region_height))

    # Start the video capturing in a separate thread
    video_thread = threading.Thread(target=record_video)
    video_thread.start()

    update_status("Recording Started", "red")
    start_button.config(state="disabled", fg="white",  cursor="circle")  # Disable and set to grey
    stop_button.config(state="normal", bg="red", fg="white", cursor="arrow")  # Active stop button with red background
    capture_button.config(state="normal", bg="lightblue", fg="black")  # Active capture button

# Function to stop screen recording
def stop_recording():
    global is_recording, out, video_thread
    is_recording = False
    if out:
        out.release()

    video_thread.join()  # Ensure video thread has finished
    update_status("Recording Stopped", "green")

    start_button.config(state="normal", bg="green", fg="white", cursor="circle")  # Enable and set to green
    stop_button.config(state="disabled", bg="white", fg="white")  # Disable and set to grey
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
    window.withdraw()
    window.update_idletasks()


    # Ask the user where to save the screenshot
    screenshot_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
    
    screenshot = pyautogui.screenshot()
    if screenshot_path:
        screenshot.save(screenshot_path)
        messagebox.showinfo("Screenshot Captured", f"Screenshot has been saved as {screenshot_path}")
    else:
        messagebox.showwarning("Save Cancelled", "Screenshot not saved.")


    window.deiconify()
def start_recording():
    global is_recording, is_paused, recording_region

    select_video_path()
    if not output_file:
        messagebox.showerror("Error", "No path selected for video file.")
        return

    recording_region = select_recording_area()
    if not recording_region:
        messagebox.showwarning("Cancelled", "No area selected for recording.")
        return

    # Show visual blur on screen immediately
    show_blurred_overlay(recording_region)

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

# Function to capture the screen and save video frames
def record_video():
    global is_recording, is_paused, out, recording_region
    import time

    # Use full screen resolution for final output
    screen_width, screen_height = pyautogui.size()
    out = cv2.VideoWriter(output_file, codec, frame_rate, (screen_width, screen_height))

    left, top, right, bottom = recording_region
    prev = time.time()
    frame_interval = 1 / frame_rate

    while is_recording:
        if not is_paused:
            full_img = ImageGrab.grab()
            full_frame = np.array(full_img)
            full_frame = cv2.cvtColor(full_frame, cv2.COLOR_BGR2RGB)

            # Create a blurred version of the full screen
            blurred_frame = cv2.GaussianBlur(full_frame, (51, 51), 0)

            # Extract the selected area from the original frame (not blurred)
            clear_region = full_frame[top:bottom, left:right]

            # Paste the clear region into the blurred frame
            blurred_frame[top:bottom, left:right] = clear_region

            # Add mouse cursor if it's inside the screen
            mouse_x, mouse_y = pyautogui.position()
            if 0 <= mouse_x < screen_width and 0 <= mouse_y < screen_height:
                cv2.circle(blurred_frame, (mouse_x, mouse_y), 8, (0, 0, 255), -1)

            # Write the final frame (entire screen with blurred background and clear selected region)
            out.write(blurred_frame)

        time.sleep(1 / frame_rate)

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
    from PIL import ImageTk, Image

    left, top, right, bottom = selected_region
    screen = ImageGrab.grab()
    screen_np = np.array(screen)
    screen_np = cv2.cvtColor(screen_np, cv2.COLOR_BGR2RGB)

    # Blur entire screen
    blurred = cv2.GaussianBlur(screen_np, (51, 51), 0)

    # Fill the selected area with black (which we will make transparent)
    blurred[top:bottom, left:right] = (0, 0, 0)

    # Convert to image
    image = Image.fromarray(blurred)
    overlay_img = ImageTk.PhotoImage(image)

    # Create overlay
    overlay = tk.Toplevel()
    overlay.attributes("-fullscreen", True)
    overlay.attributes("-topmost", True)

    # Make black areas transparent (Windows only)
    overlay.wm_attributes("-transparentcolor", "black")

    # Remove window border and background
    overlay.overrideredirect(True)

    # Set transparent background (black will be transparent)
    label = tk.Label(overlay, image=overlay_img, bg="black")
    label.image = overlay_img
    label.pack()

    # Create a stop button inside the overlay (not click-through)
    stop_btn = tk.Button(
        overlay, text="Stop Recording",
        font=("Helvetica", 14, "bold"),
        bg="red", fg="white", cursor="hand2",
        command=lambda: stop_overlay_and_recording(overlay)
    )
    stop_btn.place(relx=0.5, rely=0.9, anchor="center", width=200, height=40)

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
    window.iconbitmap("icon.ico")
    window.resizable(False, False)

    # Set a gradient background (using a canvas widget)
    canvas = tk.Canvas(window, width=400, height=300, bg="snow3", highlightthickness=0)
    canvas.pack(fill="both", expand=True)


    # Create the buttons and labels
    global start_button, stop_button, capture_button, status_label

    start_button = create_button(window, "Start Recording", start_recording, "RoyalBlue3", "SpringGreen2")
    start_button.place(x=120, y=20, width=160, height=40)

    stop_button = create_button(window, "Stop Recording", stop_recording, "DeepSkyBlue3", "salmon1", cursor="circle")
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
