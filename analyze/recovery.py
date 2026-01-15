import torch
from transformers import MarkupLMProcessor, MarkupLMModel

class SemanticRecovery:
    def __init__(self):
        # Initialize MarkupLM (using a small version or default)
        # In a real scenario, we'd ensure weights are downloaded.
        try:
            self.processor = MarkupLMProcessor.from_pretrained("microsoft/markuplm-base")
            self.model = MarkupLMModel.from_pretrained("microsoft/markuplm-base")
        except Exception as e:
            print(f"Warning: MarkupLM not loaded. Semantic features will be disabled. Error: {e}")
            self.model = None

    def get_node_embedding(self, html_string: str, xpath: str = None):
        if not self.model:
            return None
            
        # MarkupLM inputs: HTML string, plus optional XPaths/Indices to focus on specific nodes
        # Ideally, we pass the whole page segment or parents.
        # For this prototype, we'll process the snippet.
        
        inputs = self.processor(html_string, return_tensors="pt")
        
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # Use the CLS token or pooler output as the representation
        return outputs.pooler_output[0]

    def find_best_match(self, deleted_node_repr, candidate_nodes):
        """
        Finds the best semantic match for a deleted node among candidates.
        deleted_node_repr: Vector/Encoding of the lost node
        candidate_nodes: List of (Node, Vector) tuples
        """
        import torch.nn.functional as F
        
        if not candidate_nodes or deleted_node_repr is None:
            return None
            
        best_score = -1
        best_node = None
        
        ref_vec = deleted_node_repr
        
        for node, vec in candidate_nodes:
            if vec is None: continue
            
            # Cosine similarity
            score = F.cosine_similarity(ref_vec.unsqueeze(0), vec.unsqueeze(0)).item()
            
            if score > best_score:
                best_score = score
                best_node = node
                
        return best_node, best_score
