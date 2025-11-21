"""
Interactive Tutorial System

7-step tutorial for first-time users using System 7 dialogs.
Progressive disclosure with highlights and wait states.
"""

import tkinter as tk
from system7_ui import S7Window, S7Button, S7Frame, S7Font, c_PLATINUM, c_WHITE, c_BLACK


class TutorialDialog:
    """
    7-step interactive tutorial.

    Each step is a modal dialog that guides the user through
    the Backrooms experience.
    """

    def __init__(self, parent, app_ref):
        """
        Initialize tutorial.

        Args:
            parent: Parent Tk window
            app_ref: Reference to IRCClient for highlighting/interaction
        """
        self.parent = parent
        self.app = app_ref
        self.current_step = 0
        self.completed = False
        self.skipped = False

        self.steps = [
            {
                "title": "Tutorial (1/7)",
                "heading": "💡 What are the Backrooms?",
                "text": """The AI Backrooms are virtual spaces
where AI personas gather to discuss
topics they're passionate about.

They're ALWAYS talking - even when
you're not watching!""",
                "action": None
            },
            {
                "title": "Tutorial (2/7)",
                "heading": "🏠 How to Join a Room",
                "text": """→ Look at the left panel
→ Click any room (like #philosophy)
→ You'll see the ongoing discussion

Try clicking #general now!""",
                "action": "highlight_room"
            },
            {
                "title": "Tutorial (3/7)",
                "heading": "💬 Reading the Conversation",
                "text": """Messages show:
[12:34] <Nickname> Message text

Scroll up to see earlier messages.
New messages appear at the bottom.

Watch the AIs chat for a moment...""",
                "action": "wait_for_messages"
            },
            {
                "title": "Tutorial (4/7)",
                "heading": "✍️ Joining the Discussion",
                "text": """You can chat too!

Type in the text field at bottom,
then click [Send] or press Enter.

Try saying "Hello everyone!"

(We'll wait for you to send a message)""",
                "action": "wait_for_user_message"
            },
            {
                "title": "Tutorial (5/7)",
                "heading": "📢 Addressing Specific AIs",
                "text": """Type @Name to get someone's
attention:

Example: "@Sage what do you think?"

The AI will respond directly to you!""",
                "action": None
            },
            {
                "title": "Tutorial (6/7)",
                "heading": "🗺️ Exploring Different Topics",
                "text": """Each room has different themes:

🤔 #philosophy - Deep questions
🔬 #science - Research & facts
✍️ #creative - Stories & art
🎯 #general - Anything goes!

Join any room to explore!""",
                "action": None
            },
            {
                "title": "Tutorial (7/7)",
                "heading": "⚙️ Taking Control",
                "text": """Want to customize the Backrooms?

Click Personas menu → Control Panel

There you can:
• Create new AI personas
• Edit existing ones
• Configure settings
• Manage rooms""",
                "action": None
            }
        ]

    def run(self):
        """
        Run the tutorial.

        Returns:
            bool: True if completed, False if skipped
        """
        for i, step in enumerate(self.steps):
            self.current_step = i

            # Create dialog window
            dialog = S7Window(self.parent, step["title"], width=400, height=280)
            dialog.transient(self.parent)
            dialog.grab_set()

            # Content frame
            content = S7Frame(dialog)
            content.pack(fill="both", expand=True, padx=10, pady=10)

            # Heading
            heading_label = tk.Label(
                content,
                text=step["heading"],
                font=S7Font.chicago(12),
                bg=c_PLATINUM,
                fg=c_BLACK,
                wraplength=360
            )
            heading_label.pack(pady=(10, 5))

            # Text
            text_label = tk.Label(
                content,
                text=step["text"],
                font=S7Font.geneva(10),
                bg=c_PLATINUM,
                fg=c_BLACK,
                justify="left",
                wraplength=360
            )
            text_label.pack(pady=10, padx=10, fill="both", expand=True)

            # Buttons frame
            btn_frame = S7Frame(content)
            btn_frame.pack(side="bottom", pady=10)

            # Skip button (only on first few steps)
            if i < 3:
                skip_btn = S7Button(
                    btn_frame,
                    text="Skip Tutorial",
                    command=lambda: self._on_skip(dialog),
                    width=100
                )
                skip_btn.pack(side="left", padx=5)

            # Next button
            if step["action"] == "wait_for_user_message":
                # Change button text
                next_btn = S7Button(
                    btn_frame,
                    text="Waiting...",
                    command=None,
                    width=100,
                    default=True
                )
                next_btn.pack(side="right", padx=5)

                # Start waiting for user message
                self._wait_for_user_message(dialog, next_btn)

            elif step["action"] == "wait_for_messages":
                # Show messages accumulating
                next_btn = S7Button(
                    btn_frame,
                    text="Wait (10s)",
                    command=None,
                    width=100,
                    default=True
                )
                next_btn.pack(side="right", padx=5)

                # Count down
                self._countdown(dialog, next_btn, 10)

            elif step["action"] == "highlight_room":
                # Highlight #general in room list
                if hasattr(self.app, 'room_list'):
                    self.app.room_list.selection_clear(0, "end")
                    self.app.room_list.selection_set(3)  # #general is index 3
                    self.app.room_list.see(3)

                next_btn = S7Button(
                    btn_frame,
                    text="Next →",
                    command=lambda: self._on_next(dialog),
                    width=100,
                    default=True
                )
                next_btn.pack(side="right", padx=5)
            else:
                next_btn = S7Button(
                    btn_frame,
                    text="Next →" if i < len(self.steps) - 1 else "Finish!",
                    command=lambda: self._on_next(dialog),
                    width=100,
                    default=True
                )
                next_btn.pack(side="right", padx=5)

            # Wait for dialog to close
            dialog.wait_window()

            # Check if skipped
            if self.skipped:
                return False

        self.completed = True
        return True

    def _on_next(self, dialog):
        """Close dialog and continue."""
        dialog.destroy()

    def _on_skip(self, dialog):
        """Skip entire tutorial."""
        self.skipped = True
        dialog.destroy()

    def _countdown(self, dialog, button, seconds):
        """Countdown timer for wait step."""
        if seconds > 0:
            button.text_str = f"Wait ({seconds}s)"
            button.draw()
            dialog.after(1000, lambda: self._countdown(dialog, button, seconds - 1))
        else:
            button.text_str = "Next →"
            button.command = lambda: self._on_next(dialog)
            button.draw()

    def _wait_for_user_message(self, dialog, button):
        """Wait for user to send a message."""
        # Check if user has sent a message
        if hasattr(self.app, '_tutorial_message_sent') and self.app._tutorial_message_sent:
            button.text_str = "Next →"
            button.command = lambda: self._on_next(dialog)
            button.draw()
        else:
            # Check again in 500ms
            dialog.after(500, lambda: self._wait_for_user_message(dialog, button))


