"""First-run tutorial and onboarding for new users."""

import streamlit as st

from src.utils.html_sanitizer import secure_renderer


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

    # Show tutorial in a prominent container using secure HTML rendering
    tutorial_html = """
    <div style="background-color: #f0f8ff; padding: 20px; border-radius: 10px; border: 2px solid #4CAF50;">
        <h2 style="color: #2E7D32; margin-top: 0;">👋 Welcome to Infinite AI Backrooms!</h2>
    </div>
    """

    safe_tutorial_html = secure_renderer.render_with_fallback(
        tutorial_html,
        fallback_text="👋 Welcome to Infinite AI Backrooms!"
    )

    st.markdown(safe_tutorial_html, unsafe_allow_html=False)

    st.markdown(
        """
        ### 🚀 Quick Start Guide

        Follow these simple steps to create your first AI conversation:

        1. **📥 Add Personas**: Choose from preset personas or create your own custom AI personalities
        2. **⚙️ Configure Settings**: Adjust response timeout, context length, and other preferences
        3. **▶️ Start Conversation**: Enable personas and begin your AI dialogue
        4. **💬 Interact**: Add messages, watch AI personas respond, and explore different conversation dynamics

        ### 🎯 Key Features

        - **Multiple AI Personas**: Create diverse AI personalities with different roles and behaviors
        - **Real-time Conversation**: Watch AI personas interact with each other in real-time
        - **Customizable Prompts**: Fine-tune persona behavior with custom system prompts
        - **Conversation History**: Keep track of all your AI conversations
        - **@Mentions**: AI personas can reference and respond to each other using @mentions
        """
    )

    # Tutorial completion buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Got it!", type="primary"):
            st.session_state.tutorial_completed = True
            st.rerun()

    with col2:
        if st.button("⏭️ Skip for now"):
            st.session_state.tutorial_completed = True
            st.rerun()

    st.markdown("---")
    st.markdown(
        """
        💡 **Pro Tip**: You can always access this tutorial again from the settings menu or by clearing your browser data.
        """
    )

    return True


def show_feature_highlights():
    """Show feature highlights for returning users."""
    highlights_html = """
    <div style="background-color: #fff3cd; padding: 15px; border-radius: 8px; border: 1px solid #ffeaa7; margin: 10px 0;">
        <h4 style="color: #856404; margin-top: 0;">✨ New Features</h4>
        <ul style="color: #856404;">
            <li>Enhanced AI conversation quality</li>
            <li>Improved persona management</li>
            <li>Better conversation history tracking</li>
        </ul>
    </div>
    """

    safe_highlights = secure_renderer.render_with_fallback(
        highlights_html,
        fallback_text="✨ New Features: Enhanced AI conversation, improved personas, better history tracking"
    )

    st.markdown(safe_highlights, unsafe_allow_html=False)


def reset_tutorial():
    """Reset the tutorial completion status."""
    if "tutorial_completed" in st.session_state:
        st.session_state.tutorial_completed = False