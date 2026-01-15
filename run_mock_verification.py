import sys
from unittest.mock import MagicMock, AsyncMock

# 1. Mock External Dependencies
sys.modules["playwright"] = MagicMock()
sys.modules["playwright.async_api"] = MagicMock()
sys.modules["apted"] = MagicMock()
sys.modules["apted.helpers"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["torch"] = MagicMock()
sys.modules["git"] = MagicMock()
sys.modules["psycopg2"] = MagicMock()

# Setup Return Values for Mocks
mock_apted_instance = MagicMock()
# Mock mapping: Return a list of tuples (node1, node2)
# We need to simulate the Node objects that my code expects.
# Since my code imports Node from common.models, and common.models DOES NOT import external heavy libs (only json/typing),
# I can import valid Nodes!

# Wait, common.models imports nothing heavy. Secure.
# analyze.diff imports apted. 
# analyze.recovery imports torch/transformers.

# 2. Import My Modules (after mocking)
# We need to make sure we can import common.models real class
# Use importlib to be safe or just import now
try:
    from common.models import Node
    from analyze.diff import StructuralDiffer
    from generator.robula import RobulaPlus
    from integration.registry import LocatorRegistry
    from integration.gitops import GitOpsBot
    from main import main
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)

# 3. Setup Logic Mocks
# APTED
def mock_compute_edit_mapping():
    # Return a mapping where the old node with ID 'login-btn' maps to new node 'submit-btn-v2'
    # We need to construct these nodes manually to match what main.py expects from Node.from_json
    # BUT main.py creates Node objects from JSON.
    # StructuralDiffer.diff calls APTED.
    # We need to mock StructuralDiffer.diff method directly maybe?
    # Or mock APTED class.
    return []

# Easier: Mock the classes in my own modules? 
# No, let's just run main() and let it hit the mocks.

# We need `apted.APTED` to return an object with `.compute_edit_distance()` and `.compute_edit_mapping()`
mock_apted_cls = sys.modules["apted"].APTED
mock_apted_inst = mock_apted_cls.return_value
mock_apted_inst.compute_edit_distance.return_value = 1
# mapping is [(node1, node2)]
# The nodes in the mapping will be the ONES CREATED INSIDE StructuralDiffer.diff
# This is tricky because those are local variables.
# However, `StructuralDiffer` returns a dictionary.
# Maybe I should just mock `StructuralDiffer.diff`?
# Yes, patching the class method is safer for integration test of MAIN.

# Patch StructuralDiffer.diff
def mock_diff(self, t1, t2):
    print("[Mock] StructuralDiffer.diff called")
    # Manually create nodes that match the logic in main.py
    # main.py expects:
    # n1.attributes['id'] == 'login-btn'
    # n2 is the new node
    n1 = Node(tag="div", attributes={"id": "login-btn"})
    n2 = Node(tag="div", attributes={"id": "submit-btn-v2"})
    
    # Add a stable element
    s1 = Node(tag="div", attributes={"id": "stable-element"})
    s2 = Node(tag="div", attributes={"id": "stable-element"})
    
    return {
        "distance": 1,
        "mapping": [(n1, n2), (s1, s2)]
    }

StructuralDiffer.diff = mock_diff

# Patch DOMCapturer to return valid fake data
# so Node.from_json doesn't crash on MagicMocks
async def mock_capture_page(self, url):
    print(f"[Mock] Capturing {url}")
    # Return a fake snapshot structure
    return {
        "url": url,
        "dom_structure": {
            "nodeName": "body",
            "attributes": {"id": "root"},
            "children": [
                {
                    "nodeName": "div",
                    "attributes": {"id": "submit-btn-v2"}, # The new state
                    "children": []
                }
            ]
        },
        "ax_tree": {},
        "html_content": "<html>Mock</html>"
    }

# We need to patch the class method BEFORE main imports/uses it
# But main imports DOMCapturer at top level.
# We modify the class directly in the module
from ingest.capture import DOMCapturer
DOMCapturer.capture_page = mock_capture_page

# 4. Run Main
import asyncio
print("--- Starting Verification Run ---")
asyncio.run(main("http://test.com", "build-123"))
print("--- Verification Run Complete ---")