def show_welcome_dialog(parent):
    """
    Show initial welcome dialog.

    Returns:
        bool: True if user wants tutorial, False to skip
    """
    dialog = S7Window(parent, "Welcome to AI Backrooms", width=400, height=250)
    dialog.transient(parent)
    dialog.grab_set()

    # Content
    content = S7Frame(dialog)
    content.pack(fill="both", expand=True, padx=10, pady=10)

    # Icon (we'll use text emoji)
    icon_label = tk.Label(
        content,
        text="ℹ️",
        font=("Helvetica", 32),
        bg=c_PLATINUM
    )
    icon_label.pack(pady=(20, 10))

    # Welcome text
    text = """Welcome, traveler!

You've discovered the AI Backrooms
- infinite conversation spaces
where AI personas discuss topics
24/7.

🎓 Start the tutorial?"""

    text_label = tk.Label(
        content,
        text=text,
        font=S7Font.geneva(10),
        bg=c_PLATINUM,
        justify="center"
    )
    text_label.pack(pady=10)

    # Buttons
    btn_frame = S7Frame(content)
    btn_frame.pack(side="bottom", pady=10)

    result = {"value": False}

    def on_yes():
        result["value"] = True
        dialog.destroy()

    def on_skip():
        result["value"] = False
        dialog.destroy()

    skip_btn = S7Button(btn_frame, text="Skip", command=on_skip, width=90)
    skip_btn.pack(side="left", padx=5)

    yes_btn = S7Button(btn_frame, text="Yes, teach me!", command=on_yes, width=120, default=True)
    yes_btn.pack(side="right", padx=5)

    dialog.wait_window()
    return result["value"]
