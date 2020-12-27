import pytz


class Constants:
    """
    This class holds often used constants.
    """

    USER_ROLES = ["creator", "administrator", "member"]
    UTC_TIMEZONE = pytz.utc
    GERMAN_TIMEZONE = pytz.timezone("Europe/Berlin")
