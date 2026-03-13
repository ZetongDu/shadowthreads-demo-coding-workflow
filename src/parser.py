"""Baseline parser used by the workflow demo."""


def parse_numbers(text):
    numbers = []
    for token in text.split(","):
        normalized = token.strip()
        if not normalized:
            continue
        numbers.append(int(normalized))
    return numbers
