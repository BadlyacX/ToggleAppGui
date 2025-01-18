import tkinter as tk
from tkinter import ttk, filedialog
import os
import google.generativeai as genai
import cv2
from ffpyplayer.player import MediaPlayer
import tkinter as tk
from PIL import Image, ImageTk
import keyboard as kb
import threading
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("GEMINI_CHAT_TOKEN")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

class ToggleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("功能切換介面")

        self.items_frame = ttk.Frame(root)
        self.items_frame.pack(pady=10)

        self.items = {}
        self.infinite_windows_active = False
        self.open_windows = []
        self.black_screen_window = None
        self.count_files_window_instance = None
        self.gemini_chat_window_instance = None

    def create_item(self, item_name):
        if item_name and item_name not in self.items:
            item_frame = ttk.Frame(self.items_frame)
            item_frame.pack(fill="x", pady=5)

            item_label = ttk.Label(item_frame, text=item_name)
            item_label.pack(side="left", padx=10)

            toggle_button = ttk.Button(item_frame, text="OFF", command=lambda: self.toggle_status(item_name))
            toggle_button.pack(side="right", padx=10)

            self.items[item_name] = {
                "button": toggle_button,
                "status": "OFF"
            }

    def toggle_status(self, item_name):
        if item_name in self.items:
            current_status = self.items[item_name]["status"]
            new_status = "ON" if current_status == "OFF" else "OFF"
            self.items[item_name]["status"] = new_status
            self.items[item_name]["button"].config(text=new_status)

            if item_name == "infinite windows":
                if new_status == "ON":
                    self.infinite_windows_active = True
                    self.infinite_windows()
                else:
                    self.infinite_windows_active = False
                    self.close_all_windows()

            if item_name == "black screen":
                if new_status == "ON":
                    self.show_black_screen()
                else:
                    self.close_black_screen()

            if item_name == "count files":
                if new_status == "ON":
                    self.count_files_window()
                else:
                    self.close_count_files_window()

            if item_name == "gemini chat":
                if new_status == "ON":
                    self.gemini_chat_window()
                else:
                    self.close_gemini_chat_window()

            if item_name == "rickroll trolling": 
                if new_status == "ON":
                    monitor_key_and_trigger(callback=lambda: play_video("rickroll.mp4"))
                else:
                    stop_monitoring()   
                return

    def get_status(self, item_name):
        return self.items.get(item_name, {}).get("status", None)

    def infinite_windows(self):
        if self.infinite_windows_active:
            new_window = tk.Toplevel(self.root)
            new_window.attributes("-topmost", True)
            self.open_windows.append(new_window)
            new_window.title("ERROR")
        
            new_window.protocol("WM_DELETE_WINDOW", lambda: self.on_window_close(new_window))

    def on_window_close(self, closed_window):
        if self.infinite_windows_active:
            if closed_window in self.open_windows:
                self.open_windows.remove(closed_window)
            closed_window.destroy()
            self.infinite_windows()
            self.infinite_windows()

    def close_all_windows(self):
        for window in self.open_windows:
            window.destroy()
        self.open_windows.clear()

    def show_black_screen(self):
        if self.black_screen_window is None:
            self.black_screen_window = tk.Toplevel(self.root)
            self.black_screen_window.title("黑屏")
            self.black_screen_window.configure(bg="black")
            self.black_screen_window.attributes("-topmost", True)
            self.black_screen_window.protocol("WM_DELETE_WINDOW", self.show_black_screen)

    def close_black_screen(self):
        if self.black_screen_window is not None:
            self.black_screen_window.destroy()
            self.black_screen_window = None

    def count_files_window(self):
        if self.count_files_window_instance is not None:
            return

        def scan_directory(directory):
            file_structure = {}
            total_files = 0
            for root, dirs, files in os.walk(directory):
                relative_path = os.path.relpath(root, directory)
                file_structure[relative_path] = files
                total_files += len(files)
            return file_structure, total_files

        def count_files():
            directory = filedialog.askdirectory()
            if directory:
                file_structure, total_files = scan_directory(directory)
                result_text = f"總檔案數量: {total_files}\n\n"
                for folder, files in file_structure.items():
                    result_text += f"{folder}\\\n" + "\n".join([f"  {file}" for file in files]) + "\n\n"
                result_textbox.delete(1.0, tk.END)
                result_textbox.insert(tk.END, result_text)

        self.count_files_window_instance = tk.Toplevel(self.root)
        self.count_files_window_instance.title("Count Files")
        self.count_files_window_instance.protocol("WM_DELETE_WINDOW", self.close_count_files_window)

        instruction_label = ttk.Label(self.count_files_window_instance, text="選擇一個目錄來計算檔案數量")
        instruction_label.pack(pady=10)

        browse_button = ttk.Button(self.count_files_window_instance, text="瀏覽目錄", command=count_files)
        browse_button.pack(pady=5)

        text_frame = ttk.Frame(self.count_files_window_instance)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)

        text_scrollbar = ttk.Scrollbar(text_frame)
        text_scrollbar.pack(side="right", fill="y")

        result_textbox = tk.Text(text_frame, wrap="none", yscrollcommand=text_scrollbar.set)
        result_textbox.pack(fill="both", expand=True)

        text_scrollbar.config(command=result_textbox.yview)

    def close_count_files_window(self):
        if self.count_files_window_instance is not None:
            self.count_files_window_instance.destroy()
            self.count_files_window_instance = None

    def gemini_chat_window(self):
        if self.gemini_chat_window_instance is not None:
            return

        def send_message():
            user_message = user_input.get()
            if user_message:
                chat_display.insert(tk.END, f"User: {user_message}\n")
                user_input.delete(0, tk.END)
                try:
                    response = model.generate_content(user_message)
                    gemini_message = response.text
                except Exception as e:
                    gemini_message = f"Error: {e}"
                chat_display.insert(tk.END, f"Gemini: {gemini_message}\n")
                chat_display.see(tk.END)

        self.gemini_chat_window_instance = tk.Toplevel(self.root)
        self.gemini_chat_window_instance.title("Gemini Chat")
        self.gemini_chat_window_instance.protocol("WM_DELETE_WINDOW", self.close_gemini_chat_window)

        text_frame = ttk.Frame(self.gemini_chat_window_instance)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)

        text_scrollbar = ttk.Scrollbar(text_frame)
        text_scrollbar.pack(side="right", fill="y")

        chat_display = tk.Text(text_frame, wrap="word", yscrollcommand=text_scrollbar.set, state="normal")
        chat_display.pack(fill="both", expand=True)

        text_scrollbar.config(command=chat_display.yview)

        user_input_frame = ttk.Frame(self.gemini_chat_window_instance)
        user_input_frame.pack(fill="x", padx=10, pady=5)

        user_input = ttk.Entry(user_input_frame)
        user_input.pack(side="left", fill="x", expand=True, padx=(0, 5))

        send_button = ttk.Button(user_input_frame, text="Send", command=send_message)
        send_button.pack(side="right")

    def close_gemini_chat_window(self):
        if self.gemini_chat_window_instance is not None:
            self.gemini_chat_window_instance.destroy()
            self.gemini_chat_window_instance = None


