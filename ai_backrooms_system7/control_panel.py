"""
Control Panel - System Configuration Interface

4-tab interface for managing:
- Personas (create, edit, delete AI characters)
- Rooms (manage discussion channels)
- Settings (display, behavior, AI parameters)
- API Keys (Ollama connection, future cloud APIs)
"""

import tkinter as tk
from tkinter import messagebox
from system7_ui import S7Window, S7Button, S7Frame, S7InsetFrame, S7Font, c_PLATINUM, c_WHITE, c_BLACK


class ControlPanel(S7Window):
    """
    Main control panel window with tabbed interface.
    """

    def __init__(self, parent, engine, settings):
        """
        Initialize control panel.

        Args:
            parent: Parent window
            engine: BackroomsEngine instance
            settings: Settings dict
        """
        super().__init__(parent, "AI Backrooms Control Panel", width=700, height=550)
        self.engine = engine
        self.settings = settings
        self.current_tab = 0

        # Center on parent
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        self.geometry(f"+{parent_x + 50}+{parent_y + 50}")

        self.build_ui()

    def build_ui(self):
        """Build the control panel UI."""
        # Main container
        main_frame = S7Frame(self)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Tab buttons
        tab_frame = S7Frame(main_frame)
        tab_frame.pack(fill="x", pady=(5, 10))

        self.tab_buttons = []
        tab_names = ["Personas", "Rooms", "Settings", "API Keys"]

        for i, name in enumerate(tab_names):
            btn = S7Button(
                tab_frame,
                text=name,
                command=lambda idx=i: self.switch_tab(idx),
                width=100,
                default=(i == 0)
            )
            btn.pack(side="left", padx=2)
            self.tab_buttons.append(btn)

        # Content area
        self.content_frame = S7Frame(main_frame)
        self.content_frame.pack(fill="both", expand=True)

        # Build initial tab
        self.switch_tab(0)

        # Bottom buttons
        bottom_frame = S7Frame(main_frame)
        bottom_frame.pack(fill="x", pady=(10, 5))

        close_btn = S7Button(
            bottom_frame,
            text="Close",
            command=self.destroy,
            width=80
        )
        close_btn.pack(side="right", padx=5)

    def switch_tab(self, tab_index):
        """Switch to specified tab."""
        self.current_tab = tab_index

        # Update button appearances
        for i, btn in enumerate(self.tab_buttons):
            btn.is_default = (i == tab_index)
            btn.draw()

        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Build new content
        if tab_index == 0:
            self.build_personas_tab()
        elif tab_index == 1:
            self.build_rooms_tab()
        elif tab_index == 2:
            self.build_settings_tab()
        elif tab_index == 3:
            self.build_api_keys_tab()

    def build_personas_tab(self):
        """Build personas management tab."""
        # Header
        tk.Label(
            self.content_frame,
            text="📋 Active Personas",
            font=S7Font.chicago(11),
            bg=c_PLATINUM
        ).pack(anchor="w", pady=(5, 5))

        # Persona list
        list_frame = S7InsetFrame(self.content_frame)
        list_frame.pack(fill="both", expand=True, pady=5)

        self.persona_listbox = tk.Listbox(
            list_frame,
            bg=c_WHITE,
            fg=c_BLACK,
            font=S7Font.geneva(9),
            selectmode="single",
            selectbackground="black",
            selectforeground="white"
        )
        scrollbar = tk.Scrollbar(list_frame, command=self.persona_listbox.yview)
        self.persona_listbox.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.persona_listbox.pack(side="left", fill="both", expand=True)

        # Populate list
        self.refresh_persona_list()

        # Buttons
        btn_frame = S7Frame(self.content_frame)
        btn_frame.pack(fill="x", pady=5)

        S7Button(btn_frame, text="New Persona...", command=self.new_persona, width=110).pack(side="left", padx=2)
        S7Button(btn_frame, text="Edit Selected", command=self.edit_persona, width=110).pack(side="left", padx=2)
        S7Button(btn_frame, text="Delete", command=self.delete_persona, width=80).pack(side="left", padx=2)

        # Details frame
        tk.Label(
            self.content_frame,
            text="📝 Selected Persona Details",
            font=S7Font.chicago(10),
            bg=c_PLATINUM
        ).pack(anchor="w", pady=(10, 5))

        details_frame = S7InsetFrame(self.content_frame, height=120)
        details_frame.pack(fill="x", pady=5)
        details_frame.pack_propagate(False)

        self.details_text = tk.Text(
            details_frame,
            bg=c_WHITE,
            fg=c_BLACK,
            font=S7Font.geneva(9),
            state="disabled",
            wrap="word",
            insertbackground=c_BLACK
        )
        self.details_text.pack(fill="both", expand=True)

        # Bind selection
        self.persona_listbox.bind('<<ListboxSelect>>', self.on_persona_select)

    def refresh_persona_list(self):
        """Refresh the persona listbox."""
        self.persona_listbox.delete(0, "end")
        for p in self.engine.personas:
            enabled_icon = "☑️" if p.get("enabled", True) else "☐"
            self.persona_listbox.insert("end", f"{enabled_icon} {p['name']} - {p['role']}")

    def on_persona_select(self, event):
        """Handle persona selection."""
        selection = self.persona_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        persona = self.engine.personas[idx]

        # Update details
        self.details_text.config(state="normal")
        self.details_text.delete(1.0, "end")
        self.details_text.insert("end", f"Name: {persona['name']}\n")
        self.details_text.insert("end", f"Role: {persona['role']}\n")
        self.details_text.insert("end", f"Model: {persona.get('model', 'llama3')}\n")
        self.details_text.insert("end", f"\nPrompt:\n{persona['prompt']}")
        self.details_text.config(state="disabled")

    def new_persona(self):
        """Open dialog to create new persona."""
        # TODO: Implement full persona editor dialog
        messagebox.showinfo("New Persona", "Persona editor coming soon!\n\nFor now, edit engine.py DEFAULT_PERSONAS")

    def edit_persona(self):
        """Edit selected persona."""
        selection = self.persona_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a persona to edit")
            return

        messagebox.showinfo("Edit Persona", "Persona editor coming soon!\n\nFor now, edit engine.py DEFAULT_PERSONAS")

    def delete_persona(self):
        """Delete selected persona."""
        selection = self.persona_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a persona to delete")
            return

        idx = selection[0]
        persona = self.engine.personas[idx]

        if messagebox.askyesno("Confirm Delete", f"Delete persona '{persona['name']}'?"):
            self.engine.personas.pop(idx)
            self.refresh_persona_list()

    def build_rooms_tab(self):
        """Build rooms management tab."""
        tk.Label(
            self.content_frame,
            text="📚 Available Rooms",
            font=S7Font.chicago(11),
            bg=c_PLATINUM
        ).pack(anchor="w", pady=(5, 5))

        # Room list
        list_frame = S7InsetFrame(self.content_frame)
        list_frame.pack(fill="both", expand=True, pady=5)

        room_listbox = tk.Listbox(
            list_frame,
            bg=c_WHITE,
            fg=c_BLACK,
            font=S7Font.geneva(9),
            selectbackground="black",
            selectforeground="white"
        )
        scrollbar = tk.Scrollbar(list_frame, command=room_listbox.yview)
        room_listbox.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        room_listbox.pack(side="left", fill="both", expand=True)

        # Populate
        from engine import DEFAULT_ROOMS
        for room in DEFAULT_ROOMS:
            room_listbox.insert("end", f"# {room['name']} - {room['topic']}")

        # Info
        tk.Label(
            self.content_frame,
            text="💡 Room management features coming soon!",
            font=S7Font.geneva(9),
            bg=c_PLATINUM,
            fg=c_BLACK
        ).pack(pady=10)

    def build_settings_tab(self):
        """Build settings tab."""
        # Scrollable frame
        canvas = tk.Canvas(self.content_frame, bg=c_PLATINUM, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.content_frame, command=canvas.yview)
        scrollable_frame = S7Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Display Settings
        tk.Label(
            scrollable_frame,
            text="🖥️ Display Settings",
            font=S7Font.chicago(11),
            bg=c_PLATINUM
        ).pack(anchor="w", pady=(5, 5))

        self.show_timestamps_var = tk.BooleanVar(value=self.settings.get("show_timestamps", True))
        tk.Checkbutton(
            scrollable_frame,
            text="Show timestamps",
            variable=self.show_timestamps_var,
            bg=c_PLATINUM,
            font=S7Font.geneva(9)
        ).pack(anchor="w", padx=20)

        self.show_join_part_var = tk.BooleanVar(value=self.settings.get("show_join_part", False))
        tk.Checkbutton(
            scrollable_frame,
            text="Show join/part messages",
            variable=self.show_join_part_var,
            bg=c_PLATINUM,
            font=S7Font.geneva(9)
        ).pack(anchor="w", padx=20)

        # Behavior Settings
        tk.Label(
            scrollable_frame,
            text="⚙️ Behavior Settings",
            font=S7Font.chicago(11),
            bg=c_PLATINUM
        ).pack(anchor="w", pady=(15, 5))

        self.auto_scroll_var = tk.BooleanVar(value=self.settings.get("auto_scroll", True))
        tk.Checkbutton(
            scrollable_frame,
            text="Auto-scroll to new messages",
            variable=self.auto_scroll_var,
            bg=c_PLATINUM,
            font=S7Font.geneva(9)
        ).pack(anchor="w", padx=20)

        self.notify_mention_var = tk.BooleanVar(value=self.settings.get("notify_on_mention", True))
        tk.Checkbutton(
            scrollable_frame,
            text="Notify on @mention",
            variable=self.notify_mention_var,
            bg=c_PLATINUM,
            font=S7Font.geneva(9)
        ).pack(anchor="w", padx=20)

        self.enable_sounds_var = tk.BooleanVar(value=self.settings.get("enable_sounds", False))
        tk.Checkbutton(
            scrollable_frame,
            text="Enable sound effects",
            variable=self.enable_sounds_var,
            bg=c_PLATINUM,
            font=S7Font.geneva(9)
        ).pack(anchor="w", padx=20)

        # Save button
        S7Button(
            scrollable_frame,
            text="Save Settings",
            command=self.save_settings,
            width=120,
            default=True
        ).pack(pady=20)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def save_settings(self):
        """Save settings changes."""
        self.settings["show_timestamps"] = self.show_timestamps_var.get()
        self.settings["show_join_part"] = self.show_join_part_var.get()
        self.settings["auto_scroll"] = self.auto_scroll_var.get()
        self.settings["notify_on_mention"] = self.notify_mention_var.get()
        self.settings["enable_sounds"] = self.enable_sounds_var.get()

        messagebox.showinfo("Settings Saved", "Your settings have been saved!")

    def build_api_keys_tab(self):
        """Build API keys tab."""
        tk.Label(
            self.content_frame,
            text="🔌 Ollama Connection",
            font=S7Font.chicago(11),
            bg=c_PLATINUM
        ).pack(anchor="w", pady=(5, 5))

        # URL field
        url_frame = S7Frame(self.content_frame)
        url_frame.pack(fill="x", pady=5, padx=10)

        tk.Label(
            url_frame,
            text="Server URL:",
            font=S7Font.geneva(9),
            bg=c_PLATINUM,
            width=12,
            anchor="w"
        ).pack(side="left")

        url_entry = tk.Entry(
            url_frame,
            font=S7Font.monaco(9),
            bg=c_WHITE,
            fg=c_BLACK,
            insertbackground=c_BLACK,
            width=40
        )
        url_entry.insert(0, self.engine.ollama.url)
        url_entry.pack(side="left", padx=5)

        # Test button
        S7Button(
            self.content_frame,
            text="Test Connection",
            command=lambda: self.test_ollama_connection(url_entry.get()),
            width=130
        ).pack(pady=10)

        # Status
        self.ollama_status_label = tk.Label(
            self.content_frame,
            text="● Status: Unknown",
            font=S7Font.geneva(9),
            bg=c_PLATINUM,
            anchor="w"
        )
        self.ollama_status_label.pack(fill="x", padx=10, pady=5)

        # Available models
        tk.Label(
            self.content_frame,
            text="Available models:",
            font=S7Font.geneva(9),
            bg=c_PLATINUM,
            anchor="w"
        ).pack(fill="x", padx=10, pady=(10, 5))

        models_frame = S7InsetFrame(self.content_frame, height=150)
        models_frame.pack(fill="x", padx=10, pady=5)

        self.models_text = tk.Text(
            models_frame,
            bg=c_WHITE,
            fg=c_BLACK,
            font=S7Font.monaco(9),
            state="disabled",
            insertbackground=c_BLACK
        )
        self.models_text.pack(fill="both", expand=True)

        # Future APIs
        tk.Label(
            self.content_frame,
            text="☁️ Cloud AI Integration (Coming Soon)",
            font=S7Font.chicago(10),
            bg=c_PLATINUM
        ).pack(anchor="w", pady=(20, 5), padx=10)

        tk.Label(
            self.content_frame,
            text="Future support for: OpenAI, Anthropic, Google AI",
            font=S7Font.geneva(9),
            bg=c_PLATINUM,
            fg="#666666"
        ).pack(anchor="w", padx=20)

    def test_ollama_connection(self, url):
        """Test Ollama connection."""
        import urllib.request
        import json

        try:
            req = urllib.request.Request(f"{url}/api/tags")
            with urllib.request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read().decode('utf-8'))
                models = result.get('models', [])

                self.ollama_status_label.config(
                    text=f"● Status: Connected ({len(models)} models)",
                    fg="darkgreen"
                )

                # Update models list
                self.models_text.config(state="normal")
                self.models_text.delete(1.0, "end")
                for model in models:
                    self.models_text.insert("end", f"• {model['name']}\n")
                self.models_text.config(state="disabled")

                messagebox.showinfo("Connection Success", f"Connected!\n\nFound {len(models)} models")

        except Exception as e:
            self.ollama_status_label.config(
                text=f"● Status: Disconnected",
                fg="darkred"
            )
            messagebox.showerror("Connection Failed", f"Could not connect to Ollama:\n\n{str(e)}")
