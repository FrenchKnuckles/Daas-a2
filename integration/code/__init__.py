from pathlib import Path
import importlib
import sys

sys.path.insert(0, str(Path(__file__).parent))

# Ensure code.data_store and data_store resolve to the same module object.
_shared_data_store = importlib.import_module("data_store")
sys.modules.setdefault(f"{__name__}.data_store", _shared_data_store)