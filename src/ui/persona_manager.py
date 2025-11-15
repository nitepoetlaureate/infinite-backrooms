"""Persona Management UI components for Streamlit interface.

Handles all persona creation, editing, and management UI components
with proper separation from business logic and state management.
"""

from __future__ import annotations

import streamlit as st
from typing import List, Optional

from src.models.persona import AIPersona
from src.state.session_manager import SecureSessionManager
from src.ui.components import (
    get_persona_avatar,
    highlight_mentions,
    render_persona_header,
    render_persona_list_item,
)


class PersonaManager:
    """UI manager for persona management interface.

    Handles all Streamlit UI rendering for persona CRUD operations
    while keeping business logic separate.

    Attributes:
        session_manager: Session state manager
    """

    def __init__(self, session_manager: SecureSessionManager) -> None:
        """Initialize the persona manager UI.

        Args:
            session_manager: Session state manager for persona data
        """
        self.session_manager = session_manager

    def render_persona_management_interface(self) -> None:
        """Render the complete persona management interface."""
        st.header("🤖 AI Persona Management")

        # Create two columns for persona list and creation form
        col1, col2 = st.columns([2, 1])

        with col1:
            self._render_persona_list()

        with col2:
            self._render_persona_creation_form()

        st.divider()
        self._render_bulk_operations()

    def _render_persona_list(self) -> None:
        """Render the list of existing personas."""
        personas = self.session_manager.get_personas()

        if not personas:
            st.info("No personas created yet. Create your first persona using the form!")
            return

        st.subheader("📋 Your AI Personas")

        # Filter controls
        with st.expander("🔍 Filter Personas", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                show_enabled = st.checkbox("Show Enabled", value=True)
            with col2:
                show_disabled = st.checkbox("Show Disabled", value=True)
            with col3:
                sort_order = st.selectbox("Sort Order", ["Name", "Created", "Model"])

        # Filter and sort personas
        filtered_personas = self._filter_personas(personas, show_enabled, show_disabled)
        sorted_personas = self._sort_personas(filtered_personas, sort_order)

        # Render personas
        for i, persona in enumerate(sorted_personas):
            with st.expander(f"🤖 {persona.name}", expanded=i == 0):
                self._render_persona_details(persona)
                self._render_persona_controls(persona)

    def _render_persona_details(self, persona: AIPersona) -> None:
        """Render detailed information about a persona.

        Args:
            persona: Persona to display details for
        """
        col1, col2 = st.columns([1, 3])

        with col1:
            # Avatar and basic info
            avatar = get_persona_avatar(persona)
            st.markdown(avatar)

            st.markdown(f"**Model:** `{persona.model}`")

            if persona.role:
                st.markdown(f"**Role:** `{persona.role}`")

            status = "✅ Enabled" if persona.enabled else "❌ Disabled"
            st.markdown(f"**Status:** {status}")

        with col2:
            # Description and system prompt
            if persona.description:
                st.markdown("**Description:**")
                st.markdown(persona.description)

            if persona.system_prompt:
                with st.expander("🧠 System Prompt", expanded=False):
                    st.code(persona.system_prompt, language="text")

    def _render_persona_controls(self, persona: AIPersona) -> None:
        """Render control buttons for a persona.

        Args:
            persona: Persona to render controls for
        """
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button(f"✏️ Edit", key=f"edit_{persona.name}", use_container_width=True):
                st.session_state[f"editing_persona_{persona.name}"] = True

        with col2:
            toggle_text = "🔇 Disable" if persona.enabled else "🔊 Enable"
            if st.button(
                toggle_text,
                key=f"toggle_{persona.name}",
                use_container_width=True
            ):
                self._toggle_persona_status(persona)

        with col3:
            if st.button(f"📋 Copy", key=f"copy_{persona.name}", use_container_width=True):
                self._copy_persona(persona)

        with col4:
            if st.button(
                f"🗑️ Delete",
                key=f"delete_{persona.name}",
                use_container_width=True,
                type="secondary"
            ):
                self._delete_persona(persona)

        # Edit form (shown when editing)
        if st.session_state.get(f"editing_persona_{persona.name}", False):
            self._render_edit_form(persona)

    def _render_persona_creation_form(self) -> None:
        """Render the persona creation form."""
        st.subheader("➕ Create New Persona")

        available_models = self.session_manager.get_available_models()
        if not available_models:
            st.warning("⚠️ No models available. Please connect to Ollama first.")
            return

        with st.form(key="create_persona_form"):
            # Basic information
            name = st.text_input(
                "🏷️ Name *",
                placeholder="e.g., Dr. Sarah Chen",
                help="Unique name for this AI persona"
            )

            model = st.selectbox(
                "🧠 Model *",
                options=available_models,
                help="AI model to use for this persona"
            )

            role = st.selectbox(
                "👤 Role",
                options=["", "Moderator", "Note-Taker", "Expert", "Creative", "Analyst"],
                help="Predefined role with specific behavior patterns"
            )

            description = st.text_area(
                "📝 Description *",
                placeholder="Describe the persona's personality, background, and expertise...",
                height=120,
                help="What makes this persona unique? How should they behave?"
            )

            system_prompt = st.text_area(
                "⚙️ System Prompt (Optional)",
                placeholder="Additional instructions for the AI...",
                height=100,
                help="Custom instructions that override or supplement the role-based behavior"
            )

            # Advanced settings
            with st.expander("🔧 Advanced Settings", expanded=False):
                thinking_enabled = st.checkbox(
                    "🧠 Enable Thinking Mode",
                    value=True,
                    help="Show AI's reasoning process (works with compatible models)"
                )

                auto_enabled = st.checkbox(
                    "🔄 Enable for Auto-Conversation",
                    value=True,
                    help="Include this persona in automatic conversation rotation"
                )

            # Submit button
            submitted = st.form_submit_button("✨ Create Persona", use_container_width=True)

            if submitted:
                self._create_persona(
                    name=name,
                    model=model,
                    role=role,
                    description=description,
                    system_prompt=system_prompt,
                    thinking_enabled=thinking_enabled,
                    enabled=auto_enabled
                )

    def _render_edit_form(self, persona: AIPersona) -> None:
        """Render the persona editing form.

        Args:
            persona: Persona being edited
        """
        st.markdown("---")
        st.markdown(f"**✏️ Editing: {persona.name}**")

        with st.form(key=f"edit_persona_form_{persona.name}"):
            # Editable fields
            name = st.text_input("🏷️ Name", value=persona.name)
            model = st.selectbox(
                "🧠 Model",
                options=self.session_manager.get_available_models(),
                index=self.session_manager.get_available_models().index(persona.model) if persona.model in self.session_manager.get_available_models() else 0
            )
            role = st.selectbox(
                "👤 Role",
                options=["", "Moderator", "Note-Taker", "Expert", "Creative", "Analyst"],
                index=["", "Moderator", "Note-Taker", "Expert", "Creative", "Analyst"].index(persona.role) if persona.role in ["", "Moderator", "Note-Taker", "Expert", "Creative", "Analyst"] else 0
            )
            description = st.text_area("📝 Description", value=persona.description, height=120)
            system_prompt = st.text_area("⚙️ System Prompt", value=persona.system_prompt, height=100)

            # Advanced settings
            thinking_enabled = st.checkbox("🧠 Enable Thinking Mode", value=persona.thinking_enabled)
            enabled = st.checkbox("🔄 Enable for Auto-Conversation", value=persona.enabled)

            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("💾 Save Changes", use_container_width=True)
            with col2:
                cancelled = st.form_submit_button("❌ Cancel", use_container_width=True)

            if submitted:
                self._update_persona(persona, name, model, role, description, system_prompt, thinking_enabled, enabled)
            elif cancelled:
                st.session_state[f"editing_persona_{persona.name}"] = False
                st.rerun()

    def _render_bulk_operations(self) -> None:
        """Render bulk operations for persona management."""
        personas = self.session_manager.get_personas()

        if not personas:
            return

        st.subheader("⚡ Bulk Operations")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("🔊 Enable All", use_container_width=True):
                self._bulk_enable_disable_all(True)

        with col2:
            if st.button("🔇 Disable All", use_container_width=True):
                self._bulk_enable_disable_all(False)

        with col3:
            if st.button("🗑️ Delete All", use_container_width=True, type="secondary"):
                st.session_state.show_delete_all_confirm = True

        with col4:
            if st.button("📥 Export All", use_container_width=True):
                self._export_all_personas()

        # Delete all confirmation
        if st.session_state.get("show_delete_all_confirm", False):
            st.error("⚠️ **WARNING**: This will delete ALL personas and cannot be undone!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Yes, Delete All", type="primary"):
                    self._delete_all_personas()
            with col2:
                if st.button("❌ Cancel"):
                    st.session_state.show_delete_all_confirm = False
                    st.rerun()

    def _filter_personas(
        self,
        personas: List[AIPersona],
        show_enabled: bool,
        show_disabled: bool
    ) -> List[AIPersona]:
        """Filter personas based on status.

        Args:
            personas: List of all personas
            show_enabled: Whether to show enabled personas
            show_disabled: Whether to show disabled personas

        Returns:
            Filtered list of personas
        """
        filtered = []
        for persona in personas:
            if persona.enabled and show_enabled:
                filtered.append(persona)
            elif not persona.enabled and show_disabled:
                filtered.append(persona)
        return filtered

    def _sort_personas(self, personas: List[AIPersona], sort_order: str) -> List[AIPersona]:
        """Sort personas by specified criteria.

        Args:
            personas: List of personas to sort
            sort_order: Sort criteria ("Name", "Created", "Model")

        Returns:
            Sorted list of personas
        """
        if sort_order == "Name":
            return sorted(personas, key=lambda p: p.name.lower())
        elif sort_order == "Model":
            return sorted(personas, key=lambda p: p.model.lower())
        elif sort_order == "Created":
            # Note: This would require creation timestamp tracking
            return personas  # Placeholder - would need timestamp in persona model
        return personas

    def _toggle_persona_status(self, persona: AIPersona) -> None:
        """Toggle enabled/disabled status of a persona.

        Args:
            persona: Persona to toggle
        """
        updated_persona = AIPersona(
            name=persona.name,
            model=persona.model,
            description=persona.description,
            role=persona.role,
            system_prompt=persona.system_prompt,
            thinking_enabled=persona.thinking_enabled,
            enabled=not persona.enabled
        )
        self.session_manager.update_persona(persona.name, updated_persona)
        st.success(f"✅ {'Enabled' if updated_persona.enabled else 'Disabled'} {persona.name}")
        st.rerun()

    def _copy_persona(self, persona: AIPersona) -> None:
        """Create a copy of a persona.

        Args:
            persona: Persona to copy
        """
        new_name = f"{persona.name} (Copy)"
        new_persona = AIPersona(
            name=new_name,
            model=persona.model,
            description=persona.description,
            role=persona.role,
            system_prompt=persona.system_prompt,
            thinking_enabled=persona.thinking_enabled,
            enabled=False  # Start disabled to avoid conflicts
        )
        self.session_manager.add_persona(new_persona)
        st.success(f"✅ Created copy: {new_name}")
        st.rerun()

    def _delete_persona(self, persona: AIPersona) -> None:
        """Delete a persona.

        Args:
            persona: Persona to delete
        """
        self.session_manager.remove_persona(persona.name)
        st.success(f"🗑️ Deleted {persona.name}")
        st.rerun()

    def _create_persona(
        self,
        name: str,
        model: str,
        role: str,
        description: str,
        system_prompt: str,
        thinking_enabled: bool,
        enabled: bool
    ) -> None:
        """Create a new persona.

        Args:
            name: Persona name
            model: AI model to use
            role: Persona role
            description: Persona description
            system_prompt: Custom system prompt
            thinking_enabled: Whether thinking mode is enabled
            enabled: Whether persona is enabled for conversations
        """
        # Validation
        if not name.strip():
            st.error("❌ Name is required")
            return
        if not description.strip():
            st.error("❌ Description is required")
            return

        # Check for duplicate names
        existing_names = [p.name.lower() for p in self.session_manager.get_personas()]
        if name.strip().lower() in existing_names:
            st.error(f"❌ Persona '{name}' already exists")
            return

        # Create persona
        persona = AIPersona(
            name=name.strip(),
            model=model,
            description=description.strip(),
            role=role.strip() if role else "",
            system_prompt=system_prompt.strip(),
            thinking_enabled=thinking_enabled,
            enabled=enabled
        )

        try:
            self.session_manager.add_persona(persona)
            st.success(f"✅ Created persona: {persona.name}")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Failed to create persona: {str(e)}")

    def _update_persona(
        self,
        original_persona: AIPersona,
        name: str,
        model: str,
        role: str,
        description: str,
        system_prompt: str,
        thinking_enabled: bool,
        enabled: bool
    ) -> None:
        """Update an existing persona.

        Args:
            original_persona: Original persona being updated
            name: New name
            model: New model
            role: New role
            description: New description
            system_prompt: New system prompt
            thinking_enabled: New thinking mode setting
            enabled: New enabled setting
        """
        # Validation
        if not name.strip():
            st.error("❌ Name is required")
            return
        if not description.strip():
            st.error("❌ Description is required")
            return

        # Check for name conflicts (excluding current persona)
        existing_names = [p.name.lower() for p in self.session_manager.get_personas() if p.name != original_persona.name]
        if name.strip().lower() in existing_names:
            st.error(f"❌ Persona '{name}' already exists")
            return

        # Update persona
        updated_persona = AIPersona(
            name=name.strip(),
            model=model,
            description=description.strip(),
            role=role.strip() if role else "",
            system_prompt=system_prompt.strip(),
            thinking_enabled=thinking_enabled,
            enabled=enabled
        )

        try:
            self.session_manager.update_persona(original_persona.name, updated_persona)
            st.success(f"✅ Updated persona: {updated_persona.name}")
            st.session_state[f"editing_persona_{original_persona.name}"] = False
            st.rerun()
        except Exception as e:
            st.error(f"❌ Failed to update persona: {str(e)}")

    def _bulk_enable_disable_all(self, enabled: bool) -> None:
        """Enable or disable all personas.

        Args:
            enabled: Whether to enable (True) or disable (False) all personas
        """
        personas = self.session_manager.get_personas()
        for persona in personas:
            updated_persona = AIPersona(
                name=persona.name,
                model=persona.model,
                description=persona.description,
                role=persona.role,
                system_prompt=persona.system_prompt,
                thinking_enabled=persona.thinking_enabled,
                enabled=enabled
            )
            self.session_manager.update_persona(persona.name, updated_persona)

        action = "enabled" if enabled else "disabled"
        st.success(f"✅ {len(personas)} personas {action}")
        st.rerun()

    def _delete_all_personas(self) -> None:
        """Delete all personas."""
        personas = self.session_manager.get_personas()
        for persona in personas:
            self.session_manager.remove_persona(persona.name)

        st.success(f"🗑️ Deleted {len(personas)} personas")
        st.session_state.show_delete_all_confirm = False
        st.rerun()

    def _export_all_personas(self) -> None:
        """Export all personas as JSON."""
        personas = self.session_manager.get_personas()
        persona_data = [persona.to_dict() for persona in personas]

        st.download_button(
            label="📥 Download Personas (JSON)",
            data=str(persona_data).replace("'", '"'),  # Convert to JSON-like string
            file_name=f"ai_personas_{st.session_state.session_id}.json",
            mime="application/json"
        )
        st.info("📄 Personas exported successfully!")

    def render_persona_selector(
        self,
        key: str = "persona_selector",
        help_text: str = "Select personas for conversation"
    ) -> List[AIPersona]:
        """Render a persona selection interface.

        Args:
            key: Unique key for the widget
            help_text: Help text to display

        Returns:
            List of selected personas
        """
        personas = self.session_manager.get_enabled_personas()

        if not personas:
            st.warning("⚠️ No enabled personas available. Please create and enable some personas first.")
            return []

        st.subheader("👥 Select Conversation Participants")
        st.caption(help_text)

        # Multi-select for personas
        persona_names = [p.name for p in personas]
        persona_info = [f"{p.name} ({p.model})" for p in personas]

        selected_indices = st.multiselect(
            "Choose personas:",
            options=range(len(persona_info)),
            format_func=lambda i: persona_info[i],
            key=key,
            default=list(range(min(3, len(personas))))  # Select first 3 by default
        )

        selected_personas = [personas[i] for i in selected_indices]

        # Show selected personas summary
        if selected_personas:
            st.info(f"✅ Selected {len(selected_personas)} persona(s): {', '.join([p.name for p in selected_personas])}")
        else:
            st.warning("⚠️ No personas selected")

        return selected_personas