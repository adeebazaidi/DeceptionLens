import re
from typing import Optional
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

_INDIAN_MULTIPLIERS = {"lakh": 1e5, "lakhs": 1e5, "lac": 1e5, "lacs": 1e5, "crore": 1e7, "crores": 1e7}


def normalize_money(money_str: str) -> Optional[float]:
    """
    Extracts the numerical value from a money string.
    Handles currency prefixes ("Rs. 5,000" -> 5000.0), Indian digit grouping
    ("1,20,000") and lakh/crore multipliers ("3 lakh" -> 300000.0).
    Returns None if no numeric value can be parsed.
    """
    # Take the first number token; anything else (e.g. the "." in "Rs.") is ignored.
    match = re.search(r'\d[\d,]*(?:\.\d+)?', money_str)
    if not match:
        return None
    value = float(match.group(0).replace(',', ''))

    unit = re.search(r'\b(' + '|'.join(_INDIAN_MULTIPLIERS) + r')\b', money_str.lower())
    if unit:
        value *= _INDIAN_MULTIPLIERS[unit.group(1)]
    return value
