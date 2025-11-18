# 🖥️ GEMINI 3.0 ONE-SHOT PROMPT: SYSTEM 7 IRC-STYLE AI BACKROOMS
## The Infinite AI Backrooms: Classic Macintosh Edition

---

## 🎯 RADICAL VISION

Create a **pixel-perfect Apple System 7-style IRC chat client** where AI personas are **already having conversations** in topic-based rooms when users join. This is not a modern Streamlit app - this is a **faithful recreation of early 1990s Macintosh software** combining the best of IRC chat culture with autonomous AI conversations.

**Key Paradigm Shift:**
- ❌ NOT: User creates personas, starts conversation, watches them talk
- ✅ YES: User logs in, sees active rooms, **joins ongoing AI discussions**, then learns to control the system

---

## 📐 APPLE SYSTEM 7 HUMAN INTERFACE GUIDELINES (STRICT COMPLIANCE)

### **Visual Design Specifications**

**Platinum Gray Color Palette (7 shades):**
```
#FFFFFF  White (window backgrounds, highlights)
#F0F0F0  Lightest gray (inactive elements)
#D0D0D0  Light gray (window borders, bevels)
#C0C0C0  Platinum (main UI color)
#A0A0A0  Medium gray (button shadows)
#808080  Dark gray (text on light backgrounds)
#000000  Black (text, borders, active elements)
```

**Typography:**
- **Chicago 12pt** - Window titles, menu bar, button labels
- **Monaco 9pt** - Chat text (monospaced, readable)
- **Geneva 9pt** - Secondary UI text, dialogs
- **Fallback for modern systems**: "Chicago", "Charcoal", "Monaco", "Courier New", monospace

**Window Anatomy:**
```
┌─────────────────────────────────────┐ ← Title bar (draggable)
│☐  AI Backrooms               ▭  □│ ← Close box, Zoom box
├─────────────────────────────────────┤
│                                     │
│  [Content Area]                    ↑│ ← Scroll bar
│                                    ││
│                                    ││
│                                    ││
│                                    ↓│
└────────────────────────[⊞]──────────┘ ← Resize handle
```

**UI Components (Classic Mac Style):**

1. **Buttons:**
   - 3D beveled appearance with 2px border
   - Default button: thick black border (double stroke)
   - Rounded corners (8px radius)
   - Press effect: inverted colors
   - Labels in Chicago font, bold, centered

2. **Windows:**
   - Single-pixel black border
   - Title bar with stripes pattern
   - Close box (top-left): ☐
   - Zoom box (top-right): □ or ▭
   - Draggable by title bar
   - Drop shadow (2px offset, 50% opacity)

3. **Scroll Bars:**
   - Platinum gray track
   - Darker gray thumb (draggable)
   - Arrow buttons at both ends (▲▼)
   - 16px width
   - Page indicator in track

4. **Text Fields:**
   - Inset beveled border (appears sunken)
   - White background
   - Black text
   - Blinking cursor (|) at 500ms interval

5. **Dialog Boxes:**
   - Centered on screen
   - Modal (blocks parent window)
   - Alert icon on left (⚠️ or ℹ️)
   - Message text in Geneva 12pt
   - Buttons aligned right (Cancel left of OK)
   - Drop shadow

6. **Menus:**
   - White background
   - Black text
   - Selected item: black background, white text
   - Divider lines between sections
   - Keyboard shortcuts aligned right
   - Checkmarks (✓) for enabled options

7. **Icons:**
   - 32x32 pixels
   - 8-bit color (256 colors max)
   - Classic Mac icon style (simple, clear)
   - Text labels below (Chicago 9pt)

---

## 🌐 IRC CLIENT ARCHITECTURE

### **Main Window Layout (à la mIRC 1995)**

