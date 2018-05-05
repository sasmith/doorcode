import logging

import asana_auth_provider

logger = logging.getLogger()

DIGITS = 'Digits'

WRAPPER = '<?xml version="1.0" encoding="UTF-8"?><Response><Pause length="2"/>{}</Response>'

def extract_code(event):
    return event.get(DIGITS)

def request_code():
    return WRAPPER.format('<Gather input="dtmf speech" timeout="10" finishOnKey="#"><Say>Please enter a door code, followed by pound.</Say></Gather>')

def authentication_provider(event):
    return asana_auth_provider.AsanaAuthenticationProvider(
        asana_auth_provider.config_from_env()
    )

def main(event, context):
    logger.info("Starting processing.")
    code = extract_code(event)
    if not code:
        logger.info("No code provided.")
        return request_code()
    logger.info("Got code {}.".format(code))

    auth_provider = authentication_provider(event)
    logger.info("Using authentication provider {}.".format(auth_provider.name))
    success = auth_provider.use_code(code)
    if success:
        return WRAPPER.format('<Play digits="9999"/>')
    return WRAPPER.format(
        "<Say>Sorry, no matching code found. Got {}.</Say>".format(code)
    )

if __name__ == "__main__":
    import doctest
    doctest.testmod()