class VideoPlayerWithAudio:
    def __init__(self, video_path, root):
        self.video_path = video_path
        self.player = MediaPlayer(video_path)
        self.cap = cv2.VideoCapture(video_path)

        self.root = root
        self.root.title("Video Player with Audio")

        self.video_label = tk.Label(self.root)
        self.video_label.pack()

        self.close_button = tk.Button(self.root, text="Close", command=self.stop)
        self.close_button.pack()

        self.running = True

    def start(self):
        self.update_frame()
        self.root.protocol("WM_DELETE_WINDOW", self.stop)
        self.root.mainloop()

    def stop(self):
        self.running = False
        self.cap.release()
        self.player.close_player()
        self.root.destroy()

    def update_frame(self):
        if not self.running:
            return

        ret, frame = self.cap.read()
        if ret:
        
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=image)
            self.imgtk = ImageTk.PhotoImage(image=image)
            self.video_label.configure(image=self.imgtk)

        else:
            self.stop()
            return

        audio_frame, _ = self.player.get_frame()

        self.root.after(10, self.update_frame)

def play_video(video_path):
    new_window = tk.Toplevel()
    new_window.attributes("-topmost", True)
    player = VideoPlayerWithAudio(video_path, new_window)
    player.start()

def monitor_key_and_trigger(callback=None):
    def key_listener():
        target_sequence = "rickroll"
        buffer = ""

        try:
            while monitor_key_and_trigger.running:
                event = kb.read_event()
                if event.event_type == "down":
                    key = event.name.lower()
                    buffer += key
                    if len(buffer) > len(target_sequence):
                        buffer = buffer[-len(target_sequence):]

                    if target_sequence in buffer:
                        buffer = ""
                        if callback:
                            root.after(0, callback) 
        except Exception as e:
            print(f"鍵盤監控出錯：{e}")

    monitor_key_and_trigger.running = True
    listener_thread = threading.Thread(target=key_listener, daemon=True)
    listener_thread.start()

def stop_monitoring():
    monitor_key_and_trigger.running = False

if __name__ == "__main__":
    root = tk.Tk()
    app = ToggleApp(root)

    app.create_item("infinite windows")
    app.create_item("black screen")
    app.create_item("count files")
    app.create_item("gemini chat")
    app.create_item("rickroll trolling")

    root.mainloop()
