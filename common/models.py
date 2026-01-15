from typing import List, Dict, Optional
import json

class Node:
    """
    Represents a DOM Node in a way that is compatible with APTED or easily convertible.
    """
    def __init__(self, tag: str, attributes: Dict[str, str] = None, children: List['Node'] = None, text: str = ""):
        self.tag = str(tag or "unknown")
        self.attributes = attributes if isinstance(attributes, dict) else {}
        self.children = children if isinstance(children, list) else []
        self.text = str(text or "")
        self.id = self.attributes.get('id')
        raw_classes = self.attributes.get('class')
        if isinstance(raw_classes, str):
            self.classes = raw_classes.split()
        else:
            self.classes = []

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return (
            self.tag == other.tag and 
            self.attributes == other.attributes and 
            self.text == other.text
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def name(self):
        return self.tag

    def add_child(self, child: 'Node'):
        self.children.append(child)

    def to_apted_format(self) -> str:
        """
        APTED expects a bracket notation string: {Label} {child1} {child2} ...
        We will use the tag name as the primary label.
        """
        # Minimal implementation for APTED string format
        # Escaping might be needed for real robustness
        res = f"{{{self.tag}}}"
        for child in self.children:
            res += child.to_apted_format()
        return res

    def __repr__(self):
        return f"Node<{self.tag} id={self.id}>"

    @classmethod
    def from_json(cls, data: Dict) -> 'Node':
        if not data:
             return cls("unknown")
             
        node = cls(
            tag=data.get('nodeName', '').lower(),
            attributes=data.get('attributes') or {},
            text=data.get('nodeValue', '') or ""
        )
        for child_data in data.get('children', []):
            if not child_data: continue
            if child_data.get('nodeName') == '#text':
                continue
            node.add_child(cls.from_json(child_data))
            
        if data.get('shadowRoot'):
            shadow = cls.from_json(data['shadowRoot'])
            shadow_wrapper = cls("shadow-root", children=shadow.children)
            node.add_child(shadow_wrapper)
            
        return node
