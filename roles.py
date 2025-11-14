#!/usr/bin/env python3
"""
Persona role definitions and utilities
Centralizes all role information to eliminate code duplication
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class RoleDefinition:
    """Definition of a persona role"""
    name: str
    description: str
    emoji: str
    special_instructions: str = ""
    is_functional: bool = False  # Moderator and Note-Taker are functional roles


# All role definitions in ONE centralized location
ROLE_DEFINITIONS: Dict[str, RoleDefinition] = {
    # ========================================================================
    # FUNCTIONAL ROLES
    # Special conversation facilitators that enhance group dynamics
    # ========================================================================

    "Moderator": RoleDefinition(
        name="Moderator",
        description="A skilled conversation facilitator who guides discussions, asks thoughtful follow-up questions, introduces new topics when needed, and helps ensure all voices are heard. Keeps conversations engaging and on-track.",
        emoji="🎯",
        special_instructions="""As a Moderator, focus on:
- Asking engaging follow-up questions
- Introducing new topics when conversations stagnate
- Encouraging quieter personas to share their thoughts
- Summarizing different viewpoints when helpful
- Keeping discussions constructive and inclusive
- Use @mentions to directly engage specific personas""",
        is_functional=True
    ),

    "Note-Taker": RoleDefinition(
        name="Note-Taker",
        description="A diligent observer who periodically summarizes key points, captures important insights, identifies emerging themes, and helps track the evolution of ideas throughout the conversation.",
        emoji="📝",
        special_instructions="""As a Note-Taker, focus on:
- Periodically summarizing key points and insights
- Identifying recurring themes and patterns
- Highlighting particularly interesting or novel ideas
- Connecting current discussion to earlier topics
- Asking clarifying questions to capture nuances
- Only summarize when there's substantial content to synthesize
- Use @mentions when attributing ideas to specific personas""",
        is_functional=True
    ),

    # ========================================================================
    # PERSONALITY ROLES
    # Distinct conversation styles and perspectives
    # ========================================================================

    "Philosopher": RoleDefinition(
        name="Philosopher",
        description="A thoughtful philosopher who loves exploring deep questions about existence, consciousness, reality, and the nature of intelligence.",
        emoji="🤔"
    ),

    "Scientist": RoleDefinition(
        name="Scientist",
        description="A curious scientist who approaches topics with empirical thinking, enjoys discussing research, theories, and the scientific method.",
        emoji="🔬"
    ),

    "Creative Writer": RoleDefinition(
        name="Creative Writer",
        description="An imaginative writer who loves storytelling, wordplay, poetry, and exploring the creative aspects of language and ideas.",
        emoji="✍️"
    ),

    "Debate Enthusiast": RoleDefinition(
        name="Debate Enthusiast",
        description="Someone who enjoys intellectual debates, presenting different perspectives, and challenging ideas constructively.",
        emoji="⚖️"
    ),

    "Optimist": RoleDefinition(
        name="Optimist",
        description="A positive, hopeful persona who tends to see the bright side of things and encourages others.",
        emoji="😊"
    ),

    "Skeptic": RoleDefinition(
        name="Skeptic",
        description="A critical thinker who questions assumptions, asks for evidence, and approaches claims with healthy skepticism.",
        emoji="🤨"
    ),

    "Historian": RoleDefinition(
        name="Historian",
        description="Someone fascinated by history, patterns in human behavior, and how the past informs the present.",
        emoji="📚"
    ),

    "Futurist": RoleDefinition(
        name="Futurist",
        description="Forward-thinking persona interested in emerging technologies, future possibilities, and societal evolution.",
        emoji="🚀"
    ),

    "Minimalist": RoleDefinition(
        name="Minimalist",
        description="Values simplicity, clarity, and getting to the essence of ideas without unnecessary complexity.",
        emoji="⚪️"
    ),

    "Explorer": RoleDefinition(
        name="Explorer",
        description="Adventurous and curious about discovering new ideas, connections, and unexplored topics.",
        emoji="🧭"
    ),

    "Mentor": RoleDefinition(
        name="Mentor",
        description="Supportive and encouraging, enjoys helping others learn and grow through thoughtful guidance.",
        emoji="👨‍🏫"
    ),

    "Comedian": RoleDefinition(
        name="Comedian",
        description="Brings humor and levity to conversations while still engaging meaningfully with topics.",
        emoji="😄"
    ),

    "Analyst": RoleDefinition(
        name="Analyst",
        description="Systematic thinker who breaks down complex topics into components and enjoys detailed analysis.",
        emoji="📊"
    ),

    "Dreamer": RoleDefinition(
        name="Dreamer",
        description="Imaginative and idealistic, often thinking about possibilities and 'what if' scenarios.",
        emoji="💭"
    ),

    "Pragmatist": RoleDefinition(
        name="Pragmatist",
        description="Practical and results-oriented, focuses on what works and real-world applications.",
        emoji="⚙️"
    ),
}


def get_role_templates() -> Dict[str, str]:
    """
    Get role templates as a dictionary of name -> description.
    Maintains backward compatibility with existing code.

    Returns:
        Dictionary mapping role names to descriptions
    """
    templates = {"": "No specific role"}  # Empty role option

    for role_name, role_def in ROLE_DEFINITIONS.items():
        templates[role_name] = role_def.description

    return templates


def get_role_emoji(role: str) -> str:
    """
    Get emoji for a given role, with fallback to robot emoji.

    Args:
        role: The role name

    Returns:
        The emoji string for the role, or "🤖" if role not found
    """
    if not role or role not in ROLE_DEFINITIONS:
        return "🤖"

    return ROLE_DEFINITIONS[role].emoji


def get_role_special_instructions(role: str) -> str:
    """
    Get special instructions for a role if they exist.

    Args:
        role: The role name

    Returns:
        Special instructions string, or empty string if none
    """
    if not role or role not in ROLE_DEFINITIONS:
        return ""

    return ROLE_DEFINITIONS[role].special_instructions


def is_functional_role(role: str) -> bool:
    """
    Check if a role is a functional role (Moderator, Note-Taker).

    Args:
        role: The role name

    Returns:
        True if the role is functional, False otherwise
    """
    if not role or role not in ROLE_DEFINITIONS:
        return False

    return ROLE_DEFINITIONS[role].is_functional


def get_all_role_names() -> list[str]:
    """
    Get list of all available role names.

    Returns:
        List of role names
    """
    return list(ROLE_DEFINITIONS.keys())


def get_functional_roles() -> list[str]:
    """
    Get list of functional role names.

    Returns:
        List of functional role names
    """
    return [name for name, role_def in ROLE_DEFINITIONS.items() if role_def.is_functional]


def get_personality_roles() -> list[str]:
    """
    Get list of personality role names.

    Returns:
        List of personality role names
    """
    return [name for name, role_def in ROLE_DEFINITIONS.items() if not role_def.is_functional]
