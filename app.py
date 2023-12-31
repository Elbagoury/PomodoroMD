# pomodoro_app.py
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, timedelta
import re
import os
import configparser

class PomodoroModel:
    def __init__(self, tasks_directory, sessions_directory):
        self.start_time = None
        self.session_count = 0
        self.tasks_directory = tasks_directory
        self.sessions_directory = sessions_directory

    def start_timer(self):
        self.start_time = datetime.now()
        self.session_count += 1

    def stop_timer(self):
        self.start_time = None

    def calculate_duration(self, end_time):
        if self.start_time:
            duration = end_time - self.start_time
            minutes, seconds = divmod(duration.seconds, 60)
            return f"{str(minutes).zfill(2)}:{str(seconds).zfill(2)}"
        return "00:00"

class PomodoroView:
    def __init__(self, root, controller, tasks_directory, sessions_directory, theme):
        self.root = root
        self.controller = controller
        self.tasks_directory = tasks_directory
        self.sessions_directory = sessions_directory
        self.theme = theme

        self.task_name = tk.StringVar()
        self.time_left = tk.StringVar()
        self.session_duration = tk.IntVar(value=25)

        self.task_list = self.read_tasks_from_files()

        self.create_widgets()

    def create_widgets(self):
        self.root.title("PomodoroMD")
        self.root.configure(bg='#282c34' if self.theme == 'dark' else 'white')  # Set background color based on theme

        task_label = tk.Label(self.root, text="Task Name:", bg='#282c34' if self.theme == 'dark' else 'white', fg='white' if self.theme == 'dark' else 'black')
        task_label.pack(pady=5)

        task_dropdown = tk.OptionMenu(self.root, self.task_name, *self.task_list)
        task_dropdown.config(bg='#282c34' if self.theme == 'dark' else 'white', fg='white' if self.theme == 'dark' else 'black', width=50)
        task_dropdown.pack(pady=5)

        duration_label = tk.Label(self.root, text="Session Duration (minutes):", bg='#282c34' if self.theme == 'dark' else 'white', fg='white' if self.theme == 'dark' else 'black')
        duration_label.pack(pady=5)

        duration_entry = tk.Entry(self.root, textvariable=self.session_duration, bg='#282c34' if self.theme == 'dark' else 'white', fg='white' if self.theme == 'dark' else 'black', insertbackground='white' if self.theme == 'dark' else 'black')
        duration_entry.pack(pady=5)

        timer_label = tk.Label(self.root, textvariable=self.time_left, font=("Helvetica", 24), bg='#282c34' if self.theme == 'dark' else 'white', fg='white' if self.theme == 'dark' else 'black')
        timer_label.pack(pady=20)

        style = ttk.Style()
        style.configure("TButton", padding=6, relief="flat", background='#61dafb' if self.theme == 'dark' else 'white', foreground='black' if self.theme == 'dark' else 'black')

        start_button = ttk.Button(self.root, text="Start", command=self.controller.start_timer, style="TButton")
        start_button.pack(side=tk.LEFT, padx=10)

        stop_button = ttk.Button(self.root, text="Stop", command=self.controller.stop_timer, state=tk.DISABLED, style="TButton")
        stop_button.pack(side=tk.LEFT, padx=10)

        reset_button = ttk.Button(self.root, text="Reset", command=self.controller.reset_timer, state=tk.DISABLED, style="TButton")
        reset_button.pack(side=tk.LEFT, padx=10)

        save_button = ttk.Button(self.root, text="Save Session", command=self.controller.save_session, style="TButton")
        save_button.pack(pady=20)

    def read_tasks_from_files(self):
        tasks = []
        for filename in os.listdir(self.tasks_directory):
            if filename.endswith(".md"):
                with open(os.path.join(self.tasks_directory, filename), "r") as file:
                    content = file.read()
                    tasks += [f"{os.path.splitext(filename)[0]} | {task.strip('- [] ')}" for task in re.findall(r"- \[ \].*", content)]
        return tasks

    def update_time(self, time_left):
        self.time_left.set(time_left)

    def show_session_completed_message(self, duration):
        messagebox.showinfo("PomodoroMD", f"Session Completed! Duration: {duration}")

class PomodoroController:
    def __init__(self, root):
        self.config = self.load_config()
        tasks_directory = self.config.get("Directories", "TasksDirectory")
        sessions_directory = self.config.get("Directories", "SessionsDirectory")
        theme = self.config.get("Theme", "AppTheme")

        self.model = PomodoroModel(tasks_directory, sessions_directory)
        self.view = PomodoroView(root, self, tasks_directory, sessions_directory, theme)

    def load_config(self):
        config = configparser.ConfigParser()
        config.read("config.ini")
        return config

    def start_timer(self):
        self.model.start_timer()
        self.view.update_time(f"{str(self.view.session_duration.get()).zfill(2)}:00")
        self.view.root.after_id = self.view.root.after(1000, self.update_timer)
        self.enable_stop_reset_buttons()

    def update_timer(self):
        current_time = self.view.time_left.get()
        if current_time != "00:00":
            minutes, seconds = map(int, current_time.split(':'))
            total_seconds = minutes * 60 + seconds
            total_seconds -= 1
            minutes, seconds = divmod(total_seconds, 60)
            self.view.time_left.set(f"{str(minutes).zfill(2)}:{str(seconds).zfill(2)}")
            self.view.root.after_id = self.view.root.after(1000, self.update_timer)
        else:
            self.stop_timer()
            end_time = datetime.now().strftime('%H:%M')
            duration = self.model.calculate_duration(datetime.now())
            self.view.show_session_completed_message(duration)

    def stop_timer(self):
        self.view.root.after_cancel(self.view.root.after_id)
        self.disable_stop_reset_buttons()

    def reset_timer(self):
        self.view.time_left.set(f"{str(self.view.session_duration.get()).zfill(2)}:00")
        self.disable_stop_reset_buttons()

    def enable_stop_reset_buttons(self):
        self.view.root.children['!button2'].config(state=tk.NORMAL)
        self.view.root.children['!button3'].config(state=tk.NORMAL)

    def disable_stop_reset_buttons(self):
        self.view.root.children['!button2'].config(state=tk.DISABLED)
        self.view.root.children['!button3'].config(state=tk.DISABLED)

    def save_session(self):
        task_name = self.view.task_name.get()
        if task_name and self.model.start_time:
            end_time = datetime.now().strftime('%H:%M')
            duration = self.model.calculate_duration(datetime.now())

            filename = os.path.splitext(task_name.split("|")[0].strip())[0].strip()

            session_info = f"{end_time} [[{filename}]] {task_name} duration: ({duration})\n"

            today_date = datetime.now().strftime('%Y-%m-%d')
            file_path = os.path.join(self.model.sessions_directory, f"{today_date}.md")

            with open(file_path, "a") as file:
                file.write(session_info)

            messagebox.showinfo("PomodoroMD", "Session saved successfully!")
        else:
            messagebox.showwarning("PomodoroMD", "Please start a session before saving the session.")

if __name__ == "__main__":
    root = tk.Tk()
    controller = PomodoroController(root)
    root.mainloop()
