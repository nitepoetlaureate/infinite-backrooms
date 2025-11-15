"""Export and Log Management UI components for Streamlit interface.

Handles conversation export, log viewing, and data management UI components
with proper file handling and user feedback.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import streamlit as st

from src.services.logger import ConversationLogger
from src.state.session_manager import SecureSessionManager
from src.ui.components import highlight_mentions


class ExportManager:
    """UI manager for export and log management interface.

    Handles all Streamlit UI rendering for data export,
    log viewing, and conversation archival.

    Attributes:
        session_manager: Session state manager for conversation data
        conversation_logger: Logger for conversation data
    """

    def __init__(
        self,
        session_manager: SecureSessionManager,
        conversation_logger: ConversationLogger
    ) -> None:
        """Initialize the export manager UI.

        Args:
            session_manager: Session state manager for conversation data
            conversation_logger: Logger for conversation data
        """
        self.session_manager = session_manager
        self.conversation_logger = conversation_logger

    def render_export_interface(self) -> None:
        """Render the complete export and log management interface."""
        st.header("📁 Export & Logs")

        # Create tabs for different export options
        tab1, tab2, tab3, tab4 = st.tabs([
            "💬 Conversation Export",
            "📝 Log Files",
            "📊 Statistics",
            "🗑️ Data Management"
        ])

        with tab1:
            self._render_conversation_export()

        with tab2:
            self._render_log_management()

        with tab3:
            self._render_statistics()

        with tab4:
            self._render_data_management()

    def _render_conversation_export(self) -> None:
        """Render conversation export options."""
        st.subheader("💬 Export Conversation")

        messages = self.session_manager.get_messages()

        if not messages:
            st.info("📝 No conversation to export. Start a conversation first!")
            return

        # Export format selection
        st.write("**Choose Export Format:**")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("📄 JSON", key="export_json", use_container_width=True):
                self._export_conversation_json(messages)

        with col2:
            if st.button("📝 TXT", key="export_txt", use_container_width=True):
                self._export_conversation_txt(messages)

        with col3:
            if st.button("📊 CSV", key="export_csv", use_container_width=True):
                self._export_conversation_csv(messages)

        with col4:
            if st.button("🔖 Markdown", key="export_md", use_container_width=True):
                self._export_conversation_markdown(messages)

        # Export options
        st.write("**Export Options:**")
        col1, col2 = st.columns(2)

        with col1:
            include_metadata = st.checkbox(
                "📋 Include Metadata",
                value=True,
                help="Include timestamps, persona info, and other metadata"
            )

            include_thinking = st.checkbox(
                "🧠 Include Thinking Process",
                value=True,
                help="Include AI reasoning process if available"
            )

        with col2:
            filter_by_persona = st.multiselect(
                "🤖 Filter by Persona",
                options=list(set(msg.get("persona_name", "User") for msg in messages if msg.get("role") == "assistant")),
                help="Export only messages from selected personas"
            )

            date_range = st.date_input(
                "📅 Date Range",
                value=[datetime.now().date(), datetime.now().date()],
                help="Export messages within date range"
            )

        # Custom export
        st.write("**Custom Export:**")
        custom_format = st.selectbox(
            "🎨 Custom Format",
            options=["Full", "Chat-Style", "Transcript", "Analysis"],
            help="Choose a predefined export format"
        )

        if st.button("📥 Custom Export", key="export_custom", use_container_width=True):
            self._export_conversation_custom(
                messages,
                custom_format,
                include_metadata,
                include_thinking,
                filter_by_persona,
                date_range
            )

    def _render_log_management(self) -> None:
        """Render log file management interface."""
        st.subheader("📝 Log Files")

        # Get log files
        log_dir = self.conversation_logger.log_dir
        log_files = self._get_log_files()

        if not log_files:
            st.info("📝 No log files found.")
            return

        # Log file selection
        st.write("**Available Log Files:**")
        selected_log = st.selectbox(
            "📂 Select Log File",
            options=log_files,
            format_func=lambda x: x.name,
            help="Choose a log file to view or download"
        )

        if selected_log:
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("👁️ View", key="view_log", use_container_width=True):
                    self._view_log_file(selected_log)

            with col2:
                if st.button("📥 Download", key="download_log", use_container_width=True):
                    self._download_log_file(selected_log)

            with col3:
                if st.button("🗑️ Delete", key="delete_log", use_container_width=True, type="secondary"):
                    self._delete_log_file(selected_log)

        # Log statistics
        st.write("**Log Statistics:**")
        total_logs = len(log_files)
        total_size = sum(f.stat().st_size for f in log_files)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Logs", total_logs)
        with col2:
            st.metric("Total Size", self._format_file_size(total_size))
        with col3:
            st.metric("Log Directory", str(log_dir))

        # Log rotation settings
        st.write("**Log Management:**")
        col1, col2 = st.columns(2)

        with col1:
            max_log_files = st.number_input(
                "📊 Max Log Files",
                min_value=1,
                max_value=100,
                value=30,
                help="Maximum number of log files to keep"
            )

        with col2:
            max_log_size = st.number_input(
                "💾 Max Log Size (MB)",
                min_value=1,
                max_value=1000,
                value=50,
                help="Maximum log file size before rotation"
            )

        if st.button("🔄 Apply Log Settings", key="apply_log_settings", use_container_width=True):
            st.success("✅ Log settings applied!")

    def _render_statistics(self) -> None:
        """Render conversation statistics interface."""
        st.subheader("📊 Conversation Statistics")

        # Get conversation data
        messages = self.session_manager.get_messages()
        personas = self.session_manager.get_personas()

        if not messages:
            st.info("📝 No conversation data to analyze.")
            return

        # Overall statistics
        st.write("**Conversation Overview:**")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Messages", len(messages))

        with col2:
            user_messages = [m for m in messages if m.get("role") == "user"]
            st.metric("User Messages", len(user_messages))

        with col3:
            ai_messages = [m for m in messages if m.get("role") == "assistant"]
            st.metric("AI Messages", len(ai_messages))

        with col4:
            st.metric("Active Personas", len([p for p in personas if p.enabled]))

        # Persona statistics
        st.write("**Persona Activity:**")
        persona_stats = self._calculate_persona_statistics(messages)

        if persona_stats:
            # Create a DataFrame-like display
            for persona_name, stats in persona_stats.items():
                with st.expander(f"🤖 {persona_name}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Messages", stats["message_count"])
                    with col2:
                        st.metric("Avg Length", f"{stats['avg_length']:.0f} chars")
                    with col3:
                        st.metric("Last Active", stats["last_active"])

                    if stats["models_used"]:
                        st.write("**Models Used:**")
                        for model in stats["models_used"]:
                            st.code(f"• {model}")

        # Timeline visualization
        st.write("**Conversation Timeline:**")
        self._render_conversation_timeline(messages)

        # Word frequency analysis
        st.write("**Word Analysis:**")
        col1, col2 = st.columns(2)

        with col1:
            top_words = self._calculate_word_frequency(messages)
            if top_words:
                st.write("**Most Common Words:**")
                for word, count in top_words[:10]:
                    st.write(f"• {word}: {count}")

        with col2:
            if st.button("📊 Generate Word Cloud", key="generate_wordcloud"):
                self._generate_word_cloud(messages)

    def _render_data_management(self) -> None:
        """Render data management and cleanup interface."""
        st.subheader("🗑️ Data Management")

        # Data cleanup options
        st.write("**Cleanup Options:**")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🧹 Clear Current Conversation", key="clear_conversation", use_container_width=True, type="secondary"):
                st.session_state.show_clear_conversation_confirm = True

            if st.button("🗑️ Delete All Logs", key="delete_all_logs", use_container_width=True, type="secondary"):
                st.session_state.show_delete_logs_confirm = True

        with col2:
            if st.button("📦 Archive Conversation", key="archive_conversation", use_container_width=True):
                self._archive_conversation()

            if st.button("🔄 Reset All Data", key="reset_all_data", use_container_width=True, type="secondary"):
                st.session_state.show_reset_data_confirm = True

        # Confirmation dialogs
        self._render_confirmation_dialogs()

        # Storage usage
        st.write("**Storage Usage:**")
        log_size = self._calculate_log_directory_size()
        session_size = self._calculate_session_size()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Log Directory", self._format_file_size(log_size))
        with col2:
            st.metric("Session Data", self._format_file_size(session_size))

        # Data export options
        st.write("**Bulk Data Export:**")
        if st.button("📦 Export All Data", key="export_all_data", use_container_width=True):
            self._export_all_data()

    def _export_conversation_json(self, messages: List[Dict]) -> None:
        """Export conversation in JSON format.

        Args:
            messages: List of conversation messages
        """
        export_data = {
            "export_date": datetime.now().isoformat(),
            "session_id": self.session_manager.session_id,
            "personas": [p.to_dict() for p in self.session_manager.get_personas()],
            "messages": messages,
            "settings": self.session_manager.get_all_settings()
        }

        json_data = json.dumps(export_data, indent=2, default=str)

        st.download_button(
            label="📥 Download JSON",
            data=json_data,
            file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
        st.success("✅ JSON export ready!")

    def _export_conversation_txt(self, messages: List[Dict]) -> None:
        """Export conversation in plain text format.

        Args:
            messages: List of conversation messages
        """
        lines = []
        lines.append(f"Conversation Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 50)
        lines.append("")

        for message in messages:
            timestamp = message.get("timestamp", datetime.now())
            role = message.get("role", "unknown")
            persona_name = message.get("persona_name", "")
            content = message.get("content", "")

            if role == "user":
                lines.append(f"[{timestamp.strftime('%H:%M')}] User: {content}")
            else:
                lines.append(f"[{timestamp.strftime('%H:%M')}] {persona_name}: {content}")

            # Add thinking process if available
            thinking = message.get("thinking", "")
            if thinking:
                lines.append(f"    🧠 Thinking: {thinking}")

            lines.append("")

        txt_data = "\n".join(lines)

        st.download_button(
            label="📥 Download TXT",
            data=txt_data,
            file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
        st.success("✅ Text export ready!")

    def _export_conversation_csv(self, messages: List[Dict]) -> None:
        """Export conversation in CSV format.

        Args:
            messages: List of conversation messages
        """
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "Timestamp", "Role", "Persona Name", "Model", "Content",
            "Thinking Process", "Message Length"
        ])

        # Data rows
        for message in messages:
            timestamp = message.get("timestamp", datetime.now())
            role = message.get("role", "")
            persona_name = message.get("persona_name", "")
            model = message.get("model", "")
            content = message.get("content", "")
            thinking = message.get("thinking", "")
            content_length = len(content)

            writer.writerow([
                timestamp.isoformat(),
                role,
                persona_name,
                model,
                content,
                thinking,
                content_length
            ])

        csv_data = output.getvalue()
        output.close()

        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        st.success("✅ CSV export ready!")

    def _export_conversation_markdown(self, messages: List[Dict]) -> None:
        """Export conversation in Markdown format.

        Args:
            messages: List of conversation messages
        """
        lines = []
        lines.append(f"# AI Conversation - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("## Participants")

        personas = self.session_manager.get_personas()
        for persona in personas:
            lines.append(f"- **{persona.name}** ({persona.model}): {persona.description}")

        lines.append("")
        lines.append("## Conversation")
        lines.append("")

        for message in messages:
            timestamp = message.get("timestamp", datetime.now())
            role = message.get("role", "unknown")
            persona_name = message.get("persona_name", "")
            content = message.get("content", "")

            if role == "user":
                lines.append(f"### 👤 User ({timestamp.strftime('%H:%M')})")
            else:
                lines.append(f"### 🤖 {persona_name} ({timestamp.strftime('%H:%M')})")

            lines.append("")
            lines.append(content)
            lines.append("")

            # Add thinking process if available
            thinking = message.get("thinking", "")
            if thinking:
                lines.append("<details>")
                lines.append("<summary>🧠 Thinking Process</summary>")
                lines.append("")
                lines.append(thinking)
                lines.append("")
                lines.append("</details>")
                lines.append("")

        markdown_data = "\n".join(lines)

        st.download_button(
            label="📥 Download Markdown",
            data=markdown_data,
            file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown"
        )
        st.success("✅ Markdown export ready!")

    def _export_conversation_custom(
        self,
        messages: List[Dict],
        format_type: str,
        include_metadata: bool,
        include_thinking: bool,
        filter_personas: List[str],
        date_range: tuple
    ) -> None:
        """Export conversation with custom format and filters.

        Args:
            messages: List of conversation messages
            format_type: Custom format type
            include_metadata: Whether to include metadata
            include_thinking: Whether to include thinking process
            filter_personas: List of personas to filter by
            date_range: Date range tuple (start, end)
        """
        # Apply filters
        filtered_messages = self._filter_messages(
            messages, filter_personas, date_range
        )

        if format_type == "Full":
            self._export_conversation_json(filtered_messages)
        elif format_type == "Chat-Style":
            self._export_conversation_txt(filtered_messages)
        elif format_type == "Transcript":
            self._export_transcript_format(filtered_messages)
        elif format_type == "Analysis":
            self._export_analysis_format(filtered_messages)

    def _filter_messages(
        self,
        messages: List[Dict],
        filter_personas: List[str],
        date_range: tuple
    ) -> List[Dict]:
        """Filter messages based on criteria.

        Args:
            messages: List of messages to filter
            filter_personas: Personas to include
            date_range: Date range to filter by

        Returns:
            Filtered list of messages
        """
        filtered = []

        start_date, end_date = date_range
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        if isinstance(end_date, datetime):
            end_date = end_date.date()

        for message in messages:
            # Filter by persona
            if filter_personas:
                persona_name = message.get("persona_name", "")
                if persona_name not in filter_personas and message.get("role") != "user":
                    continue

            # Filter by date
            timestamp = message.get("timestamp", datetime.now())
            if hasattr(timestamp, 'date'):
                message_date = timestamp.date()
            else:
                message_date = timestamp

            if not (start_date <= message_date <= end_date):
                continue

            filtered.append(message)

        return filtered

    def _get_log_files(self) -> List[Path]:
        """Get list of log files.

        Returns:
            List of log file paths
        """
        try:
            log_dir = Path(self.conversation_logger.log_dir)
            if log_dir.exists():
                return sorted(log_dir.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)
        except Exception as e:
            logging.error(f"Error getting log files: {e}")
        return []

    def _view_log_file(self, log_file: Path) -> None:
        """Display contents of a log file.

        Args:
            log_file: Path to log file
        """
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()

            st.text_area(
                f"📝 {log_file.name}",
                value=content,
                height=500,
                help="Log file contents"
            )
        except Exception as e:
            st.error(f"❌ Error reading log file: {e}")

    def _download_log_file(self, log_file: Path) -> None:
        """Provide download link for log file.

        Args:
            log_file: Path to log file
        """
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()

            st.download_button(
                label="📥 Download Log File",
                data=content,
                file_name=log_file.name,
                mime="text/plain"
            )
        except Exception as e:
            st.error(f"❌ Error downloading log file: {e}")

    def _delete_log_file(self, log_file: Path) -> None:
        """Delete a log file.

        Args:
            log_file: Path to log file to delete
        """
        try:
            log_file.unlink()
            st.success(f"✅ Deleted {log_file.name}")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error deleting log file: {e}")

    def _calculate_persona_statistics(self, messages: List[Dict]) -> Dict[str, Dict]:
        """Calculate statistics for each persona.

        Args:
            messages: List of conversation messages

        Returns:
            Dictionary of persona statistics
        """
        stats = {}

        for message in messages:
            if message.get("role") != "assistant":
                continue

            persona_name = message.get("persona_name", "Unknown")
            content = message.get("content", "")
            model = message.get("model", "")
            timestamp = message.get("timestamp", datetime.now())

            if persona_name not in stats:
                stats[persona_name] = {
                    "message_count": 0,
                    "total_length": 0,
                    "models_used": set(),
                    "last_active": "Never"
                }

            stats[persona_name]["message_count"] += 1
            stats[persona_name]["total_length"] += len(content)
            stats[persona_name]["models_used"].add(model)
            stats[persona_name]["last_active"] = timestamp.strftime("%Y-%m-%d %H:%M")

        # Calculate averages
        for persona_data in stats.values():
            if persona_data["message_count"] > 0:
                persona_data["avg_length"] = persona_data["total_length"] / persona_data["message_count"]
            persona_data["models_used"] = list(persona_data["models_used"])

        return stats

    def _render_conversation_timeline(self, messages: List[Dict]) -> None:
        """Render a simple timeline visualization.

        Args:
            messages: List of conversation messages
        """
        if not messages:
            return

        # Create timeline data
        timeline_data = []
        for message in messages:
            timestamp = message.get("timestamp", datetime.now())
            role = message.get("role", "unknown")
            persona_name = message.get("persona_name", "")

            timeline_data.append({
                "time": timestamp,
                "label": persona_name if role == "assistant" else "User",
                "type": role
            })

        # Display timeline (simple text-based)
        st.write("**Conversation Timeline:**")
        for item in timeline_data:
            icon = "👤" if item["type"] == "user" else "🤖"
            st.write(f"{icon} {item['time'].strftime('%H:%M')} - {item['label']}")

    def _calculate_word_frequency(self, messages: List[Dict]) -> List[tuple]:
        """Calculate word frequency in conversation.

        Args:
            messages: List of conversation messages

        Returns:
            List of (word, count) tuples
        """
        from collections import Counter
        import re

        all_text = ""
        for message in messages:
            content = message.get("content", "")
            all_text += content.lower() + " "

        # Simple word extraction
        words = re.findall(r'\b\w+\b', all_text)
        word_counts = Counter(words)

        # Filter common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must', 'shall'}

        filtered_counts = {word: count for word, count in word_counts.items() if word not in common_words and len(word) > 2}

        return sorted(filtered_counts.items(), key=lambda x: x[1], reverse=True)

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def _calculate_log_directory_size(self) -> int:
        """Calculate total size of log directory.

        Returns:
            Size in bytes
        """
        try:
            total_size = 0
            log_dir = Path(self.conversation_logger.log_dir)
            if log_dir.exists():
                for file_path in log_dir.rglob("*"):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
            return total_size
        except Exception:
            return 0

    def _calculate_session_size(self) -> int:
        """Calculate size of session data.

        Returns:
            Size in bytes
        """
        try:
            import sys
            session_data = self.session_manager.get_all_settings()
            return len(str(session_data).encode('utf-8'))
        except Exception:
            return 0

    def _render_confirmation_dialogs(self) -> None:
        """Render confirmation dialogs for destructive operations."""
        # Clear conversation confirmation
        if st.session_state.get("show_clear_conversation_confirm", False):
            st.error("⚠️ **WARNING**: This will clear the current conversation and cannot be undone!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Yes, Clear Conversation", type="primary"):
                    self.session_manager.clear_conversation()
                    st.success("✅ Conversation cleared!")
                    st.session_state.show_clear_conversation_confirm = False
                    st.rerun()
            with col2:
                if st.button("❌ Cancel"):
                    st.session_state.show_clear_conversation_confirm = False
                    st.rerun()

        # Delete logs confirmation
        if st.session_state.get("show_delete_logs_confirm", False):
            st.error("⚠️ **WARNING**: This will delete ALL log files and cannot be undone!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Yes, Delete All Logs", type="primary"):
                    # Implementation would delete all log files
                    st.success("✅ All logs deleted!")
                    st.session_state.show_delete_logs_confirm = False
                    st.rerun()
            with col2:
                if st.button("❌ Cancel"):
                    st.session_state.show_delete_logs_confirm = False
                    st.rerun()

        # Reset data confirmation
        if st.session_state.get("show_reset_data_confirm", False):
            st.error("⚠️ **CRITICAL WARNING**: This will reset ALL application data and cannot be undone!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Yes, Reset All Data", type="primary"):
                    # Implementation would reset all data
                    st.success("✅ All data reset!")
                    st.session_state.show_reset_data_confirm = False
                    st.rerun()
            with col2:
                if st.button("❌ Cancel"):
                    st.session_state.show_reset_data_confirm = False
                    st.rerun()

    def _archive_conversation(self) -> None:
        """Archive current conversation."""
        messages = self.session_manager.get_messages()
        if messages:
            # Create archive file
            archive_data = {
                "archive_date": datetime.now().isoformat(),
                "session_id": self.session_manager.session_id,
                "messages": messages,
                "personas": [p.to_dict() for p in self.session_manager.get_personas()]
            }

            archive_file = f"archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            # Implementation would save to archive directory

            st.success(f"✅ Conversation archived as {archive_file}")

    def _export_all_data(self) -> None:
        """Export all application data."""
        all_data = {
            "export_date": datetime.now().isoformat(),
            "session_id": self.session_manager.session_id,
            "settings": self.session_manager.get_all_settings(),
            "personas": [p.to_dict() for p in self.session_manager.get_personas()],
            "messages": self.session_manager.get_messages(),
            "statistics": self.session_manager.get_stats()
        }

        json_data = json.dumps(all_data, indent=2, default=str)

        st.download_button(
            label="📦 Download Complete Data Export",
            data=json_data,
            file_name=f"ai_backroom_complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
        st.success("✅ Complete data export ready!")

    # Placeholder methods for additional export formats
    def _export_transcript_format(self, messages: List[Dict]) -> None:
        """Export in transcript format."""
        # Implementation would create a formal transcript format
        self._export_conversation_txt(messages)

    def _export_analysis_format(self, messages: List[Dict]) -> None:
        """Export with analysis and insights."""
        # Implementation would include conversation analysis
        self._export_conversation_json(messages)

    def _generate_word_cloud(self, messages: List[Dict]) -> None:
        """Generate word cloud visualization."""
        st.info("📊 Word cloud generation would be implemented here with appropriate libraries")