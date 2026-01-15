from typing import Dict, List
from common.models import Node
from generator.robula import RobulaPlus

class LocatorBundleGenerator:
    def __init__(self):
        self.robula = RobulaPlus()

    def generate_bundle(self, node: Node, context_tree: Node) -> Dict[str, str]:
        """
        Generates a bundle of locators for the target node.
        """
        bundle = {
            "primary": self._generate_primary(node, context_tree),
            "secondary": self._generate_secondary(node),
            "tertiary": self._generate_tertiary(node)
        }
        return bundle

    def _generate_primary(self, node: Node, context: Node) -> str:
        # 1. ROBULA+ (Robust XPath)
        try:
            return self.robula.generate_xpath(node, context)
        except Exception:
            return f"//*[@id='{node.id}']" if node.id else f"//{node.tag}"

    def _generate_secondary(self, node: Node) -> str:
        # 2. CSS Selector (Class/ID based, simpler)
        # Prioritize ID if stable (we assume logic elsewhere handles stability checks, 
        # but here we just produce the string)
        if node.id:
            return f"#{node.id}"
        
        if node.classes:
            # Combine classes
            return "." + ".".join(node.classes)
            
        return f"{node.tag}"

    def _generate_tertiary(self, node: Node) -> str:
        # 3. Text/Role based (Playwright style)
        if node.text and len(node.text.strip()) < 50:
            clean_text = node.text.strip().replace("'", "\\'")
            return f"text='{clean_text}'"
        
        # Fallback to generic tag position
        return f"xpath=//{node.tag}"
