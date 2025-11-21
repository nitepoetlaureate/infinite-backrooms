#!/usr/bin/env python3
"""
AI Backrooms - System 7 IRC Edition
A retro chat client where AI personas discuss topics 24/7

COMPLETE IMPLEMENTATION with all features:
- Tutorial system
- Control Panel
- Data persistence
- IRC commands
- @mention highlighting
- Sound effects
- Daily logging

Usage:
    python3 main.py

Prerequisites:
    - Python 3.8+
    - (Optional) Ollama running locally with a model pulled

Memory footprint: ~35MB
"""

import tkinter as tk
import queue
import re
from system7_ui import (
    S7Window, S7Button, S7Frame, S7InsetFrame, S7Font,
    c_PLATINUM, c_WHITE, c_BLACK, c_DK_GRAY
)
from engine import BackroomsEngine, DEFAULT_ROOMS
from persistence import DataManager
from tutorial import TutorialDialog, show_welcome_dialog
from control_panel import ControlPanel
from irc_commands import IRCCommandHandler
import sounds


class IRCClient:
    """
    Main IRC client application with full feature set.

    Integrates:
    - System 7 UI components
    - Background conversation engine
    - Thread-safe message queue
    - Room management
    - Tutorial system
    - Control Panel
    - Data persistence
    - IRC commands
    - @mention detection
    - Sound effects
    """

    def __init__(self, root):
        self.root = root
        self.root.title("AI Backrooms")
        self.root.configure(bg=c_PLATINUM)

        # Initialize data manager
        self.data_manager = DataManager()

        # Load settings
        self.settings = self.data_manager.load_settings()

        # Apply window geometry
        geometry = self.settings.get("window_geometry", "800x600")
        self.root.geometry(geometry)

        # Initialize sound system
        sounds.init_sounds(self.settings.get("enable_sounds", False))

        # Message Queue (Thread -> GUI)
        self.msg_queue = queue.Queue()

        # Engine with logging callback
        self.engine = BackroomsEngine(
            self.on_engine_message,
            log_callback=self.data_manager.log_message
        )

        # Load custom personas if available
        custom_personas = self.data_manager.load_personas()
        if custom_personas:
            self.engine.personas = custom_personas

        self.current_room = "general"
        self.user_nickname = "You"
        self._tutorial_message_sent = False

        # IRC command handler
        self.irc_commands = IRCCommandHandler(self)

        # Build UI
        self.setup_ui()

        # Show tutorial if first time
        if not self.settings.get("tutorial_completed", False):
            self.root.after(500, self.show_first_time_tutorial)

        # Start Engine
        self.engine.start()

        # Start Queue Poller
        self.root.after(100, self.process_queue)

        # Save settings on close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        """Handle window close."""
        # Save window geometry
        self.settings["window_geometry"] = self.root.geometry()
        self.data_manager.save_settings(self.settings)

        # Save personas
        self.data_manager.save_personas(self.engine.personas)

        # Stop engine
        self.engine.stop()

        # Destroy window
        self.root.destroy()

    def show_first_time_tutorial(self):
        """Show tutorial on first launch."""
        if show_welcome_dialog(self.root):
            tutorial = TutorialDialog(self.root, self)
            completed = tutorial.run()

            if completed:
                self.settings["tutorial_completed"] = True
                self.data_manager.save_settings(self.settings)

    def on_engine_message(self, msg):
        """Callback from engine when new message is generated."""
        self.msg_queue.put(msg)

    def process_queue(self):
        """Poll the message queue and update UI."""
        try:
            while True:
                msg = self.msg_queue.get_nowait()
                if msg['room'] == self.current_room:
                    self.display_message(msg)

                # Play sound for new messages
                if msg.get('is_ai', False) and sounds.get_sound_player():
                    sounds.play_quack()

        except queue.Empty:
            pass
        self.root.after(100, self.process_queue)

    def setup_ui(self):
        """Build the main IRC client interface."""

        # --- Menu Bar ---
        menubar = tk.Frame(self.root, bg=c_WHITE, height=20, bd=1, relief="raised")
        menubar.pack(fill="x", side="top")

        # Menu items
        menu_frame = tk.Frame(menubar, bg=c_WHITE)
        menu_frame.pack(side="left")

        # File menu (fake, just labels for now)
        for menu_name in [" File ", " Edit ", " View ", " Rooms ", " Personas ", " Help "]:
            label = tk.Label(
                menu_frame,
                text=menu_name,
                bg=c_WHITE,
                fg=c_BLACK,
                font=S7Font.chicago(10),
                cursor="hand2"
            )
            label.pack(side="left")

            # Bind click for Personas menu
            if "Personas" in menu_name:
                label.bind("<Button-1>", lambda e: self.open_control_panel())

        # --- Main Layout ---
        main_frame = S7Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Left Panel: Rooms
        left_panel = S7Frame(main_frame, width=150)
        left_panel.pack(side="left", fill="y", padx=2)

        tk.Label(
            left_panel,
            text="📡 Servers",
            font=S7Font.chicago(),
            bg=c_PLATINUM,
            fg=c_BLACK
        ).pack(anchor="w")

        tk.Label(
            left_panel,
            text="⚡ Local Ollama",
            font=S7Font.geneva(),
            bg=c_PLATINUM,
            fg="darkgreen"
        ).pack(anchor="w", padx=10)

        tk.Label(
            left_panel,
            text="📚 Rooms",
            font=S7Font.chicago(),
            bg=c_PLATINUM,
            fg=c_BLACK
        ).pack(anchor="w", pady=(10, 0))

        self.room_list = tk.Listbox(
            left_panel,
            bg=c_WHITE,
            fg=c_BLACK,
            font=S7Font.geneva(),
            bd=1,
            relief="sunken",
            selectbackground="black",
            selectforeground="white"
        )
        self.room_list.pack(fill="both", expand=True)

        for r in DEFAULT_ROOMS:
            self.room_list.insert("end", f"# {r['name']}")
        self.room_list.bind('<<ListboxSelect>>', self.change_room)

        # Center Panel: Chat
        center_panel = S7Frame(main_frame)
        center_panel.pack(side="left", fill="both", expand=True, padx=2)

        # Header
        self.header_label = tk.Label(
            center_panel,
            text=f"# {self.current_room} [Loading...]",
            font=S7Font.chicago(),
            bg=c_PLATINUM,
            fg=c_BLACK
        )
        self.header_label.pack(fill="x", pady=2)

        # Chat Area
        chat_frame = S7InsetFrame(center_panel)
        chat_frame.pack(fill="both", expand=True)

        self.chat_text = tk.Text(
            chat_frame,
            bg=c_WHITE,
            fg=c_BLACK,
            font=S7Font.monaco(),
            state="disabled",
            wrap="word",
            bd=0,
            insertbackground=c_BLACK
        )
        scrollbar = tk.Scrollbar(chat_frame, command=self.chat_text.yview)
        self.chat_text.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.chat_text.pack(side="left", fill="both", expand=True)

        # Tags for styling
        self.chat_text.tag_config("timestamp", foreground="gray")
        self.chat_text.tag_config("nick", font=S7Font.monaco(9) + ("bold",))
        self.chat_text.tag_config("self", foreground="blue")
        self.chat_text.tag_config("ai", foreground="black")
        self.chat_text.tag_config("system", foreground="darkgreen", font=S7Font.geneva(9) + ("italic",))
        self.chat_text.tag_config("mention", background="yellow", foreground="black")

        # Input Area
        input_frame = S7Frame(center_panel, height=40)
        input_frame.pack(fill="x", pady=4)

        self.msg_entry = tk.Entry(
            input_frame,
            font=S7Font.monaco(),
            bg=c_WHITE,
            fg=c_BLACK,
            insertbackground=c_BLACK,
            bd=1,
            relief="sunken"
        )
        self.msg_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.msg_entry.bind("<Return>", self.send_message)

        send_btn = S7Button(
            input_frame,
            text="Send",
            command=self.send_message,
            width=60,
            default=True
        )
        send_btn.pack(side="right")

        # Right Panel: Users
        right_panel = S7Frame(main_frame, width=120)
        right_panel.pack(side="right", fill="y", padx=2)

        tk.Label(
            right_panel,
            text="👥 Users",
            font=S7Font.chicago(),
            bg=c_PLATINUM,
            fg=c_BLACK
        ).pack(anchor="w")

        self.user_list = tk.Listbox(
            right_panel,
            bg=c_WHITE,
            fg=c_BLACK,
            font=S7Font.geneva(),
            bd=1,
            relief="sunken",
            selectbackground="black",
            selectforeground="white"
        )
        self.user_list.pack(fill="both", expand=True)
        self.refresh_user_list()

    def refresh_user_list(self):
        """Update the user list display."""
        self.user_list.delete(0, "end")
        self.user_list.insert("end", f"{self.user_nickname} [O]")
        for p in self.engine.personas:
            self.user_list.insert("end", f"{p['name']} [AI]")

    def change_room(self, event):
        """Handle room selection change."""
        selection = self.room_list.curselection()
        if not selection:
            return

        room_name = self.room_list.get(selection[0]).replace("# ", "")
        self.current_room = room_name
        self.header_label.config(text=f"# {room_name}")

        # Clear and reload history
        self.chat_text.config(state="normal")
        self.chat_text.delete(1.0, "end")

        history = self.engine.rooms[room_name]
        for msg in history:
            self.display_message(msg)

        self.chat_text.config(state="disabled")

        # Auto-scroll if enabled
        if self.settings.get("auto_scroll", True):
            self.chat_text.see("end")

    def display_message(self, msg):
        """
        Display a message in the chat area with @mention highlighting.

        Args:
            msg: Message dict with timestamp, user, text, etc.
        """
        self.chat_text.config(state="normal")

        # Show timestamps if enabled
        if self.settings.get("show_timestamps", True):
            self.chat_text.insert("end", f"[{msg['timestamp']}] ", "timestamp")

        # Insert Nickname
        tag = "self" if msg['user'] == self.user_nickname else "ai"
        self.chat_text.insert("end", f"<{msg['user']}> ", "nick")

        # Highlight @mentions
        text = msg['text']
        if "@" in text:
            # Find all @mentions
            parts = re.split(r'(@\w+)', text)
            for part in parts:
                if part.startswith("@"):
                    # Check if it's a valid persona mention
                    mentioned = False
                    for persona in self.engine.personas:
                        if part == f"@{persona['name']}":
                            self.chat_text.insert("end", part, "mention")
                            mentioned = True

                            # Play notification sound if user is mentioned
                            if part == f"@{self.user_nickname}":
                                if sounds.get_sound_player():
                                    sounds.play_notify()
                            break
                    if not mentioned:
                        self.chat_text.insert("end", part, tag)
                else:
                    self.chat_text.insert("end", part, tag)
        else:
            self.chat_text.insert("end", text, tag)

        self.chat_text.insert("end", "\n")

        # Auto-scroll if enabled
        if self.settings.get("auto_scroll", True):
            self.chat_text.see("end")

        self.chat_text.config(state="disabled")

    def show_system_message(self, text):
        """Display a system message (for IRC commands, etc.)."""
        self.chat_text.config(state="normal")

        self.chat_text.insert("end", "*** ", "system")
        self.chat_text.insert("end", text, "system")
        self.chat_text.insert("end", "\n")

        if self.settings.get("auto_scroll", True):
            self.chat_text.see("end")

        self.chat_text.config(state="disabled")

    def send_message(self, event=None):
        """Send user message to current room."""
        text = self.msg_entry.get().strip()
        if not text:
            return

        # Check if it's an IRC command
        if self.irc_commands.is_command(text):
            self.irc_commands.execute(text)
            self.msg_entry.delete(0, "end")
            return

        # Send normal message
        self.engine.user_post(self.current_room, text, self.user_nickname)
        self.msg_entry.delete(0, "end")

        # Mark tutorial message as sent
        self._tutorial_message_sent = True

    def open_control_panel(self):
        """Open the control panel window."""
        panel = ControlPanel(self.root, self.engine, self.settings)


if __name__ == "__main__":
    root = tk.Tk()
    app = IRCClient(root)
    root.mainloop()
