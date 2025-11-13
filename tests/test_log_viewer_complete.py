"""Comprehensive tests for log_viewer module to achieve 80%+ coverage"""

import re
import shutil
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest

from log_viewer import (
    LogParser,
    apply_filters,
    create_sidebar_filters,
    display_messages,
    display_persona_breakdown,
    display_statistics,
)


class TestLogParserErrorHandling:
    """Test error handling in LogParser"""

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

    def test_get_available_log_files_nonexistent_directory(self):
        """Test that empty list is returned when directory doesn't exist"""
        parser = LogParser(log_dir="/nonexistent/directory/12345")
        log_files = parser.get_available_log_files()
        assert log_files == []

    def test_parse_log_file_handles_os_error(self, parser, temp_log_dir):
        """Test handling of OSError when reading log file"""
        log_file = Path(temp_log_dir) / "test.txt"
        log_file.write_text("[10:00:00] Bot$ Message\n", encoding='utf-8')

        # Mock open to raise OSError
        with patch('builtins.open', side_effect=OSError("Permission denied")):
            with patch('streamlit.error') as mock_error:
                messages = parser.parse_log_file(log_file)
                assert len(messages) == 0
                mock_error.assert_called_once()

    def test_parse_log_file_handles_unicode_error(self, parser, temp_log_dir):
        """Test handling of UnicodeDecodeError"""
        log_file = Path(temp_log_dir) / "test.txt"
        log_file.write_bytes(b'\xff\xfe Invalid UTF-8')

        with patch('streamlit.error') as mock_error:
            messages = parser.parse_log_file(log_file)
            assert len(messages) == 0
            mock_error.assert_called_once()

    def test_parse_log_file_handles_value_error(self, parser, temp_log_dir):
        """Test handling of ValueError during parsing"""
        log_file = Path(temp_log_dir) / "test.txt"
        log_file.write_text("[10:00:00] Bot$ Message\n", encoding='utf-8')

        # Mock re.match to raise ValueError
        with patch('re.match', side_effect=ValueError("Invalid regex")):
            with patch('streamlit.error') as mock_error:
                messages = parser.parse_log_file(log_file)
                assert len(messages) == 0
                mock_error.assert_called_once()

    def test_parse_all_logs_handles_datetime_parse_error(self, parser, temp_log_dir):
        """Test handling of datetime parsing errors"""
        log_file = Path(temp_log_dir) / "test_invalid_date.txt"
        log_file.write_text("[99:99:99] Bot$ Invalid timestamp\n", encoding='utf-8')

        with patch('logging.warning') as mock_warning:
            df = parser.parse_all_logs()
            # Should still return dataframe with NaT for datetime
            if not df.empty:
                assert 'datetime' in df.columns


class TestApplyFilters:
    """Test apply_filters function"""

    @pytest.fixture
    def sample_df(self):
        """Create a sample dataframe for testing"""
        return pd.DataFrame({
            'persona': ['Bot1', 'Bot2', 'Bot1', 'Bot3'],
            'message': ['Hello world', 'Test message', 'Another test', 'Final message'],
            'datetime': pd.to_datetime([
                '2025-01-15 10:00:00',
                '2025-01-15 11:00:00',
                '2025-01-16 10:00:00',
                '2025-01-16 11:00:00'
            ])
        })

    def test_apply_filters_empty_dataframe(self):
        """Test that empty dataframe is returned unchanged"""
        empty_df = pd.DataFrame()
        result = apply_filters(empty_df, [], "", "Contains", date.today(), date.today())
        assert result.empty

    def test_apply_filters_persona_filter(self, sample_df):
        """Test filtering by persona"""
        result = apply_filters(sample_df, ['Bot1'], "", "Contains",
                             date(2025, 1, 15), date(2025, 1, 16))
        assert len(result) == 2
        assert all(result['persona'] == 'Bot1')

    def test_apply_filters_empty_persona_list(self, sample_df):
        """Test with empty persona list returns all"""
        result = apply_filters(sample_df, [], "", "Contains",
                             date(2025, 1, 15), date(2025, 1, 16))
        assert len(result) == len(sample_df)

    def test_apply_filters_date_range(self, sample_df):
        """Test filtering by date range"""
        result = apply_filters(sample_df, ['Bot1', 'Bot2', 'Bot3'], "", "Contains",
                             date(2025, 1, 15), date(2025, 1, 15))
        assert len(result) == 2  # Only messages from Jan 15

    def test_apply_filters_search_contains(self, sample_df):
        """Test search with 'Contains' mode"""
        result = apply_filters(sample_df, ['Bot1', 'Bot2', 'Bot3'], "test", "Contains",
                             date(2025, 1, 15), date(2025, 1, 16))
        assert len(result) == 2  # Messages containing 'test'

    def test_apply_filters_search_exact_match(self, sample_df):
        """Test search with 'Exact Match' mode"""
        result = apply_filters(sample_df, ['Bot1', 'Bot2', 'Bot3'], "hello", "Exact Match",
                             date(2025, 1, 15), date(2025, 1, 16))
        assert len(result) == 1
        assert 'Hello world' in result['message'].values

    def test_apply_filters_search_regex(self, sample_df):
        """Test search with 'Regex' mode"""
        result = apply_filters(sample_df, ['Bot1', 'Bot2', 'Bot3'], r'^Test.*', "Regex",
                             date(2025, 1, 15), date(2025, 1, 16))
        assert len(result) == 1

    def test_apply_filters_invalid_regex(self, sample_df):
        """Test handling of invalid regex pattern"""
        with patch('streamlit.error') as mock_error:
            result = apply_filters(sample_df, ['Bot1', 'Bot2', 'Bot3'], '[invalid(', "Regex",
                                 date(2025, 1, 15), date(2025, 1, 16))
            assert len(result) == 0  # No matches due to invalid regex
            mock_error.assert_called_once()

    def test_apply_filters_combined(self, sample_df):
        """Test applying multiple filters together"""
        result = apply_filters(sample_df, ['Bot1'], "test", "Contains",
                             date(2025, 1, 15), date(2025, 1, 16))
        assert len(result) == 1
        assert result.iloc[0]['persona'] == 'Bot1'
        assert 'test' in result.iloc[0]['message'].lower()


