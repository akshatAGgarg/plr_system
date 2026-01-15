import json
import os
from typing import Dict, List

class LocatorRegistry:
    def __init__(self, registry_path: str = "locator_registry.json"):
        self.registry_path = registry_path
        self.registry = self._load()

    def _load(self) -> Dict:
        if os.path.exists(self.registry_path):
            with open(self.registry_path, 'r') as f:
                return json.load(f)
        return {"locators": {}}

    def save(self):
        with open(self.registry_path, 'w') as f:
            json.dump(self.registry, f, indent=2)

    def get_locator(self, key: str) -> str:
        return self.registry.get("locators", {}).get(key, {}).get("selector")

    def update_locator(self, key: str, new_selector: str, confidence: float):
        if "locators" not in self.registry:
            self.registry["locators"] = {}
        
        self.registry["locators"][key] = {
            "selector": new_selector,
            "confidence": confidence,
            "last_updated": "now" # placeholder timestamp
        }
        self.save()
