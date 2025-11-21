"""
IRC Command Parser

Handles classic IRC commands:
- /join #room
- /part
- /nick NewName
- /me does something
- /clear
- /help
"""


class IRCCommandHandler:
    """
    Parses and executes IRC-style commands.
    """

    def __init__(self, app_ref):
        """
        Initialize command handler.

        Args:
            app_ref: Reference to main IRCClient
        """
        self.app = app_ref

        # Command registry
        self.commands = {
            "join": self.cmd_join,
            "part": self.cmd_part,
            "nick": self.cmd_nick,
            "me": self.cmd_me,
            "clear": self.cmd_clear,
            "help": self.cmd_help,
            "list": self.cmd_list,
            "users": self.cmd_users,
        }

    def is_command(self, text):
        """
        Check if text is a command.

        Args:
            text: Input text

        Returns:
            bool: True if starts with /
        """
        return text.strip().startswith("/")

    def execute(self, text):
        """
        Execute IRC command.

        Args:
            text: Command string (e.g., "/join #philosophy")

        Returns:
            bool: True if command was executed, False if invalid
        """
        if not self.is_command(text):
            return False

        # Parse command
        parts = text.strip()[1:].split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        # Execute
        if cmd in self.commands:
            try:
                self.commands[cmd](args)
                return True
            except Exception as e:
                self.app.show_system_message(f"Error executing /{cmd}: {str(e)}")
                return True
        else:
            self.app.show_system_message(f"Unknown command: /{cmd}. Type /help for commands.")
            return True

    def cmd_join(self, args):
        """
        Join a room.

        Usage: /join #roomname
        """
        if not args or not args.startswith("#"):
            self.app.show_system_message("Usage: /join #roomname")
            return

        room_name = args[1:].strip()  # Remove #

        # Check if room exists
        from engine import DEFAULT_ROOMS
        room_names = [r['name'] for r in DEFAULT_ROOMS]

        if room_name not in room_names:
            self.app.show_system_message(f"Room #{room_name} not found. Available: {', '.join(f'#{r}' for r in room_names)}")
            return

        # Switch to room
        try:
            # Find index in listbox
            for i in range(self.app.room_list.size()):
                if room_name in self.app.room_list.get(i):
                    self.app.room_list.selection_clear(0, "end")
                    self.app.room_list.selection_set(i)
                    self.app.room_list.see(i)
                    self.app.change_room(None)
                    self.app.show_system_message(f"Joined #{room_name}")
                    break
        except Exception as e:
            self.app.show_system_message(f"Error joining room: {e}")

    def cmd_part(self, args):
        """
        Leave current room.

        Usage: /part
        """
        current = self.app.current_room
        self.app.show_system_message(f"You have left #{current} (to rejoin: /join #{current})")

    def cmd_nick(self, args):
        """
        Change nickname.

        Usage: /nick NewName
        """
        if not args.strip():
            self.app.show_system_message("Usage: /nick YourNewName")
            return

        new_nick = args.strip()

        # Update nickname (stored in app)
        old_nick = getattr(self.app, 'user_nickname', 'You')
        self.app.user_nickname = new_nick

        self.app.show_system_message(f"You are now known as {new_nick} (was: {old_nick})")

    def cmd_me(self, args):
        """
        Send action message.

        Usage: /me does something
        """
        if not args.strip():
            return

        # Send as action
        action_text = f"* {getattr(self.app, 'user_nickname', 'You')} {args.strip()}"

        # Post to room
        self.app.engine.user_post(self.app.current_room, action_text)

    def cmd_clear(self, args):
        """
        Clear chat display.

        Usage: /clear
        """
        self.app.chat_text.config(state="normal")
        self.app.chat_text.delete(1.0, "end")
        self.app.chat_text.config(state="disabled")

        self.app.show_system_message("Chat cleared (history preserved in logs)")

    def cmd_help(self, args):
        """
        Show available commands.

        Usage: /help
        """
        help_text = """Available IRC commands:

/join #room   - Join a room
/part         - Leave current room
/nick Name    - Change your nickname
/me action    - Send action message
/clear        - Clear chat display
/list         - List all rooms
/users        - List users in current room
/help         - Show this help

Tip: Use @PersonaName to mention someone!"""

        self.app.show_system_message(help_text)

    def cmd_list(self, args):
        """
        List all available rooms.

        Usage: /list
        """
        from engine import DEFAULT_ROOMS

        room_list = "Available rooms:\n"
        for room in DEFAULT_ROOMS:
            room_list += f"\n  #{room['name']} - {room['topic']}"

        self.app.show_system_message(room_list)

    def cmd_users(self, args):
        """
        List users in current room.

        Usage: /users
        """
        personas = self.app.engine.personas
        user_list = f"Users in #{self.app.current_room}:\n"
        user_list += f"\n  {getattr(self.app, 'user_nickname', 'You')} [Human]"

        for p in personas:
            user_list += f"\n  {p['name']} [AI - {p['role']}]"

        self.app.show_system_message(user_list)
