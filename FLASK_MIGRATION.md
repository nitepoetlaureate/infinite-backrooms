# Flask Migration - System.css Integration

## Overview

This migration moves Infinite Backrooms from Streamlit to Flask with **proper system.css integration**. The new implementation uses the actual system.css CDN stylesheet, giving full control over styling with the authentic retro Apple System OS aesthetic.

## Why Flask Instead of Streamlit?

**Problem with Streamlit:**
- Streamlit's rendering engine overrides custom CSS with its own theme
- Inline styles get stripped or overridden during HTML sanitization
- Impossible to achieve true system.css aesthetic within Streamlit's framework
- Fighting against the framework instead of working with it

**Benefits of Flask:**
- Full control over HTML/CSS rendering
- Direct system.css CDN integration (`https://unpkg.com/@sakun/system.css`)
- No framework CSS overrides or sanitization
- Real-time updates via Socket.IO
- Clean separation of backend (Flask) and frontend (HTML/JS)

## Architecture

### Backend (`app.py`)
- **Flask**: Web framework for routing and templates
- **Flask-SocketIO**: Real-time bidirectional communication
- **OllamaClient**: Async streaming chat generation
- **ConversationLogger**: Daily conversation logs
- **AIPersona**: Persona management with colors, roles, system prompts

### Frontend (`templates/`)
- **base.html**: Base template with system.css CDN integration
- **chat.html**: Chat interface with system.css components
- **Socket.IO client**: Real-time message streaming

### Design System
- **System.css via CDN**: Authentic retro Apple aesthetic
- **Design tokens**: Consistent spacing (1px, 2px, 4px, 8px)
- **Black borders**: All windows and components have 1px solid black borders
- **Minimal border-radius**: 2-3px maximum (system.css standard)
- **Chicago/Geneva fonts**: Proper retro typography
- **Monochrome + muted accents**: System 6 color palette

## Running the Flask App

### 1. Ensure Dependencies are Installed
```bash
uv sync
```

### 2. Start Ollama
Make sure Ollama is running on `http://localhost:11434`

### 3. Run Flask App
```bash
uv run python app.py
```

The app will start on `http://localhost:5000`

### 4. Open Browser
Navigate to `http://localhost:5000` to see the chat interface with proper system.css styling.

## Features

### Implemented
- ✅ Real-time chat streaming via Socket.IO
- ✅ Multiple AI personas with custom colors
- ✅ System.css CDN integration (authentic styling)
- ✅ Persona badges with black borders and minimal border-radius
- ✅ Daily conversation logging
- ✅ Enable/disable personas on the fly
- ✅ Proper retro Apple aesthetic (no Streamlit overrides!)

### UI Components (System.css)
- **Windows**: Black borders, white background, drop shadows
- **Title bars**: Chicago font, control buttons
- **Buttons**: Classic System OS button style
- **Messages**: Clean containers with proper spacing
- **Persona badges**:
  - Black borders (`1px solid #000000`)
  - Minimal border-radius (`2px`)
  - Chicago font
  - Bold white text on colored background
- **Status bar**: Fixed bottom bar with time display

## File Structure

```
infinite-backrooms/
├── app.py                      # Flask application
├── templates/
│   ├── base.html              # Base template with system.css CDN
│   └── chat.html              # Chat interface
├── static/
│   ├── css/                   # (Future: custom CSS overrides)
│   └── js/                    # (Future: additional JS modules)
├── ui_design_tokens.py        # Design tokens (still used for reference)
├── conversations/             # Daily conversation logs
└── FLASK_MIGRATION.md         # This file
```

## Key Differences from Streamlit Version

| Feature | Streamlit | Flask |
|---------|-----------|-------|
| Styling | Inline strings (overridden) | System.css CDN (native) |
| Real-time | st.rerun() polling | Socket.IO streaming |
| HTML Control | Limited (sanitized) | Full control |
| CSS Control | Fighting framework | Native integration |
| Border-radius | Overridden to 8px+ | Proper 2px |
| Borders | Removed by theme | Black 1px solid |
| Fonts | Streamlit defaults | Chicago/Geneva |
| Aesthetic | Modern/rounded | Retro/sharp |

## Validation

### Visual Checks
- ✅ Black borders on all windows
- ✅ 2px border-radius on persona badges
- ✅ Chicago font in title bars
- ✅ Geneva font in messages
- ✅ Proper drop shadows (2px 2px)
- ✅ White background on windows
- ✅ Gray (#c0c0c0) page background

### Functional Checks
- ✅ Socket.IO connects on page load
- ✅ Personas load in sidebar
- ✅ Click "Start Conversation" triggers chat
- ✅ Messages stream in real-time
- ✅ Persona badges show correct colors
- ✅ Enable/disable personas works
- ✅ Clear messages works

## Next Steps

### Future Enhancements
1. **Persona management UI**: Add/edit/delete personas
2. **Settings panel**: Configure Ollama URL, timeout, models
3. **Export conversations**: Download as TXT/JSON
4. **Theme customization**: Allow color scheme switching
5. **User input**: Let users inject messages into conversation
6. **Message threading**: Reply-based conversation structure
7. **Authentication**: Multi-user support

### Design System Expansion
1. Use more system.css components (dialogs, menus, tabs)
2. Add system.css form elements
3. Create reusable component library
4. Add transitions (optional - not traditional system.css)

## Troubleshooting

### Port Already in Use
If port 5000 is taken, edit `app.py` line 331:
```python
socketio.run(app, debug=True, host="0.0.0.0", port=5001)  # Changed to 5001
```

### Ollama Not Connected
Ensure Ollama is running:
```bash
ollama serve
```

### Socket.IO Not Connecting
Check browser console for errors. Try hard refresh (Cmd+Shift+R / Ctrl+Shift+R).

## Conclusion

This Flask migration solves the fundamental incompatibility between Streamlit and system.css. By using Flask with the actual system.css CDN, we now have:

1. **Authentic retro aesthetic** - No framework overrides
2. **Full styling control** - Black borders, minimal radius, proper fonts
3. **Real-time streaming** - Socket.IO instead of polling
4. **Maintainable code** - Clean separation of concerns
5. **System.css compliant** - Passes all visual standards

**The result**: A true System OS 1984-1991 aesthetic that "looks the way it should" - exactly what was requested.

---

**Migration Date**: 2025-11-21
**System.css Version**: Latest from unpkg CDN
**Flask Version**: 3.1.2
**Socket.IO Version**: 5.5.1
