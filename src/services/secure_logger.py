"""Secure conversation logging service with comprehensive security protections."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.utils.constants import LOG_DIRECTORY, LOG_FILE_PREFIX

# Configure secure logging
secure_logger = logging.getLogger('secure_logger')
secure_logger.setLevel(logging.INFO)


class SecurityError(Exception):
    """Security-related errors for logging operations."""
    pass


class PathValidator:
    """Validates and sanitizes file paths to prevent directory traversal attacks."""

    # Dangerous path components that should never be allowed
    DANGEROUS_COMPONENTS = {
        '..', '~', '$', '%', '&', '*', ';', '|', '`', '$(', '${',
        '<', '>', '"', "'", '\\', '\n', '\r', '\t', '\x00'
    }

    # Dangerous file extensions that should never be allowed
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js',
        '.jar', '.app', '.deb', '.rpm', '.dmg', '.pkg', '.msi', '.sh'
    }

    @staticmethod
    def validate_log_directory(log_dir: str, base_allowed_path: Optional[str] = None) -> Path:
        """Validate and secure the log directory path.

        Args:
            log_dir: The requested log directory
            base_allowed_path: Base path that logs are allowed in (optional)

        Returns:
            Validated and secured Path object

        Raises:
            SecurityError: If path is dangerous or invalid
        """
        if not log_dir or not isinstance(log_dir, str):
            raise SecurityError("Invalid log directory: must be a non-empty string")

        # Sanitize the input path
        sanitized_path = PathValidator.sanitize_path_component(log_dir)

        try:
            requested_path = Path(sanitized_path).resolve()
        except (OSError, ValueError) as e:
            raise SecurityError(f"Invalid path format: {e}")

        # If base_allowed_path is specified, ensure the log directory is within it
        if base_allowed_path:
            try:
                base_path = Path(base_allowed_path).resolve()
                if not str(requested_path).startswith(str(base_path)):
                    raise SecurityError(
                        f"Log directory must be within allowed base path: {base_allowed_path}"
                    )
            except (OSError, ValueError) as e:
                raise SecurityError(f"Invalid base path: {e}")

        # Additional security checks
        PathValidator.check_path_safety(requested_path)

        return requested_path

    @staticmethod
    def validate_filename(filename: str) -> str:
        """Validate and sanitize a filename.

        Args:
            filename: The requested filename

        Returns:
            Sanitized filename

        Raises:
            SecurityError: If filename is dangerous or invalid
        """
        if not filename or not isinstance(filename, str):
            raise SecurityError("Invalid filename: must be a non-empty string")

        # Remove path separators and dangerous characters
        sanitized = PathValidator.sanitize_path_component(filename)

        # Ensure it's just a filename, not a path
        sanitized = Path(sanitized).name

        # Check for dangerous extensions
        file_ext = Path(sanitized).suffix.lower()
        if file_ext in PathValidator.DANGEROUS_EXTENSIONS:
            raise SecurityError(f"Dangerous file extension not allowed: {file_ext}")

        # Ensure filename is not too long (prevent DoS)
        if len(sanitized) > 255:
            raise SecurityError("Filename too long (max 255 characters)")

        # Ensure filename is not empty after sanitization
        if not sanitized or sanitized in ('.', '..'):
            raise SecurityError("Invalid filename after sanitization")

        return sanitized

    @staticmethod
    def sanitize_path_component(path_component: str) -> str:
        """Sanitize a path component to remove dangerous characters.

        Args:
            path_component: The path component to sanitize

        Returns:
            Sanitized path component
        """
        if not path_component:
            return ""

        # Replace dangerous characters with underscores
        sanitized = path_component
        for dangerous in PathValidator.DANGEROUS_COMPONENTS:
            sanitized = sanitized.replace(dangerous, '_')

        # Remove control characters
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)

        # Remove consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)

        # Strip leading/trailing underscores and whitespace
        sanitized = sanitized.strip('_ ').strip()

        return sanitized

    @staticmethod
    def check_path_safety(path: Path) -> None:
        """Check if a path is safe for logging operations.

        Args:
            path: The path to check

        Raises:
            SecurityError: If path is unsafe
        """
        # Check for symlinks that could lead to unauthorized locations
        if path.exists() and path.is_symlink():
            try:
                resolved = path.resolve()
                # Ensure resolved path is still within expected bounds
                if not str(resolved).startswith(str(path.parent.resolve())):
                    raise SecurityError("Symbolic link points outside allowed directory")
            except (OSError, ValueError):
                raise SecurityError("Invalid symbolic link")

        # Check for suspicious path patterns
        path_str = str(path).lower()
        suspicious_patterns = [
            'system32', 'windows', 'program files', 'etc/passwd',
            'etc/shadow', 'proc/', 'sys/', 'dev/'
        ]

        for pattern in suspicious_patterns:
            if pattern in path_str:
                secure_logger.warning(f"Suspicious path pattern detected: {pattern} in {path}")


class InputSanitizer:
    """Sanitizes input data to prevent injection attacks."""

    @staticmethod
    def sanitize_message(message: str, max_length: int = 10000) -> str:
        """Sanitize message content for safe logging.

        Args:
            message: The message to sanitize
            max_length: Maximum allowed message length

        Returns:
            Sanitized message
        """
        if not isinstance(message, str):
            message = str(message)

        # Remove thinking blocks (preserve existing functionality)
        sanitized = re.sub(r"<thinking>.*?</thinking>", "", message, flags=re.DOTALL | re.IGNORECASE)

        # Remove dangerous content that could be exploited in log files
        sanitized = InputSanitizer._remove_dangerous_content(sanitized)

        # Control character sanitization
        sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', sanitized)

        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()

        # Length validation to prevent log file bloat/DoS
        if len(sanitized) > max_length:
            truncated = sanitized[:max_length-3] + "..."
            secure_logger.warning(f"Message truncated due to length limit: {len(sanitized)} -> {len(truncated)}")
            sanitized = truncated

        return sanitized

    @staticmethod
    def sanitize_persona(persona: str, max_length: int = 100) -> str:
        """Sanitize persona name for safe logging.

        Args:
            persona: The persona name to sanitize
            max_length: Maximum allowed persona length

        Returns:
            Sanitized persona name
        """
        if not isinstance(persona, str):
            persona = str(persona)

        # Remove dangerous characters
        sanitized = re.sub(r'[<>"\'&;|`$()\\[\]{}]', '', persona)

        # Remove control characters
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)

        # Normalize whitespace
        sanitized = re.sub(r'\s+', '_', sanitized.strip())

        # Length validation
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized

    @staticmethod
    def _remove_dangerous_content(content: str) -> str:
        """Remove potentially dangerous content from messages.

        Args:
            content: The content to clean

        Returns:
            Cleaned content
        """
        # Remove script-like content
        script_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'on\w+\s*=',  # Event handlers like onclick=
            r'expression\s*\(',
        ]

        for pattern in script_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)

        # Remove potential file paths that shouldn't be in logs
        path_patterns = [
            r'[A-Za-z]:[\\/][\w\\./]*',  # Windows paths
            r'/[\w./-]*\.(conf|config|key|pem|p12)',  # Config/keys
        ]

        for pattern in path_patterns:
            content = re.sub(pattern, '[REDACTED_PATH]', content, flags=re.IGNORECASE)

        return content


class AtomicFileWriter:
    """Provides atomic file writing operations to prevent log corruption."""

    @staticmethod
    def write_atomically(file_path: Path, content: str, encoding: str = 'utf-8') -> None:
        """Write content to a file atomically.

        Args:
            file_path: Path to the file to write
            content: Content to write
            encoding: File encoding

        Raises:
            SecurityError: If write operation fails
        """
        if not content:
            return  # Nothing to write

        # Ensure parent directory exists
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise SecurityError(f"Failed to create parent directory: {e}")

        # Create temporary file in the same directory
        try:
            temp_fd, temp_path = tempfile.mkstemp(
                prefix='.tmp_log_',
                suffix='.tmp',
                dir=file_path.parent
            )
        except OSError as e:
            raise SecurityError(f"Failed to create temporary file: {e}")

        try:
            # Write to temporary file
            with os.fdopen(temp_fd, 'w', encoding=encoding) as temp_file:
                temp_file.write(content)
                temp_file.flush()
                os.fsync(temp_file.fileno())  # Force write to disk

            # Atomic move to final location
            os.replace(temp_path, file_path)

        except (OSError, IOError) as e:
            # Clean up temp file if write failed
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise SecurityError(f"Failed to write file atomically: {e}")

    @staticmethod
    def append_atomically(file_path: Path, content: str, encoding: str = 'utf-8') -> None:
        """Append content to a file with proper locking.

        Args:
            file_path: Path to the file to append
            content: Content to append
            encoding: File encoding

        Raises:
            SecurityError: If append operation fails
        """
        if not content:
            return  # Nothing to write

        # Ensure parent directory exists
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise SecurityError(f"Failed to create parent directory: {e}")

        # Use file locking for safe appending
        lock_file = file_path.with_suffix(file_path.suffix + '.lock')

        try:
            # Acquire lock
            with open(lock_file, 'w') as lock:
                # Try to acquire exclusive lock
                import fcntl
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX)

                # Append to file
                with open(file_path, 'a', encoding=encoding) as f:
                    f.write(content)
                    f.flush()
                    os.fsync(f.fileno())  # Force write to disk

        except ImportError:
            # Fallback for systems without fcntl (Windows)
            try:
                with open(file_path, 'a', encoding=encoding) as f:
                    f.write(content)
                    f.flush()
                    os.fsync(f.fileno())
            except (OSError, IOError) as e:
                raise SecurityError(f"Failed to append to file: {e}")
        except (OSError, IOError) as e:
            raise SecurityError(f"Failed to acquire lock or append to file: {e}")
        finally:
            # Clean up lock file
            try:
                if lock_file.exists():
                    lock_file.unlink()
            except OSError:
                pass


class SecureConversationLogger:
    """Secure conversation logger with comprehensive security protections.

    Features:
    - Path validation and sandboxing to prevent directory traversal
    - Input sanitization to prevent injection attacks
    - Atomic file writing to prevent log corruption
    - Thread-safe operations
    - Comprehensive error handling
    - Activity monitoring and audit logging
    """

    def __init__(
        self,
        log_dir: str = str(LOG_DIRECTORY),
        max_message_length: int = 10000,
        max_persona_length: int = 100,
        enable_audit_logging: bool = True
    ) -> None:
        """Initialize secure conversation logger.

        Args:
            log_dir: Directory to store log files
            max_message_length: Maximum allowed message length
            max_persona_length: Maximum allowed persona name length
            enable_audit_logging: Whether to enable audit logging

        Raises:
            SecurityError: If initialization fails security checks
        """
        self.max_message_length = max_message_length
        self.max_persona_length = max_persona_length
        self.enable_audit_logging = enable_audit_logging
        self._lock = threading.RLock()

        # Validate and secure log directory
        self.log_dir = PathValidator.validate_log_directory(log_dir)

        # Create log directory if it doesn't exist
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            # Set secure permissions (owner read/write/execute only)
            os.chmod(self.log_dir, 0o700)
        except OSError as e:
            raise SecurityError(f"Failed to create secure log directory: {e}")

        # Initialize audit logger
        if self.enable_audit_logging:
            self._init_audit_logger()

        secure_logger.info(f"SecureConversationLogger initialized with directory: {self.log_dir}")

    def _init_audit_logger(self) -> None:
        """Initialize audit logging for security events."""
        self.audit_log_file = self.log_dir / "security_audit.log"

        # Ensure audit log exists with secure permissions
        if not self.audit_log_file.exists():
            AtomicFileWriter.write_atomically(
                self.audit_log_file,
                f"# Security audit log started at {datetime.now().isoformat()}\n"
            )

        # Set secure permissions
        try:
            os.chmod(self.audit_log_file, 0o600)
        except OSError:
            secure_logger.warning("Failed to set secure permissions on audit log")

    def _log_security_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log a security event to the audit log.

        Args:
            event_type: Type of security event
            details: Event details
        """
        if not self.enable_audit_logging:
            return

        try:
            event_record = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'details': details
            }

            audit_entry = json.dumps(event_record) + '\n'
            AtomicFileWriter.append_atomically(self.audit_log_file, audit_entry)

        except Exception as e:
            secure_logger.error(f"Failed to log security event: {e}")

    def get_daily_log_file(self) -> Path:
        """Get the log file path for today with validation.

        Returns:
            Validated Path object for today's log file
        """
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"{LOG_FILE_PREFIX}_{today}.txt"

        # Validate filename
        safe_filename = PathValidator.validate_filename(filename)

        log_file = self.log_dir / safe_filename
        PathValidator.check_path_safety(log_file)

        return log_file

    def get_daily_log_file_for_date(self, date: datetime) -> Path:
        """Get the log file path for a specific date with validation.

        Args:
            date: Date for the log file

        Returns:
            Validated Path object for the specified date's log file
        """
        date_str = date.strftime("%Y-%m-%d")
        filename = f"{LOG_FILE_PREFIX}_{date_str}.txt"

        # Validate filename
        safe_filename = PathValidator.validate_filename(filename)

        log_file = self.log_dir / safe_filename
        PathValidator.check_path_safety(log_file)

        return log_file

    def clean_message(self, message: str) -> str:
        """Clean and sanitize message content.

        Args:
            message: Raw message text potentially containing thinking tags

        Returns:
            Sanitized message with dangerous content removed
        """
        with self._lock:
            try:
                cleaned = InputSanitizer.sanitize_message(
                    message,
                    self.max_message_length
                )

                # Log sanitization if significant content was removed
                if len(cleaned) < len(message) * 0.8:
                    self._log_security_event('message_sanitized', {
                        'original_length': len(message),
                        'cleaned_length': len(cleaned),
                        'reduction_percentage': round((1 - len(cleaned)/len(message)) * 100, 2)
                    })

                return cleaned

            except Exception as e:
                self._log_security_event('message_sanitization_error', {
                    'error': str(e),
                    'message_length': len(message) if message else 0
                })
                # Return safe fallback
                return "[Message sanitization failed]"

    def log_message(
        self,
        persona: str,
        message: str,
        timestamp: Optional[datetime] = None
    ) -> None:
        """Log a message securely with comprehensive validation.

        Args:
            persona: Name of the persona sending the message
            message: Message content
            timestamp: Optional timestamp (defaults to now)

        Raises:
            SecurityError: If logging fails security validation
        """
        with self._lock:
            if timestamp is None:
                timestamp = datetime.now()

            try:
                # Validate and sanitize inputs
                safe_persona = InputSanitizer.sanitize_persona(
                    persona,
                    self.max_persona_length
                )
                safe_message = self.clean_message(message)

                # Only log if there's content after cleaning
                if not safe_message.strip():
                    self._log_security_event('empty_message_logged', {
                        'persona': safe_persona,
                        'original_length': len(message) if message else 0
                    })
                    return

                # Get validated log file path
                log_file = self.get_daily_log_file_for_date(timestamp)

                # Format log entry safely
                log_entry = self._format_log_entry(safe_persona, safe_message, timestamp)

                # Write atomically
                AtomicFileWriter.append_atomically(log_file, log_entry)

                # Log successful write (for monitoring)
                self._log_security_event('message_logged', {
                    'persona': safe_persona,
                    'message_length': len(safe_message),
                    'log_file': str(log_file)
                })

            except SecurityError:
                # Re-raise security errors
                raise
            except Exception as e:
                self._log_security_event('logging_error', {
                    'error': str(e),
                    'persona': persona if persona else 'unknown',
                    'timestamp': timestamp.isoformat() if timestamp else None
                })
                raise SecurityError(f"Failed to log message: {e}")

    def _format_log_entry(self, persona: str, message: str, timestamp: datetime) -> str:
        """Format a log entry safely.

        Args:
            persona: Sanitized persona name
            message: Sanitized message content
            timestamp: Timestamp for the entry

        Returns:
            Formatted log entry
        """
        # Use safe formatting to prevent injection
        time_str = timestamp.strftime('%H:%M:%S')
        return f"[{time_str}] {persona}$ {message}\n"

    def parse_log_file(self, log_file_path: str) -> List[Dict[str, str]]:
        """Parse a log file safely with comprehensive validation.

        Args:
            log_file_path: Path to the log file to parse

        Returns:
            List of dictionaries containing parsed message data

        Raises:
            SecurityError: If file path is invalid or unsafe
        """
        with self._lock:
            try:
                # Validate the requested file path
                if not isinstance(log_file_path, str):
                    raise SecurityError("Invalid file path type")

                requested_path = Path(log_file_path)

                # Ensure the file is within our log directory
                if not str(requested_path.resolve()).startswith(str(self.log_dir.resolve())):
                    raise SecurityError("Attempted to access file outside log directory")

                # Validate filename
                PathValidator.validate_filename(requested_path.name)

                # Check file safety
                PathValidator.check_path_safety(requested_path)

                # Ensure it's a regular file within our log directory pattern
                if not requested_path.is_file():
                    return []

                # Verify it's a log file (basic pattern check)
                if not requested_path.name.startswith(LOG_FILE_PREFIX):
                    raise SecurityError("Invalid log file name pattern")

                # Read file size to prevent processing extremely large files
                file_size = requested_path.stat().st_size
                if file_size > 50 * 1024 * 1024:  # 50MB limit
                    raise SecurityError("Log file too large to parse safely")

                # Read and parse content
                content = requested_path.read_text(encoding='utf-8')

                # Parse log format with validation
                return self._parse_log_content(content)

            except SecurityError:
                raise
            except Exception as e:
                self._log_security_event('log_parsing_error', {
                    'error': str(e),
                    'file_path': log_file_path
                })
                raise SecurityError(f"Failed to parse log file: {e}")

    def _parse_log_content(self, content: str) -> List[Dict[str, str]]:
        """Parse log content safely.

        Args:
            content: Log file content

        Returns:
            Parsed message data
        """
        messages = []

        if not content:
            return messages

        # Parse log format: [HH:MM:SS] PersonaName$ Message content
        pattern = r'\[(\d{2}:\d{2}:\d{2})\]\s+([^$]+)\$\s+(.+)'

        line_number = 0
        for line in content.split('\n'):
            line_number += 1

            if not line.strip():
                continue

            try:
                match = re.match(pattern, line)
                if match:
                    timestamp, persona, message_content = match.groups()

                    # Sanitize parsed data
                    clean_timestamp = InputSanitizer.sanitize_message(timestamp.strip(), 20)
                    clean_persona = InputSanitizer.sanitize_persona(persona.strip(), 100)
                    clean_content = InputSanitizer.sanitize_message(message_content.strip())

                    messages.append({
                        'timestamp': clean_timestamp,
                        'persona': clean_persona,
                        'content': clean_content
                    })
                else:
                    # Log unexpected format
                    if line_number < 1000:  # Don't spam the audit log
                        self._log_security_event('unexpected_log_format', {
                            'line_number': line_number,
                            'line_preview': line[:100] if line else ''
                        })

            except Exception as e:
                self._log_security_event('log_line_parsing_error', {
                    'line_number': line_number,
                    'error': str(e)
                })
                continue

        return messages

    def get_security_status(self) -> Dict[str, Any]:
        """Get security status and statistics.

        Returns:
            Dictionary containing security status information
        """
        with self._lock:
            try:
                status = {
                    'log_directory': str(self.log_dir),
                    'directory_exists': self.log_dir.exists(),
                    'directory_writable': os.access(self.log_dir, os.W_OK),
                    'audit_logging_enabled': self.enable_audit_logging,
                    'audit_log_exists': self.audit_log_file.exists() if self.enable_audit_logging else False,
                    'log_files': [],
                    'security_events_count': 0
                }

                # Count log files
                if status['directory_exists']:
                    for log_file in self.log_dir.glob(f"{LOG_FILE_PREFIX}_*.txt"):
                        try:
                            file_stat = log_file.stat()
                            status['log_files'].append({
                                'name': log_file.name,
                                'size': file_stat.st_size,
                                'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                            })
                        except OSError:
                            continue

                # Count security events if audit logging is enabled
                if self.enable_audit_logging and self.audit_log_file.exists():
                    try:
                        content = self.audit_log_file.read_text(encoding='utf-8')
                        # Count non-comment lines
                        status['security_events_count'] = len([
                            line for line in content.split('\n')
                            if line.strip() and not line.startswith('#')
                        ])
                    except OSError:
                        pass

                return status

            except Exception as e:
                self._log_security_event('security_status_error', {
                    'error': str(e)
                })
                return {'error': f'Failed to get security status: {e}'}