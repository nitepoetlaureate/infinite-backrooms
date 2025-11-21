"""
Data Persistence Layer

Handles saving and loading:
- User settings
- Custom personas
- Room configurations
- Conversation logs

Uses ~/.backrooms/ directory for all data.
"""

import os
import json
from datetime import datetime
from pathlib import Path


class DataManager:
    """
    Manages persistent data storage.

    All data stored in: ~/.backrooms/
    - settings.json
    - personas.json
    - rooms.json
    - logs/YYYY-MM-DD-#room.txt
    """

    def __init__(self):
        self.data_dir = Path.home() / ".backrooms"
        self.logs_dir = self.data_dir / "logs"

        # Ensure directories exist
        self.data_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

    def load_settings(self):
        """
        Load user settings.

        Returns:
            dict: Settings dictionary
        """
        settings_file = self.data_dir / "settings.json"

        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    return json.load(f)
            except:
                pass

        # Default settings
        return {
            "show_timestamps": True,
            "show_join_part": False,
            "auto_scroll": True,
            "notify_on_mention": True,
            "enable_sounds": False,
            "theme": "platinum",
            "font_size": 9,
            "window_geometry": "800x600",
            "tutorial_completed": False,
            "ollama_url": "http://localhost:11434"
        }

    def save_settings(self, settings):
        """
        Save user settings.

        Args:
            settings: Settings dict to save
        """
        settings_file = self.data_dir / "settings.json"

        try:
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def load_personas(self):
        """
        Load persona definitions.

        Returns:
            list: List of persona dicts, or None if not found
        """
        personas_file = self.data_dir / "personas.json"

        if personas_file.exists():
            try:
                with open(personas_file, 'r') as f:
                    return json.load(f)
            except:
                pass

        return None  # Use defaults from engine.py

    def save_personas(self, personas):
        """
        Save persona definitions.

        Args:
            personas: List of persona dicts
        """
        personas_file = self.data_dir / "personas.json"

        try:
            with open(personas_file, 'w') as f:
                json.dump(personas, f, indent=2)
        except Exception as e:
            print(f"Error saving personas: {e}")

    def load_rooms(self):
        """
        Load room definitions.

        Returns:
            list: List of room dicts, or None if not found
        """
        rooms_file = self.data_dir / "rooms.json"

        if rooms_file.exists():
            try:
                with open(rooms_file, 'r') as f:
                    return json.load(f)
            except:
                pass

        return None  # Use defaults from engine.py

    def save_rooms(self, rooms):
        """
        Save room definitions.

        Args:
            rooms: List of room dicts
        """
        rooms_file = self.data_dir / "rooms.json"

        try:
            with open(rooms_file, 'w') as f:
                json.dump(rooms, f, indent=2)
        except Exception as e:
            print(f"Error saving rooms: {e}")

    def log_message(self, room_name, msg):
        """
        Log a message to daily room log.

        Args:
            room_name: Name of the room
            msg: Message dict with timestamp, user, text
        """
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.logs_dir / f"{today}-{room_name}.txt"

        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{msg['timestamp']}] <{msg['user']}> {msg['text']}\n")
        except Exception as e:
            print(f"Error logging message: {e}")

    def get_recent_logs(self, days=7):
        """
        Get list of recent log files.

        Args:
            days: Number of days to look back

        Returns:
            list: List of Path objects for log files
        """
        log_files = sorted(self.logs_dir.glob("*.txt"), reverse=True)
        return log_files[:days * 10]  # Assume max 10 rooms per day

    def export_conversation(self, room_name, messages):
        """
        Export conversation to JSON.

        Args:
            room_name: Room name
            messages: List of message dicts

        Returns:
            str: JSON export filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file = self.data_dir / f"export_{room_name}_{timestamp}.json"

        try:
            export_data = {
                "room": room_name,
                "exported_at": datetime.now().isoformat(),
                "message_count": len(messages),
                "messages": messages
            }

            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2)

            return str(export_file)
        except Exception as e:
            print(f"Error exporting conversation: {e}")
            return None
