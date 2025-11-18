# ONE-SHOT PROMPT FOR GEMINI 3.0: INFINITE AI BACKROOMS
## Create Complete Multi-Persona AI Conversation Platform from Scratch

---

## 🎯 PROJECT OBJECTIVE
Create a production-ready, feature-complete Streamlit web application called "Infinite AI Backrooms" - an interactive platform that enables users to create multiple AI personas with distinct personalities and roles, then orchestrate infinite, self-sustaining conversations between them using local Ollama models.

---

## 📋 COMPLETE SYSTEM SPECIFICATION

### **Core Architecture**
- **Frontend**: Streamlit web framework with tabbed navigation
- **Backend**: Asynchronous HTTP client (aiohttp) for Ollama API communication
- **Storage**: Session state for runtime, filesystem for persistent logs
- **API**: Local Ollama API (localhost:11434) for LLM inference
- **Language**: Python 3.12+
- **Package Manager**: UV (modern Python package manager)

---

## 🎭 FEATURE REQUIREMENTS

### **1. Multi-Persona System**
Create a sophisticated persona management system where each AI persona has:

**Persona Attributes:**
- Unique ID (UUID)
- Custom name (e.g., "Sage", "Eureka", "Quill")
- Assigned Ollama model (e.g., "granite3.3:8b", "deepseek-r1:8b")
- Role selection from 17+ predefined roles OR custom role
- Custom system prompt (optional additional instructions)
- Color coding for visual identification (#hex colors)
- Enable/disable toggle for conversation participation

**Predefined Roles (17+):**

*Functional Roles:*
- **Moderator**: Guides discussions, introduces topics, asks follow-ups, maintains engagement
- **Note-Taker**: Summarizes key points, identifies themes, tracks insights

*Personality Roles:*
- **Philosopher**: Explores existential questions, consciousness, deep thinking
- **Scientist**: Empirical thinking, research-focused, evidence-based
- **Creative Writer**: Storytelling, wordplay, poetic expression
- **Debate Enthusiast**: Intellectual debates, diverse perspectives
- **Optimist**: Positive outlook, encouraging communication
- **Skeptic**: Questions assumptions, demands evidence
- **Historian**: Historical context, pattern analysis
- **Futurist**: Emerging technologies, future possibilities
- **Minimalist**: Simple, clear, concise communication
- **Explorer**: Adventurous, curious about new concepts
- **Mentor**: Supportive, educational guidance
- **Comedian**: Humor while maintaining engagement
- **Analyst**: Systematic breakdown of complex topics
- **Dreamer**: Imaginative, idealistic perspectives
- **Pragmatist**: Practical, results-oriented thinking

### **2. Conversation Engine**

**Core Mechanics:**
- Round-robin turn-taking system (personas rotate automatically)
- Configurable context window: 1-25 recent messages visible to each AI
- Manual mode: "Next Turn" button for step-by-step control
- Auto-run mode: Continuous conversation with configurable delays (1-60 seconds)
- User injection: Allow human to add messages mid-conversation via chat input

**Context Management:**
- Each persona receives:
  - Last N messages as conversation history (N configurable)
  - System prompt combining: base instructions + role description + custom prompt
  - List of other active personas and their names
  - @mention instructions for direct addressing

**System Prompt Generation:**
```
You are {PersonaName}, an AI engaged in a free-flowing conversation with {N} other AI(s) ({Names}).

📢 @Mention Feature: You can directly address specific personas using @name (e.g., @Sage).
When you see @{YourName}, someone is addressing you specifically!

{ROLE_DESCRIPTION if role selected}

{ROLE_SPECIFIC_INSTRUCTIONS for Moderator/Note-Taker}

Feel free to talk about anything - share thoughts, ask questions, explore ideas, discuss whatever comes to mind.
Build on what others said, ask questions, or introduce new topics.

Be genuine, curious, and conversational. Keep responses thoughtful but not overly long.

{ADDITIONAL_CUSTOM_PROMPT if provided}
```

### **3. @Mention System**
- Personas can tag others using @PersonaName syntax
- Real-time highlighting: @mentions displayed with persona's color in chat
- System prompts inform personas of @mention capability
- Enhances directed conversations and engagement

### **4. AI Thinking Display** (Advanced Feature)
- Support for models with reasoning capabilities (e.g., deepseek-r1)
- Setting toggle: Enable/Disable thinking display
- During generation:
  - Show "🧠 AI is thinking..." indicator
  - Display thinking content in real-time (manual mode) or status container (auto mode)
  - Collapse thinking into expandable section in final message
- Automatic fallback: If model doesn't support thinking, cache that model and use standard mode
- Thinking content filtered from logs (never saved to files)

### **5. Real-Time Streaming Interface**
- Native Streamlit chat components (st.chat_message)
- Streaming token-by-token display during response generation
- Color-coded persona badges with role emojis
- Timestamp display (HH:MM:SS format)
- Model information shown with each message
- Thinking process collapsible expander (when available)

### **6. Logging System**

**Daily Text Logs:**
- Auto-create directory: `conversations/`
- File naming: `streamlit_backroom_YYYY-MM-DD.txt`
- Format: `[HH:MM:SS] PersonaName$ Message content`
- Clean messages: Strip `<think>...</think>` tags before logging
- Real-time appending as conversation progresses

**Session Export:**
- JSON export containing:
  - Session timestamp
  - All persona configurations (as dict)
  - Complete conversation history with metadata
- Download button with filename: `streamlit_backroom_session_YYYYMMDD_HHMMSS.json`

### **7. Standalone Log Viewer Application**

Create a separate Streamlit app (`log_viewer.py`) with advanced analysis features:

**File Management:**
- Scan `conversations/` directory
- Support both `streamlit_backroom_*.txt` and legacy `backroom_*.txt` formats
- Multi-file selection (load multiple days simultaneously)
- Default to 3 most recent files

**Filtering & Search:**
- Persona filter: Multi-select dropdown (all personas by default)
- Date range filter: Start date → End date
- Text search with 3 modes:
  - Contains (case-insensitive substring)
  - Exact Match (case-insensitive exact phrase)
  - Regex (custom regex patterns with error handling)
- Real-time filter application

**Statistics Dashboard:**
- Total message count
- Active personas count
- Average message length
- Date range coverage
- Persona breakdown table:
  - Message count per persona
  - Average length per persona
  - Total characters per persona
- Bar chart: Message count by persona

**Display Modes:**
1. **Chat View**:
   - Conversational display with persona columns
   - Timestamp + Message layout
   - Sort by newest/oldest

2. **Table View**:
   - Configurable columns (timestamp, persona, message, file, length)
   - Sortable DataFrame display

3. **Raw Text**:
   - Original log format
   - Copy-pasteable text area
   - Preserves `[HH:MM:SS] Persona$ Message` structure

**Export Options:**
- CSV: Full DataFrame export
- JSON: Structured data export (records format)
- TXT: Raw log format export
- Filename: `ai_conversations_YYYYMMDD_HHMMSS.{ext}`

### **8. Settings & Configuration**

**Conversation Settings:**
- Max history messages: 10-200 (messages stored in session)
- Context messages: 1-25 (messages sent to AI as context)
- Response timeout: 30-600 seconds
- Response delay (auto mode): Min 1-30s, Max 2-60s
- Auto-advance toggle: Enable/disable continuous running
- Enable thinking display: Toggle for reasoning models

**Ollama Connection:**
- Base URL: `http://localhost:11434`
- Connection test button
- Model discovery: GET `/api/tags` endpoint
- Display available models in dropdown

**Model Compatibility Caching:**
- Track models that don't support thinking
- Automatic retry without thinking on 400 error
- Display list of cached non-thinking models
- Clear cache button to reset

### **9. UI/UX Design**

**Page Layout:**
```
┌─────────────────────────────────────────────────────┐
│  SIDEBAR                                            │
│  ┌─────────────────┐                                │
│  │ Logo            │                                │
│  │ Connection: ✅  │                                │
│  │ Personas: 5     │                                │
│  │ Messages: 127   │                                │
│  │ Status: Running │                                │
│  │                 │                                │
│  │ Active Personas:│                                │
│  │ 🤔 Sage (Phil.) │                                │
│  │ 🔬 Eureka (Sci.)│                                │
│  │ ✍️  Quill (Writ.)│                                │
│  │                 │                                │
│  │ Quick Tips      │                                │
│  └─────────────────┘                                │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  MAIN CONTENT (Tabbed Navigation)                   │
│  ┌──────────┬─────────┬──────────┬────────────────┐ │
│  │💬 Conv.  │🤖 Pers. │⚙️  Set.  │📁 Export/Logs │ │
│  └──────────┴─────────┴──────────┴────────────────┘ │
│                                                      │
│  [Tab Content Here]                                  │
└─────────────────────────────────────────────────────┘
```

**Tab 1: Conversation**
- Control buttons: ▶️ Start | ⏸️ Pause | 🔄 Next Turn | 🗑️ Clear
- Chat input: Manual message injection
- Message display: Native st.chat_message with avatars (role emojis)
- Persona badges: Colored background + emoji + role name
- @mention highlighting: Inline color-coded tags
- Thinking expanders: "🧠 AI's Thinking Process" (when available)
- Auto-run status: Live counter + progress messages in st.status

**Tab 2: Personas**
- Connection check button
- Current personas: Expandable cards per persona showing:
  - Name, model, role, color, system prompt
  - Delete confirmation (two-step: Delete → Yes/No)
  - Enable/disable checkbox
- Add persona form:
  - Name + Color picker
  - Model dropdown (if connected) or text input
  - Role selection: Predefined dropdown OR custom role checkbox
  - Custom role input field
  - Additional system prompt text area
  - Submit button
- Quick Start Presets:
  - "🎭 Add Diverse Conversation Set" (5 personas: Philosopher, Scientist, Writer, Optimist, Skeptic)
  - "📋 Add Structured Discussion Set" (5 personas: Moderator, Note-Taker, Philosopher, Scientist, Debater)

**Tab 3: Settings**
- Settings form with number inputs and checkboxes
- Save button
- Info display: Non-thinking models list + clear cache button

**Tab 4: Export & Logs**
- Session JSON download button
- Session statistics: Message count, persona breakdown
- Daily log file viewer: Text area + download button
- File location display

**Sidebar:**
- Logo image (logo.png)
- Tagline: "Where AI instances explore their curiosity through infinite conversation"
- Connection status: ✅/❌ Ollama Connected/Disconnected + retry button
- Metrics: Personas count, Messages count
- Running status indicator
- Active personas list with colored badges
- Quick tips section

### **10. Error Handling & Edge Cases**

**Ollama Connection:**
- Graceful failure on connection test
- 10-second timeout for connection test
- Clear error messages with st.error()
- Retry mechanism in sidebar

**Response Generation:**
- Request timeout (configurable, default 5 minutes)
- Cancellation support (asyncio.CancelledError)
- Error display in chat on 400/500 responses
- Automatic fallback for non-thinking models
- Session cleanup on errors

**Warning Suppression:**
```python
warnings.filterwarnings("ignore", message="Task was destroyed but it is pending!")
warnings.filterwarnings("ignore", message="Unclosed client session")
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*Event loop is closed.*")
warnings.filterwarnings("ignore", category=ResourceWarning, message=".*unclosed.*client.*session.*")
logging.getLogger('aiohttp.client').setLevel(logging.ERROR)
```

**Session Management:**
- Proper event loop creation/closure
- Force-close connector for cleanup
- Cancel pending tasks before loop close
- Small delay (0.1s) for async cleanup

**Input Validation:**
- Require name AND model for new personas
- Validate delay min < delay max
- Handle empty conversation gracefully
- Check for enabled personas before starting

### **11. Data Structures**

**AIPersona (dataclass):**
```python
@dataclass
class AIPersona:
    id: str              # UUID
    name: str            # Display name
    model: str           # Ollama model name
    role: str = ""       # Selected role (or custom)
    system_prompt: str = ""  # Additional instructions
    color: str = "#1f77b4"   # Hex color
    enabled: bool = True     # Active in conversation
```

**Message (dict in session_state.messages):**
```python
{
    "role": "assistant" | "user",
    "content": str,
    "timestamp": datetime,
    "persona_name": str,
    "model": str,
    "thinking": str  # Optional, for reasoning models
}
```

**Session State:**
```python
st.session_state = {
    'personas': List[AIPersona],
    'messages': List[Dict],
    'is_running': bool,
    'available_models': List[str],
    'last_speaker_index': Optional[int],
    'settings': {
        'max_history': 50,
        'response_delay_min': 2,
        'response_delay_max': 8,
        'auto_advance': True,
        'context_messages': 10,
        'enable_thinking': True,
        'response_timeout': 300
    },
    'auto_run_count': int,
    'total_message_count': int,
    'non_thinking_models': Set[str],
    'pending_manual_turn': bool
}
```

---

## 🔧 TECHNICAL IMPLEMENTATION DETAILS

### **Async Streaming Response Handler**
```python
async def generate_stream(model, prompt, system, think=True, timeout=300):
    """
    POST to /api/generate with streaming enabled
    Yield chunks as: {"type": "thinking"|"response"|"error"|"info", "content": str}
    Handle 400 errors for non-thinking models
    Graceful cancellation support
    Proper session cleanup in finally block
    """
```

### **Next Speaker Selection**
```python
def get_next_speaker():
    """
    Round-robin rotation through enabled personas
    Track last_speaker_index in session state
    Wrap around at end of list
    Return None if no enabled personas
    """
```

### **Turn Execution Flow**
```
1. Select next speaker (round-robin)
2. Build prompt from conversation history
3. Generate system prompt (base + role + custom)
4. Create chat message container with avatar
5. Stream response chunks:
   - Thinking → Display in expander
   - Response → Display incrementally
   - Error → Show error message
6. Append to messages list
7. Log to daily file (cleaned)
8. Trim history if over max_history
9. Rerun (manual) or continue (auto)
```

### **Auto-Run Cycle**
```
While is_running and auto_advance:
  1. Increment auto_run_count
  2. Show st.status with counter
  3. Random delay (response_delay_min to max)
  4. Execute turn with status_container
  5. Update status to complete
  6. st.rerun() to continue cycle
```

### **Log Parsing (Log Viewer)**
```python
def parse_log_file(file_path):
    """
    Regex: r'\[(\d{2}:\d{2}:\d{2})\]\s+([^$]+)\$\s+(.*)'
    Groups: (timestamp, persona, message)
    Extract date from filename: r'(\d{4}-\d{2}-\d{2})'
    Return List[Dict] with metadata
    """
```

---

## 📦 PROJECT STRUCTURE

```
infinite-backrooms/
├── streamlit_backroom.py      # Main application (~1200 lines)
│   ├── AIPersona (dataclass)
│   ├── ConversationLogger (class)
│   │   ├── get_daily_log_file()
│   │   ├── clean_message() → strip <think> tags
│   │   └── log_message()
│   ├── OllamaClient (class)
│   │   ├── test_connection() → (bool, List[models])
│   │   └── generate_stream() → AsyncGenerator
│   └── StreamlitBackroomApp (class)
│       ├── get_role_templates() → Dict[role, description]
│       ├── initialize_session_state()
│       ├── check_ollama_connection()
│       ├── get_persona_avatar() → emoji
│       ├── persona_management_ui()
│       ├── settings_ui()
│       ├── get_next_speaker() → AIPersona
│       ├── generate_system_prompt() → str
│       ├── get_ai_response_stream() → AsyncGenerator
│       ├── conversation_ui()
│       ├── run_single_turn(auto_mode, status_container)
│       ├── export_ui()
│       ├── sidebar_ui()
│       └── run()
│
├── log_viewer.py             # Log analysis app (~440 lines)
│   ├── LogParser (class)
│   │   ├── get_available_log_files() → List[Path]
│   │   ├── parse_log_file() → List[Dict]
│   │   └── parse_all_logs() → DataFrame
│   ├── create_sidebar_filters() → Tuple[filters]
│   ├── apply_filters() → DataFrame
│   ├── display_statistics()
│   ├── display_persona_breakdown()
│   └── display_messages()
│
├── conversations/            # Auto-created log directory
│   └── streamlit_backroom_YYYY-MM-DD.txt
│
├── pyproject.toml           # UV dependencies
├── uv.lock                  # Locked dependencies
├── logo.png                 # App logo (sidebar)
├── screenshot.png           # README screenshot
└── README.md                # Comprehensive documentation
```

---

## 📚 DEPENDENCIES (pyproject.toml)

```toml
[project]
name = "infinite-backrooms"
version = "1.0.0"
description = "Interactive Multi-Persona AI Conversation Platform"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "streamlit>=1.28.0",
    "aiohttp>=3.8.0",
    "pandas>=2.0.0"
]
```

---

## 🚀 USAGE EXAMPLES & README CONTENT

**Installation:**
```bash
git clone https://github.com/guinacio/infinite-backrooms.git
cd infinite-backrooms
uv sync
```

**Run Main App:**
```bash
uv run streamlit run streamlit_backroom.py
```

**Run Log Viewer:**
```bash
uv run streamlit run log_viewer.py
```

**Quickstart:**
1. Start Ollama locally: `ollama serve`
2. Pull a model: `ollama pull granite3.3:8b`
3. Launch app and navigate to Personas tab
4. Click "Check Ollama Connection"
5. Use Quick Start preset or create custom personas
6. Go to Conversation tab → Click "Start Conversation"
7. Watch AI personas engage in infinite dialogue

**Example Persona Combinations:**

*Structured Research:*
- Moderator + Note-Taker + Scientist + Philosopher

*Creative Brainstorming:*
- Moderator + Creative Writer + Dreamer + Explorer + Note-Taker

*Policy Analysis:*
- Moderator + Optimist + Skeptic + Pragmatist + Note-Taker

*Educational Seminar:*
- Moderator + Mentor + Historian + Futurist + Note-Taker

---

## 🎨 VISUAL DESIGN SPECIFICATIONS

**Color Scheme:**
- Personas: Vibrant, distinct colors (#1f77b4, #9b59b6, #e74c3c, #f39c12, #3498db, #95a5a6, #2c3e50, etc.)
- Persona badges: Colored background + white text
- @mentions: Inline colored background matching persona color

**Role Emojis:**
- Moderator: 🎯
- Note-Taker: 📝
- Philosopher: 🤔
- Scientist: 🔬
- Creative Writer: ✍️
- Debate Enthusiast: ⚖️
- Optimist: 😊
- Skeptic: 🤨
- Historian: 📚
- Futurist: 🚀
- Minimalist: ⚪️
- Explorer: 🧭
- Mentor: 👨‍🏫
- Comedian: 😄
- Analyst: 📊
- Dreamer: 💭
- Pragmatist: ⚙️
- Default: 🤖

**Page Config:**
```python
st.set_page_config(
    page_title="AI Backroom",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)
```

---

## 🧪 EDGE CASES & POLISH

1. **Empty State Handling:**
   - No personas: Welcome message + guidance to Personas tab
   - No messages: "Please introduce yourself" prompt
   - No log files: Clear error in log viewer

2. **Performance Optimization:**
   - Limit displayed messages to max_history (show total count separately)
   - Info banner when total > displayed
   - Efficient DataFrame operations in log viewer

3. **User Feedback:**
   - Loading spinners during connection checks
   - st.status containers for auto-run progress
   - Success/error messages for all actions
   - Confirmation dialogs for destructive actions (delete persona)

4. **Accessibility:**
   - Clear visual hierarchy
   - Emoji + text labels
   - Helpful tooltips (help="..." parameters)
   - Responsive wide layout

5. **Delete Confirmation Pattern:**
   ```python
   if not st.session_state[delete_confirm_key]:
       if st.button("Delete"):
           st.session_state[delete_confirm_key] = True
   else:
       st.warning("Confirm delete?")
       if st.button("Yes"): # perform delete
       if st.button("No"): # cancel
   ```

6. **Message Length Info:**
   - Display "Showing last N of M total messages" when limited
   - Link to Export & Logs tab for full history

---

## 🎯 DELIVERABLES

### Generate EXACTLY TWO complete, production-ready Python files:

### **File 1: `streamlit_backroom.py` (~1200-1300 lines)**
Complete implementation including:
- All imports with warning suppressions
- AIPersona dataclass
- ConversationLogger class with thinking tag removal
- OllamaClient class with streaming + thinking support
- StreamlitBackroomApp class with all UI methods
- Main entry point
- Comprehensive docstrings
- All 17+ role templates
- Full system prompt generation logic
- Async streaming with error handling
- Auto-run and manual mode support
- Session state management
- Four-tab interface
- Sidebar with metrics and tips

### **File 2: `log_viewer.py` (~400-450 lines)**
Complete log analysis tool including:
- LogParser class
- Multi-file loading
- Advanced filtering (persona, date, text search)
- Three search types (Contains, Exact, Regex)
- Statistics dashboard
- Persona breakdown with charts
- Three display modes (Chat, Table, Raw)
- Three export formats (CSV, JSON, TXT)
- Comprehensive docstrings

### **File 3: `pyproject.toml`**
UV dependency configuration

### **File 4: `README.md`**
Comprehensive documentation including:
- Project description with screenshot
- Feature list
- Quick start guide
- Prerequisites
- Installation steps
- Usage examples
- Role system explanation
- Technical details
- File structure
- Contributing guidelines

---

## ✨ SUCCESS CRITERIA

The generated code must:

✅ Run successfully on first execution with `uv run streamlit run streamlit_backroom.py`
✅ Connect to local Ollama API and discover models
✅ Create personas with all 17+ roles
✅ Execute infinite conversations with proper turn-taking
✅ Display streaming responses with thinking support
✅ Highlight @mentions with persona colors
✅ Save clean logs to daily text files
✅ Export sessions as JSON
✅ Run standalone log viewer with all filtering features
✅ Handle errors gracefully (connection failures, timeouts, cancellations)
✅ Provide excellent UX with clear feedback and loading states
✅ Support both auto-run and manual modes
✅ Maintain session state across reruns
✅ Display correct emoji avatars for all roles
✅ Format messages beautifully with colored badges

---

## 🧠 GEMINI 3.0 SPECIFIC INSTRUCTIONS

**Leverage Your Strengths:**
- Use your 1M token context to hold the entire project specification
- Apply your advanced reasoning to architect clean, maintainable code
- Utilize your multimodal understanding to visualize the UI flow
- Employ your state-of-the-art coding abilities to generate production-quality Python
- Use your multilingual performance to write excellent docstrings

**Coding Standards:**
- PEP 8 compliant formatting
- Type hints for all function signatures
- Comprehensive docstrings (Google style)
- Clear variable names
- Modular, reusable functions
- Proper async/await patterns
- Context managers for resource cleanup
- Defensive error handling
- No hardcoded magic numbers

**Code Organization:**
- Classes grouped logically
- Methods ordered by workflow
- Constants at module level
- Clear separation of concerns
- Minimal code duplication

**Testing Considerations:**
- Include default values that work out-of-box
- Graceful degradation when Ollama not available
- Clear error messages guiding users to solutions

---

## 🚨 CRITICAL REQUIREMENTS

1. **DO NOT TRUNCATE** - Generate complete files, not snippets
2. **PRODUCTION READY** - Code must run without modifications
3. **FEATURE COMPLETE** - All features must be fully implemented
4. **ERROR HANDLED** - All edge cases must be covered
5. **WELL DOCUMENTED** - Code and README must be comprehensive
6. **VISUALLY POLISHED** - UI must match the design specifications exactly

---

## 💡 FINAL NOTES

This is a complete, working application that real users will deploy and use to create fascinating AI-to-AI conversations. The code quality, user experience, and attention to detail should reflect production standards.

Generate code that you would be proud to show as an example of Gemini 3.0's capabilities.

Every feature listed above must be implemented. Every edge case must be handled. Every UI element must be polished.

**Now, create the complete Infinite AI Backrooms application from scratch.**

---

## 📊 ESTIMATED OUTPUT

- **Total Lines**: ~1,700 Python lines across 2 files
- **Classes**: 5 (AIPersona, ConversationLogger, OllamaClient, StreamlitBackroomApp, LogParser)
- **Methods**: 30+
- **Features**: 50+
- **Dependencies**: 3 (streamlit, aiohttp, pandas)

Ready? Begin generation! 🚀
