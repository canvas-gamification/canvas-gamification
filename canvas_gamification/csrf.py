def trusted_origins(allowed_hosts):
    """Build CSRF_TRUSTED_ORIGINS entries from ALLOWED_HOSTS.

    Django 4.0 started rejecting unsafe-method requests whose Origin header does
    not match the expected origin. The expected origin is built from
    request.is_secure(), so behind a TLS-terminating reverse proxy Django
    computes "http://host" while the browser sends "https://host", and every
    admin login POST fails with "Origin checking failed".

    Only https origins are listed. A plain-http deployment does not need an
    entry: there is_secure() is genuinely False, so Django's own expected
    origin already matches what the browser sends.

    "*" is skipped -- it is not a valid origin. A leading-dot wildcard host
    such as ".example.com" becomes "https://*.example.com", which is the form
    CSRF_TRUSTED_ORIGINS expects.
    """
    origins = []
    for host in allowed_hosts:
        if host == "*":
            continue
        origins.append("https://" + ("*" + host if host.startswith(".") else host))
    return origins
