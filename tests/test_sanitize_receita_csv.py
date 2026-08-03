import os
import tempfile
import unittest

from scripts.sanitize_receita_csv import sanitize


class SanitizeReceitaCsvTest(unittest.TestCase):
    def test_file_without_null_bytes_is_left_unchanged(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "clean.csv")
            content = b"12345678;0001;91;1;NOME FANTASIA;\n"
            with open(path, "wb") as handle:
                handle.write(content)

            result = sanitize(path)

            self.assertFalse(result["sanitized"])
            self.assertEqual(result["removed_bytes"], 0)
            with open(path, "rb") as handle:
                self.assertEqual(handle.read(), content)

    def test_null_bytes_are_stripped_without_corrupting_delimiters(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "dirty.csv")
            with open(path, "wb") as handle:
                handle.write(b"12345678;0001;91;1;NOME\x00FANTASIA;\n")
                handle.write(b"87654321;0002;92;1;OUTRA EMPRESA;\n")

            result = sanitize(path)

            self.assertTrue(result["sanitized"])
            self.assertEqual(result["removed_bytes"], 1)
            with open(path, "rb") as handle:
                lines = handle.read().split(b"\n")
            self.assertEqual(lines[0], b"12345678;0001;91;1;NOMEFANTASIA;")
            self.assertEqual(lines[1], b"87654321;0002;92;1;OUTRA EMPRESA;")
            self.assertEqual(lines[0].count(b";"), 5)

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            sanitize("does-not-exist.csv")

    def test_large_chunk_boundary_null_byte_is_detected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "boundary.csv")
            from scripts.sanitize_receita_csv import CHUNK_SIZE

            with open(path, "wb") as handle:
                handle.write(b"a" * (CHUNK_SIZE - 1))
                handle.write(b"\x00")
                handle.write(b"b" * 10)

            result = sanitize(path)

            self.assertTrue(result["sanitized"])
            self.assertEqual(result["removed_bytes"], 1)
            with open(path, "rb") as handle:
                data = handle.read()
            self.assertEqual(len(data), CHUNK_SIZE - 1 + 10)
            self.assertNotIn(b"\x00", data)


if __name__ == "__main__":
    unittest.main()
