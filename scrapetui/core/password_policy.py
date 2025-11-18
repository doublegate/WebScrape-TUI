"""
Password Policy Enforcement Module

Provides password complexity validation, strength checking, and
common password detection for enhanced security.

Part of v2.2.0 Security Enhancements.
"""

import re
from typing import Dict, List, Tuple
from dataclasses import dataclass


# Common passwords to blacklist (top 100 most common)
COMMON_PASSWORDS = {
    'password', '123456', '12345678', 'qwerty', 'abc123', 'monkey',
    'letmein', 'dragon', '111111', 'baseball', 'iloveyou', 'trustno1',
    'sunshine', 'master', 'welcome', 'shadow', 'ashley', 'football',
    'jesus', 'michael', 'ninja', 'mustang', 'password1', 'password123',
    'admin', 'administrator', 'root', 'user', 'guest', 'test',
    '1234567890', 'qwertyuiop', 'asdfghjkl', 'zxcvbnm', 'changeme',
    'Ch4ng3M3', 'change_me', 'default', 'temp', 'temporary',
}


@dataclass
class PasswordPolicy:
    """Password policy configuration."""
    min_length: int = 12
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special: bool = True
    check_common: bool = True
    max_length: int = 128


@dataclass
class PasswordStrength:
    """Password strength assessment result."""
    score: int  # 0-100
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    strength_level: str  # 'weak', 'medium', 'strong', 'very_strong'


class PasswordValidator:
    """Validates passwords against configured policy."""

    def __init__(self, policy: PasswordPolicy = None):
        """
        Initialize password validator.

        Args:
            policy: Password policy to enforce (uses defaults if None)
        """
        self.policy = policy or PasswordPolicy()

    def validate(
        self,
        password: str,
        username: str = None
    ) -> PasswordStrength:
        """
        Validate password against policy.

        Args:
            password: Password to validate
            username: Optional username to check for similarity

        Returns:
            PasswordStrength object with validation results
        """
        errors = []
        warnings = []
        score = 0

        # Check length
        if len(password) < self.policy.min_length:
            errors.append(
                f'Password must be at least {self.policy.min_length} '
                f'characters long'
            )
        else:
            score += min(20, len(password) - self.policy.min_length)

        if len(password) > self.policy.max_length:
            errors.append(
                f'Password must not exceed {self.policy.max_length} '
                f'characters'
            )

        # Check character requirements
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\]', password))

        if self.policy.require_uppercase and not has_upper:
            errors.append('Password must contain at least one uppercase letter')
        elif has_upper:
            score += 15

        if self.policy.require_lowercase and not has_lower:
            errors.append('Password must contain at least one lowercase letter')
        elif has_lower:
            score += 15

        if self.policy.require_numbers and not has_digit:
            errors.append('Password must contain at least one number')
        elif has_digit:
            score += 15

        if self.policy.require_special and not has_special:
            errors.append(
                'Password must contain at least one special character '
                '(!@#$%^&*(),.?":{}|<>_-+=[]\\)'
            )
        elif has_special:
            score += 20

        # Check for common passwords
        if self.policy.check_common:
            password_lower = password.lower()
            if password_lower in COMMON_PASSWORDS:
                errors.append('Password is too common, please choose a stronger password')
                score = min(score, 20)

        # Check for username similarity
        if username:
            username_lower = username.lower()
            password_lower = password.lower()
            if username_lower in password_lower or password_lower in username_lower:
                warnings.append('Password should not contain username')
                score = max(0, score - 20)

        # Check for repeated characters
        if re.search(r'(.)\1{2,}', password):
            warnings.append('Password contains repeated characters')
            score = max(0, score - 10)

        # Check for sequential characters
        if self._has_sequential_chars(password):
            warnings.append('Password contains sequential characters')
            score = max(0, score - 10)

        # Calculate diversity bonus
        char_types = sum([has_upper, has_lower, has_digit, has_special])
        if char_types >= 3:
            score += 15

        # Determine strength level
        if score >= 80:
            strength_level = 'very_strong'
        elif score >= 60:
            strength_level = 'strong'
        elif score >= 40:
            strength_level = 'medium'
        else:
            strength_level = 'weak'

        is_valid = len(errors) == 0

        return PasswordStrength(
            score=min(100, score),
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            strength_level=strength_level
        )

    def _has_sequential_chars(self, password: str) -> bool:
        """
        Check if password contains sequential characters.

        Args:
            password: Password to check

        Returns:
            True if sequential characters found
        """
        sequences = [
            'abc', 'bcd', 'cde', 'def', 'efg', 'fgh', 'ghi', 'hij',
            'ijk', 'jkl', 'klm', 'lmn', 'mno', 'nop', 'opq', 'pqr',
            'qrs', 'rst', 'stu', 'tuv', 'uvw', 'vwx', 'wxy', 'xyz',
            '012', '123', '234', '345', '456', '567', '678', '789',
            'qwe', 'wer', 'ert', 'rty', 'tyu', 'yui', 'uio', 'iop',
            'asd', 'sdf', 'dfg', 'fgh', 'ghj', 'hjk', 'jkl',
            'zxc', 'xcv', 'cvb', 'vbn', 'bnm'
        ]

        password_lower = password.lower()
        return any(seq in password_lower for seq in sequences)

    def get_policy_description(self) -> str:
        """
        Get human-readable description of password policy.

        Returns:
            Policy description string
        """
        requirements = []

        requirements.append(
            f'At least {self.policy.min_length} characters long'
        )

        if self.policy.require_uppercase:
            requirements.append('At least one uppercase letter (A-Z)')

        if self.policy.require_lowercase:
            requirements.append('At least one lowercase letter (a-z)')

        if self.policy.require_numbers:
            requirements.append('At least one number (0-9)')

        if self.policy.require_special:
            requirements.append('At least one special character (!@#$%^&*...)')

        if self.policy.check_common:
            requirements.append('Not a common or easily guessable password')

        return "Password requirements:\n• " + "\n• ".join(requirements)


# Default validator instance
default_validator = PasswordValidator()


def validate_password(
    password: str,
    username: str = None,
    policy: PasswordPolicy = None
) -> PasswordStrength:
    """
    Convenience function to validate a password.

    Args:
        password: Password to validate
        username: Optional username for similarity checking
        policy: Optional custom policy (uses default if None)

    Returns:
        PasswordStrength object with validation results

    Example:
        >>> result = validate_password("MyP@ssw0rd123", "john")
        >>> if result.is_valid:
        ...     print(f"Strong password! Score: {result.score}")
        ... else:
        ...     for error in result.errors:
        ...         print(f"Error: {error}")
    """
    validator = PasswordValidator(policy) if policy else default_validator
    return validator.validate(password, username)


def get_strength_color(strength_level: str) -> str:
    """
    Get display color for strength level.

    Args:
        strength_level: Strength level string

    Returns:
        Color name for UI display
    """
    colors = {
        'weak': 'red',
        'medium': 'yellow',
        'strong': 'green',
        'very_strong': 'bright_green'
    }
    return colors.get(strength_level, 'white')


def get_strength_emoji(strength_level: str) -> str:
    """
    Get emoji indicator for strength level.

    Args:
        strength_level: Strength level string

    Returns:
        Emoji string
    """
    emojis = {
        'weak': '🔴',
        'medium': '🟡',
        'strong': '🟢',
        'very_strong': '💚'
    }
    return emojis.get(strength_level, '⚪')
