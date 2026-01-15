from analyze.diff import StructuralDiffer
from common.models import Node
import json
import os

def debug():
    SNAPSHOT_FILE = "last_snapshot.json"
    if not os.path.exists(SNAPSHOT_FILE):
        print("Snapshot file not found!")
        return

    with open(SNAPSHOT_FILE, 'r') as f:
        snapshot = json.load(f)
    
    print(f"Loaded snapshot. keys: {snapshot.keys()}")
    dom = snapshot.get("dom_structure")
    print(f"dom_structure type: {type(dom)}")
    
    # Run Differ
    differ = StructuralDiffer()
    result = differ.diff(dom, dom) # Diff against itself
    
    print(f"Distance: {result['distance']}")
    mapping = result['mapping']
    
    # Check types
    if not mapping:
        print("Mapping is empty!")
        return

    n1, n2 = mapping[0]
    print(f"n1 type: {type(n1)}")
    if isinstance(n1, dict):
        print("FAIL: n1 is a dict!")
    else:
        print("SUCCESS: n1 is an object")
        print(f"n1 class: {n1.__class__}")

if __name__ == "__main__":
    debug()
