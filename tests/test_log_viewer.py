"""Tests for log_viewer module"""

import pytest
from pathlib import Path
from log_viewer import LogParser
import tempfile
import shutil


class TestLogParser:
    """Test log parsing functionality"""

    @pytest.fixture
    def temp_log_dir(self):
        """Create a temporary directory for test logs"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def parser(self, temp_log_dir):
        """Create a parser instance with temp directory"""
        return LogParser(log_dir=temp_log_dir)

    @pytest.fixture
    def sample_log_file(self, temp_log_dir):
        """Create a sample log file for testing"""
        log_file = Path(temp_log_dir) / "streamlit_backroom_2025-01-15.txt"
        content = """[14:30:45] Bot1$ Hello from Bot1
[14:31:00] Bot2$ Response from Bot2
[14:31:15] Bot1$ Another message from Bot1
"""
        log_file.write_text(content, encoding='utf-8')
        return log_file

    def test_get_available_log_files_empty_directory(self, parser):
        """Test getting log files from empty directory"""
        log_files = parser.get_available_log_files()
        assert log_files == []

    def test_get_available_log_files_finds_streamlit_logs(self, parser, sample_log_file):
        """Test that streamlit log files are found"""
        log_files = parser.get_available_log_files()

        assert len(log_files) > 0
        assert any('streamlit_backroom' in f.name for f in log_files)

    def test_get_available_log_files_finds_legacy_logs(self, temp_log_dir, parser):
        """Test that legacy backroom log files are found"""
        legacy_log = Path(temp_log_dir) / "backroom_2025-01-15.txt"
        legacy_log.write_text("[10:00:00] Bot$ Message\n", encoding='utf-8')

        log_files = parser.get_available_log_files()

        assert len(log_files) > 0
        assert any('backroom' in f.name for f in log_files)

    def test_get_available_log_files_sorted_by_date(self, temp_log_dir, parser):
        """Test that log files are sorted with most recent first"""
        older_log = Path(temp_log_dir) / "streamlit_backroom_2025-01-10.txt"
        newer_log = Path(temp_log_dir) / "streamlit_backroom_2025-01-20.txt"

        older_log.write_text("[10:00:00] Bot$ Old message\n", encoding='utf-8')
        newer_log.write_text("[10:00:00] Bot$ New message\n", encoding='utf-8')

        log_files = parser.get_available_log_files()

        # Most recent should be first
        assert log_files[0].name > log_files[1].name

    def test_parse_log_file_extracts_messages(self, parser, sample_log_file):
        """Test that messages are correctly parsed from log file"""
        messages = parser.parse_log_file(sample_log_file)

        assert len(messages) == 3
        assert messages[0]['persona'] == 'Bot1'
        assert messages[0]['message'] == 'Hello from Bot1'
        assert messages[0]['timestamp'] == '14:30:45'

    def test_parse_log_file_includes_metadata(self, parser, sample_log_file):
        """Test that parsed messages include all metadata"""
        messages = parser.parse_log_file(sample_log_file)

        first_message = messages[0]
        assert 'timestamp' in first_message
        assert 'full_timestamp' in first_message
        assert 'persona' in first_message
        assert 'message' in first_message
        assert 'file' in first_message
        assert 'line_number' in first_message
        assert 'message_length' in first_message

    def test_parse_log_file_handles_empty_lines(self, temp_log_dir, parser):
        """Test that empty lines are skipped"""
        log_file = Path(temp_log_dir) / "test_empty_lines.txt"
        content = """[10:00:00] Bot1$ Message 1

[10:00:01] Bot2$ Message 2

"""
        log_file.write_text(content, encoding='utf-8')

        messages = parser.parse_log_file(log_file)

        assert len(messages) == 2  # Empty lines should be skipped

    def test_parse_log_file_calculates_message_length(self, parser, sample_log_file):
        """Test that message length is calculated correctly"""
        messages = parser.parse_log_file(sample_log_file)

        first_message = messages[0]
        assert first_message['message_length'] == len('Hello from Bot1')

    def test_parse_all_logs_combines_multiple_files(self, temp_log_dir, parser):
        """Test that multiple log files are combined"""
        log1 = Path(temp_log_dir) / "streamlit_backroom_2025-01-15.txt"
        log2 = Path(temp_log_dir) / "streamlit_backroom_2025-01-16.txt"

        log1.write_text("[10:00:00] Bot1$ Day 1 message\n", encoding='utf-8')
        log2.write_text("[11:00:00] Bot2$ Day 2 message\n", encoding='utf-8')

        df = parser.parse_all_logs()

        assert len(df) == 2
        assert 'Bot1' in df['persona'].values
        assert 'Bot2' in df['persona'].values

    def test_parse_all_logs_returns_empty_dataframe_if_no_logs(self, parser):
        """Test that empty DataFrame is returned when no logs exist"""
        df = parser.parse_all_logs()

        assert len(df) == 0
        assert df.empty

    def test_parse_all_logs_creates_datetime_column(self, temp_log_dir, parser):
        """Test that datetime column is created from timestamps"""
        log_file = Path(temp_log_dir) / "streamlit_backroom_2025-01-15.txt"
        log_file.write_text("[10:00:00] Bot$ Message\n", encoding='utf-8')

        df = parser.parse_all_logs()

        assert 'datetime' in df.columns

    def test_parse_all_logs_sorts_by_datetime(self, temp_log_dir, parser):
        """Test that results are sorted by datetime (newest first)"""
        log_file = Path(temp_log_dir) / "streamlit_backroom_2025-01-15.txt"
        content = """[10:00:00] Bot1$ First
[10:00:01] Bot2$ Second
[10:00:02] Bot3$ Third
"""
        log_file.write_text(content, encoding='utf-8')

        df = parser.parse_all_logs()

        # Should be in descending order (newest first)
        assert df.iloc[0]['timestamp'] == '10:00:02'
        assert df.iloc[1]['timestamp'] == '10:00:01'
        assert df.iloc[2]['timestamp'] == '10:00:00'
