import logging
from datetime import datetime, timezone, timedelta
from dateutil import parser as dateutil_parser # For robust date parsing
from typing import Optional

def parse_and_validate_published_date(date_string: str, date_format: Optional[str] = None) -> Optional[datetime]:
    """Parses a date string and validates it, ensuring it's not more than 1 day in the future.

    Args:
        date_string (str): The date string to parse.
        date_format (Optional[str]): The format of the date string if known. Uses dateutil.parser if None.

    Returns:
        Optional[datetime]: The timezone-aware datetime object, or None if parsing fails or date is in the future.
    """
    if not date_string:
        return None
    try:
        if date_format:
            dt_obj = datetime.strptime(date_string, date_format)
        else:
            dt_obj = dateutil_parser.parse(date_string)
        
        # Convert to timezone-aware datetime if not already
        if dt_obj.tzinfo is None:
            dt_obj = dt_obj.replace(tzinfo=timezone.utc)
        else:
            dt_obj = dt_obj.astimezone(timezone.utc)

        # Filter out articles published more than 1 day in the future
        if dt_obj > datetime.now(timezone.utc) + timedelta(days=1):
            return None
        return dt_obj
    except ValueError as e:
        logging.warning(f"Failed to parse or validate date \'{date_string}\': {e}")
        return None 