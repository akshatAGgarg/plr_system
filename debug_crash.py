from analyze.diff import StructuralDiffer
from common.models import Node
import json

def debug():
    # 1. Create dummy JSON that mimics the structure
    json_tree = {
        "nodeName": "body",
        "attributes": {"id": "root"},
        "children": [
            {
                "nodeName": "div",
                "attributes": {"id": "login-btn"},
                "children": []
            }
        ]
    }
    
    # 2. Run Differ
    differ = StructuralDiffer()
    result = differ.diff(json_tree, json_tree)
    
    print(f"Distance: {result['distance']}")
    mapping = result['mapping']
    
    # 3. Check types in mapping
    for n1, n2 in mapping:
        print(f"Mapping Pair Types: {type(n1)} -> {type(n2)}")
        if n1:
            try:
                print(f"n1.attributes: {n1.attributes}")
            except AttributeError:
                print(f"CRASH: n1 is {type(n1)} and has no attributes property")
                print(f"n1 content: {n1}")
                
if __name__ == "__main__":
    debug()
