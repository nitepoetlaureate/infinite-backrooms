"""Unit tests for PersonaManager UI component."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import streamlit as st

from src.ui.persona_manager import PersonaManager
from src.state.session_manager import SecureSessionManager
from src.models.persona import AIPersona


class TestPersonaManager:
    """Test suite for PersonaManager class."""

    @pytest.fixture
    def mock_session_manager(self):
        """Create mock session manager."""
        manager = Mock(spec=SecureSessionManager)
        manager.session_id = "test_session_123"
        manager.get_personas.return_value = []
        manager.get_available_models.return_value = ["llama2", "mistral", "codellama"]
        return manager

    @pytest.fixture
    def persona_manager(self, mock_session_manager):
        """Create PersonaManager instance with mock session manager."""
        return PersonaManager(mock_session_manager)

    @pytest.fixture
    def sample_personas(self):
        """Create sample personas for testing."""
        return [
            AIPersona(
                name="TestBot1",
                model="llama2",
                description="First test persona",
                role="Expert",
                enabled=True
            ),
            AIPersona(
                name="TestBot2",
                model="mistral",
                description="Second test persona",
                role="Creative",
                enabled=False
            )
        ]

    @pytest.fixture
    def mock_streamlit(self):
        """Mock Streamlit components."""
        with patch('streamlit.subheader'), \
             patch('streamlit.columns'), \
             patch('streamlit.expander'), \
             patch('streamlit.form'), \
             patch('streamlit.text_input'), \
             patch('streamlit.selectbox'), \
             patch('streamlit.text_area'), \
             patch('streamlit.checkbox'), \
             patch('streamlit.form_submit_button'), \
             patch('streamlit.button'), \
             patch('streamlit.success'), \
             patch('streamlit.error'), \
             patch('streamlit.info'), \
             patch('streamlit.warning'), \
             patch('streamlit.caption'), \
             patch('streamlit.code'), \
             patch('streamlit.write'), \
             patch('streamlit.markdown'), \
             patch('streamlit.multiselect'), \
             patch('streamlit.number_input'), \
             patch('streamlit.download_button'), \
             patch('streamlit.session_state', {}):
            yield

    def test_persona_manager_initialization(self, mock_session_manager):
        """Test PersonaManager initialization."""
        manager = PersonaManager(mock_session_manager)

        assert manager.session_manager == mock_session_manager
        assert isinstance(manager, PersonaManager)

    def test_render_persona_management_interface_no_personas(
        self, persona_manager, mock_session_manager, mock_streamlit
    ):
        """Test rendering interface when no personas exist."""
        mock_session_manager.get_personas.return_value = []

        # Mock the various Streamlit components
        with patch('streamlit.columns') as mock_columns:
            mock_col1 = Mock()
            mock_col2 = Mock()
            mock_columns.return_value = [mock_col1, mock_col2]

            persona_manager.render_persona_management_interface()

            # Verify that subheader was called
            assert patch('streamlit.subheader').called

    def test_render_persona_management_interface_with_personas(
        self, persona_manager, mock_session_manager, sample_personas, mock_streamlit
    ):
        """Test rendering interface with existing personas."""
        mock_session_manager.get_personas.return_value = sample_personas

        with patch('streamlit.columns') as mock_columns:
            mock_col1 = Mock()
            mock_col2 = Mock()
            mock_columns.return_value = [mock_col1, mock_col2]

            persona_manager.render_persona_management_interface()

            # Verify persona list should be rendered
            mock_col1.__enter__.return_value._render_persona_list.assert_called_once()

    def test_render_persona_creation_form_no_models(
        self, persona_manager, mock_session_manager, mock_streamlit
    ):
        """Test persona creation form when no models are available."""
        mock_session_manager.get_available_models.return_value = []

        persona_manager._render_persona_creation_form()

        # Should show warning about no models
        assert patch('streamlit.warning').called

    def test_filter_personas_enabled_only(
        self, persona_manager, sample_personas
    ):
        """Test filtering personas by enabled status."""
        # Filter only enabled personas
        filtered = persona_manager._filter_personas(
            sample_personas,
            show_enabled=True,
            show_disabled=False
        )

        assert len(filtered) == 1
        assert filtered[0].name == "TestBot1"
        assert filtered[0].enabled is True

    def test_filter_personas_disabled_only(
        self, persona_manager, sample_personas
    ):
        """Test filtering personas by disabled status."""
        # Filter only disabled personas
        filtered = persona_manager._filter_personas(
            sample_personas,
            show_enabled=False,
            show_disabled=True
        )

        assert len(filtered) == 1
        assert filtered[0].name == "TestBot2"
        assert filtered[0].enabled is False

    def test_filter_personas_both(
        self, persona_manager, sample_personas
    ):
        """Test filtering personas showing both enabled and disabled."""
        # Show both enabled and disabled personas
        filtered = persona_manager._filter_personas(
            sample_personas,
            show_enabled=True,
            show_disabled=True
        )

        assert len(filtered) == 2
        assert filtered[0].name == "TestBot1"
        assert filtered[1].name == "TestBot2"

    def test_sort_personas_by_name(
        self, persona_manager, sample_personas
    ):
        """Test sorting personas by name."""
        # Add persona with name that should sort first
        personas = sample_personas + [
            AIPersona(
                name="AlphaBot",
                model="codellama",
                description="Alpha test persona",
                enabled=True
            )
        ]

        sorted_personas = persona_manager._sort_personas(personas, "Name")

        assert sorted_personas[0].name == "AlphaBot"
        assert sorted_personas[1].name == "TestBot1"
        assert sorted_personas[2].name == "TestBot2"

    def test_sort_personas_by_model(
        self, persona_manager, sample_personas
    ):
        """Test sorting personas by model."""
        sorted_personas = persona_manager._sort_personas(sample_personas, "Model")

        # Should be sorted by model name
        assert sorted_personas[0].model == "llama2"
        assert sorted_personas[1].model == "mistral"

    def test_create_persona_success(
        self, persona_manager, mock_session_manager, mock_streamlit
    ):
        """Test successful persona creation."""
        mock_session_manager.get_personas.return_value = []  # No existing personas

        # Mock successful persona addition
        mock_session_manager.add_persona.return_value = None

        persona_manager._create_persona(
            name="NewPersona",
            model="llama2",
            role="Expert",
            description="Test persona description",
            system_prompt="Test system prompt",
            thinking_enabled=True,
            enabled=True
        )

        # Verify add_persona was called
        mock_session_manager.add_persona.assert_called_once()

        # Check the persona object passed to add_persona
        call_args = mock_session_manager.add_persona.call_args[0][0]
        assert isinstance(call_args, AIPersona)
        assert call_args.name == "NewPersona"
        assert call_args.model == "llama2"
        assert call_args.role == "Expert"
        assert call_args.description == "Test persona description"

    def test_create_persona_missing_name(
        self, persona_manager, mock_session_manager, mock_streamlit
    ):
        """Test persona creation with missing name."""
        with patch('streamlit.error') as mock_error:
            persona_manager._create_persona(
                name="",  # Empty name
                model="llama2",
                role="",
                description="Test description",
                system_prompt="",
                thinking_enabled=False,
                enabled=True
            )

            # Should show error about missing name
            mock_error.assert_called_with("❌ Name is required")

    def test_create_persona_missing_description(
        self, persona_manager, mock_session_manager, mock_streamlit
    ):
        """Test persona creation with missing description."""
        with patch('streamlit.error') as mock_error:
            persona_manager._create_persona(
                name="TestPersona",
                model="llama2",
                role="",
                description="",  # Empty description
                system_prompt="",
                thinking_enabled=False,
                enabled=True
            )

            # Should show error about missing description
            mock_error.assert_called_with("❌ Description is required")

    def test_create_persona_duplicate_name(
        self, persona_manager, mock_session_manager, sample_personas, mock_streamlit
    ):
        """Test persona creation with duplicate name."""
        mock_session_manager.get_personas.return_value = sample_personas

        with patch('streamlit.error') as mock_error:
            persona_manager._create_persona(
                name="TestBot1",  # Duplicate name
                model="llama2",
                role="",
                description="Test description",
                system_prompt="",
                thinking_enabled=False,
                enabled=True
            )

            # Should show error about duplicate name
            mock_error.assert_called_with("❌ Persona 'TestBot1' already exists")

    def test_toggle_persona_status(
        self, persona_manager, mock_session_manager, sample_personas
    ):
        """Test toggling persona status."""
        persona = sample_personas[0]  # TestBot1 (enabled=True)

        # Mock update_persona
        mock_session_manager.update_persona.return_value = None

        persona_manager._toggle_persona_status(persona)

        # Verify update_persona was called
        mock_session_manager.update_persona.assert_called_once()

        # Check that status was toggled
        call_args = mock_session_manager.update_persona.call_args[0]
        original_name = call_args[0]
        updated_persona = call_args[1]

        assert original_name == "TestBot1"
        assert updated_persona.enabled is False  # Should be toggled

    def test_copy_persona(
        self, persona_manager, mock_session_manager, sample_personas
    ):
        """Test copying a persona."""
        persona = sample_personas[0]

        # Mock add_persona
        mock_session_manager.add_persona.return_value = None

        with patch('streamlit.success') as mock_success, \
             patch('streamlit.rerun') as mock_rerun:

            persona_manager._copy_persona(persona)

            # Verify add_persona was called
            mock_session_manager.add_persona.assert_called_once()

            # Check the copied persona
            call_args = mock_session_manager.add_persona.call_args[0][0]
            assert isinstance(call_args, AIPersona)
            assert call_args.name == "TestBot1 (Copy)"
            assert call_args.model == persona.model
            assert call_args.enabled is False  # Copies start disabled

    def test_delete_persona(
        self, persona_manager, mock_session_manager, sample_personas
    ):
        """Test deleting a persona."""
        persona = sample_personas[0]

        # Mock remove_persona
        mock_session_manager.remove_persona.return_value = None

        with patch('streamlit.success') as mock_success, \
             patch('streamlit.rerun') as mock_rerun:

            persona_manager._delete_persona(persona)

            # Verify remove_persona was called
            mock_session_manager.remove_persona.assert_called_with("TestBot1")

    def test_bulk_enable_disable_all_enable(
        self, persona_manager, mock_session_manager, sample_personas
    ):
        """Test bulk enabling all personas."""
        # Mock update_persona
        mock_session_manager.update_persona.return_value = None

        with patch('streamlit.success') as mock_success, \
             patch('streamlit.rerun') as mock_rerun:

            persona_manager._bulk_enable_disable_all(True)

            # Verify update_persona was called for each persona
            assert mock_session_manager.update_persona.call_count == 2

            # Check that all personas were enabled
            for call in mock_session_manager.update_persona.call_args_list:
                updated_persona = call[0][1]
                assert updated_persona.enabled is True

    def test_bulk_enable_disable_all_disable(
        self, persona_manager, mock_session_manager, sample_personas
    ):
        """Test bulk disabling all personas."""
        # Mock update_persona
        mock_session_manager.update_persona.return_value = None

        with patch('streamlit.success') as mock_success, \
             patch('streamlit.rerun') as mock_rerun:

            persona_manager._bulk_enable_disable_all(False)

            # Verify update_persona was called for each persona
            assert mock_session_manager.update_persona.call_count == 2

            # Check that all personas were disabled
            for call in mock_session_manager.update_persona.call_args_list:
                updated_persona = call[0][1]
                assert updated_persona.enabled is False

    def test_render_persona_selector_with_personas(
        self, persona_manager, mock_session_manager, sample_personas, mock_streamlit
    ):
        """Test persona selector with available personas."""
        mock_session_manager.get_enabled_personas.return_value = sample_personas

        with patch('streamlit.subheader'), \
             patch('streamlit.caption'), \
             patch('streamlit.multiselect') as mock_multiselect, \
             patch('streamlit.info') as mock_info:

            # Mock multiselect to return first two personas
            mock_multiselect.return_value = [0, 1]

            selected = persona_manager.render_persona_selector()

            # Should return selected personas
            assert len(selected) == 2
            assert selected[0].name == "TestBot1"
            assert selected[1].name == "TestBot2"

    def test_render_persona_selector_no_personas(
        self, persona_manager, mock_session_manager, mock_streamlit
    ):
        """Test persona selector with no available personas."""
        mock_session_manager.get_enabled_personas.return_value = []

        with patch('streamlit.subheader'), \
             patch('streamlit.caption'), \
             patch('streamlit.warning') as mock_warning, \
             patch('streamlit.multiselect'):

            selected = persona_manager.render_persona_selector()

            # Should return empty list and show warning
            assert selected == []
            mock_warning.assert_called()

    def test_update_persona_success(
        self, persona_manager, mock_session_manager, sample_personas, mock_streamlit
    ):
        """Test successful persona update."""
        persona = sample_personas[0]

        # Mock update_persona
        mock_session_manager.update_persona.return_value = None

        with patch('streamlit.success') as mock_success, \
             patch('streamlit.rerun') as mock_rerun:

            persona_manager._update_persona(
                original_persona=persona,
                name="UpdatedName",
                model="mistral",
                role="Creative",
                description="Updated description",
                system_prompt="Updated prompt",
                thinking_enabled=False,
                enabled=False
            )

            # Verify update_persona was called
            mock_session_manager.update_persona.assert_called_once()

            # Check the updated persona
            call_args = mock_session_manager.update_persona.call_args[0]
            original_name = call_args[0]
            updated_persona = call_args[1]

            assert original_name == "TestBot1"
            assert updated_persona.name == "UpdatedName"
            assert updated_persona.model == "mistral"
            assert updated_persona.role == "Creative"
            assert updated_persona.description == "Updated description"

    def test_update_persona_missing_name(
        self, persona_manager, mock_session_manager, sample_personas, mock_streamlit
    ):
        """Test persona update with missing name."""
        persona = sample_personas[0]

        with patch('streamlit.error') as mock_error:
            persona_manager._update_persona(
                original_persona=persona,
                name="",  # Empty name
                model="mistral",
                role="",
                description="Updated description",
                system_prompt="",
                thinking_enabled=False,
                enabled=False
            )

            # Should show error about missing name
            mock_error.assert_called_with("❌ Name is required")

    @patch('streamlit.download_button')
    def test_export_all_personas(
        self, mock_download, persona_manager, mock_session_manager, sample_personas
    ):
        """Test exporting all personas."""
        mock_session_manager.get_personas.return_value = sample_personas

        persona_manager._export_all_personas()

        # Should show download button
        mock_download.assert_called_once()

    def test_get_setting_summary(
        self, persona_manager, mock_session_manager
    ):
        """Test getting settings summary."""
        # Mock session manager settings
        mock_session_manager.get_setting.side_effect = lambda key, default=None: {
            "auto_advance": True,
            "thinking_enabled": False,
            "context_messages": 10,
            "debug_mode": False
        }.get(key, default)

        mock_session_manager.get_available_models.return_value = ["llama2", "mistral"]

        summary = persona_manager.get_setting_summary()

        assert summary["auto_advance"] is True
        assert summary["thinking_enabled"] is False
        assert summary["context_messages"] == 10
        assert summary["available_models"] == 2
        assert summary["debug_mode"] is False


class TestPersonaManagerIntegration:
    """Integration tests for PersonaManager with real SessionManager."""

    @pytest.fixture
    def real_session_manager(self):
        """Create real session manager for integration tests."""
        return SecureSessionManager()

    @pytest.fixture
    def persona_manager_real(self, real_session_manager):
        """Create PersonaManager with real session manager."""
        return PersonaManager(real_session_manager)

    def test_create_and_retrieve_persona(
        self, persona_manager_real, real_session_manager
    ):
        """Test creating and retrieving a persona through the manager."""
        # Create a persona
        persona = AIPersona(
            name="IntegrationTest",
            model="llama2",
            description="Integration test persona",
            role="Test",
            enabled=True
        )

        real_session_manager.add_persona(persona)

        # Verify it exists in session manager
        personas = real_session_manager.get_personas()
        assert len(personas) == 1
        assert personas[0].name == "IntegrationTest"

        # Test filtering
        filtered = persona_manager_real._filter_personas(
            personas,
            show_enabled=True,
            show_disabled=False
        )
        assert len(filtered) == 1
        assert filtered[0].enabled is True

    def test_persona_workflow(
        self, persona_manager_real, real_session_manager
    ):
        """Test complete persona management workflow."""
        # Create initial persona
        persona = AIPersona(
            name="WorkflowTest",
            model="mistral",
            description="Workflow test persona",
            role="Expert",
            enabled=True
        )

        real_session_manager.add_persona(persona)

        # Test toggle status
        persona_manager_real._toggle_persona_status(persona)

        # Verify status changed
        updated_personas = real_session_manager.get_personas()
        assert updated_personas[0].enabled is False

        # Test copy
        persona_manager_real._copy_persona(updated_personas[0])

        # Verify copy exists
        all_personas = real_session_manager.get_personas()
        assert len(all_personas) == 2
        copy_names = [p.name for p in all_personas if "Copy" in p.name]
        assert len(copy_names) == 1

        # Test delete
        persona_manager_real._delete_persona(all_personas[0])

        # Verify deletion
        final_personas = real_session_manager.get_personas()
        assert len(final_personas) == 1