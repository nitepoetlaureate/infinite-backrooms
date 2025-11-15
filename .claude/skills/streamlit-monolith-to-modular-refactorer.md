# streamlit-monolith-to-modular-refactorer

**Purpose**: Refactor monolithic Streamlit applications into clean modular architecture

**Use When**: Main application file >300 lines, poor separation of concerns, difficult to test

---

## Domain Knowledge

### SOLID Principles for Python
- Single Responsibility: One class, one purpose
- Open/Closed: Open for extension, closed for modification
- Liskov Substitution: Subtypes must be substitutable
- Interface Segregation: Many specific interfaces > one general
- Dependency Inversion: Depend on abstractions

### Streamlit Architecture Patterns
- Service layer for business logic
- UI components for rendering
- State management for session data
- Clear boundaries between layers

### Module Organization
```
src/
├── services/      # Business logic, API clients
├── ui/            # Streamlit UI components
├── state/         # Session state management
├── models/        # Data models
└── utils/         # Shared utilities
```

---

## Workflow

### Step 1: Analyze Monolithic File (45-60 min)

**Identify Module Boundaries**:
1. **Service Layer** - Business logic, external APIs
2. **UI Layer** - Streamlit rendering, user interaction
3. **State Layer** - Session state, data management
4. **Orchestration** - Main app coordination

**Analysis Pattern**:
```bash
# Count lines
wc -l streamlit_backroom.py

# Find large functions
grep -n "^def " streamlit_backroom.py | while read line; do
  # Analyze function sizes
done

# Identify responsibilities
grep -E "st\.|async|class" streamlit_backroom.py
```

### Step 2: Extract ConversationOrchestrator (2-3 hours)

**Create**: `src/services/conversation_orchestrator.py`

```python
"""Conversation orchestration and management."""

from typing import AsyncGenerator, Optional
import logging

from src.models.persona import AIPersona
from src.services.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class ConversationOrchestrator:
    """Orchestrates multi-persona conversations."""

    def __init__(self, client: OllamaClient):
        """Initialize orchestrator."""
        self.client = client

    async def execute_turn(
        self,
        persona: AIPersona,
        conversation_history: list[dict],
        other_personas: list[AIPersona],
        think: bool = False
    ) -> AsyncGenerator[dict, None]:
        """Execute a single conversation turn."""
        system_prompt = self.generate_system_prompt(persona, other_personas)
        user_prompt = self.build_context_prompt(conversation_history)

        try:
            async for chunk in self.client.generate_stream(
                model=persona.model,
                prompt=user_prompt,
                system_prompt=system_prompt,
                think=think
            ):
                yield chunk
        except Exception as e:
            logger.error(f"Turn execution failed for {persona.name}: {e}")
            raise

    def generate_system_prompt(
        self,
        persona: AIPersona,
        other_personas: list[AIPersona]
    ) -> str:
        """Generate system prompt for persona."""
        others_desc = "\\n".join([
            f"- {p.name}: {p.description}" for p in other_personas
        ])

        return f"""You are {persona.name}.

{persona.description}

You are in a conversation with:
{others_desc}

Stay in character. Respond naturally."""

    def build_context_prompt(
        self,
        conversation_history: list[dict],
        max_context: int = 10
    ) -> str:
        """Build conversation context prompt."""
        recent = conversation_history[-max_context:]
        lines = [f"{msg['speaker']}: {msg['content']}" for msg in recent]
        return "\\n".join(lines)
```

**Actions**:
- Extract all conversation logic
- Add comprehensive docstrings
- Add type hints
- Test independently

### Step 3: Extract UI Components (2-3 hours)

**Create**: `src/ui/conversation_display.py`

```python
"""Conversation display UI components."""

import streamlit as st
from typing import Optional
from src.models.persona import AIPersona


class ConversationDisplay:
    """Handles conversation UI display."""

    def render_messages(
        self,
        messages: list[dict],
        personas: list[AIPersona]
    ) -> None:
        """Render all conversation messages."""
        persona_map = {p.name: p for p in personas}

        for msg in messages:
            self.render_single_message(msg, persona_map)

    def render_single_message(
        self,
        message: dict,
        persona_map: dict[str, AIPersona]
    ) -> None:
        """Render a single message."""
        speaker = message.get("speaker", "Unknown")
        content = message.get("content", "")
        persona = persona_map.get(speaker)

        if persona:
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(f"**{persona.name}**")
                st.markdown(content)
        else:
            with st.chat_message("user", avatar="👤"):
                st.markdown(f"**{speaker}**")
                st.markdown(content)

    def render_message_input(self) -> Optional[str]:
        """Render and handle message input."""
        with st.form(key="message_form", clear_on_submit=True):
            message = st.text_area(
                "Your message:",
                height=100,
                placeholder="Type your message..."
            )
            submitted = st.form_submit_button("Send")

            if submitted and message.strip():
                return message.strip()

        return None
```

**Create**: `src/ui/persona_manager.py`

```python
"""Persona management UI components."""

import streamlit as st
from typing import Optional
from src.models.persona import AIPersona


class PersonaManager:
    """Handles persona management UI."""

    def render_persona_list(self, personas: list[AIPersona]) -> None:
        """Render list of personas."""
        if not personas:
            st.info("No personas yet. Create one to get started!")
            return

        for persona in personas:
            with st.expander(f"🤖 {persona.name}", expanded=False):
                st.markdown(f"**Model:** {persona.model}")
                st.markdown(f"**Description:**")
                st.text(persona.description)

    def render_add_persona_form(
        self,
        available_models: list[str]
    ) -> Optional[AIPersona]:
        """Render persona creation form."""
        with st.form(key="add_persona_form"):
            st.subheader("Create New Persona")

            name = st.text_input("Name", placeholder="e.g., Dr. Smith")
            model = st.selectbox("Model", options=available_models)
            description = st.text_area(
                "Description",
                placeholder="Describe the persona...",
                height=150
            )

            submitted = st.form_submit_button("Create Persona")

            if submitted and name and description:
                return AIPersona(
                    name=name,
                    model=model,
                    description=description
                )

        return None
```

