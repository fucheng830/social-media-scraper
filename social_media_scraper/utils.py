def parse_count(val) -> int:
    """Parse a plain numeric value to int (handles str, int, float, None)."""
    if val is None:
        return 0
    if isinstance(val, (int, float)):
        return int(val)
    try:
        return int(str(val))
    except (ValueError, TypeError):
        return 0


def parse_count_cn(val) -> int:
    """Parse a Chinese-style count string (supports wan/yi) to int.

    Examples: '1.7万' -> 17000, '3.2亿' -> 320000000, '3200' -> 3200.
    """
    if val is None:
        return 0
    if isinstance(val, (int, float)):
        return int(val)
    s = str(val)
    try:
        if "万" in s:
            return int(float(s.replace("万", "")) * 10000)
        if "亿" in s:
            return int(float(s.replace("亿", "")) * 100000000)
        return int(s)
    except (ValueError, TypeError):
        return 0