class TestCreateSidebarFilters:
    """Test create_sidebar_filters function"""

    def test_create_sidebar_filters_empty_dataframe(self):
        """Test with empty dataframe"""
        empty_df = pd.DataFrame()

        with patch('streamlit.sidebar') as mock_sidebar:
            mock_sidebar.header = Mock()
            mock_sidebar.multiselect = Mock(return_value=[])
            mock_sidebar.text_input = Mock(return_value="")
            mock_sidebar.radio = Mock(return_value="Contains")
            mock_sidebar.date_input = Mock(return_value=date.today())
            mock_sidebar.caption = Mock()

            personas, search_term, search_type, start_date, end_date = create_sidebar_filters(empty_df)

            assert personas == []
            assert search_term == ""
            assert search_type == "Contains"

    def test_create_sidebar_filters_with_data(self):
        """Test with valid dataframe"""
        df = pd.DataFrame({
            'persona': ['Bot1', 'Bot2'],
            'message': ['Hello', 'World'],
            'datetime': pd.to_datetime(['2025-01-15', '2025-01-16'])
        })

        with patch('streamlit.sidebar') as mock_sidebar:
            mock_sidebar.header = Mock()
            mock_sidebar.multiselect = Mock(return_value=['Bot1'])
            mock_sidebar.text_input = Mock(return_value="test")
            mock_sidebar.radio = Mock(return_value="Contains")
            mock_sidebar.date_input = Mock(side_effect=[date(2025, 1, 15), date(2025, 1, 16)])
            mock_sidebar.caption = Mock()

            personas, search_term, search_type, start_date, end_date = create_sidebar_filters(df)

            assert personas == ['Bot1']
            assert search_term == "test"
            assert search_type == "Contains"
            # Verify caption is called when search is active
            mock_sidebar.caption.assert_called()

    def test_create_sidebar_filters_nat_dates(self):
        """Test handling of NaT dates in dataframe"""
        df = pd.DataFrame({
            'persona': ['Bot1'],
            'message': ['Hello'],
            'datetime': pd.Series([pd.NaT], dtype='datetime64[ns]')
        })

        with patch('streamlit.sidebar') as mock_sidebar:
            mock_sidebar.header = Mock()
            mock_sidebar.multiselect = Mock(return_value=['Bot1'])
            mock_sidebar.text_input = Mock(return_value="")
            mock_sidebar.radio = Mock(return_value="Contains")

            personas, search_term, search_type, start_date, end_date = create_sidebar_filters(df)

            # Should default to today's date when dates are NaT
            assert start_date == date.today()
            assert end_date == date.today()


