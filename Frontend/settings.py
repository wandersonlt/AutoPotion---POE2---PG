import customtkinter as ctk
import json
import os

class SettingsWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Settings")
        self.window.geometry("400x300")
        self.window.resizable(False, False)
        
        self.window.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - 200
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - 150
        self.window.geometry(f"400x300+{x}+{y}")
        
        self.setup_ui()
    
    def setup_ui(self):
        main_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        title_label = ctk.CTkLabel(
            main_frame,
            text="Settings",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        theme_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        theme_frame.pack(fill="x", pady=10)
        
        theme_label = ctk.CTkLabel(
            theme_frame,
            text="Theme:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        theme_label.pack(anchor="w", pady=(0, 5))
        
        self.theme_var = ctk.StringVar(value="Dark")
        theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=["Dark", "Light"],
            variable=self.theme_var,
            command=self.change_theme
        )
        theme_menu.pack(fill="x")
        
        close_button = ctk.CTkButton(
            main_frame,
            text="Close",
            command=self.window.destroy,
            height=40
        )
        close_button.pack(pady=20)
    
    def change_theme(self, choice):
        if choice == "Dark":
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")
    
    def run(self):
        self.window.grab_set()
        self.window.wait_window()