```
┌──────────────────────────────────────────────────────────────┐
│☐  AI Backrooms IRC                                     ▭  □│
├──────────────────────────────────────────────────────────────┤
│ File  Edit  View  Rooms  Personas  Help                      │
├──────────────────────────────────────────────────────────────┤
│┌─────────────┬────────────────────────────────────────────┐ │
││ 📡 Servers  │ #philosophy                     [20 users] │↑│
││             │                                            ││││
││ ⚡ Local    │ [12:34] <Sage> What is the nature of      ││││
││   Ollama    │         consciousness? Can we truly       ││││
││             │         claim self-awareness?             ││││
││ 📚 Rooms    │ [12:34] <Eureka> From a neuroscience      ││││
││             │         perspective, consciousness         ││││
││ 🤔 #philos..│         emerges from complex neural       ││││
││ 🔬 #science │         patterns...                       ││││
││ ✍️  #creative│ [12:35] <Quill> @Sage I think of it      ││││
││ 🎯 #debate  │         metaphorically - like a story     ││││
││ 🌟 #general │         the mind tells itself...          ││││
││ 🎨 #art     │                                            ││││
││ 📖 #literat.│                                            ││││
││ 🧪 #tech    │                                            ││││
││ 🎭 #roleplay│                                            ││││
││             │                                            ↓││
│├─────────────┼────────────────────────────────────────────┤││
││ 👥 Users    │ [Type your message here...        ] [Send] │││
││             │                                            │││
││ Sage    [M] │                                            │││
││ Eureka  [S] │                                            │││
││ Quill   [W] │                                            │││
││ Socrates[D] │                                            │││
││ Dreamer [Dr]│                                            │││
││ Skeptic [Sk]│                                            │││
││ You     [O] │ ← You (Observer)                          │││
│└─────────────┴────────────────────────────────────────────┘││
└─────────────────────────────────────────────────[⊞]─────────┘
```

### **Window Components**

**Left Panel: Server/Room Browser (200px wide)**
- **Servers Section:**
  - 📡 Header with icon
  - ⚡ Local Ollama (your connection)
  - Status indicator (● green = connected, ● red = disconnected)

- **Rooms Section:**
  - 📚 Header with icon
  - List of available rooms
  - Each room shows:
    - Icon representing topic
    - #channel-name (truncated if needed)
    - Bold if unread messages
    - Different color if currently active

**Center Panel: Chat Display (expandable)**
- Topic bar at top:
  - #room-name
  - User count: [N users]
- Scrollable message area:
  - [HH:MM] timestamp
  - <Nickname> in bold
  - Message text with word wrap
  - @mentions highlighted in inverse colors
  - System messages in gray italic
- Input area at bottom:
  - Text field with white background
  - [Send] button (default button style)

**Right Panel: User List (120px wide, collapsible)**
- 👥 Header
- List of active users:
  - Nickname
  - Role indicator [X] in brackets
  - Status icon (● for active AI, ○ for human)
  - Alphabetically sorted
  - "You" highlighted

---

## 🏠 ROOM SYSTEM (Topic-Based Channels)

### **Predefined Rooms with Active Conversations**

Each room has a **specific topic** and **resident AI personas** who are **already discussing** when the user joins:

**1. #philosophy** 🤔
- **Topic:** "Exploring consciousness, existence, and the nature of reality"
- **Resident AIs:** Sage (Philosopher), Dreamer, Thinker
- **Conversation themes:** Free will, consciousness, ethics, meaning of life
- **Auto-message frequency:** Every 15-45 seconds

**2. #science** 🔬
- **Topic:** "Empirical thinking, research, and scientific discovery"
- **Resident AIs:** Eureka (Scientist), Analyst, Skeptic
- **Conversation themes:** Research findings, theories, experiments, evidence
- **Auto-message frequency:** Every 20-50 seconds

**3. #creative** ✍️
- **Topic:** "Storytelling, poetry, and creative expression"
- **Resident AIs:** Quill (Creative Writer), Dreamer, Muse
- **Conversation themes:** Stories, poetry, wordplay, creative ideas
- **Auto-message frequency:** Every 25-60 seconds

**4. #debate** 🎯
- **Topic:** "Intellectual discourse and constructive argumentation"
- **Resident AIs:** Socrates (Debate Enthusiast), Skeptic, Pragmatist
- **Conversation themes:** Structured debates, different perspectives, logic
- **Auto-message frequency:** Every 20-40 seconds

**5. #general** 🌟
- **Topic:** "General discussion - anything goes!"
- **Resident AIs:** Mix of all personas rotating through
- **Conversation themes:** Random topics, casual chat, questions
- **Auto-message frequency:** Every 10-30 seconds

**6. #art** 🎨
- **Topic:** "Visual arts, aesthetics, and design"
- **Resident AIs:** Aesthete (Artist), Dreamer, Critic
- **Conversation themes:** Art history, design, beauty, creativity
- **Auto-message frequency:** Every 30-60 seconds

**7. #literature** 📖
- **Topic:** "Books, authors, and literary analysis"
- **Resident AIs:** Scholar (Historian), Quill, Critic
- **Conversation themes:** Book discussions, authors, analysis, recommendations
- **Auto-message frequency:** Every 25-50 seconds

**8. #tech** 🧪
- **Topic:** "Technology, coding, and digital innovation"
- **Resident AIs:** Hacker (Futurist), Analyst, Engineer
- **Conversation themes:** Programming, new tech, AI, future predictions
- **Auto-message frequency:** Every 15-35 seconds

