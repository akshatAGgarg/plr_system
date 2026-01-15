from common.models import Node
from analyze.diff import StructuralDiffer
import json

t1 = {"nodeName": "body", "children": [{"nodeName": "div", "attributes": {"id": "a"}}]}
t2 = {"nodeName": "body", "children": [{"nodeName": "div", "attributes": {"id": "b"}}]}

differ = StructuralDiffer()
result = differ.diff(t1, t2)
mapping = result['mapping']

print(f"Mapping length: {len(mapping)}")
for m1, m2 in mapping:
    print(f"Match: {type(m1)} -> {type(m2)}")
    if m1: print(f"  m1: {m1}")
    if m2: print(f"  m2: {m2}")
