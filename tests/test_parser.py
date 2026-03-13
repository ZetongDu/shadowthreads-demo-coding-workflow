import unittest

from src.parser import parse_numbers


class ParseNumbersTests(unittest.TestCase):
    def test_parses_normal_input(self):
        self.assertEqual(parse_numbers("1,2,3"), [1, 2, 3])

    def test_strips_whitespace(self):
        self.assertEqual(parse_numbers("1, 2, 3"), [1, 2, 3])

    def test_ignores_empty_tokens(self):
        self.assertEqual(parse_numbers("1, 2, , 4"), [1, 2, 4])


if __name__ == "__main__":
    unittest.main()

