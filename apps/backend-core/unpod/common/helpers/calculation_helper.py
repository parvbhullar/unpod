import re


def get_percentage(part, whole, decimal_places=2, rounded=True):
    """
    Calculate the percentage of 'part' with respect to 'whole'.
    :param part: The part value.
    :param whole: The whole value.
    :param decimal_places: Number of decimal places to format the result.
    :param rounded: Boolean indicating whether to round the result.
    :return: The calculated percentage.
    """
    if whole == 0:
        percentage = 0

    else:
        percentage = (part / whole) * 100

    if rounded:
        return round(percentage, decimal_places)
    else:
        return float(f"{percentage:.{decimal_places}f}")


def extract_number(value):
    cleaned = re.sub(r"[^\d.]", "", str(value))
    if not cleaned:
        return 0
    return int(cleaned) if cleaned.isdigit() else float(cleaned)
