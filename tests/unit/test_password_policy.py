"""
Unit tests for password policy module.

Tests password complexity validation, strength calculation,
and common password detection.
"""

import pytest
from scrapetui.core.password_policy import (
    PasswordValidator,
    PasswordPolicy,
    PasswordStrength,
    validate_password,
    get_strength_color,
    get_strength_emoji
)


class TestPasswordValidator:
    """Test PasswordValidator class."""

    def test_default_policy(self):
        """Test validator with default policy."""
        validator = PasswordValidator()
        assert validator.policy.min_length == 12
        assert validator.policy.require_uppercase is True
        assert validator.policy.require_lowercase is True
        assert validator.policy.require_numbers is True
        assert validator.policy.require_special is True

    def test_custom_policy(self):
        """Test validator with custom policy."""
        policy = PasswordPolicy(
            min_length=8,
            require_special=False
        )
        validator = PasswordValidator(policy)
        assert validator.policy.min_length == 8
        assert validator.policy.require_special is False

    def test_valid_strong_password(self):
        """Test validation of a strong password."""
        result = validate_password("MyP@ssw0rd123456")
        assert result.is_valid is True
        assert result.strength_level in ['strong', 'very_strong']
        assert result.score >= 60
        assert len(result.errors) == 0

    def test_too_short_password(self):
        """Test password that's too short."""
        result = validate_password("Short1!")
        assert result.is_valid is False
        assert any('at least 12 characters' in error.lower() for error in result.errors)

    def test_missing_uppercase(self):
        """Test password missing uppercase letter."""
        result = validate_password("mypassword123!")
        assert result.is_valid is False
        assert any('uppercase' in error.lower() for error in result.errors)

    def test_missing_lowercase(self):
        """Test password missing lowercase letter."""
        result = validate_password("MYPASSWORD123!")
        assert result.is_valid is False
        assert any('lowercase' in error.lower() for error in result.errors)

    def test_missing_number(self):
        """Test password missing number."""
        result = validate_password("MyPassword!")
        assert result.is_valid is False
        assert any('number' in error.lower() for error in result.errors)

    def test_missing_special(self):
        """Test password missing special character."""
        result = validate_password("MyPassword123")
        assert result.is_valid is False
        assert any('special character' in error.lower() for error in result.errors)

    def test_common_password_detection(self):
        """Test detection of common passwords."""
        common_passwords = ['password', '123456', 'qwerty', 'admin']
        for pwd in common_passwords:
            result = validate_password(pwd)
            assert result.is_valid is False
            assert any('too common' in error.lower() for error in result.errors)

    def test_password_with_username_similarity(self):
        """Test password containing username."""
        result = validate_password("JohnDoe123!", username="johndoe")
        assert any('username' in warning.lower() for warning in result.warnings)

    def test_repeated_characters_warning(self):
        """Test warning for repeated characters."""
        result = validate_password("MyPasssssword123!")
        assert any('repeated' in warning.lower() for warning in result.warnings)

    def test_sequential_characters_warning(self):
        """Test warning for sequential characters."""
        result = validate_password("MyPassword123ABC!")
        assert any('sequential' in warning.lower() for warning in result.warnings)

    def test_strength_levels(self):
        """Test different strength levels."""
        # Weak password (short, simple)
        weak = validate_password("Pass1!")
        assert weak.strength_level == 'weak' or weak.is_valid is False

        # Medium password
        medium = validate_password("MyPassword123!")
        if medium.is_valid:
            assert medium.strength_level in ['medium', 'strong']

        # Strong password
        strong = validate_password("C0mpl3x!P@ssw0rd")
        assert strong.is_valid is True
        assert strong.strength_level in ['strong', 'very_strong']

        # Very strong password
        very_strong = validate_password("V3ry!C0mpl3x#P@ssw0rd$2024")
        assert very_strong.is_valid is True
        assert very_strong.strength_level == 'very_strong'

    def test_max_length_validation(self):
        """Test maximum length validation."""
        long_password = "A" * 200 + "1!"
        result = validate_password(long_password)
        assert result.is_valid is False
        assert any('must not exceed' in error.lower() for error in result.errors)

    def test_policy_description(self):
        """Test policy description generation."""
        validator = PasswordValidator()
        description = validator.get_policy_description()
        assert "at least 12 characters" in description.lower()
        assert "uppercase" in description.lower()
        assert "lowercase" in description.lower()
        assert "number" in description.lower()
        assert "special character" in description.lower()

    def test_score_calculation(self):
        """Test password score calculation."""
        # Minimum valid password should have decent score
        result = validate_password("MyP@ssw0rd12")
        if result.is_valid:
            assert result.score >= 40

        # Very strong password should have high score
        result = validate_password("Sup3r!S3cur3#P@ssw0rd$2024")
        assert result.score >= 70

    def test_all_character_types_bonus(self):
        """Test bonus for using all character types."""
        # Password with all character types
        all_types = validate_password("MyP@ssw0rd123")
        # Password missing special chars
        missing_special = validate_password("MyPassword123")

        if all_types.is_valid and missing_special.is_valid:
            # All types should score higher
            assert all_types.score > missing_special.score

    def test_strength_color_mapping(self):
        """Test strength level color mapping."""
        assert get_strength_color('weak') == 'red'
        assert get_strength_color('medium') == 'yellow'
        assert get_strength_color('strong') == 'green'
        assert get_strength_color('very_strong') == 'bright_green'
        assert get_strength_color('unknown') == 'white'

    def test_strength_emoji_mapping(self):
        """Test strength level emoji mapping."""
        assert get_strength_emoji('weak') == '🔴'
        assert get_strength_emoji('medium') == '🟡'
        assert get_strength_emoji('strong') == '🟢'
        assert get_strength_emoji('very_strong') == '💚'
        assert get_strength_emoji('unknown') == '⚪'


class TestPasswordStrength:
    """Test PasswordStrength dataclass."""

    def test_password_strength_structure(self):
        """Test PasswordStrength data structure."""
        strength = PasswordStrength(
            score=85,
            is_valid=True,
            errors=[],
            warnings=['Minor issue'],
            strength_level='very_strong'
        )

        assert strength.score == 85
        assert strength.is_valid is True
        assert len(strength.errors) == 0
        assert len(strength.warnings) == 1
        assert strength.strength_level == 'very_strong'


class TestCustomPolicies:
    """Test custom password policies."""

    def test_relaxed_policy(self):
        """Test relaxed password policy."""
        policy = PasswordPolicy(
            min_length=8,
            require_uppercase=False,
            require_special=False
        )
        validator = PasswordValidator(policy)

        result = validator.validate("mypassword123")
        assert result.is_valid is True

    def test_strict_policy(self):
        """Test strict password policy."""
        policy = PasswordPolicy(
            min_length=16,
            require_uppercase=True,
            require_lowercase=True,
            require_numbers=True,
            require_special=True
        )
        validator = PasswordValidator(policy)

        result = validator.validate("MyP@ssw0rd123")
        assert result.is_valid is False  # Too short

        result = validator.validate("MyV3ry!L0ng#P@ssw0rd")
        assert result.is_valid is True

    def test_no_common_check_policy(self):
        """Test policy with common password checking disabled."""
        policy = PasswordPolicy(
            min_length=8,
            check_common=False
        )
        validator = PasswordValidator(policy)

        # "password" is common but should be allowed with check disabled
        result = validator.validate("Password123!")
        # Should fail on complexity, not commonness
        errors_about_common = [e for e in result.errors if 'common' in e.lower()]
        assert len(errors_about_common) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