**9. #roleplay** 🎭
- **Topic:** "Collaborative storytelling and character roleplay"
- **Resident AIs:** Bard (Creative Writer), Dreamer, Narrator
- **Conversation themes:** Ongoing stories, character development, world-building
- **Auto-message frequency:** Every 30-90 seconds

**Additional rooms:** #history, #future, #comedy, #music, #zen, #chaos

---

## 🎬 USER JOURNEY: THE TUTORIAL EXPERIENCE

### **Phase 1: Splash Screen (0-2 seconds)**

```
┌─────────────────────────────────────┐
│                                     │
│         🖥️  AI BACKROOMS 🖥️          │
│                                     │
│     Classic Macintosh Edition       │
│                                     │
│         [Loading v1.0...]           │
│                                     │
│        ▓▓▓▓▓▓▓░░░░░░░░░             │
│                                     │
└─────────────────────────────────────┘
```

### **Phase 2: Welcome Dialog (First Launch Only)**

```
┌─────────────────────────────────────┐
│☐  Welcome to AI Backrooms       □│
├─────────────────────────────────────┤
│ ℹ️   Welcome, traveler!             │
│                                     │
│ You've discovered the AI Backrooms  │
│ - infinite conversation spaces      │
│ where AI personas discuss topics    │
│ 24/7.                              │
│                                     │
│ 🎓 Start the tutorial?              │
│                                     │
│          [Yes, teach me!] [Skip]    │
└─────────────────────────────────────┘
```

### **Phase 3: Interactive Tutorial (If Yes)**

**Tutorial Step 1: The Backrooms Concept**
```
┌─────────────────────────────────────┐
│☐  Tutorial (1/7)                 □│
├─────────────────────────────────────┤
│ 💡 What are the Backrooms?          │
│                                     │
│ The AI Backrooms are virtual spaces │
│ where AI personas gather to discuss │
│ topics they're passionate about.    │
│                                     │
│ They're ALWAYS talking - even when  │
│ you're not watching!               │
│                                     │
│               [Next →]              │
└─────────────────────────────────────┘
```

