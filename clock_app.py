import customtkinter as ctk
import time
import math
from datetime import datetime
import pytz
from PIL import Image
import playsound
import threading
import sys
import os
import pathlib

base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

window = ctk.CTk(fg_color="#202020")
window.title("Clock App")
window.geometry("800x600")

# Footer Frame
footer_frame = ctk.CTkFrame(window, height=70, fg_color="#323232", corner_radius=20)
footer_frame.pack(fill="x", side="bottom")

# Icons
# Image Paths
start_img = ctk.CTkImage(Image.open(os.path.join(base_path, "assets", "play.png")).resize((70, 70)))
stop_img = ctk.CTkImage(Image.open(os.path.join(base_path, "assets", "pause.png")).resize((70, 70)))
reset_img = ctk.CTkImage(Image.open(os.path.join(base_path, "assets", "reset.png")).resize((70, 70)))
lap_img = ctk.CTkImage(Image.open(os.path.join(base_path, "assets", "flag.png")).resize((70, 70)))
plus_img = ctk.CTkImage(Image.open(os.path.join(base_path, "assets", "add.png")).resize((70, 70)))



timer_start_img = start_img
timer_stop_img = stop_img

# State Trackers
active_button = None
active_pos_x = 100
button_spacing = 200
button_y = 35
start_x = 100
clock_running = False
stopwatch_running = False
stopwatch_start_time = 0
elapsed_time = 0
lap_count = 0
timer_running = False
timer_paused = False
timer_seconds = 0
timer_countdown_job = None
sound_playing = False
sound_thread = None

# Timer Frame & Buttons
timer_button_frame = ctk.CTkFrame(window, fg_color="#202020")
timer_start_stop_button = ctk.CTkButton(timer_button_frame, image=timer_start_img, text="", width=70, height=70, fg_color="#202020", hover_color="#323232", command=lambda: toggle_timer())
timer_reset_button = ctk.CTkButton(timer_button_frame, image=reset_img, text="", width=70, height=70, fg_color="#202020", hover_color="#323232", command=lambda: reset_timer())
stop_sound_button = ctk.CTkButton(window, text="Stop Sound", fg_color="#C62828", text_color="white", hover_color="#C62828", command=lambda: stop_sound())

timer_hour_entry = ctk.CTkEntry(timer_button_frame, width=60, placeholder_text="HH")
timer_min_entry = ctk.CTkEntry(timer_button_frame, width=60, placeholder_text="MM")
timer_sec_entry = ctk.CTkEntry(timer_button_frame, width=60, placeholder_text="SS")

timer_hour_entry.grid(row=0, column=0, padx=5)
timer_min_entry.grid(row=0, column=1, padx=5)
timer_sec_entry.grid(row=0, column=2, padx=5)
timer_start_stop_button.grid(row=1, column=0, columnspan=2, pady=10)
timer_reset_button.grid(row=1, column=2, pady=10)

# Highlight Bar
highlight = ctk.CTkFrame(footer_frame, width=100, height=50, fg_color="#202020", corner_radius=20)
highlight.place(x=start_x, y=button_y, anchor="center")
highlight.lift()

# Clock Widgets
time_label = ctk.CTkLabel(window, text="", font=("Arial Rounded MT Bold", 40), text_color="white", fg_color="#202020")
timezone_spacer = ctk.CTkFrame(window, fg_color="#202020", height=40)
timezone_list = [
    ("New York (EST)", "America/New_York"),
    ("London (GMT)", "Europe/London"),
    ("Dubai (GST)", "Asia/Dubai"),
    ("India (IST)", "Asia/Kolkata"),
    ("Tokyo (JST)", "Asia/Tokyo"),
    ("Sydney (AEST)", "Australia/Sydney")
]
timezone_labels = [ctk.CTkLabel(window, text="", font=("Arial Rounded MT Bold", 20), text_color="white", fg_color="#202020") for _ in timezone_list]

# Other Tabs
alarm_label = ctk.CTkLabel(window, text="Alarms:", font=("Arial Rounded MT Bold", 40), text_color="white", fg_color="#202020")
stopwatch_label = ctk.CTkLabel(window, text="00:00:00.00", font=("Arial Rounded MT Bold", 40), text_color="white", fg_color="#202020")
stopwatch_button_frame = ctk.CTkFrame(window, fg_color="#202020")

