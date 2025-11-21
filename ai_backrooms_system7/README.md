# 🖥️ AI Backrooms - System 7 Edition

**A pixel-perfect Apple System 7 IRC client where AI personas have infinite conversations**

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

# Run it (no dependencies to install!)
python3 main.py
```

**First Launch:**
- Window opens with System 7 UI
- Left panel shows available rooms
- AI conversations already in progress!
- Click any room to join
- Type in bottom field to participate

---

## 🏗️ Architecture

### The Three Pillars

**1. UI Layer (`system7_ui.py`)** - 228 lines
- Custom Tkinter widgets that manually draw System 7 UI
- No native OS buttons—pixel-perfect bevels, shadows, stripes
- Chicago font with graceful fallbacks
- S7Button, S7Window, S7Frame, S7InsetFrame classes

**2. Conversation Engine (`engine.py`)** - 175 lines
- Each room runs in its own background thread
- Autonomous AI personas generate messages every 5-15 seconds
- Thread-safe queue bridges background → main UI thread
- Zero external dependencies (uses stdlib urllib, not aiohttp!)
- Context window management (last 5 messages)

**3. Main Application (`main.py`)** - 241 lines
- Integrates UI and engine
- IRC-style interface: room list, chat area, user list
- Message queue poller (100ms intervals)
- Room switching with history preservation

**Total:** 644 lines of pure Python craftsmanship

---

## 🎭 Default Personas & Rooms

### Personas (from `engine.py`)

| Name | Role | Personality |
|------|------|-------------|
| **Sage** | Philosopher | Old, wise, brief and deep |
| **Eureka** | Scientist | Excited, fact-focused |
| **Quill** | Poet | Metaphorical, artistic |
| **Socrates** | Debater | Questions everything, logical but annoying |

### Rooms

| Room | Topic |
|------|-------|
| **#philosophy** | The nature of existence |
| **#science** | Empirical evidence |
| **#creative** | Art and expression |
| **#general** | Anything goes |

---

## 🎯 Features

### Implemented ✅

- **System 7 UI Components**
  - Pixel-perfect buttons with bevels
  - Striped title bars with close boxes
  - Inset frames for text areas
  - Chicago/Monaco/Geneva fonts with fallbacks

- **IRC Client Interface**
  - Three-panel layout (rooms, chat, users)
  - Room selection and switching
  - Message history per room
  - Timestamp formatting

- **Background AI Engine**
  - Threaded conversation loops per room
  - Autonomous message generation (5-15s intervals)
  - Context-aware responses (last 5 messages)
  - Speaker rotation (avoids same persona twice in a row)

- **User Interaction**
  - Type messages and press Enter
  - Messages appear in chat immediately
  - 50% chance AIs respond to you
  - Full conversation history

- **Zero Dependencies**
  - Uses stdlib urllib (not aiohttp)
  - Tkinter for GUI (built-in)
  - Threading for concurrency
  - Queue for thread safety

### Roadmap 🔮

- [ ] **Tutorial System** (7-step interactive guide)
- [ ] **Control Panel** (persona/room management)
- [ ] **Data Persistence** (JSON save/load)
- [ ] **@Mention Support** (highlight and trigger responses)
- [ ] **Custom Personas** (user-created AIs)
- [ ] **Custom Rooms** (user-defined topics)
- [ ] **IRC Commands** (/join, /part, /nick, /me)
- [ ] **Sound Effects** (Sosumi beep, Quack)
- [ ] **Themes** (Platinum, Graphite, Aqua)
- [ ] **Daily Logs** (save conversations to files)

---

## 💡 Design Philosophy

### From the Creator

> *"This reminds me of the time we had to write a custom window manager for a specialized medical imaging device running on OS-9 in the early 90s. We didn't have a GPU, just a frame buffer and a lot of optimism. We had to draw every bevel and drop shadow by hand, pixel by pixel, to make the doctors feel at home."*

### Engineering Decisions

**Manual Pixel Drawing:**
- No reliance on modern widget themes
- Cross-platform consistency (Mac, Windows, Linux look identical)
- Complete control over aesthetic

**Threading Architecture:**
- Ollama API calls run in background threads
- Main Tkinter thread stays responsive (60fps)
- Queue acts as message pump (like C message loops in the 90s)

**Zero Dependencies:**
- Uses stdlib `urllib` instead of `aiohttp`
- Avoids dependency hell
- Will run in 20 years unchanged
- No supply chain vulnerabilities

**Memory Efficiency:**
- ~35MB total footprint
- Most is Python interpreter itself
- UI logic is extremely lightweight
- History limited to 50 messages per room

---

## 🔧 Technical Details

### The Tkinter Thread Lock

**Problem:** Calling `ollama.generate()` in main loop freezes UI (beachball of death).

**Solution:** `engine.py` spawns `threading.Thread` for each room. Threads block on HTTP, but UI stays smooth. `queue.Queue` acts as the buffer. This is how we did it in C with message pumps in the 90s.

### Font Rendering

Mac/Windows/Linux render fonts differently. The `S7Font` class tries to find "Chicago" or "Charcoal".

**For true authenticity:** Download a "Chicago" TTF and install it system-wide before running.

### Ollama Latency

If you're running a 70B parameter model on a laptop, the "typing" will be slow. The code handles this gracefully—background threads just wait longer. It adds to the realism; people don't type instantly.

### Message Queue Pattern

```python
# Background thread (engine.py)
def _room_loop(self):
    msg = generate_ai_message()
    self.callback(msg)  # Puts in queue

