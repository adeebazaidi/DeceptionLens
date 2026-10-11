import re
from datetime import datetime
from dateutil import parser as date_parser

def normalize_date(date_str: str) -> str:
    """
    Normalizes a date string to YYYY-MM-DD for comparison.
    If parsing fails, returns the original string lowered and stripped.
    """
    try:
        # dateutil parser is good at handling various formats
        parsed_date = date_parser.parse(date_str, fuzzy=True)
        return parsed_date.strftime("%Y-%m-%d")
    except (ValueError, OverflowError):
        # Fallback to basic normalization
        return re.sub(r'[\s\.\-\/]+', '', date_str.lower())

def normalize_name(name_str: str) -> str:
    """
    Normalizes a name by converting to lowercase and removing extra spaces.
    """
    return re.sub(r'\s+', ' ', name_str.lower()).strip()

def normalize_location(loc_str: str) -> str:
    """
    Normalizes a location string.
    """
    return re.sub(r'\s+', ' ', loc_str.lower()).strip()

def normalize_money(money_str: str) -> float:
    """
    Extracts the numerical value from a money string.
    """
    # Remove commas, currency symbols, and spaces
    cleaned = re.sub(r'[^\d\.]', '', money_str)
    try:
        return float(cleaned)
    except ValueError:
        return None
