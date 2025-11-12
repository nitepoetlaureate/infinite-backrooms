# REFACTORED CODE FOR persona_management_ui
# This file contains all 7 helper methods + the refactored main function
# Ready to copy into streamlit_backroom.py

# ============================================================================
# HELPER METHOD 1: Ollama Connection Check
# ============================================================================

def _render_ollama_connection_check(self) -> None:
    """Render Ollama connection check button and status display"""
    if st.button("🔄 Check Ollama Connection"):
        with st.status("Checking Ollama connection...", expanded=True) as status:
            st.write("Connecting to Ollama API...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                connected = loop.run_until_complete(self.check_ollama_connection())
                if connected:
                    st.write(f"✅ Found {len(st.session_state.available_models)} models")
                    for model in st.session_state.available_models:
                        st.write(f"• {model}")
                    status.update(label="Connection successful!", state="complete", expanded=False)
                else:
                    st.write("❌ Connection failed")
                    status.update(label="Connection failed", state="error", expanded=False)
            finally:
                loop.close()


# ============================================================================
# HELPER METHOD 2: Persona Delete Controls
# ============================================================================

def _render_persona_delete_controls(self, persona: AIPersona, col: Any) -> None:
    """Render delete button with confirmation dialog for a persona

    Args:
        persona: The persona to manage deletion for
        col: The Streamlit column object to render controls in
    """
    delete_key = f"delete_confirm_{persona.id}"
    if delete_key not in st.session_state:
        st.session_state[delete_key] = False

    if not st.session_state[delete_key]:
        if col.button("🗑️ Delete", key=f"delete_{persona.id}", type="secondary", help="Delete this persona"):
            st.session_state[delete_key] = True
            st.rerun()
    else:
        col.warning(f"Delete {persona.name}?")
        col_yes, col_no = col.columns(2)
        with col_yes:
            if st.button("✅ Yes", key=f"delete_yes_{persona.id}", type="primary"):
                st.session_state.personas = [p for p in st.session_state.personas if p.id != persona.id]
                st.session_state[delete_key] = False
                st.success(f"Deleted persona: {persona.name}")
                st.rerun()
        with col_no:
            if st.button("❌ No", key=f"delete_no_{persona.id}", type="secondary"):
                st.session_state[delete_key] = False
                st.rerun()


# ============================================================================
# HELPER METHOD 3: Individual Persona Details
# ============================================================================

def _render_persona_details(self, persona: AIPersona, index: int) -> None:
    """Render detailed view of a single persona in an expander

    Args:
        persona: The persona to display
        index: Index in the persona list (used for unique keys)
    """
    avatar = self.get_persona_avatar(persona)
    role_display = f" - {persona.role}" if persona.role else ""

    with st.expander(f"{avatar} {persona.name} ({persona.model}){role_display}", expanded=False):
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            st.write(f"**Model:** {persona.model}")
            st.write(f"**Role:** {persona.role or 'No specific role'}")
            st.write(f"**Enabled:** {'✅' if persona.enabled else '❌'}")
            st.color_picker("Color", value=persona.color, key=f"color_{persona.id}", disabled=True)

        with col2:
            if persona.role and persona.role in self.role_templates:
                st.text_area("Role Description", value=self.role_templates[persona.role],
                           key=f"role_desc_{persona.id}", disabled=True, height=100)
            st.text_area("Custom System Prompt", value=persona.system_prompt,
                       key=f"prompt_{persona.id}", disabled=True, height=100)

        with col3:
            self._render_persona_delete_controls(persona, col3)

            # Only show enabled checkbox if not in delete confirmation mode
            delete_key = f"delete_confirm_{persona.id}"
            if not st.session_state.get(delete_key, False):
                enabled_new = st.checkbox("Enabled", value=persona.enabled, key=f"enabled_{persona.id}")
                if enabled_new != persona.enabled:
                    persona.enabled = enabled_new
                    st.rerun()


# ============================================================================
# HELPER METHOD 4: Persona List Display
# ============================================================================

def _render_persona_list(self) -> None:
    """Display list of all existing personas"""
    if st.session_state.personas:
        st.subheader("Current Personas")
        for i, persona in enumerate(st.session_state.personas):
            self._render_persona_details(persona, i)


# ============================================================================
# HELPER METHOD 5: Add New Persona Form
# ============================================================================

def _render_add_persona_form(self) -> None:
    """Render form for creating a new persona with full configuration"""
    st.subheader("Add New Persona")
    with st.form("new_persona_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Persona Name", placeholder="e.g., Granite, Qwen, Gemma")
            color = st.color_picker("Chat Color", value=DEFAULT_PERSONA_COLOR)

        with col2:
            if st.session_state.available_models:
                model = st.selectbox("Model", st.session_state.available_models)
            else:
                model = st.text_input("Model", placeholder="e.g., granite3.3:8b")
            enabled = st.checkbox("Enabled", value=True)

        # Role selection
        st.subheader("🎭 Role Configuration")
        role_col1, role_col2 = st.columns([1, 2])

        with role_col1:
            role_options = list(self.role_templates.keys())
            selected_role = st.selectbox("Predefined Role", role_options,
                                        format_func=lambda x: x if x else "No specific role")

            # Option for custom role
            use_custom_role = st.checkbox("Use custom role instead")
            if use_custom_role:
                custom_role = st.text_input("Custom Role Name",
                                           placeholder="e.g., Tech Enthusiast, Poet, etc.")
                role = custom_role if custom_role else ""
            else:
                role = selected_role

        with role_col2:
            if role and role in self.role_templates:
                st.text_area("Role Description", value=self.role_templates[role],
                           disabled=True, height=100)
            elif use_custom_role:
                st.info("💡 Define a custom role to give your persona unique characteristics and conversation style.")

        system_prompt = st.text_area(
            "Additional System Prompt (Optional)",
            placeholder="Any additional custom instructions for this persona...",
            height=100,
            help="This will be combined with the role-based prompt if a role is selected."
        )

        if st.form_submit_button("➕ Add Persona"):
            if name and model:
                new_persona = AIPersona(
                    id=str(uuid.uuid4()),
                    name=name,
                    model=model,
                    role=role,
                    system_prompt=system_prompt,
                    color=color,
                    enabled=enabled
                )
                st.session_state.personas.append(new_persona)
                role_text = f" as {role}" if role else ""
                st.success(f"Added persona: {name}{role_text}")
                st.rerun()
            else:
                st.error("Please provide both name and model")


# ============================================================================
# HELPER METHOD 6: Add Preset Personas (Shared Logic)
# ============================================================================

def _add_preset_personas(self, preset_list: List[Dict[str, str]], success_message: str) -> None:
    """Add multiple personas from a preset configuration

    Args:
        preset_list: List of dicts with 'name', 'role', and 'color' keys
        success_message: Message to display upon successful addition
    """
    if st.session_state.available_models:
        models = st.session_state.available_models
        added_count = 0

        for i, preset in enumerate(preset_list):
            if len(models) > 0:
                model = models[i % len(models)]  # Rotate through available models
                new_persona = AIPersona(
                    id=str(uuid.uuid4()),
                    name=preset["name"],
                    model=model,
                    role=preset["role"],
                    system_prompt="",
                    color=preset["color"],
                    enabled=True
                )
                st.session_state.personas.append(new_persona)
                added_count += 1

        if added_count > 0:
            st.success(f"✅ {success_message.format(count=added_count)}")
            st.rerun()
    else:
        st.warning("⚠️ Please check Ollama connection first to load available models.")


# ============================================================================
# HELPER METHOD 7: Quick Start Presets
# ============================================================================

def _render_quick_start_presets(self) -> None:
    """Render quick start preset buttons for adding multiple personas at once"""
    st.markdown("---")
    st.subheader("🚀 Quick Start Presets")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🎭 Add Diverse Conversation Set"):
            diverse_personas = [
                {"name": "Sage", "role": "Philosopher", "color": "#9b59b6"},
                {"name": "Eureka", "role": "Scientist", "color": "#3498db"},
                {"name": "Quill", "role": "Creative Writer", "color": "#e74c3c"},
                {"name": "Bright", "role": "Optimist", "color": "#f39c12"},
                {"name": "Quest", "role": "Skeptic", "color": "#95a5a6"}
            ]
            self._add_preset_personas(diverse_personas, "Added {count} diverse personas!")

    with col2:
        if st.button("📋 Add Structured Discussion Set"):
            structured_personas = [
                {"name": "Guide", "role": "Moderator", "color": "#2c3e50"},
                {"name": "Chronicle", "role": "Note-Taker", "color": "#34495e"},
                {"name": "Sage", "role": "Philosopher", "color": "#9b59b6"},
                {"name": "Eureka", "role": "Scientist", "color": "#3498db"},
                {"name": "Socrates", "role": "Debate Enthusiast", "color": "#e67e22"}
            ]
            self._add_preset_personas(structured_personas, "Added {count} personas for structured discussions!")


# ============================================================================
# REFACTORED MAIN FUNCTION
# ============================================================================

def persona_management_ui(self) -> None:
    """UI for managing AI personas"""
    st.header("🤖 AI Persona Management")

    self._render_ollama_connection_check()
    self._render_persona_list()
    self._render_add_persona_form()
    self._render_quick_start_presets()


# ============================================================================
# USAGE INSTRUCTIONS
# ============================================================================
#
# To apply this refactoring:
# 1. Add all 7 helper methods to the BackroomApp class (before persona_management_ui)
# 2. Replace the existing persona_management_ui method with the refactored version above
# 3. Ensure proper indentation (all methods should be class methods with 'self')
# 4. Add type hints import if not present: from typing import List, Dict, Any
#
# The refactored code maintains 100% functional equivalence while improving:
# - Readability (main function is now 8 lines vs 216)
# - Maintainability (each section is isolated)
# - Testability (each helper can be tested independently)
# - Reusability (helpers can be called from other contexts)
