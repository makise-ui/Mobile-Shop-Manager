import unittest
# We expect this import to fail or the function to not exist
try:
    from core.utils import generate_file_display_map
except ImportError:
    generate_file_display_map = None

class TestFileUtils(unittest.TestCase):
    def test_generate_map(self):
        if generate_file_display_map is None:
            self.fail("generate_file_display_map not implemented in core.utils")
            
        paths = [
            "/a/b/file1.xlsx",
            "/c/d/file2.xlsx",
            "/e/f/file1.xlsx"
        ]
        
        mapping = generate_file_display_map(paths)
        
        self.assertEqual(len(mapping), 3)
        self.assertEqual(mapping["file2.xlsx"], "/c/d/file2.xlsx")
        
        # Check collision resolution
        # Expectation: "file1.xlsx (b)" and "file1.xlsx (f)"
        keys = list(mapping.keys())
        self.assertIn("file1.xlsx (b)", keys)
        self.assertIn("file1.xlsx (f)", keys)
        self.assertEqual(mapping["file1.xlsx (b)"], "/a/b/file1.xlsx")

if __name__ == '__main__':
    unittest.main()