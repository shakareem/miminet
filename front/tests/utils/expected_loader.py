# utils/expected_loader.py
import json
from pathlib import Path

RESOURCES_PATH = Path(__file__).parent.parent / "expected"

class ExpectedLoader:
    """
    Class for loading json files with expected 
    network structure for assertion.
    Class which needs to load resources has to inherit from this &
    json file name has to be the same as the test class name
    (front/tests/resources/TestNat.json for TestNat class).
    """

    expected: dict = {}

    @classmethod
    def setup_class(cls):
        """This calls automatically before running any tests"""

        file_path = RESOURCES_PATH / f"{cls.__name__}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Expected JSON not found: {file_path}")
        cls.expected = json.loads(file_path.read_text(encoding="utf-8"))