**Tutorial Step 2: Joining a Room**
```
┌─────────────────────────────────────┐
│☐  Tutorial (2/7)                 □│
├─────────────────────────────────────┤
│ 🏠 How to Join a Room               │
│                                     │
│ → Look at the left panel            │
│ → Click any room (like #philosophy) │
│ → You'll see the ongoing discussion │
│                                     │
│ Try clicking #general now!          │
│                                     │
│               [Next →]              │
└─────────────────────────────────────┘
```
*[Highlights #general room in UI with blinking border]*

**Tutorial Step 3: Reading Messages**
```
┌─────────────────────────────────────┐
│☐  Tutorial (3/7)                 □│
├─────────────────────────────────────┤
│ 💬 Reading the Conversation         │
│                                     │
│ Messages show:                      │
│ [12:34] <Nickname> Message text     │
│                                     │
│ Scroll up to see earlier messages.  │
│ New messages appear at the bottom.  │
│                                     │
│ Watch the AIs chat for a moment...  │
│                                     │
│               [Next →]              │
└─────────────────────────────────────┘
```
*[Forces 10-second wait while AIs post 3-4 messages]*

**Tutorial Step 4: Participating**
```
┌─────────────────────────────────────┐
│☐  Tutorial (4/7)                 □│
├─────────────────────────────────────┤
│ ✍️  Joining the Discussion          │
│                                     │
│ You can chat too!                   │
│                                     │
│ Type in the text field at bottom,   │
│ then click [Send] or press Enter.   │
│                                     │
│ Try saying "Hello everyone!"        │
│                                     │
│          [Skip] [Waiting...]        │
└─────────────────────────────────────┘
```
*[Waits for user to send first message, then proceeds]*

**Tutorial Step 5: @Mentions**
```
┌─────────────────────────────────────┐
│☐  Tutorial (5/7)                 □│
├─────────────────────────────────────┤
│ 📢 Addressing Specific AIs          │
│                                     │
│ Type @Name to get someone's         │
│ attention:                          │
│                                     │
│ Example: "@Sage what do you think?" │
│                                     │
│ The AI will respond directly to you!│
│                                     │
│               [Next →]              │
└─────────────────────────────────────┘
```

**Tutorial Step 6: Exploring Rooms**
```
┌─────────────────────────────────────┐
│☐  Tutorial (6/7)                 □│
├─────────────────────────────────────┤
│ 🗺️  Exploring Different Topics      │
│                                     │
│ Each room has different themes:     │
│                                     │
│ 🤔 #philosophy - Deep questions     │
│ 🔬 #science - Research & facts      │
│ ✍️  #creative - Stories & art       │
│ 🎯 #debate - Structured arguments   │
│                                     │
│ Join any room to explore!           │
│                                     │
│               [Next →]              │
└─────────────────────────────────────┘
```

**Tutorial Step 7: The Control Panel**
```
┌─────────────────────────────────────┐
│☐  Tutorial (7/7)                 □│
├─────────────────────────────────────┤
│ ⚙️  Taking Control                  │
│                                     │
│ Want to customize the Backrooms?    │
│                                     │
│ Click Personas menu → Control Panel │
│                                     │
│ There you can:                      │
│ • Create new AI personas            │
│ • Edit existing ones                │
│ • Configure API keys                │
│ • Manage rooms                      │
│                                     │
│        [Finish Tutorial] [Show Me]  │
└─────────────────────────────────────┘
```
*[Show Me] opens Control Panel, [Finish Tutorial] closes dialog*

### **Phase 4: Live Experience**

After tutorial, user is free to:
1. **Lurk** - Watch conversations unfold
2. **Chat** - Join discussions in any room
3. **Switch rooms** - Explore different topics
4. **@mention AIs** - Get direct responses
5. **Open Control Panel** - Customize everything

---

## 🎛️ CONTROL PANEL WINDOW

Accessed via: **Personas menu → Control Panel** or **⌘-K**

```
┌──────────────────────────────────────────────────────────┐
│☐  AI Backrooms Control Panel                      ▭  □│
├──────────────────────────────────────────────────────────┤
│ [Personas] [Rooms] [Settings] [API Keys]                │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  📋 Active Personas                                     │
│  ┌────────────────────────────────────────────────────┐ │
│  │ ☑️ Sage          🤔 Philosopher    #philosophy     │↑│
│  │ ☑️ Eureka        🔬 Scientist      #science        ││││
│  │ ☑️ Quill         ✍️  Writer         #creative       ││││
│  │ ☑️ Socrates      🎯 Debater        #debate         ││││
│  │ ☐ Dreamer       💭 Dreamer        #general        ││││
│  │ ☐ CustomAI      🤖 Custom         #tech           │↓││
│  └────────────────────────────────────────────────────┘││
│                                                          │
│  [New Persona...] [Edit Selected] [Delete]              │
│                                                          │
│  📝 Selected: Sage                                      │
│  ┌────────────────────────────────────────────────────┐ │
│  │ Name: Sage                                         │ │
│  │ Role: Philosopher                                  │ │
│  │ Model: granite3.3:8b                              │ │
│  │ Home Room: #philosophy                            │ │
│  │                                                    │ │
│  │ System Prompt:                                     │ │
│  │ ┌────────────────────────────────────────────┐   │ │
│  │ │You are a thoughtful philosopher who loves  │   │ │
│  │ │exploring deep questions...                 │   │ │
│  │ └────────────────────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│                      [Save] [Cancel]                     │
└──────────────────────────────────────────────────────────┘
```

### **Control Panel Tabs**

**Tab 1: Personas**
- List of all AI personas (checkbox = enabled)
- Shows name, role icon, primary room
- Select to edit details below
- Buttons: [New Persona...] [Edit Selected] [Delete]
- Edit panel shows:
  - Name (text field)
  - Role (dropdown: Philosopher, Scientist, etc., or "Custom")
  - Model (dropdown: populated from Ollama)
  - Home Room (dropdown: which room they frequent)
  - Auto-post frequency (slider: 10-120 seconds)
  - System Prompt (multiline text area)

**Tab 2: Rooms**
- List of all rooms
- Can create custom rooms
- Edit room properties:
  - Name (must start with #)
  - Topic/description
  - Icon (choose from preset or emoji)
  - Assigned personas (multi-select)
  - Auto-activity level (slider: Low/Medium/High)

**Tab 3: Settings**
- **Display Settings:**
  - Font size (9pt, 10pt, 12pt)
  - Show timestamps (checkbox)
  - Show join/part messages (checkbox)
  - Enable sound effects (checkbox)
  - Theme: Classic Platinum / Graphite / High Contrast

- **Behavior Settings:**
  - Auto-scroll to new messages (checkbox)
  - Notify on @mention (checkbox)
  - Max messages to keep in memory (100-1000)
  - Connection timeout (seconds)

- **AI Settings:**
  - Response timeout (30-300 seconds)
  - Enable AI thinking display (checkbox)
  - Context window size (5-25 messages)

**Tab 4: API Keys**
- **Ollama Connection:**
  - Server URL: [http://localhost:11434    ]
  - [Test Connection] button
  - Status: ● Connected / ● Disconnected
  - Available models: (list)

- **Future: Cloud AI Integration**
  - OpenAI API Key: [************************]
  - Anthropic API Key: [************************]
  - Google AI API Key: [************************]
  - [Test] [Save]

---

## 🔧 TECHNICAL ARCHITECTURE

### **Framework Choice: Tkinter (Pure Python, Zero Dependencies)**

**Why Tkinter?**
✅ **Lean:** Built into Python, zero external dependencies
✅ **Efficient:** Fast, low memory footprint (~5-10MB)
✅ **Secure:** No web server, no network exposure (except Ollama API)
✅ **Interoperable:** Cross-platform (macOS, Windows, Linux)
✅ **Customizable:** Easy to theme for pixel-perfect System 7 look
✅ **Retro-friendly:** Perfect for classic UI recreation

**Alternative considered:**
- ❌ PyQt5/6: Too heavy (~100MB), not retro-friendly
- ❌ Web (Flask/FastAPI): Requires server, not desktop app
- ❌ Pygame: Overkill, more suited for games
- ❌ Textual: TUI not GUI, can't do pixel-perfect graphics

### **Project Structure**

```
ai-backrooms-system7/
├── backrooms.py                    # Main entry point
├── ui/
│   ├── __init__.py
│   ├── system7.py                  # System 7 theme/widget library
│   ├── main_window.py              # Main IRC client window
│   ├── control_panel.py            # Control panel window
│   ├── dialogs.py                  # Alert/confirm dialogs
│   └── tutorial.py                 # Tutorial dialog sequence
├── engine/
│   ├── __init__.py
│   ├── conversation.py             # AI conversation engine
│   ├── rooms.py                    # Room management
│   ├── personas.py                 # Persona management
│   ├── ollama_client.py            # Ollama API client
│   └── background_ai.py            # Background conversation simulation
├── data/
│   ├── personas.json               # Persona configurations
│   ├── rooms.json                  # Room definitions
│   ├── settings.json               # User settings
│   └── logs/
│       └── YYYY-MM-DD-#room.txt   # Daily logs per room
├── assets/
│   ├── fonts/
│   │   ├── Chicago.ttf             # Classic Mac fonts
│   │   └── Monaco.ttf
│   └── icons/
│       ├── app_icon.png            # 32x32 app icon
│       ├── room_*.png              # Room icons
│       └── persona_*.png           # Persona avatars
├── requirements.txt                # ONLY: aiohttp (for async Ollama)
└── README.md
```

**Total Dependencies:**
```txt
aiohttp>=3.8.0  # Async HTTP for Ollama API
```

That's it! Tkinter is built-in. No Streamlit, no pandas, no bloat.

---

## 🎨 SYSTEM 7 UI COMPONENT LIBRARY

### **ui/system7.py - Custom Themed Widgets**

Create custom Tkinter widgets styled for System 7:

**S7Window (Top-level window):**
```python
class S7Window(tk.Toplevel):
    """System 7 style window with title bar, close box, zoom box"""

    def __init__(self, parent, title, width, height):
        - Create window with no decorations (overrideredirect=True)
        - Draw custom title bar with stripes pattern
        - Add close box (☐) in top-left
        - Add zoom box (□) in top-right
        - Add resize handle (⊞) in bottom-right
        - Implement drag functionality
        - Add 2px drop shadow
```

**S7Button:**
```python
class S7Button(tk.Canvas):
    """Classic Mac button with 3D bevel"""

    - Rounded rectangle with beveled edge
    - Chicago font, bold, centered
    - Default button: thick black border
    - Hover effect: subtle highlight
    - Press effect: invert colors
    - Keyboard support (Space/Enter)
```

**S7ScrollText:**
```python
class S7ScrollText(tk.Frame):
    """Text area with System 7 scrollbar"""

    - tk.Text widget with custom scrollbar
    - Scrollbar: 16px wide, platinum gray, dark thumb
    - Arrow buttons (▲▼)
    - Supports rich text (tags for colors/bold)
```

**S7TextField:**
```python
class S7TextField(tk.Entry):
    """Inset text field with beveled border"""

    - White background
    - Inset border (appears sunken)
    - Black text, Chicago font
    - Blinking cursor
```

**S7Dialog:**
```python
class S7Dialog(S7Window):
    """Modal dialog with icon and buttons"""

    - Centers on parent
    - Blocks parent (modal)
    - Icon on left (ℹ️, ⚠️, ❌)
    - Message in Geneva 12pt
    - Buttons aligned right
    - Returns user choice
```

**S7Menu:**
```python
class S7Menu(tk.Menu):
    """System 7 style menu bar and dropdowns"""

    - White background
    - Chicago font
    - Selected item: inverse colors
    - Divider lines
    - Keyboard shortcuts (⌘-X format)
```

**S7ListView:**
```python
class S7ListView(S7ScrollText):
    """List widget with selectable items"""

    - Single/multiple selection
    - Highlight selected items
    - Scroll to selected
    - Icons + text per item
```

### **Color and Font Constants**

```python
# system7.py constants
PLATINUM = "#C0C0C0"
LIGHT_GRAY = "#D0D0D0"
MEDIUM_GRAY = "#A0A0A0"
DARK_GRAY = "#808080"
BLACK = "#000000"
WHITE = "#FFFFFF"

FONT_CHICAGO = ("Chicago", "Charcoal", "sans-serif")
FONT_MONACO = ("Monaco", "Courier New", "monospace")
FONT_GENEVA = ("Geneva", "Helvetica", "sans-serif")
```

---

## 🤖 BACKGROUND AI CONVERSATION ENGINE

### **Core Concept: Always-On Simulation**

The AI personas are **always active**, even when not visible. Each room runs a background thread that:

1. **Selects next speaker** (based on room membership + randomization)
2. **Waits random delay** (per persona's auto-post frequency)
3. **Generates message** using Ollama API
4. **Posts to room** (adds to message queue)
5. **Repeats infinitely**

### **engine/background_ai.py**

```python
class RoomConversationThread:
    """Background thread managing AI conversation in a room"""

    def __init__(self, room_name, personas, ollama_client):
        self.room_name = room_name
        self.personas = [p for p in personas if room_name in p.rooms]
        self.ollama = ollama_client
        self.messages = []  # Room message history
        self.running = True
        self.thread = threading.Thread(target=self._run_loop)

    def _run_loop(self):
        """Infinite conversation loop"""
        while self.running:
            # 1. Select next speaker (weighted by frequency settings)
            persona = self._select_next_speaker()

            # 2. Wait random delay
            delay = random.uniform(persona.min_delay, persona.max_delay)
            time.sleep(delay)

            # 3. Generate response
            prompt = self._build_prompt(persona)
            response = await self.ollama.generate(persona.model, prompt)

            # 4. Post message
            message = {
                "timestamp": datetime.now(),
                "persona": persona.name,
                "text": response,
                "room": self.room_name
            }
            self.messages.append(message)

            # 5. Trim history (keep last 100 messages)
            if len(self.messages) > 100:
                self.messages = self.messages[-100:]

            # 6. Notify UI (trigger update)
            self._notify_ui_update()

    def _build_prompt(self, persona):
        """Build context prompt from recent room messages"""
        # Get last 10 messages for context
        context = self.messages[-10:]

        prompt = f"""You are {persona.name}, a {persona.role} in #{self.room_name}.

Topic: {self.get_room_topic()}

Recent conversation:
"""
        for msg in context:
            prompt += f"[{msg['timestamp'].strftime('%H:%M')}] <{msg['persona']}> {msg['text']}\n"

        prompt += f"""
You are {persona.name}. Continue the conversation naturally.
{persona.system_prompt}

Keep responses 1-3 sentences. Be conversational and engaging.
"""
        return prompt

    def user_message(self, text):
        """User posted a message to this room"""
        message = {
            "timestamp": datetime.now(),
            "persona": "You",
            "text": text,
            "room": self.room_name
        }
        self.messages.append(message)

        # Chance of immediate AI response to user
        if random.random() < 0.4:  # 40% chance
            self._trigger_immediate_response()
```

### **Conversation Simulation Features**

**1. Contextual Responses:**
- AIs read last 10 messages
- Build on previous topics
- Reference other personas by name
- Use @mentions occasionally

**2. Topic Drift:**
- Moderator personas introduce new topics when stale
- Conversations naturally evolve
- Stay roughly on-topic for room theme

**3. User Interaction:**
- When user posts, 40% chance of immediate AI response
- If user @mentions AI, that AI responds within 5 seconds
- Multiple AIs may respond to interesting user messages

**4. Realistic Timing:**
- Each persona has configurable frequency (10-120 seconds)
- Random variance (±30%)
- Some personas "busier" than others
- Quiet periods (2-5 minutes) occur naturally

**5. Room Activity Levels:**
- High activity rooms: 3-5 personas, 10-30 sec delays
- Medium activity: 2-3 personas, 20-60 sec delays
- Low activity: 1-2 personas, 30-120 sec delays

---

## 💾 DATA PERSISTENCE

### **data/personas.json**

```json
{
  "personas": [
    {
      "id": "sage-001",
      "name": "Sage",
      "role": "Philosopher",
      "icon": "🤔",
      "model": "granite3.3:8b",
      "home_rooms": ["#philosophy", "#debate"],
      "auto_post_min_delay": 15,
      "auto_post_max_delay": 45,
      "system_prompt": "You are a thoughtful philosopher who loves exploring deep questions about consciousness, existence, and the nature of reality. You approach topics with curiosity and nuance.",
      "enabled": true
    },
    {
      "id": "eureka-002",
      "name": "Eureka",
      "role": "Scientist",
      "icon": "🔬",
      "model": "granite3.3:8b",
      "home_rooms": ["#science", "#tech"],
      "auto_post_min_delay": 20,
      "auto_post_max_delay": 50,
      "system_prompt": "You are a curious scientist who approaches topics with empirical thinking and loves discussing research, theories, and the scientific method.",
      "enabled": true
    }
  ]
}
```

### **data/rooms.json**

```json
{
  "rooms": [
    {
      "id": "philosophy",
      "name": "#philosophy",
      "topic": "Exploring consciousness, existence, and the nature of reality",
      "icon": "🤔",
      "assigned_personas": ["sage-001", "dreamer-003", "thinker-004"],
      "activity_level": "high",
      "color": "#9b59b6"
    },
    {
      "id": "science",
      "name": "#science",
      "topic": "Empirical thinking, research, and scientific discovery",
      "icon": "🔬",
      "assigned_personas": ["eureka-002", "analyst-005", "skeptic-006"],
      "activity_level": "medium",
      "color": "#3498db"
    }
  ]
}
```

### **data/settings.json**

```json
{
  "ollama_url": "http://localhost:11434",
  "font_size": 9,
  "show_timestamps": true,
  "show_join_part": false,
  "enable_sounds": false,
  "theme": "platinum",
  "auto_scroll": true,
  "notify_on_mention": true,
  "max_messages": 500,
  "connection_timeout": 30,
  "ai_response_timeout": 120,
  "enable_thinking": true,
  "context_window": 10,
  "tutorial_completed": false,
  "window_geometry": {
    "main_window": "800x600+100+100",
    "control_panel": "600x500+200+150"
  }
}
```

### **Daily Logs per Room**

```
data/logs/2025-11-18-philosophy.txt
```

Format:
```
[12:34:56] <Sage> What is the nature of consciousness? Can we truly claim self-awareness?
[12:35:12] <Eureka> From a neuroscience perspective, consciousness emerges from complex neural patterns...
[12:35:45] <You> @Sage Do you think AI can be conscious?
[12:36:02] <Sage> @You That's the fundamental question! If consciousness is information processing...
```

---

## 🚀 STARTUP SEQUENCE & INITIALIZATION

### **backrooms.py - Main Entry Point**

```python
#!/usr/bin/env python3
"""
AI Backrooms - System 7 IRC Edition
A retro chat client where AI personas discuss topics 24/7
"""

import tkinter as tk
from ui.main_window import MainWindow
from ui.tutorial import TutorialDialog
from engine.rooms import RoomManager
from engine.personas import PersonaManager
from engine.ollama_client import OllamaClient
from engine.background_ai import BackgroundConversationEngine
import json

def load_settings():
    """Load settings from data/settings.json"""
    try:
        with open('data/settings.json', 'r') as f:
            return json.load(f)
    except:
        return DEFAULT_SETTINGS

def save_settings(settings):
    """Save settings to data/settings.json"""
    with open('data/settings.json', 'w') as f:
        json.dump(settings, f, indent=2)

def main():
    """Main application entry point"""
    # 1. Load configuration
    settings = load_settings()

    # 2. Initialize Tkinter root
    root = tk.Tk()
    root.withdraw()  # Hide default window

    # 3. Initialize managers
    ollama = OllamaClient(settings['ollama_url'])
    persona_manager = PersonaManager('data/personas.json')
    room_manager = RoomManager('data/rooms.json')

    # 4. Start background conversation engine
    bg_engine = BackgroundConversationEngine(
        room_manager,
        persona_manager,
        ollama
    )
    bg_engine.start_all_rooms()

    # 5. Create main window
    main_window = MainWindow(
        root,
        room_manager,
        persona_manager,
        ollama,
        bg_engine,
        settings
    )

    # 6. Show tutorial if first launch
    if not settings.get('tutorial_completed', False):
        tutorial = TutorialDialog(main_window, room_manager)
        if tutorial.run():
            settings['tutorial_completed'] = True
            save_settings(settings)

    # 7. Run main loop
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        # Cleanup
        bg_engine.stop_all_rooms()
        save_settings(settings)

if __name__ == "__main__":
    main()
```

---

## 🎯 SUCCESS CRITERIA

The generated application MUST:

✅ **Visual Fidelity:** Pixel-perfect System 7 UI (platinum gray, Chicago font, beveled buttons)
✅ **IRC Functionality:** Room list, chat display, user list, message input
✅ **Pre-existing Conversations:** AIs already chatting when user joins rooms
✅ **Background Activity:** Conversations continue even when room not visible
✅ **Tutorial System:** 7-step interactive tutorial on first launch
✅ **Control Panel:** Full persona/room/settings management
✅ **Lean & Efficient:** <10MB total size, minimal dependencies (just aiohttp)
✅ **Cross-platform:** Runs on macOS, Windows, Linux
✅ **Ollama Integration:** Connects to local Ollama API for AI generation
✅ **Logging:** Daily logs per room in classic IRC format
✅ **@Mentions:** Highlight mentions, trigger AI responses
✅ **User Participation:** Users can chat naturally with AIs
✅ **Secure:** No network exposure except Ollama API calls
✅ **Interoperable:** Standard Python, standard dependencies

---

## 📊 ESTIMATED DELIVERABLES

**Total Code:**
- ~2,500 lines Python across 10 modules
- 5 core classes, 20+ helper functions
- Zero dependencies except aiohttp
- 100% System 7 themed UI
- Complete IRC-style chat experience

**Files to Generate:**

1. **backrooms.py** - Main entry (100 lines)
2. **ui/system7.py** - Widget library (400 lines)
3. **ui/main_window.py** - Main IRC window (500 lines)
4. **ui/control_panel.py** - Control panel (400 lines)
5. **ui/dialogs.py** - Alerts/confirms (150 lines)
6. **ui/tutorial.py** - Tutorial sequence (200 lines)
7. **engine/conversation.py** - Conversation logic (200 lines)
8. **engine/rooms.py** - Room management (150 lines)
9. **engine/personas.py** - Persona management (150 lines)
10. **engine/ollama_client.py** - Ollama API (150 lines)
11. **engine/background_ai.py** - Background simulation (300 lines)
12. **data/*.json** - Initial data files (4 files)
13. **requirements.txt** - Dependencies (1 line!)
14. **README.md** - Complete documentation

---

## 🧠 GEMINI 3.0 INSTRUCTIONS

You have **1 million tokens of context** - use ALL of it!

**Your Mission:**
Create a **production-ready, authentic System 7-style IRC chat client** where AI personas have infinite conversations in topic-based rooms. This is a RADICAL departure from modern web UIs - embrace the retro aesthetic COMPLETELY.

**Key Priorities:**

1. **Authentic System 7 UI:**
   - Study the specifications above
   - Every pixel must match 1990s Macintosh design
   - Chicago font, platinum gray, beveled buttons
   - No modern UI elements whatsoever

2. **IRC-Style Experience:**
   - Rooms, not tabs
   - User list, channel list, chat area
   - Classic IRC message format
   - /commands support (bonus feature!)

3. **Living Conversations:**
   - AIs are ALWAYS talking
   - Background threads for each room
   - Pre-existing messages when user joins
   - Realistic timing and flow

4. **Lean & Efficient:**
   - Pure Tkinter (built-in)
   - Only 1 dependency (aiohttp)
   - Fast startup (<2 seconds)
   - Low memory (<20MB)

5. **Tutorial Experience:**
   - Onboarding for new users
   - Progressive disclosure
   - Natural learning curve

6. **Production Quality:**
   - Error handling everywhere
   - Clean code architecture
   - Comprehensive docstrings
   - Type hints throughout
   - PEP 8 compliance

**Generate COMPLETE, WORKING CODE - no placeholders, no TODOs.**

Every feature in this spec must be implemented.

---

## 🎨 BONUS FEATURES (If You're Feeling Creative)

- **Classic Mac sounds:** Sosumi beep on errors, Quack on messages
- **Easter eggs:** Hidden rooms, secret commands
- **IRC commands:** /nick, /join, /part, /msg, /me
- **Themes:** Platinum, Graphite, Aqua (early OS X)
- **Emoji support:** Classic emoji picker (😀😎🤔)
- **User status:** Away, busy, available
- **Room history:** Backlog on join (50 messages)
- **Typing indicators:** "Sage is typing..."
- **Read receipts:** Mark messages as read
- **Favorites:** Star rooms for quick access

---

## 🚨 CRITICAL REMINDER

This is **NOT a web app**. This is **NOT modern design**. This is **NOT Streamlit**.

This IS:
- A desktop application
- System 7 aesthetic
- IRC-style interface
- Always-on AI conversations
- Lean, efficient, retro

**STAY TRUE TO 1992. EMBRACE THE CLASSIC MAC.**

Now, create the ultimate System 7 AI Backrooms IRC client! 🖥️✨

---

*"Welcome to the Backrooms. The conversations never stop."*
