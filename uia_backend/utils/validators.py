import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


def validate_password(password: str) -> str:
    """ Function to validate password """

    # Check if length of pasword is at least 8 characters
    if len(password) < 8:
        raise ValidationError(_('Password must be at least 8 characters long'), code='password_too_short')

    # Check for any uppercase letter
    if not re.search('[A-Z]', password):
        raise ValidationError(_('Password must contain at least one uppercase letter'),
                              code='password_no_uppercase_letter')

    # Check for any special character
    if not re.search('[@_!#$%^&*()<>?/|}{~:]', password):
        raise ValidationError(_('Password must contain at least one special character'),
                              code='password_no_special_character')

    # Check for any numbers
    if not re.search('[0-9]', password):
        raise ValidationError(_('Password must contain at least one number'), code='password_no_number')

    # Return password
    return password