lap_button = ctk.CTkButton(stopwatch_button_frame, image=lap_img, text="", width=70, height=70, fg_color="#202020", hover_color="#323232", command=lambda: record_lap())
start_stop_button = ctk.CTkButton(stopwatch_button_frame, image=start_img, text="", width=70, height=70, fg_color="#202020", hover_color="#323232", command=lambda: toggle_stopwatch())
reset_button = ctk.CTkButton(stopwatch_button_frame, image=reset_img, text="", width=70, height=70, fg_color="#202020", hover_color="#323232", command=lambda: reset_stopwatch())

lap_display = ctk.CTkTextbox(window, width=300, height=200, fg_color="#202020", text_color="white", font=("Arial Rounded MT Bold", 20), state="disabled")
timer_label = ctk.CTkLabel(window, text="00:00:00", font=("Arial Rounded MT Bold", 40), text_color="white", fg_color="#202020")

# Alarm Frame
alarm_list_display = ctk.CTkFrame(window, fg_color="#202020")
add_alarm_button = ctk.CTkButton(window, image=plus_img, text="", width=40, height=40, fg_color="#202020", hover_color="#323232", command=lambda: open_alarm_window())




# Highlight
def animate_highlight(target_x, step=0, total_steps=40):
    global active_pos_x
    diff = target_x - active_pos_x
    progress = step / total_steps
    eased_progress = -(math.cos(math.pi * progress) - 1) / 2
    new_x = active_pos_x + diff * eased_progress
    highlight.place(x=new_x, y=button_y, anchor="center")
    if step < total_steps:
        window.after(10, lambda: animate_highlight(target_x, step + 1, total_steps))
    else:
        active_pos_x = new_x

# Clock Update
def update_time():
    if active_button == clock_button:
        time_label.configure(text=datetime.now().strftime("%I:%M:%S %p"))
        for idx, (_, tz) in enumerate(timezone_list):
            zone = pytz.timezone(tz)
            now = datetime.now(zone)
            timezone_labels[idx].configure(text=f"{timezone_list[idx][0]}: {now.strftime('%I:%M:%S %p')}")
        window.after(1000, update_time)

# Stopwatch Functions
def update_stopwatch():
    global elapsed_time
    if stopwatch_running:
        elapsed_time = time.time() - stopwatch_start_time
        stopwatch_label.configure(text=format_time(elapsed_time))
        window.after(50, update_stopwatch)

def format_time(sec):
    mins, secs = divmod(int(sec), 60)
    hours, mins = divmod(mins, 60)
    milliseconds = int((sec - int(sec)) * 100)
    return f"{hours:02}:{mins:02}:{secs:02}.{milliseconds:02}"

def toggle_stopwatch():
    global stopwatch_running, stopwatch_start_time, elapsed_time
    if not stopwatch_running:
        stopwatch_start_time = time.time() - elapsed_time
        stopwatch_running = True
        start_stop_button.configure(image=stop_img)
        update_stopwatch()
    else:
        stopwatch_running = False
        start_stop_button.configure(image=start_img)

def reset_stopwatch():
    global elapsed_time, stopwatch_running, lap_count
    stopwatch_running = False
    elapsed_time = 0
    lap_count = 0
    stopwatch_label.configure(text="00:00:00.00")
    start_stop_button.configure(image=start_img)
    lap_display.configure(state="normal")
    lap_display.delete("0.0", "end")
    lap_display.configure(state="disabled")
def record_lap():
    global lap_count
    if stopwatch_running:
        lap_count += 1
        lap_display.configure(state="normal")  
        lap_display.insert("end", f"Lap {lap_count}: {format_time(elapsed_time)}\n\n")
        lap_display.see("end")  
        lap_display.configure(state="disabled")  

# Timer Functions
def start_timer():
    global timer_seconds, timer_running, timer_paused, timer_countdown_job
    try:
        h = int(timer_hour_entry.get()) if timer_hour_entry.get() else 0
        m = int(timer_min_entry.get()) if timer_min_entry.get() else 0
        s = int(timer_sec_entry.get()) if timer_sec_entry.get() else 0
        total_seconds = h * 3600 + m * 60 + s

        if total_seconds > 0:
            timer_seconds = total_seconds
            timer_running = True
            timer_paused = False
            timer_start_stop_button.configure(image=timer_stop_img)
            countdown()
    except ValueError:
        pass

