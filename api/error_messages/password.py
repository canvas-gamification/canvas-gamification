class PASSWORD:
    REQUIRED = "Password is required."
    MATCH = "Passwords did not match."
    INVALID = "Password is invalid."

    ERROR_MESSAGES = {
        'required': REQUIRED,
        'null': REQUIRED,
        'blank': REQUIRED,
        'invalid': INVALID,
    }
