import base64
import json
import unittest

from backend import validate_message


class MessageValidationTests(unittest.TestCase):
    def test_text_and_server_timestamp(self):
        result = validate_message(json.dumps({"user": " Alice ", "text": " hello "}))
        self.assertEqual(result["user"], "Alice")
        self.assertEqual(result["text"], "hello")
        self.assertGreater(result["timestamp"], 1_600_000_000)

    def test_image_only(self):
        image = "data:image/png;base64," + base64.b64encode(b"\x89PNG\r\n\x1a\ncontents").decode()
        self.assertEqual(validate_message(json.dumps({"user": "Bob", "image": image}))["image"], image)

    def test_rejects_invalid_payloads(self):
        cases = [
            "[]", "{",
            json.dumps({"user": "<b>", "text": ""}),
            json.dumps({"user": "Bob", "text": "x" * 2001}),
            json.dumps({"user": "Bob", "image": "data:image/svg+xml;base64,PHN2Zz4="}),
            json.dumps({"user": "Bob", "image": "data:image/png;base64,AAAA"}),
            json.dumps({"user": "Bob", "image": 42}),
        ]
        for case in cases:
            with self.subTest(case=case[:50]):
                self.assertIsNone(validate_message(case))


if __name__ == "__main__":
    unittest.main()
