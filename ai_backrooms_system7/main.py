#!/usr/bin/env python3
"""
AI Backrooms - System 7 IRC Edition
A retro chat client where AI personas discuss topics 24/7

Main application that integrates the UI and conversation engine.
Handles the thread-safe message queue and room switching.

Usage:
    python3 main.py

Prerequisites:
    - Python 3.8+
    - (Optional) Ollama running locally with a model pulled

Memory footprint: ~35MB
"""

import tkinter as tk
import queue
from system7_ui import S7Window, S7Button, S7Frame, S7InsetFrame, S7Font, c_PLATINUM, c_WHITE, c_BLACK
from engine import BackroomsEngine, DEFAULT_ROOMS


class IRCClient:
    """
    Main IRC client application.

    Integrates:
    - System 7 UI components
    - Background conversation engine
    - Thread-safe message queue
    - Room management
    """

    def __init__(self, root):
        self.root = root
        self.root.title("AI Backrooms")
        self.root.geometry("800x600")
        self.root.configure(bg=c_PLATINUM)

        # Message Queue (Thread -> GUI)
        # This is critical: Tkinter is single-threaded, so background
        # threads must communicate via queue
        self.msg_queue = queue.Queue()

        # Engine
        self.engine = BackroomsEngine(self.on_engine_message)
        self.current_room = "general"

        self.setup_ui()
        self.show_tutorial()

        # Start Engine
        self.engine.start()

        # Start Queue Poller
        # This runs every 100ms and processes messages from background threads
        self.root.after(100, self.process_queue)

    def on_engine_message(self, msg):
        """
        Callback from engine when new message is generated.

        This runs in a background thread, so we safely queue it
        for the main thread to process.
        """
        self.msg_queue.put(msg)

    def process_queue(self):
        """
        Poll the message queue and update UI.

        This runs in the main Tkinter thread.
        Processes all pending messages, then reschedules itself.
        """
        try:
            while True:
                msg = self.msg_queue.get_nowait()
                if msg['room'] == self.current_room:
                    self.display_message(msg)

                # Update room list bold status if needed (omitted for brevity)
        except queue.Empty:
            pass
        self.root.after(100, self.process_queue)

    def setup_ui(self):
        """Build the main IRC client interface."""

        # --- Menu Bar (Fake) ---
        menubar = tk.Frame(self.root, bg=c_WHITE, height=20, bd=1, relief="raised")
        menubar.pack(fill="x", side="top")
        tk.Label(
            menubar,
            text=" File Edit View Rooms Personas Help",
            bg=c_WHITE,
            font=S7Font.chicago(10)
        ).pack(side="left", padx=10)

        # --- Main Layout ---
        main_frame = S7Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Left Panel: Rooms
        left_panel = S7Frame(main_frame, width=150)
        left_panel.pack(side="left", fill="y", padx=2)

        tk.Label(left_panel, text="📡 Servers", font=S7Font.chicago(), bg=c_PLATINUM).pack(anchor="w")
        tk.Label(
            left_panel,
            text="⚡ Local Ollama",
            font=S7Font.geneva(),
            bg=c_PLATINUM,
            fg="darkgreen"
        ).pack(anchor="w", padx=10)

        tk.Label(left_panel, text="📚 Rooms", font=S7Font.chicago(), bg=c_PLATINUM).pack(anchor="w", pady=(10, 0))

        self.room_list = tk.Listbox(
            left_panel,
            bg=c_WHITE,
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
            bg=c_PLATINUM
        )
        self.header_label.pack(fill="x", pady=2)

        # Chat Area
        chat_frame = S7InsetFrame(center_panel)
        chat_frame.pack(fill="both", expand=True)

        self.chat_text = tk.Text(
            chat_frame,
            bg=c_WHITE,
            font=S7Font.monaco(),
            state="disabled",
            wrap="word",
            bd=0
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

        # Input Area
        input_frame = S7Frame(center_panel, height=40)
        input_frame.pack(fill="x", pady=4)

        self.msg_entry = tk.Entry(input_frame, font=S7Font.monaco(), bd=1, relief="sunken")
        self.msg_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.msg_entry.bind("<Return>", self.send_message)

        send_btn = S7Button(input_frame, text="Send", command=self.send_message, width=60, default=True)
        send_btn.pack(side="right")

        # Right Panel: Users
        right_panel = S7Frame(main_frame, width=120)
        right_panel.pack(side="right", fill="y", padx=2)
        tk.Label(right_panel, text="👥 Users", font=S7Font.chicago(), bg=c_PLATINUM).pack(anchor="w")

        self.user_list = tk.Listbox(right_panel, bg=c_WHITE, font=S7Font.geneva(), bd=1, relief="sunken")
        self.user_list.pack(fill="both", expand=True)
        self.refresh_user_list()

    def refresh_user_list(self):
        """Update the user list display."""
        self.user_list.delete(0, "end")
        self.user_list.insert("end", "You [O]")
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

    def display_message(self, msg):
        """
        Display a message in the chat area.

        Args:
            msg: Message dict with timestamp, user, text, etc.
        """
        self.chat_text.config(state="normal")

        # Insert Timestamp
        self.chat_text.insert("end", f"[{msg['timestamp']}] ", "timestamp")

        # Insert Nickname
        tag = "self" if msg['user'] == "You" else "ai"
        self.chat_text.insert("end", f"<{msg['user']}> ", "nick")

        # Insert Message
        self.chat_text.insert("end", f"{msg['text']}\n", tag)

        self.chat_text.see("end")
        self.chat_text.config(state="disabled")

    def send_message(self, event=None):
        """Send user message to current room."""
        text = self.msg_entry.get().strip()
        if not text:
            return

        self.engine.user_post(self.current_room, text)
        self.msg_entry.delete(0, "end")

    def show_tutorial(self):
        """
        Show tutorial on first launch.

        TODO: Implement full tutorial dialog sequence.
        For now, this is a placeholder.
        """
        # Simple modal dialog simulation
        # In full version, would use S7Window with tutorial steps
        pass


if __name__ == "__main__":
    root = tk.Tk()
    app = IRCClient(root)
    root.mainloop()
