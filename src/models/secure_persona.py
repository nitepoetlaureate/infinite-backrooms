"""Secure AI Persona data model with comprehensive security controls.

This module implements a security-enhanced version of AIPersona that includes:
- Input sanitization and validation
- Authorization controls
- Audit logging
- Secure configuration management
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Set, Tuple

from src.utils.sanitization import sanitize_html, sanitize_json_string, sanitize_markdown
from src.utils.validation import (
    validate_color,
    validate_model_name,
    validate_persona_name,
    validate_role,
    validate_system_prompt,
)
from src.utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

# Constants for security
MAX_SANITIZED_LENGTH = 50000
HASH_SALT = "AI_BACKROOM_SECURE_SALT"  # In production, use environment variable
ALLOWED_PERMISSIONS = {
    'read_conversation',
    'write_conversation',
    'manage_persona',
    'export_data',
    'configure_settings'
}


class SecurityError(Exception):
    """Security-related exceptions."""
    pass


@dataclass
class AuditLog:
    """Audit log entry for security events."""
    timestamp: datetime
    action: str
    user_id: str
    resource_id: str
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class SecurityContext:
    """Security context for persona operations."""
    user_id: str
    permissions: Set[str] = field(default_factory=set)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class SecureAIPersona:
    """Security-enhanced AI Persona with comprehensive input validation and audit controls.

    This class provides:
    - Comprehensive input sanitization and validation
    - Secure configuration management
    - Audit logging of all operations
    - Authorization controls
    - Rate limiting protection
    - Secure storage of sensitive data

    Attributes:
        id: Unique identifier for the persona (UUID v4)
        name: Display name of the persona (sanitized)
        model: Ollama model to use (validated)
        role: Optional role for personality/behavior (sanitized)
        system_prompt: Custom system prompt instructions (sanitized)
        color: Color for UI display (validated hex format)
        enabled: Whether this persona is active in conversations
        created_at: Creation timestamp for audit purposes
        updated_at: Last modification timestamp
        created_by: User ID who created this persona
        permissions: Set of permissions for this persona
        checksum: Integrity checksum for verification

    Security Features:
        - All inputs are validated and sanitized
        - Audit logging for all modifications
        - Authorization checks for sensitive operations
        - Rate limiting to prevent abuse
        - Integrity verification via checksums
        - Secure storage of configuration
    """

    id: str
    name: str
    model: str
    role: str = ""
    system_prompt: str = ""
    color: str = "#1f77b4"
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = ""
    permissions: Set[str] = field(default_factory=lambda: {'read_conversation', 'write_conversation'})
    checksum: str = ""
    _rate_limiter: RateLimiter = field(default_factory=lambda: RateLimiter(max_requests=100, time_window=3600))

    def __post_init__(self) -> None:
        """Validate and initialize the secure persona.

        Raises:
            SecurityError: If security validation fails
            ValueError: If basic validation fails
        """
        self._validate_initialization()
        self._sanitize_all_fields()
        self._verify_integrity()

        # Generate initial checksum if not provided
        if not self.checksum:
            self.checksum = self._calculate_checksum()

        # Log creation event
        self._log_security_event("PERSONA_CREATED", {
            "persona_id": self.id,
            "name": self.name,
            "model": self.model
        })

    def _validate_initialization(self) -> None:
        """Validate initialization parameters."""
        if not self.id or not isinstance(self.id, str):
            raise SecurityError("Valid ID is required")

        # Validate UUID format
        try:
            uuid.UUID(self.id)
        except ValueError:
            raise SecurityError("ID must be a valid UUID")

        if not self.created_by or not isinstance(self.created_by, str):
            raise SecurityError("Creator user ID is required")

        # Validate permissions
        invalid_perms = self.permissions - ALLOWED_PERMISSIONS
        if invalid_perms:
            raise SecurityError(f"Invalid permissions: {invalid_perms}")

    def _sanitize_all_fields(self) -> None:
        """Sanitize all text fields to prevent injection attacks."""
        self.name = self._sanitize_field("name", self.name, validate_persona_name)
        self.model = self._sanitize_field("model", self.model, validate_model_name)
        self.role = self._sanitize_field("role", self.role, validate_role)
        self.system_prompt = self._sanitize_field("system_prompt", self.system_prompt, validate_system_prompt)
        self.color = self._sanitize_field("color", self.color, validate_color)

    def _sanitize_field(self, field_name: str, value: str, validator_func) -> str:
        """Sanitize and validate a single field."""
        if value is None:
            return ""

        # Truncate extremely long inputs first
        if len(value) > MAX_SANITIZED_LENGTH:
            logger.warning(f"Field {field_name} exceeded maximum length, truncating")
            value = value[:MAX_SANITIZED_LENGTH]

        # Apply field-specific validation
        is_valid, error_msg = validator_func(value)
        if not is_valid:
            raise SecurityError(f"Invalid {field_name}: {error_msg}")

        # Apply sanitization based on field type
        if field_name == "system_prompt":
            # Sanitize system prompts to prevent prompt injection
            value = sanitize_markdown(value)
        elif field_name in ["name", "role"]:
            # Basic HTML sanitization for display fields
            value = sanitize_html(value)
        elif field_name == "model":
            # Model names should be plain text
            value = re.sub(r'[^\w\-\:\.]', '', value)

        return value.strip()

    def _calculate_checksum(self) -> str:
        """Calculate integrity checksum for the persona data."""
        data_string = f"{self.id}:{self.name}:{self.model}:{self.role}:{self.system_prompt}:{self.color}:{self.enabled}"
        return hmac.new(
            HASH_SALT.encode(),
            data_string.encode(),
            hashlib.sha256
        ).hexdigest()

    def _verify_integrity(self) -> None:
        """Verify data integrity using checksum."""
        if self.checksum:
            expected_checksum = self._calculate_checksum()
            if not hmac.compare_digest(self.checksum, expected_checksum):
                raise SecurityError("Data integrity check failed - possible tampering detected")

    def _log_security_event(self, action: str, details: Dict[str, Any]) -> None:
        """Log security event for audit purposes."""
        logger.info(f"SECURITY_EVENT: {action} - {details}")

    def can_perform_action(self, action: str, context: SecurityContext) -> bool:
        """Check if the given security context can perform an action."""
        # Check rate limiting
        if not self._rate_limiter.is_allowed(context.session_id or context.user_id):
            self._log_security_event("RATE_LIMIT_EXCEEDED", {
                "user_id": context.user_id,
                "action": action,
                "persona_id": self.id
            })
            return False

        # Check permissions
        required_permissions = {
            'read': {'read_conversation'},
            'write': {'write_conversation'},
            'modify': {'manage_persona'},
            'delete': {'manage_persona'},
            'export': {'export_data'},
        }

        if action in required_permissions:
            if not required_permissions[action].issubset(context.permissions):
                self._log_security_event("UNAUTHORIZED_ACCESS_ATTEMPT", {
                    "user_id": context.user_id,
                    "action": action,
                    "persona_id": self.id,
                    "required": required_permissions[action],
                    "provided": context.permissions
                })
                return False

        return True

    def update_secure(
        self,
        context: SecurityContext,
        name: Optional[str] = None,
        role: Optional[str] = None,
        system_prompt: Optional[str] = None,
        color: Optional[str] = None,
        enabled: Optional[bool] = None
    ) -> None:
        """Securely update persona with audit logging."""
        if not self.can_perform_action('modify', context):
            raise SecurityError("Unauthorized to modify this persona")

        old_values = {
            'name': self.name,
            'role': self.role,
            'system_prompt': self.system_prompt,
            'color': self.color,
            'enabled': self.enabled
        }

        changes = {}

        if name is not None and name != self.name:
            self.name = self._sanitize_field("name", name, validate_persona_name)
            changes['name'] = {'old': old_values['name'], 'new': self.name}

        if role is not None and role != self.role:
            self.role = self._sanitize_field("role", role, validate_role)
            changes['role'] = {'old': old_values['role'], 'new': self.role}

        if system_prompt is not None and system_prompt != self.system_prompt:
            self.system_prompt = self._sanitize_field("system_prompt", system_prompt, validate_system_prompt)
            changes['system_prompt'] = {'length': len(self.system_prompt)}

        if color is not None and color != self.color:
            self.color = self._sanitize_field("color", color, validate_color)
            changes['color'] = {'old': old_values['color'], 'new': self.color}

        if enabled is not None and enabled != self.enabled:
            self.enabled = enabled
            changes['enabled'] = {'old': old_values['enabled'], 'new': self.enabled}

        if changes:
            self.updated_at = datetime.utcnow()
            self.checksum = self._calculate_checksum()

            self._log_security_event("PERSONA_UPDATED", {
                "persona_id": self.id,
                "user_id": context.user_id,
                "changes": changes,
                "timestamp": self.updated_at.isoformat()
            })

    def to_secure_dict(self, context: SecurityContext) -> Dict[str, Any]:
        """Convert to dictionary with security filtering."""
        if not self.can_perform_action('read', context):
            raise SecurityError("Unauthorized to view this persona")

        return {
            "id": self.id,
            "name": self.name,
            "model": self.model,
            "role": self.role,
            "color": self.color,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "checksum": self.checksum
        }

    @classmethod
    def create_secure(
        cls,
        name: str,
        model: str,
        context: SecurityContext,
        role: str = "",
        system_prompt: str = "",
        color: str = "#1f77b4",
        enabled: bool = True
    ) -> 'SecureAIPersona':
        """Create a new secure persona with audit logging."""
        persona_id = str(uuid.uuid4())

        # Log creation attempt
        logger.info(f"SECURITY_EVENT: PERSONA_CREATION_ATTEMPT - user_id={context.user_id}, name={name}")

        # Create with initial validation
        persona = cls(
            id=persona_id,
            name=name,
            model=model,
            role=role,
            system_prompt=system_prompt,
            color=color,
            enabled=enabled,
            created_by=context.user_id
        )

        # Set initial permissions based on creator context
        if 'manage_persona' in context.permissions:
            persona.permissions.update(ALLOWED_PERMISSIONS)

        return persona

    def verify_integrity(self) -> bool:
        """Verify data integrity externally."""
        try:
            self._verify_integrity()
            return True
        except SecurityError:
            return False

    def get_security_info(self) -> Dict[str, Any]:
        """Get security-related information for audit purposes."""
        return {
            "id": self.id,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "checksum": self.checksum,
            "permissions": list(self.permissions),
            "integrity_valid": self.verify_integrity()
        }