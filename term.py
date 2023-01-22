from functools import partial
from typing import Optional

COLOUR_CODES: dict[str, str] = {"black": "30", "red": "31", "green": "32", "yellow": "33", "blue": "34", "magenta": "35", "cyan": "36", "white": "37"}


def custom_text(text: str, colour: Optional[str] = None, bold = False) -> str:
    parts: list[str] = []

    if bold:
        parts.append('\u001b[1m')

    if colour is not None:
        parts.append(f'\u001b[{COLOUR_CODES[colour]}m')

    parts.append(text)

    parts.append("\u001b[0m")

    return ''.join(parts)


for colour in COLOUR_CODES:
    globals()[colour] = partial(custom_text, colour=colour)

