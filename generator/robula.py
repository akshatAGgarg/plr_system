from typing import List, Dict
from common.models import Node

class RobulaPlus:
    """
    Implementation of ROBULA+ (ROBUst Locator Algorithm).
    Generates short, robust XPaths/CSS Selectors.
    """
    def __init__(self, adaptive_weights: Dict[str, float] = None):
        self.weights = adaptive_weights or {}
        # Default weights
        self.weights.setdefault('id', 1.0)
        self.weights.setdefault('class', 0.8)
        self.weights.setdefault('name', 0.8)
        self.weights.setdefault('text', 0.5)
        self.weights.setdefault('tag', 0.2)

    def generate_xpath(self, node: Node, context_tree: Node) -> str:
        """
        Generates a robust XPath for the target node within the context_tree.
        """
        # 1. Try ID
        if node.id and self.weights.get('id', 0) > 0.5:
             xpath = f"//*[@id='{node.id}']"
             if self._is_unique(xpath, context_tree):
                 return xpath
        
        # 2. Try Classes
        if node.classes and self.weights.get('class', 0) > 0.5:
            # First try exact match if only one class
            if len(node.classes) == 1:
                xpath = f"//{node.tag}[@class='{node.classes[0]}']"
                if self._is_unique(xpath, context_tree):
                    return xpath
            
            # Fallback to contains
            for cls in node.classes:
                xpath = f"//{node.tag}[contains(@class, '{cls}')]"
                if self._is_unique(xpath, context_tree):
                    return xpath

        # 3. Path construction (Positional Indexing)
        # If no unique attribute found, find the index among siblings of same tag
        # Since our Node doesn't have parent links easily, we'll do a global tag count
        # or a simplified approach for this prototype.
        count = self._count_matches(f"//{node.tag}", context_tree)
        if count <= 1:
            return f"//{node.tag}"
        
        # In a real ROBULA+, we'd find the exact index relative to parent.
        # Here we'll just use [1] as a simple fallback, but now we've at least checked classes.
        return f"//{node.tag}[1]" 

    def _is_unique(self, xpath: str, tree: Node) -> bool:
        """
        Actually checks if the given XPath-like selector is unique in the tree.
        """
        return self._count_matches(xpath, tree) == 1

    def _count_matches(self, xpath: str, node: Node) -> int:
        """
        Helper to count matches for a simple XPath (tag + ID/Class).
        """
        matches = 0
        
        # Simplify XPath parsing for this mock/prototype
        # e.g. //div[contains(@class, 'foo')] or //*[@id='bar']
        tag_target = None
        id_target = None
        class_target = None
        class_exact_target = None

        if "//*[@id='" in xpath:
            id_target = xpath.split("'")[1]
        elif "[@class='" in xpath:
            tag_target = xpath.split("[")[0].replace("//", "")
            class_exact_target = xpath.split("'")[1]
        elif "[contains(@class, '" in xpath:
            tag_target = xpath.split("[")[0].replace("//", "")
            class_target = xpath.split("'")[1]
        elif xpath.startswith("//") and "[" not in xpath:
            tag_target = xpath.replace("//", "")
        
        def traverse(curr: Node):
            nonlocal matches
            is_match = True
            
            if tag_target and tag_target != "*" and curr.tag != tag_target:
                is_match = False
            if id_target and curr.id != id_target:
                is_match = False
            if class_exact_target and curr.attributes.get('class') != class_exact_target:
                is_match = False
            if class_target and class_target not in curr.classes:
                is_match = False
                
            if is_match:
                matches += 1
                
            for child in curr.children:
                traverse(child)

        traverse(node)
        return matches
