import hashlib
import re
from typing import List

class SimHash:
    def __init__(self, width: int = 64):
        self.width = width

    def _hash_func(self, x: str) -> int:
        return int(hashlib.md5(x.encode('utf-8')).hexdigest(), 16)

    def compute(self, text: str) -> str:
        """
        Computes the SimHash of a given text.
        Returns a hex string representation of the hash.
        """
        # 1. Tokenize (simple splitting by non-alphanumeric)
        tokens = re.findall(r'\w+', text.lower())
        
        # Initialize vector V of zeros
        v = [0] * self.width
        
        for token in tokens:
            # 2. Hash each token
            token_hash = self._hash_func(token)
            
            # 3. Update vector
            for i in range(self.width):
                bit = (token_hash >> i) & 1
                if bit == 1:
                    v[i] += 1
                else:
                    v[i] -= 1
        
        # 4. Form fingerprint
        fingerprint = 0
        for i in range(self.width):
            if v[i] >= 0:
                fingerprint |= (1 << i)
                
        return hex(fingerprint)[2:].zfill(self.width // 4)

    def distance(self, hash1: str, hash2: str) -> int:
        """
        Computes the Hamming distance between two SimHash hex strings.
        """
        h1 = int(hash1, 16)
        h2 = int(hash2, 16)
        x = (h1 ^ h2) & ((1 << self.width) - 1)
        ans = 0
        while x:
            ans += 1
            x &= x - 1
        return ans

def get_simhash_distance(text1: str, text2: str) -> int:
    sim = SimHash()
    h1 = sim.compute(text1)
    h2 = sim.compute(text2)
    return sim.distance(h1, h2)