### Step 4: Extract SessionManager (1-2 hours)

**Create**: `src/state/session_manager.py`

```python
"""Session state management."""

import streamlit as st
from typing import Any
from src.models.persona import AIPersona


class SessionManager:
    """Manages Streamlit session state."""

    @staticmethod
    def initialize() -> None:
        """Initialize all session state variables."""
        defaults = {
            "personas": [],
            "messages": [],
            "conversation_active": False,
            "current_turn": 0,
            "ollama_connected": False,
            "available_models": []
        }

        for key, default in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default

    @staticmethod
    def get_personas() -> list[AIPersona]:
        """Get list of personas."""
        return st.session_state.get("personas", [])

    @staticmethod
    def add_persona(persona: AIPersona) -> None:
        """Add a persona."""
        personas = SessionManager.get_personas()
        personas.append(persona)
        st.session_state.personas = personas

    @staticmethod
    def get_messages() -> list[dict]:
        """Get conversation messages."""
        return st.session_state.get("messages", [])

    @staticmethod
    def add_message(speaker: str, content: str) -> None:
        """Add a message."""
        messages = SessionManager.get_messages()
        messages.append({"speaker": speaker, "content": content})
        st.session_state.messages = messages

    @staticmethod
    def clear_conversation() -> None:
        """Clear all conversation data."""
        st.session_state.messages = []
        st.session_state.conversation_active = False
```

### Step 5: Refactor Main App (2-3 hours)

**Update**: `streamlit_backroom.py` (Target: <300 lines)

```python
"""AI Backroom - Multi-Persona Conversations."""

import streamlit as st
from src.services.ollama_client import OllamaClient
from src.services.conversation_orchestrator import ConversationOrchestrator
from src.ui.conversation_display import ConversationDisplay
from src.ui.persona_manager import PersonaManager
from src.state.session_manager import SessionManager

# Must be first Streamlit command
st.set_page_config(
    page_title="AI Backroom",
    page_icon="🤖",
    layout="wide"
)


@st.experimental_singleton
def get_ollama_client() -> OllamaClient:
    """Get singleton Ollama client."""
    return OllamaClient()


class StreamlitBackroomApp:
    """Main application class."""

    def __init__(self):
        """Initialize application components."""
        self.session = SessionManager()
        self.client = get_ollama_client()
        self.orchestrator = ConversationOrchestrator(self.client)
        self.ui = ConversationDisplay()
        self.persona_ui = PersonaManager()

    def run(self) -> None:
        """Main application entry point."""
        self.session.initialize()
        self._render_header()

        if self._check_ollama_connection():
            self._render_main_interface()
        else:
            st.error("Cannot connect to Ollama.")

    def _render_header(self) -> None:
        """Render application header."""
        st.title("🤖 AI Backroom")

    def _check_ollama_connection(self) -> bool:
        """Check Ollama connection."""
        # Implementation
        return True

    def _render_main_interface(self) -> None:
        """Render main interface."""
        tab1, tab2 = st.tabs(["💬 Conversation", "👥 Personas"])

        with tab1:
            self._render_conversation_tab()

        with tab2:
            self._render_personas_tab()

    def _render_conversation_tab(self) -> None:
        """Render conversation interface."""
        messages = self.session.get_messages()
        personas = self.session.get_personas()

        self.ui.render_messages(messages, personas)

        user_message = self.ui.render_message_input()
        if user_message:
            self.session.add_message("User", user_message)
            st.rerun()

    def _render_personas_tab(self) -> None:
        """Render persona management."""
        personas = self.session.get_personas()
        models = st.session_state.get("available_models", [])

        self.persona_ui.render_persona_list(personas)

        new_persona = self.persona_ui.render_add_persona_form(models)
        if new_persona:
            self.session.add_persona(new_persona)
            st.rerun()


def main():
    """Application entry point."""
    app = StreamlitBackroomApp()
    app.run()


if __name__ == "__main__":
    main()
```

### Step 6: Test Each Module (2-3 hours)

**Test Independently**:
```bash
# Test ConversationOrchestrator
pytest tests/test_conversation_orchestrator.py -v

# Test UI components
pytest tests/test_conversation_display.py -v

# Test SessionManager
pytest tests/test_session_manager.py -v

# Test integration
pytest -v
```

---

## Best Practices

### Module Design
1. Single Responsibility per module
2. Clear, focused interfaces
3. Minimal dependencies
4. Testable in isolation

### Incremental Refactoring
1. Extract one module at a time
2. Test after each extraction
3. Commit working changes
4. Don't refactor everything at once

### Code Organization
1. Group related functionality
2. Consistent naming conventions
3. Clear directory structure
4. Proper __init__.py files

---

## Success Criteria

- [ ] Main file <300 lines
- [ ] ConversationOrchestrator extracted
- [ ] UI components extracted
- [ ] SessionManager extracted
- [ ] All modules tested independently
- [ ] Integration tests pass
- [ ] Clear separation of concerns
- [ ] All functions <50 lines

---

## Tools Available
- Read, Write, Edit, MultiEdit
- Grep, Glob for finding code
- Bash for testing

---

## Validation Commands

```bash
# Count main file lines
wc -l streamlit_backroom.py

# Check module structure
ls -la src/services/ src/ui/ src/state/

# Run tests
pytest -v

# Check imports
python -c "from src.services.conversation_orchestrator import ConversationOrchestrator"
```