def countdown():
    global timer_seconds, timer_running, sound_thread, timer_countdown_job
    if timer_seconds > 0 and timer_running:
        mins, secs = divmod(timer_seconds, 60)
        hours, mins = divmod(mins, 60)
        timer_label.configure(text=f"{hours:02}:{mins:02}:{secs:02}")
        timer_seconds -= 1
        timer_countdown_job = window.after(1000, countdown)
    elif timer_seconds <= 0 and timer_running:
        timer_running = False
        timer_label.configure(text="00:00:00")
        timer_start_stop_button.configure(image=start_img)

        stop_sound_button.place(relx=0.5, rely=0.05, anchor="center")

        if not sound_playing:
            sound_thread = threading.Thread(target=play_sound_loop, daemon=True)
            sound_thread.start()

def toggle_timer():
    global timer_running, timer_paused
    if not timer_running and not timer_paused:
        start_timer()
    elif timer_running:
        pause_timer()
    elif timer_paused:
        resume_timer()

def pause_timer():
    global timer_running, timer_paused, timer_countdown_job
    if timer_running:
        timer_running = False
        timer_paused = True
        if timer_countdown_job:
            window.after_cancel(timer_countdown_job)
        timer_start_stop_button.configure(image=timer_start_img)

def resume_timer():
    global timer_running, timer_paused
    if timer_paused:
        timer_running = True
        timer_paused = False
        timer_start_stop_button.configure(image=timer_stop_img)
        countdown()

def reset_timer():
    global timer_seconds, timer_running, timer_paused, timer_countdown_job
    if timer_countdown_job:
        window.after_cancel(timer_countdown_job)
    timer_running = False
    timer_paused = False
    timer_seconds = 0
    timer_label.configure(text="00:00:00")
    timer_start_stop_button.configure(image=timer_start_img)


def play_sound_loop():
    global sound_playing
    sound_playing = True
    start_time = time.time()
    sound_file = os.path.join(base_path, "assets", "timer_sound.mp3")
    sound_file = str(pathlib.Path(sound_file).absolute()) 

    while sound_playing and (time.time() - start_time) < 300:
        playsound.playsound(sound_file, block=True)




def stop_sound():
    global sound_playing
    sound_playing = False
    stop_sound_button.place_forget()

# Alarm Functions
alarms = [] 

def open_alarm_window():
    alarm_window = ctk.CTkToplevel(window)
    alarm_window.title("Add Alarm")
    alarm_window.geometry("400x300")
    alarm_window.lift()
    alarm_window.focus_force()
    alarm_window.grab_set()

    time_label = ctk.CTkLabel(alarm_window, text="Set Time (HH:MM)", font=("Arial Rounded MT Bold", 20))
    time_label.pack(pady=(20, 5))

    time_entry = ctk.CTkEntry(alarm_window, placeholder_text="e.g., 07:30")
    time_entry.pack(pady=5)

    msg_label = ctk.CTkLabel(alarm_window, text="Message (Optional)", font=("Arial Rounded MT Bold", 20))
    msg_label.pack(pady=(10, 5))

    msg_entry = ctk.CTkEntry(alarm_window, placeholder_text="Wake up!")

    msg_entry.pack(pady=5)

    save_button = ctk.CTkButton(alarm_window, text="Save Alarm", fg_color="#2196F3", text_color="white", font=("Arial Rounded MT Bold", 15),
                                hover_color="#1976D2", command=lambda: save_alarm(time_entry.get(), msg_entry.get(), alarm_window))
    save_button.pack(pady=20)

def save_alarm(time_str, message, window_ref):
    try:
        time_obj = datetime.strptime(time_str.strip(), "%H:%M")
        formatted_time = time_obj.strftime("%H:%M")  # Standardize to HH:MM
        alarms.append({"time": formatted_time, "message": message, "enabled": ctk.BooleanVar(value=True)})
        refresh_alarm_display()
        window_ref.destroy()
    except ValueError:
        ctk.CTkMessageBox(title="Invalid Time", message="Enter time as HH:MM (24-hour format)", icon="warning")


def refresh_alarm_display():
    for widget in alarm_list_display.winfo_children():
        widget.destroy()

    for idx, alarm in enumerate(alarms):
        row_frame = ctk.CTkFrame(alarm_list_display, fg_color="#202020")
        row_frame.pack(fill="x", pady=2, padx=5)

        time_lbl = ctk.CTkLabel(row_frame, text=f"{idx + 1}. {alarm['time']}\n     {alarm['message']}", text_color="white", font=("Arial Rounded MT Bold", 20))
        time_lbl.pack(side="left", padx=5)

        enable_cb = ctk.CTkCheckBox(row_frame, text="", variable=alarm["enabled"], fg_color="#2196F3", hover_color="#1976D2", text_color="white")
        enable_cb.pack(side="right", padx=5)


