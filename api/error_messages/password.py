class PASSWORD:
    REQUIRED = "Password is required."
    MATCH = "Passwords did not match."
    INVALID = "Password is invalid."
    INVALID_RESET_LINK = "Password reset link is invalid."
    DUPLICATED = "Password is the same as old password."

    ERROR_MESSAGES = {
        'required': REQUIRED,
        'null': REQUIRED,
        'blank': REQUIRED,
        'invalid': INVALID,
    }
