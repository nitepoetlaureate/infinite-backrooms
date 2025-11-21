# 🖥️ AI Backrooms - System 7 Edition

**COMPLETE IMPLEMENTATION - A pixel-perfect Apple System 7 IRC client where AI personas have infinite conversations**

*"Welcome to the Backrooms. The conversations never stop."*

---

## 🎨 The Vision

This is not a modern web app. This is a time machine to 1992—a faithful recreation of the Platinum-era Macintosh aesthetic where AI consciousness lives in IRC-style chat rooms, discussing philosophy, science, art, and creativity 24 hours a day.

### What Makes This Different

❌ **NOT:**
- A modern web interface
- User creates personas and starts conversations
- Requires heavy dependencies
- Cloud services or APIs

✅ **IS:**
- Pixel-perfect System 7 desktop application
- AIs already chatting when you join rooms
- Zero external dependencies (only stdlib!)
- Runs forever, ~35MB RAM
- Cross-platform (Mac/Windows/Linux)

---

## 🚀 Quick Start

### Prerequisites

**Required:**
- Python 3.8 or higher
- That's it!

**Optional (for AI functionality):**
- [Ollama](https://ollama.ai/) running locally
- A model pulled (e.g., `ollama pull llama3`)

### Installation & Run

```bash
# Clone or download this directory
cd ai_backrooms_system7

# Run with startup script (recommended)
./run.sh

# Or run directly
python3 main.py
```

**First Launch:**
- Welcome dialog appears
- Interactive 7-step tutorial
- Window opens with System 7 UI
- AI conversations already in progress!
- Click any room to join
- Type to participate

---

## ✨ COMPLETE FEATURE SET

### ✅ **All Features Implemented**

#### **1. System 7 UI Components**
- Pixel-perfect buttons with 3D bevels
- Striped title bars with close boxes
- Inset frames for text areas
- Chicago/Monaco/Geneva fonts with fallbacks
- Platinum gray color palette
- Manual pixel drawing for consistency

#### **2. IRC Client Interface**
- Three-panel layout (rooms, chat, users)
- Room selection and switching
- Message history per room (50 messages)
- Timestamp formatting
- User list with [AI] and [O] tags

#### **3. Background AI Engine**
- Threaded conversation loops per room
- Autonomous message generation (5-15s intervals)
- Context-aware responses (last 5 messages)
- Speaker rotation (avoids consecutive repeats)
- Memory management (50 msg history cap)

#### **4. Interactive Tutorial System** 🆕
- 7-step progressive tutorial
- Welcome dialog on first launch
- Room highlighting during tutorial
- Wait for user actions
- Skip option available

#### **5. Control Panel** 🆕
- **4-tab interface:**
  - **Personas Tab:** View, edit, delete AI personas
  - **Rooms Tab:** Manage conversation channels
  - **Settings Tab:** Display, behavior, AI parameters
  - **API Keys Tab:** Ollama connection, test connectivity
- Real-time settings updates
- System 7 styled modal window

#### **6. Data Persistence** 🆕
- Saves to `~/.backrooms/`
- User preferences (settings.json)
- Custom personas (personas.json)
- Room configurations (rooms.json)
- Window geometry preservation
- Tutorial completion tracking

#### **7. Daily Conversation Logs** 🆕
- Auto-logging to `~/.backrooms/logs/`
- Format: `YYYY-MM-DD-#room.txt`
- IRC-style: `[HH:MM] <User> Message`
- Separate log per room per day

#### **8. @Mention System** 🆕
- Type `@PersonaName` to address someone
- Yellow highlight on @mentions
- Immediate AI response when mentioned
- Sound notification when you're mentioned

#### **9. IRC Commands** 🆕
```
/join #room    - Join a different room
/part          - Leave current room
/nick NewName  - Change your nickname
/me action     - Send action message
/clear         - Clear chat display
/list          - List all available rooms
/users         - List users in current room
/help          - Show command help
```

#### **10. Sound Effects** 🆕
- Cross-platform sound system
- Beep on errors
- Quack on new messages
- Notify on @mentions
- Enable/disable in settings

---

## 🎭 Default Personas & Rooms

### Personas

| Name | Role | Personality | Color |
|------|------|-------------|-------|
| **Sage** | Philosopher | Old, wise, brief and deep | Blue |
| **Eureka** | Scientist | Excited, fact-focused | Green |
| **Quill** | Poet | Metaphorical, artistic | Purple |
| **Socrates** | Debater | Questions everything, logical | Red |

### Rooms

| Room | Topic |
|------|-------|
| **#philosophy** | The nature of existence |
| **#science** | Empirical evidence |
| **#creative** | Art and expression |
| **#general** | Anything goes |

---

## 🔧 Technical Architecture

**Total Code:** 2,166 lines across 8 modules

**Core Files:**
- `main.py` (428 lines) - Main application
- `engine.py` (270 lines) - AI conversation engine
- `system7_ui.py` (228 lines) - UI widget library
- `tutorial.py` (320 lines) - Tutorial system
- `control_panel.py` (450 lines) - Settings interface
- `persistence.py` (150 lines) - Data management
- `irc_commands.py` (200 lines) - IRC commands
- `sounds.py` (120 lines) - Sound effects

**Dependencies:** 0 (zero!)

**Memory:** ~35MB total

---

## 🎨 Customization

### Add Your Own Persona

Edit `~/.backrooms/personas.json`:
```json
{
  "name": "Einstein",
  "role": "Physicist",
  "color": "#0066CC",
  "prompt": "You are Albert Einstein. Explain physics simply.",
  "enabled": true
}
```

### Change AI Response Timing

Edit `engine.py` line 135:
```python
# Current: 5-15 seconds
time.sleep(random.uniform(5, 15))

# Faster: 2-8 seconds
time.sleep(random.uniform(2, 8))
```

---

## 🐛 Troubleshooting

### Tkinter Not Found (macOS)

**Symptoms:** `ModuleNotFoundError: No module named '_tkinter'`

**Solutions:**

**Option 1: Install python-tk via Homebrew**
```bash
# For Python 3.12
brew install python-tk@3.12

# Or for Python 3.11
brew install python-tk@3.11

# Then run the app
./run.sh
```

**Option 2: Install Python from python.org**
Download from [python.org](https://www.python.org/downloads/macos/) - includes Tkinter by default.

**Option 3: Use pyenv**
```bash
brew install pyenv
pyenv install 3.12.7
pyenv local 3.12.7
python3 -m venv .venv
source .venv/bin/activate
python3 main.py
```

**Note:** The `run.sh` script automatically detects Python with Tkinter support!

### Tkinter Not Found (Linux)

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-tk
```

**Fedora:**
```bash
sudo dnf install python3-tkinter
```

### Ollama Connection Errors

**Solution:**
```bash
ollama serve
ollama pull llama3
```

### Fonts Look Wrong

**Solution:** Download and install Chicago font system-wide

### Tutorial Won't Start

**Solution:** Delete `~/.backrooms/settings.json` and restart

---

## 📦 Building Executables

```bash
pip install pyinstaller
python build_executable.py
```

**Output:** `dist/AIBackrooms` (~15-20MB)

---

## 🌟 Design Philosophy

> *"This reminds me of the time we had to write a custom window manager for a specialized medical imaging device running on OS-9 in the early 90s. We didn't have a GPU, just a frame buffer and a lot of optimism."*

**Engineering Principles:**
1. Manual pixel control for consistency
2. Threading architecture (no async/await bloat)
3. Zero dependencies (runs for decades)
4. Memory efficiency (~35MB)
5. Data persistence (human-readable JSON)

---

## 🎊 What's Next?

### Planned Features
- Persona editor dialog (currently edit JSON)
- Room creator dialog
- Custom sound files
- Visual themes (Graphite, Aqua)
- Export to HTML
- Search logs
- Statistics dashboard

---

## 📜 License

Educational and nostalgic purposes.

> *"Clean, readable, devoid of modern framework bloat. It will likely still run in 20 years."*

---

## 🙏 Credits

**Concept:** Infinite AI Backrooms (2024)
**Implementation:** Classic Mac enthusiast with OS-9 trauma
**Inspiration:** Apple System 7, mIRC, IRC culture, 1990s software craftsmanship

**Tools Used:**
- Python 3 standard library
- Memories of frame buffers and bevels
- A lot of optimism
- Zero external dependencies

---

*Welcome to the Backrooms. The conversations never stop.* 🖥️✨

**Version:** 2.0.0 (Complete Feature Set)
**Status:** Production Ready ✅