def toggle_alarm_state():
    selected_text = alarm_list_display.get("sel.first", "sel.last").strip()
    if not selected_text:
        return  

    try:
        index = int(selected_text.split(".")[0]) - 1  
        if 0 <= index < len(alarms):
            alarms[index]["enabled"] = not alarms[index]["enabled"]
            refresh_alarm_display()
    except (IndexError, ValueError):
        pass


def check_alarms():
    global sound_thread, sound_playing

    now = datetime.now().strftime("%H:%M")  

    for alarm in alarms:
        alarm_time = alarm["time"].strip()

        if alarm_time == now and alarm["enabled"].get() and not sound_playing:
            stop_sound_button.place(relx=0.5, rely=0.05, anchor="center")
            sound_thread = threading.Thread(target=play_sound_loop, daemon=True)
            sound_thread.start()
            break

    window.after(1000, check_alarms)  




# Tab Logic
def set_active(button, target_x):
    global active_button, clock_running

    if active_button:
        active_button.configure(fg_color="#323232", text_color="white")

    # Hide all
    time_label.pack_forget()
    timezone_spacer.pack_forget()
    alarm_label.place_forget()
    stopwatch_label.pack_forget()
    stopwatch_button_frame.pack_forget()
    lap_display.pack_forget()
    timer_label.pack_forget()
    timer_button_frame.pack_forget()
    add_alarm_button.place_forget()
    alarm_list_display.pack_forget()

    for lbl in timezone_labels:
        lbl.pack_forget()

    button.configure(fg_color="#202020", text_color="white")
    animate_highlight(target_x)
    active_button = button

    if sound_playing:
        stop_sound_button.place(relx=0.5, rely=0.05, anchor="center")

    if active_button == clock_button:
        time_label.pack(pady=(80, 10))
        timezone_spacer.pack()
        for lbl in timezone_labels:
            lbl.pack(pady=(2, 0))
        if not clock_running:
            clock_running = True
            update_time()
    else:
        clock_running = False

    if active_button == alarm_button:
        alarm_label.place(x=40, y=20) 
        add_alarm_button.place(x=190, y= 30)
        alarm_list_display.pack(pady=(100, 10))



    elif active_button == stopwatch_button:
        stopwatch_label.pack(pady=(80, 10))
        stopwatch_button_frame.pack(pady=(10, 20), side="bottom")
        lap_display.pack(pady=(10, 10))

    elif active_button == timer_button:
        timer_label.pack(pady=(80, 10))
        timer_button_frame.pack(pady=(10, 20))

# Button Placement
lap_button.grid(row=0, column=0, padx=10)
start_stop_button.grid(row=0, column=1, padx=10)
reset_button.grid(row=0, column=2, padx=10)

# Footer Buttons
button_style = {"corner_radius": 20, "height": 50, "width": 100, "fg_color": "#323232", "hover_color": "#202020", "text_color": "white", "bg_color": "#323232", "font": ("Arial Rounded MT Bold", 20)}
alarm_button = ctk.CTkButton(footer_frame, text="Alarm", command=lambda: set_active(alarm_button, start_x), **button_style)
clock_button = ctk.CTkButton(footer_frame, text="Clock", command=lambda: set_active(clock_button, start_x + button_spacing), **button_style)
stopwatch_button = ctk.CTkButton(footer_frame, text="Stopwatch", command=lambda: set_active(stopwatch_button, start_x + 2 * button_spacing), **button_style)
timer_button = ctk.CTkButton(footer_frame, text="Timer", command=lambda: set_active(timer_button, start_x + 3 * button_spacing), **button_style)

alarm_button.place(x=start_x, y=button_y, anchor="center")
clock_button.place(x=start_x + button_spacing, y=button_y, anchor="center")
stopwatch_button.place(x=start_x + 2 * button_spacing, y=button_y, anchor="center")
timer_button.place(x=start_x + 3 * button_spacing, y=button_y, anchor="center")

set_active(clock_button, start_x + button_spacing)
check_alarms()

window.mainloop()
