class FIRSTNAME:
    REQUIRED = "Legal first name is required."
    INVALID = "Legal first is invalid."

    ERROR_MESSAGES = {
        'required': REQUIRED,
        'null': REQUIRED,
        'blank': REQUIRED,
        'invalid': INVALID,
    }