class TestDisplayFunctions:
    """Test display functions"""

    def test_display_statistics_empty_dataframe(self):
        """Test display_statistics with empty dataframe"""
        empty_df = pd.DataFrame()

        with patch('streamlit.info') as mock_info:
            display_statistics(empty_df)
            mock_info.assert_called_once_with("No messages to display")

    def test_display_statistics_with_data(self):
        """Test display_statistics with valid dataframe"""
        df = pd.DataFrame({
            'persona': ['Bot1', 'Bot2', 'Bot1'],
            'message_length': [10, 20, 15],
            'file': ['file1.txt', 'file1.txt', 'file2.txt'],
            'datetime': pd.to_datetime(['2025-01-15', '2025-01-16', '2025-01-17'])
        })

        with patch('streamlit.columns') as mock_columns, \
             patch('streamlit.metric') as mock_metric:

            # Mock column context managers
            mock_col = MagicMock()
            mock_col.__enter__ = Mock(return_value=mock_col)
            mock_col.__exit__ = Mock(return_value=False)
            mock_col.metric = Mock()
            mock_columns.return_value = [mock_col, mock_col, mock_col, mock_col]

            display_statistics(df)

            # Verify columns were created
            mock_columns.assert_called_once_with(4)

    def test_display_persona_breakdown_empty_dataframe(self):
        """Test display_persona_breakdown with empty dataframe"""
        empty_df = pd.DataFrame()

        # Should return early without error
        display_persona_breakdown(empty_df)

    def test_display_persona_breakdown_with_data(self):
        """Test display_persona_breakdown with valid dataframe"""
        df = pd.DataFrame({
            'persona': ['Bot1', 'Bot2', 'Bot1', 'Bot2'],
            'message': ['Hi', 'Hello', 'Test', 'World'],
            'message_length': [10, 20, 15, 25]
        })

        with patch('streamlit.subheader') as mock_subheader, \
             patch('streamlit.columns') as mock_columns, \
             patch('streamlit.dataframe') as mock_dataframe, \
             patch('streamlit.bar_chart') as mock_bar_chart:

            # Mock column context managers
            mock_col = MagicMock()
            mock_col.__enter__ = Mock(return_value=mock_col)
            mock_col.__exit__ = Mock(return_value=False)
            mock_col.dataframe = Mock()
            mock_col.bar_chart = Mock()
            mock_columns.return_value = [mock_col, mock_col]

            display_persona_breakdown(df)

            # Verify subheader was called
            mock_subheader.assert_called_once()

    def test_display_messages_empty_dataframe(self):
        """Test display_messages with empty dataframe"""
        empty_df = pd.DataFrame()

        with patch('streamlit.info') as mock_info:
            display_messages(empty_df)
            mock_info.assert_called_once()

    def test_display_messages_chat_view(self):
        """Test display_messages with Chat View format"""
        df = pd.DataFrame({
            'persona': ['Bot1', 'Bot2'],
            'message': ['Hello', 'World'],
            'timestamp': ['10:00:00', '10:00:01'],
            'datetime': pd.to_datetime(['2025-01-15 10:00:00', '2025-01-15 10:00:01'])
        })

        with patch('streamlit.subheader') as mock_subheader, \
             patch('streamlit.columns') as mock_columns, \
             patch('streamlit.radio') as mock_radio, \
             patch('streamlit.selectbox') as mock_selectbox, \
             patch('streamlit.container') as mock_container, \
             patch('streamlit.write') as mock_write, \
             patch('streamlit.caption') as mock_caption, \
             patch('streamlit.divider') as mock_divider:

            # Mock components
            mock_col = MagicMock()
            mock_col.__enter__ = Mock(return_value=mock_col)
            mock_col.__exit__ = Mock(return_value=False)
            mock_col.radio = Mock(return_value="Chat View")
            mock_col.selectbox = Mock(return_value="newest")
            mock_columns.return_value = [mock_col, mock_col]

            mock_radio.return_value = "Chat View"
            mock_selectbox.return_value = "newest"

            mock_cont = MagicMock()
            mock_cont.__enter__ = Mock(return_value=mock_cont)
            mock_cont.__exit__ = Mock(return_value=False)
            mock_container.return_value = mock_cont

            display_messages(df)

            mock_subheader.assert_called_once()

    def test_display_messages_table_view(self):
        """Test display_messages with Table View format"""
        df = pd.DataFrame({
            'persona': ['Bot1'],
            'message': ['Hello'],
            'timestamp': ['10:00:00'],
            'file': ['test.txt'],
            'message_length': [5],
            'datetime': pd.to_datetime(['2025-01-15 10:00:00'])
        })

        with patch('streamlit.subheader'), \
             patch('streamlit.columns') as mock_columns, \
             patch('streamlit.radio', return_value="Table View"), \
             patch('streamlit.multiselect', return_value=['timestamp', 'persona', 'message']), \
             patch('streamlit.dataframe') as mock_dataframe:

            mock_col = MagicMock()
            mock_col.__enter__ = Mock(return_value=mock_col)
            mock_col.__exit__ = Mock(return_value=False)
            mock_col.radio = Mock(return_value="Table View")
            mock_columns.return_value = [mock_col, mock_col]

            display_messages(df)

            mock_dataframe.assert_called_once()

    def test_display_messages_raw_text(self):
        """Test display_messages with Raw Text format"""
        df = pd.DataFrame({
            'persona': ['Bot1'],
            'message': ['Hello'],
            'timestamp': ['10:00:00'],
            'datetime': pd.to_datetime(['2025-01-15 10:00:00'])
        })

        with patch('streamlit.subheader'), \
             patch('streamlit.columns') as mock_columns, \
             patch('streamlit.radio', return_value="Raw Text"), \
             patch('streamlit.text_area') as mock_text_area:

            mock_col = MagicMock()
            mock_col.__enter__ = Mock(return_value=mock_col)
            mock_col.__exit__ = Mock(return_value=False)
            mock_col.radio = Mock(return_value="Raw Text")
            mock_columns.return_value = [mock_col, mock_col]

            display_messages(df)

            mock_text_area.assert_called_once()
