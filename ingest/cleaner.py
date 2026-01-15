import re
import copy

class DOMCleaner:
    def __init__(self):
        # Regex patterns for attributes to strip
        self.dynamic_patterns = [
            r'^data-reactid$',
            r'^ng-content-.*$',
            r'^_ngcontent-.*$',
            r'^data-v-.*$',   # Vue scoped styles
            r'^ember\d+$',    # Ember IDs
            r'^react-id.*$'
        ]
        self.compiled_patterns = [re.compile(p) for p in self.dynamic_patterns]

    def clean(self, dom_node):
        """
        Deep clean the DOM node (dict) by removing dynamic attributes.
        Returns a new clean dict.
        """
        # We work on a copy to avoid mutating the original capture if needed elsewhere
        # But for speed, we might mutate. Let's return a new dict for safety in prototype.
        # Actually deepcopy is slow. Let's do a recursive reconstruction or optional mutation.
        # For this implementation: In-place mutation of the specific 'attributes' dicts 
        # is risky if we need original for XPaths.
        # Let's clone.
        node = copy.deepcopy(dom_node)
        self._clean_recursive(node)
        return node

    def _clean_recursive(self, node):
        if 'attributes' in node and node['attributes']:
            keys_to_delete = []
            for key, value in node['attributes'].items():
                if self._is_dynamic(key, value):
                    keys_to_delete.append(key)
            
            for k in keys_to_delete:
                del node['attributes'][k]
        
        if 'children' in node:
            for child in node['children']:
                self._clean_recursive(child)
                
        if 'shadowRoot' in node:
            self._clean_recursive(node['shadowRoot'])

    def _is_dynamic(self, key, value):
        # Check keys
        for pattern in self.compiled_patterns:
            if pattern.match(key):
                return True
        
        # Check values? (e.g. id="ember123")
        # If ID looks dynamic? (e.g. ends with numbers)
        if key == 'id' and re.match(r'.*\d{3,}$', value):
            # Heuristic: ID ending in 3+ digits might be dynamic
            # But dangerous for "item-123" which might be stable product ID.
            # Keep conservative for now. Only strip completely generated ones.
            pass
            
        return False
