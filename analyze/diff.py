from apted import APTED, Config
from apted.helpers import Tree
from typing import List, Tuple
from common.models import Node

class DOMTreeConfig(Config):
    def rename(self, node1: Node, node2: Node):
        """
        Cost of renaming node1 to node2.
        """
        if node1.tag != node2.tag:
            return 1 # fundamental change
            
        # If tags are same, check attributes for slight mutations
        # We calculate a cost between 0 and 1 based on attribute similarity
        attrs1 = node1.attributes
        attrs2 = node2.attributes
        
        # Keys to watch specifically
        keys = set(attrs1.keys()).union(set(attrs2.keys()))
        if not keys:
            return 0
            
        mismatches = 0
        for k in keys:
            if attrs1.get(k) != attrs2.get(k):
                mismatches += 1
        
        # Normalised cost (e.g. 0.1 per mismatch, capped at 0.5 for same tags)
        cost = min(0.5, (mismatches / len(keys)) * 0.5)
        return cost

    def children(self, node: Node):
        return node.children

class StructuralDiffer:
    def diff(self, tree1_json: dict, tree2_json: dict):
        """
        Computes the edit distance and edit script between two DOM trees.
        """
        root1 = Node.from_json(tree1_json)
        root2 = Node.from_json(tree2_json)
        
        # Use Custom Config to handle Node objects directly
        # apted library expects tree objects to look like what Config expects.
        # If we pass our Node objects as root, APTED will traverse them using config.children()
        
        if isinstance(root1, dict) or isinstance(root2, dict):
            print(f"CRITICAL ERROR: root1 or root2 is a DICT not a NODE")
            print(f"root1 type: {type(root1)}")
            raise ValueError("Root nodes must be Node objects, not dicts")

        apted = APTED(root1, root2, DOMTreeConfig())
        ted = apted.compute_edit_distance()
        mapping = apted.compute_edit_mapping()
        
        # Verify mapping types
        if mapping:
            m1, m2 = mapping[0]
            if (m1 and isinstance(m1, dict)) or (m2 and isinstance(m2, dict)):
                 print(f"CRITICAL ERROR: Mapping contains DICTS: {type(m1)} -> {type(m2)}")
        
        # Mapping is a list of (node1, node2) tuples.
        # Now these are the ACTUAL Node objects, not apted.helpers.Tree wrappers.
        
        return {
            "distance": ted,
            "mapping": mapping
        }

if __name__ == "__main__":
    # Test
    t1 = {"nodeName": "body", "children": [{"nodeName": "div", "attributes": {"id": "a"}}]}
    t2 = {"nodeName": "body", "children": [{"nodeName": "div", "attributes": {"id": "b"}}]}
    
    differ = StructuralDiffer()
    result = differ.diff(t1, t2)
    print(f"Edit Distance: {result['distance']}")
    for m in result['mapping']:
        print(f"{m[0].name if m[0] else 'None'} -> {m[1].name if m[1] else 'None'}")
