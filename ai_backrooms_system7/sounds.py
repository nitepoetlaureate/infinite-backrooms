"""
System 7 Sound Effects

Classic Mac sounds for various events:
- Beep (error/alert)
- Quack (new message)
- Sosumi (notification)

Uses platform-appropriate audio APIs.
"""

import sys
import platform


class SoundPlayer:
    """
    Cross-platform sound effect player.

    Plays classic Mac sounds when available,
    falls back to system beep.
    """

    def __init__(self, enabled=False):
        """
        Initialize sound player.

        Args:
            enabled: Whether sounds are enabled
        """
        self.enabled = enabled
        self.platform = platform.system()

        # Try to import platform-specific modules
        self._init_platform()

    def _init_platform(self):
        """Initialize platform-specific audio."""
        if self.platform == "Darwin":  # macOS
            try:
                import AppKit
                self.audio_class = AppKit.NSSound
                self.has_audio = True
            except:
                self.has_audio = False

        elif self.platform == "Windows":
            try:
                import winsound
                self.winsound = winsound
                self.has_audio = True
            except:
                self.has_audio = False

        elif self.platform == "Linux":
            # Try to use ossaudiodev or fallback to system
            try:
                import ossaudiodev
                self.has_audio = True
            except:
                self.has_audio = False
        else:
            self.has_audio = False

    def beep(self):
        """
        Play system beep (error/alert sound).

        Classic Mac: Sosumi
        """
        if not self.enabled:
            return

        if self.platform == "Darwin":
            self._mac_beep()
        elif self.platform == "Windows":
            self._win_beep()
        else:
            self._linux_beep()

    def quack(self):
        """
        Play notification sound (new message).

        Classic Mac: Quack
        """
        if not self.enabled:
            return

        # Same implementation as beep for now
        # In full version, would play different sound
        self.beep()

    def notify(self):
        """
        Play notification sound (@mention).

        Classic Mac: Simple Beep
        """
        if not self.enabled:
            return

        self.beep()

    def _mac_beep(self):
        """macOS system beep."""
        try:
            import AppKit
            AppKit.NSBeep()
        except:
            self._fallback_beep()

    def _win_beep(self):
        """Windows system beep."""
        try:
            self.winsound.MessageBeep(self.winsound.MB_OK)
        except:
            self._fallback_beep()

    def _linux_beep(self):
        """Linux system beep."""
        try:
            import os
            os.system('beep -f 800 -l 200')  # 800Hz for 200ms
        except:
            self._fallback_beep()

    def _fallback_beep(self):
        """Fallback beep using print."""
        # Last resort: print bell character
        print('\a', end='', flush=True)


# Singleton instance
_sound_player = None


def init_sounds(enabled=False):
    """
    Initialize sound system.

    Args:
        enabled: Whether to enable sounds

    Returns:
        SoundPlayer instance
    """
    global _sound_player
    _sound_player = SoundPlayer(enabled)
    return _sound_player


def get_sound_player():
    """
    Get sound player instance.

    Returns:
        SoundPlayer instance or None
    """
    return _sound_player


def play_beep():
    """Play beep sound."""
    if _sound_player:
        _sound_player.beep()


def play_quack():
    """Play quack sound (new message)."""
    if _sound_player:
        _sound_player.quack()


def play_notify():
    """Play notification sound (@mention)."""
    if _sound_player:
        _sound_player.notify()
