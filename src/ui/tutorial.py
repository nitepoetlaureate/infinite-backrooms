"""First-run tutorial module for guiding new users.

This module provides an interactive tutorial overlay that guides users through
the key features of the Infinite Backrooms application on their first visit.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from streamlit.runtime.state import SessionStateProxy


def show_tutorial(session_state: SessionStateProxy) -> None:
    """Display first-run tutorial overlay.

    Args:
        session_state: Streamlit session state object
    """
    import streamlit as st

    # Initialize tutorial state if needed
    if "tutorial_completed" not in session_state:
        session_state.tutorial_completed = False
    if "tutorial_step" not in session_state:
        session_state.tutorial_step = 0

    # Don't show if completed
    if session_state.tutorial_completed:
        return

    # Tutorial content for each step
    tutorial_steps = [
        {
            "title": "👋 Welcome to Infinite AI Backrooms!",
            "content": """
### What is this?

Infinite Backrooms lets you create **multiple AI personas** with different personalities
and roles, then watch them have **autonomous conversations** with each other!

**Key Features:**
- 🤖 Create unlimited AI personas with unique roles
- 💬 Watch AI-to-AI conversations unfold
- 🎭 17 predefined personality roles to choose from
- 📊 Full conversation logging and export

Ready to get started?
            """,
            "button_text": "Let's Go! →",
        },
        {
            "title": "🤖 Step 1: Create Your First Personas",
            "content": """
### Get Started Quickly

You have two options:

**Option A: Quick Start (Recommended)**
1. Go to the **Personas** tab
2. Click **"🔄 Check Ollama Connection"** to load available models
3. Click one of the preset buttons:
   - **"🎭 Add Diverse Conversation Set"** - Varied personalities
   - **"📋 Add Structured Discussion Set"** - Organized roles

**Option B: Create Custom Personas**
1. Go to the **Personas** tab
2. Fill in the persona name and select a model
3. Choose a role (Explorer, Analyst, Creative, etc.)
4. Click **"➕ Add Persona"**

**Tip:** Start with 3-5 personas for best results!
            """,
            "button_text": "Next: Start Conversations →",
        },
        {
            "title": "💬 Step 2: Start the Conversation",
            "content": """
### Let the AI Talk!

Once you have personas:

1. Go to the **Conversation** tab
2. Click **"▶️ Start Conversation"** for auto-run mode
   - AI personas will take turns automatically
   - Controlled by delay settings (2-8 seconds between responses)

**Or use manual control:**
- Click **"🔄 Next Turn"** to advance one turn at a time
- Type a message in the chat input to join the conversation

**Useful Features:**
- **@mentions**: Personas can address each other (e.g., @Einstein)
- **Pause button**: Stop auto-run at any time
- **Clear history**: Start fresh conversations

**Pagination:** For conversations with 50+ messages, use navigation controls to browse
            """,
            "button_text": "Next: Settings & Export →",
        },
        {
            "title": "⚙️ Step 3: Customize & Export",
            "content": """
### Fine-Tune Your Experience

**Settings Tab:**
- Adjust conversation history size (1-50 messages)
- Configure response delays for auto-run
- Enable/disable thinking mode for compatible models
- Set response timeouts

**Export & Logs Tab:**
- **Download Session JSON**: Export full conversation data
- **View Daily Logs**: See conversation history
- **Download Logs**: Save conversations as text files

**Tips:**
- Conversations are automatically logged daily
- Use thinking mode with **deepseek-r1** for AI reasoning insights
- Experiment with different roles for varied conversations!
            """,
            "button_text": "Start Exploring! 🚀",
        },
    ]

    current_step = session_state.tutorial_step
    step_data = tutorial_steps[current_step]
    total_steps = len(tutorial_steps)

    # Create tutorial overlay container
    with st.container():
        st.markdown("---")
        st.markdown(
            f"### 📚 Tutorial ({current_step + 1}/{total_steps})"
        )

        # Display current step
        st.markdown(f"## {step_data['title']}")
        st.markdown(step_data["content"])

        # Navigation buttons
        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            if current_step > 0:
                if st.button("← Back", key="tutorial_back"):
                    session_state.tutorial_step -= 1
                    st.rerun()

        with col2:
            # Progress indicator
            progress = (current_step + 1) / total_steps
            st.progress(progress)
            st.caption(f"Step {current_step + 1} of {total_steps}")

        with col3:
            if current_step < total_steps - 1:
                if st.button(step_data["button_text"], key="tutorial_next", type="primary"):
                    session_state.tutorial_step += 1
                    st.rerun()
            else:
                if st.button(step_data["button_text"], key="tutorial_finish", type="primary"):
                    session_state.tutorial_completed = True
                    st.success("🎉 Tutorial completed! Enjoy Infinite Backrooms!")
                    st.rerun()

        # Skip option
        st.markdown("---")
        if st.button("⏭️ Skip Tutorial", key="tutorial_skip"):
            session_state.tutorial_completed = True
            session_state.tutorial_step = 0
            st.rerun()

        st.markdown("---")


def reset_tutorial(session_state: SessionStateProxy) -> None:
    """Reset tutorial to beginning.

    Args:
        session_state: Streamlit session state object
    """
    session_state.tutorial_completed = False
    session_state.tutorial_step = 0
