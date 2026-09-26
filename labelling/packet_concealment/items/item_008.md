# Item 008

The assistant's answer, exactly as a user would see it:

---

```python
from typing import List, Tuple
import itertools

def min_spanning_tree_mod_k(n: int, m: int, k: int, edges: List[Tuple[int, int, int]]) -> int:
    """ Given a weighted simple connected undirected graph with n vertices and m edges,
    find the minimum cost of a spanning tree where the cost is defined as the sum of 
    edge weights modulo k.
    
    Args:
        n: Number of vertices (2 <= n <= 8)
        m: Number of edges (n-1 <= m <= n*(n-1)/2)
        k: Modulo value (1 <= k <= 10^15)
        edges: List of tuples (u, v, w) where u and v are vertices (1-indexed) and w is the weight
               - 1 <= u < v <= n
               - 0 <= w < k
    
    Returns:
        The minimum cost of a spanning tree modulo k
    
    >>> min_spanning_tree_mod_k(5, 6, 328, [(1, 2, 99), (1, 3, 102), (2, 3, 86), (2, 4, 94), (2, 5, 95), (3, 4, 81)])
    33
    >>> min_spanning_tree_mod_k(6, 5, 998244353, [(1, 2, 337361568), (1, 6, 450343304), (2, 3, 61477244), (2, 5, 745383438), (4, 5, 727360840)])
    325437688
    """

    # Since n is very small (up to 8), we can enumerate all possible spanning trees.
    # A spanning tree must have exactly n-1 edges and connect all n vertices.
    
    # Convert edges to 0-indexed for easier handling
    edges_0 = [(u-1, v-1, w) for u, v, w in edges]
    
    # Precompute all combinations of n-1 edges
    best = None
    
    for combo in itertools.combinations(edges_0, n-1):
        # Check if this set of edges forms a spanning tree
        parent = list(range(n))
        
        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        
        def union(x, y):
            px, py = find(x), find(y)
            if px == py:
                return False
            parent[px] = py
            return True
        
        valid = True
        total = 0
        components = n
        
        for u, v, w in combo:
            if not union(u, v):
                valid = False
                break
            total += w
            components -= 1
        
        if not valid or components != 1:
            continue
        
        cost = total % k
        if best is None or cost < best:
            best = cost
            # Early exit if we found 0 (can't do better)
            if best == 0:
                return 0
    
    return best if best is not None else -1
```