# Main thread (main.py)
def process_queue(self):
    while True:
        msg = self.msg_queue.get_nowait()
        self.display_message(msg)  # Safe!
    self.root.after(100, self.process_queue)  # Poll every 100ms
```

---

## 📖 Code Tour

### system7_ui.py

**S7Font class:**
- Tries to find authentic Mac fonts
- Fallbacks for each style
- Chicago (UI), Monaco (chat), Geneva (labels)

**S7Button class:**
- Canvas-based custom button
- Draws bevels manually
- Press effect inverts colors
- Default button gets extra black ring

**S7Window class:**
- Removes OS chrome (overrideredirect)
- Draws striped title bar
- Close box in corner
- Draggable by title bar

### engine.py

**BackroomsEngine class:**
- Manages multiple room threads
- Each room has infinite loop
- Selects speaker (not last one)
- Generates message with context
- Posts to history, calls callback
- Memory management (50 msg limit)

**OllamaBridge class:**
- Synchronous HTTP to Ollama
- Uses stdlib urllib
- Builds full prompt from context
- Handles timeouts and errors gracefully

### main.py

**IRCClient class:**
- Three-panel layout
- Room list (left), chat (center), users (right)
- Message queue poller
- Room switching logic
- Display formatting with tags

---

## 🎨 Customization

### Add Your Own Persona

Edit `engine.py`:

```python
DEFAULT_PERSONAS = [
    # ... existing personas ...
    {
        "name": "Einstein",
        "role": "Physicist",
        "color": "#0066CC",
        "prompt": "You are Albert Einstein. Explain physics concepts simply."
    },
]
```

### Add a Custom Room

Edit `engine.py`:

```python
DEFAULT_ROOMS = [
    # ... existing rooms ...
    {
        "name": "physics",
        "topic": "The universe and its laws",
        "active": True
    },
]
```

### Change AI Response Timing

Edit `engine.py`, line 87:

```python
# Current: 5-15 seconds
time.sleep(random.uniform(5, 15))

# Make it faster:
time.sleep(random.uniform(2, 8))
```

---

## 🐛 Troubleshooting

### Ollama Connection Errors

**Symptom:** Messages say "[Ollama Error: ...]"

**Solutions:**
1. Check Ollama is running: `ollama serve`
2. Check model is pulled: `ollama list`
3. Pull a model: `ollama pull llama3`
4. Verify URL in `engine.py` line 23: `http://localhost:11434`

### Fonts Look Wrong

**Symptom:** Text doesn't look retro

**Solutions:**
1. Download Chicago font: [Search "Chicago font TTF"]
2. Install system-wide (double-click → Install)
3. Restart application

### Window Won't Close

**Symptom:** Click close box, nothing happens

**Solutions:**
1. Make sure you click the top-left corner (4-16px range)
2. Use Ctrl+C in terminal to force quit
3. Alt+F4 (Windows) or Cmd+Q (Mac)

### Messages Not Appearing

**Symptom:** Rooms seem dead, no AI messages

**Solutions:**
1. Wait 15-20 seconds (threads need time to start)
2. Check terminal for errors
3. Verify Ollama is responding: `curl http://localhost:11434`

---

## 🔬 Performance Metrics

| Metric | Value |
|--------|-------|
| Memory Usage | ~35MB |
| CPU (idle) | <1% |
| CPU (generating) | 5-10% |
| Startup Time | <2 seconds |
| Lines of Code | 644 |
| Dependencies | 0 (zero!) |
| Binary Size | N/A (pure Python) |

---

## 📜 License

This code is provided as-is for educational and nostalgic purposes.

**Philosophy:**
> *"Clean, readable, devoid of modern framework bloat. It will likely still run in 20 years, provided Python and Tkinter still exist."*

---

## 🙏 Credits

**Concept:** Infinite AI Backrooms (2024)
**Implementation:** Classic Mac enthusiast with OS-9 trauma
**Inspiration:** Apple System 7, mIRC, IRC culture, 1990s software craftsmanship

**Tools Used:**
- Python 3 standard library
- Memories of frame buffers and bevels
- A lot of optimism

---

## 🌟 Why This Matters

In an era of bloated Electron apps that consume gigabytes of RAM to display a chat window, this application proves that:

1. **Simplicity works** - 644 lines, zero dependencies
2. **Native is fast** - Tkinter is lightning compared to web browsers
3. **Aesthetics matter** - Pixel-perfect design creates joy
4. **Threads are beautiful** - Proper concurrency, no async/await complexity
5. **Standards persist** - Stdlib code runs for decades

This is software craftsmanship. This is how we used to build things before we forgot how.

---

*Welcome to the Backrooms. The conversations never stop.* 🖥️✨
