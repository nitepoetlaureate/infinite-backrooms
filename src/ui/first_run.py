"""First-run tutorial and onboarding for new users."""

import streamlit as st


def show_first_run_tutorial() -> bool:
    """Show first-run tutorial to new users.

    Returns:
        True if tutorial was shown and completed, False if skipped or already seen
    """
    # Check if user has already seen the tutorial
    if "tutorial_completed" not in st.session_state:
        st.session_state.tutorial_completed = False

    if st.session_state.tutorial_completed:
        return False

    # Show tutorial in a prominent container
    with st.container():
        st.markdown(
            """
            <div style="background-color: #f0f8ff; padding: 20px; border-radius: 10px; border: 2px solid #4CAF50;">
                <h2 style="color: #2E7D32; margin-top: 0;">👋 Welcome to Infinite AI Backrooms!</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            ### 🚀 Quick Start Guide

            Follow these simple steps to create your first AI conversation:

            #### **Step 1: Connect to Ollama** 🔌
            - Go to the **🤖 Personas** tab
            - Click **"🔄 Check Ollama Connection"**
            - Make sure Ollama is running locally
            - Verify that at least one model is available

            #### **Step 2: Create AI Personas** 🎭
            - Still in the **Personas** tab
            - Fill out the persona form:
              - Choose a name (e.g., "Socrates", "Einstein")
              - Select a model from the dropdown
              - Pick a role (Philosopher, Scientist, Creative, etc.)
              - Optionally add custom instructions
            - Click **"➕ Add Persona"**
            - Repeat to create 2-3 personas

            **💡 Pro Tip:** Use the quick start buttons:
            - **"🎭 Add Diverse Conversation Set"** for varied perspectives
            - **"📋 Add Structured Discussion Set"** for focused discussions

            #### **Step 3: Start Conversing** 💬
            - Switch to the **💬 Conversation** tab
            - Click **"▶️ Start Conversation"** for auto-run mode
            - Or click **"🔄 Next Turn"** for manual control
            - Watch your AI personas interact!

            #### **Step 4: Customize & Explore** ⚙️
            - Visit **⚙️ Settings** to adjust:
              - Context window size
              - Response timeouts
              - Auto-advance settings
            - Check **📁 Export & Logs** to:
              - Export conversations as JSON
              - View daily log files
              - See conversation statistics

            ---

            ### 🎯 Key Features

            - **@Mentions**: AI personas can address each other directly (e.g., "@Socrates")
            - **Roles**: Choose from 18+ predefined roles or create custom ones
            - **Thinking Mode**: Enable to see AI reasoning (requires compatible models)
            - **Auto-Run**: Let personas converse autonomously
            - **Manual Mode**: Control each turn for guided discussions

            ---

            ### 💡 Tips for Great Conversations

            - **Mix roles**: Combine different personality types for richer discussions
            - **Use @mentions**: Encourage direct dialogue between specific personas
            - **Adjust context**: More context = more coherent, but slower
            - **Try different models**: Each model has unique characteristics

            ---

            ### ⚠️ Troubleshooting

            **Ollama not connecting?**
            - Make sure Ollama is installed and running: `ollama serve`
            - Verify models are available: `ollama list`
            - Check URL is correct: `http://localhost:11434`

            **Responses timing out?**
            - Increase timeout in Settings
            - Check your model is downloaded: `ollama pull <model-name>`

            **Need help?**
            - Check the sidebar for quick tips
            - Review the README.md for detailed documentation
            - Visit the GitHub repository for issues and discussions

            ---
            """
        )

        col1, col2 = st.columns([3, 1])

        with col1:
            st.success("✨ Ready to create your first AI conversation?")

        with col2:
            if st.button("🎉 Got it! Let's start", type="primary", use_container_width=True):
                st.session_state.tutorial_completed = True
                st.rerun()

        return True

    return False


def show_welcome_message() -> None:
    """Show a brief welcome message for new users (alternative to full tutorial)."""
    if not st.session_state.get("welcome_dismissed", False):
        with st.container():
            st.info(
                """
                👋 **Welcome to AI Backrooms!**

                **Get started in 3 steps:**
                1. Go to **Personas** tab → Check Ollama connection
                2. Add 2-3 personas with different roles
                3. Return to **Conversation** → Click **Start Conversation**

                Need more help? Click below for the full tutorial.
                """,
                icon="ℹ️",
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("📖 Show Full Tutorial"):
                    st.session_state.tutorial_completed = False
                    st.rerun()
            with col2:
                if st.button("✅ Dismiss"):
                    st.session_state.welcome_dismissed = True
                    st.rerun()


def show_auto_run_warning(max_turns: int = 50) -> bool:
    """Show warning before starting auto-run mode.

    Args:
        max_turns: Default maximum number of turns

    Returns:
        True if user confirmed, False otherwise
    """
    if "auto_run_confirmed" not in st.session_state:
        st.session_state.auto_run_confirmed = False

    if st.session_state.auto_run_confirmed:
        return True

    with st.container():
        st.warning(
            """
            ⚠️ **Auto-Run Mode Safety Notice**

            You're about to start auto-run mode. This will:
            - ✅ Generate AI responses automatically
            - ⏱️ Continue until you click **Pause**
            - 🔄 Consume system resources and Ollama inference time
            - 📊 Create many messages quickly

            **You can stop at any time** by clicking the **"⏸️ Pause"** button.
            """,
            icon="⚠️",
        )

        col1, col2 = st.columns([2, 1])

        with col1:
            max_turns_input = st.number_input(
                "Maximum turns (0 = unlimited)",
                min_value=0,
                max_value=1000,
                value=max_turns,
                step=10,
                help="Limit auto-run to a maximum number of turns for safety",
            )
            st.session_state.max_auto_turns = max_turns_input

        with col2:
            st.metric("Max Turns", "Unlimited" if max_turns_input == 0 else max_turns_input)

        col_confirm, col_cancel = st.columns(2)

        with col_confirm:
            if st.button("✅ Start Auto-Run", type="primary", use_container_width=True):
                st.session_state.auto_run_confirmed = True
                return True

        with col_cancel:
            if st.button("❌ Cancel", use_container_width=True):
                return False

    return False


def reset_auto_run_confirmation() -> None:
    """Reset auto-run confirmation (call this when stopping auto-run)."""
    st.session_state.auto_run_confirmed = False


def show_keyboard_shortcuts_help() -> None:
    """Display keyboard shortcuts help."""
    with st.expander("⌨️ Keyboard Shortcuts", expanded=False):
        st.markdown(
            """
            ### Available Shortcuts

            | Shortcut | Action |
            |----------|--------|
            | `Ctrl+Enter` | Send chat message |
            | `Tab` | Navigate between fields |
            | `Esc` | Close dialogs/expanders |

            ### Tips
            - Use tab navigation to quickly move through forms
            - Most buttons can be activated with `Enter` when focused
            - Use the sidebar for quick status overview
            """
        )
