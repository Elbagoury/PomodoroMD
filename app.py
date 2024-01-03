import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QMessageBox
from PyQt5.QtCore import QTimer, QDateTime, Qt, QCoreApplication
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QIcon 
import os
import re
import configparser
from qdarkstyle import load_stylesheet_pyqt5  # Import QDarkStyleSheet
from plyer import notification
import pygame

class PomodoroModel:
    def __init__(self, tasks_directory, sessions_directory):
        self.start_time = None
        self.session_count = 0
        self.tasks_directory = tasks_directory
        self.sessions_directory = sessions_directory

    def start_timer(self):
        self.start_time = QDateTime.currentDateTime()
        self.session_count += 1

    def stop_timer(self):
        self.start_time = None

    def calculate_duration(self, end_time):
        if self.start_time:
            duration = self.start_time.secsTo(end_time)
            minutes, seconds = divmod(duration, 60)
            return f"{str(minutes).zfill(2)}:{str(seconds).zfill(2)}"
        return "00:00"

class PomodoroView(QWidget):
    def __init__(self, controller, tasks_directory, sessions_directory):
        super().__init__()
        self.controller = controller
        self.tasks_directory = tasks_directory
        self.sessions_directory = sessions_directory

        self.task_name = QComboBox(self)
        self.time_left = QLabel(self)
        self.time_left.setFont(QFont("Arial", 40))
        self.session_duration = QLineEdit(self)
        self.session_duration.setText("25")

        self.task_list = self.read_tasks_from_files()
        self.task_name.addItems(self.task_list)

        self.create_widgets()

    def create_widgets(self):
        layout = QVBoxLayout(self)

        task_layout = QHBoxLayout()
        task_layout.addWidget(QLabel("Task Name:", self))
        task_layout.addWidget(self.task_name)

        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Session Duration (minutes):", self))
        duration_layout.addWidget(self.session_duration)

        timer_layout = QVBoxLayout()
        timer_layout.addWidget(self.time_left, alignment=Qt.AlignCenter)

        self.start_button = self.create_button("Start", self.controller.start_timer)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)

        layout.addLayout(task_layout)
        layout.addLayout(duration_layout)
        layout.addLayout(timer_layout)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Apply the dark theme
        self.setStyleSheet(load_stylesheet_pyqt5())

        # Set window title and icon
        self.setWindowTitle("Pomodoro")
        self.setWindowIcon(QIcon("icon.ico"))

    def create_button(self, text, function, enabled=True):
        button = QPushButton(text, self)
        button.clicked.connect(function)
        button.setEnabled(enabled)
        if text == "Start":
            self.start_button = button
        return button


    def read_tasks_from_files(self):
        tasks = []
        for filename in os.listdir(self.tasks_directory):
            if filename.endswith(".md"):
                with open(os.path.join(self.tasks_directory, filename), "r") as file:
                    content = file.read()
                    tasks += [f"{os.path.splitext(filename)[0]} | {task.strip('- [] ')}" for task in re.findall(r"- \[ \].*", content)]
        return tasks

    def update_time(self, time_left):
        self.time_left.setText(time_left)

    def show_session_completed_message(self):
        # Show notification
        notification_title = "PomodoroMD"
        notification_message = f"Achievement: Your Session Completed!"
        notification.notify(
            title=notification_title,
            message=notification_message,
            app_name=notification_title
        )

        # Play alarm sound
        pygame.mixer.init()
        pygame.mixer.music.load("C:\\Windows\\Media\\Alarm03.wav")  # Replace with the path to your alarm sound
        pygame.mixer.music.play()


class PomodoroController:
    def __init__(self, view):
        self.config = self.load_config()
        tasks_directory = self.config.get("Directories", "TasksDirectory")
        sessions_directory = self.config.get("Directories", "SessionsDirectory")

        self.model = PomodoroModel(tasks_directory, sessions_directory)
        self.view = view(self, tasks_directory, sessions_directory)

    def load_config(self):
        config = configparser.ConfigParser()
        config.read("config.ini")
        return config

    def start_timer(self):
        if not self.model.start_time:
            self.model.start_timer()
            self.view.update_time(f"{str(self.view.session_duration.text()).zfill(2)}:00")
            self.view.timer_id = QTimer(self.view)
            self.view.timer_id.timeout.connect(self.update_timer)
            self.view.timer_id.start(1000)
            self.view.start_button.setEnabled(False)  # Disable Start button
        else:
            # Continue timer
            self.view.timer_id.start(1000)
            self.view.start_button.setEnabled(False)  # Disable Start button

    def update_timer(self):
        current_time = self.view.time_left.text()
        if current_time != "00:00":
            minutes, seconds = map(int, current_time.split(':'))
            total_seconds = minutes * 60 + seconds
            total_seconds -= 1
            minutes, seconds = divmod(total_seconds, 60)
            self.view.update_time(f"{str(minutes).zfill(2)}:{str(seconds).zfill(2)}")
        else:
            self.stop_timer()
            end_time = QDateTime.currentDateTime()
            self.enable_start_button()  # Enable Start button

    def stop_timer(self):
        if self.view.timer_id.isActive():
            self.view.timer_id.stop()
            self.view.show_session_completed_message()
            self.save_session()  # Save session automatically when stopping the timer
            self.is_timer_running = False
        else:
            self.view.timer_id.start(1000)

    def enable_start_button(self):
        # Enable Start button
        self.view.start_button.setEnabled(True)

    def save_session(self):
        task_name = self.view.task_name.currentText()
        if task_name and self.model.start_time:
            end_time = QDateTime.currentDateTime()
            duration = self.model.calculate_duration(end_time)

            filename = os.path.splitext(task_name.split("|")[0].strip())[0].strip()
            today_date = end_time.toString("yyyy-MM-dd")

            session_info = f"[[{filename}]] #{task_name} duration:{duration}\n"
            file_path = os.path.join(self.model.sessions_directory, f"{today_date}.md")

            with open(file_path, "a") as file:
                file.write(session_info)

            QMessageBox.information(self.view, "PomodoroMD", "Session saved successfully!")
        else:
            QMessageBox.warning(self.view, "PomodoroMD", "Please start a session before saving the session.")
    
    def on_close(self):
        if self.model.start_time:
            self.save_session()    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(load_stylesheet_pyqt5())  # Apply the dark theme to the entire application
    pygame.mixer.init()
    pygame.mixer.music.load("C:\\Windows\\Media\\Alarm03.wav")
    controller = PomodoroController(PomodoroView)
    controller.view.show()
    sys.exit(app.exec_())
