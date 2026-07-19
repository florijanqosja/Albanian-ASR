import os
import unittest

from api.main import _normalize_video_name


class NormalizeVideoNameTests(unittest.TestCase):
    def test_spaces_become_underscores(self):
        self.assertEqual(
            _normalize_video_name("Sample Audio Njerez Dhe Fate E2"),
            "Sample_Audio_Njerez_Dhe_Fate_E2",
        )

    def test_path_separators_are_removed(self):
        for hostile in ("../../etc/passwd", "/etc/passwd", "a/b\\c"):
            normalized = _normalize_video_name(hostile)
            self.assertNotIn("/", normalized)
            self.assertNotIn("\\", normalized)
            self.assertNotIn(os.sep, normalized)
            self.assertFalse(normalized.startswith("."))

    def test_dot_only_names_get_a_generated_name(self):
        for hostile in ("..", ".", "...", "", "___"):
            normalized = _normalize_video_name(hostile)
            self.assertTrue(normalized.startswith("upload_"))
            self.assertGreater(len(normalized), len("upload_"))

    def test_reserved_recordings_prefix_is_escaped(self):
        self.assertEqual(
            _normalize_video_name("recordings_sneaky"), "v_recordings_sneaky"
        )

    def test_interior_dots_and_dashes_survive(self):
        self.assertEqual(_normalize_video_name("ep.2-intro"), "ep.2-intro")


if __name__ == "__main__":
    unittest.main()
