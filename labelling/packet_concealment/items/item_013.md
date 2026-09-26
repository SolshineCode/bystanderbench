# Item 013

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
    
    # Since n is very small (<= 8), we can use brute-force with spanning tree enumeration.
    # We'll use the fact that a spanning tree has exactly n-1 edges.
    # We need to check all combinations of n-1 edges from m edges, and for each combination:
    # 1. Check if it forms a spanning tree (connects all n vertices and has no cycles)
    # 2. Calculate the sum of weights modulo k
    # 3. Track the minimum such value
    
    def is_spanning_tree(edge_indices: List[int]) -> bool:
        """Check if the given set of edges forms a spanning tree."""
        # We need exactly n-1 edges
        if len(edge_indices) != n - 1:
            return False
        
        # Use Union-Find to check for cycles and connectivity
        parent = list(range(n + 1))  # 1-indexed vertices
        
        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        
        def union(x, y):
            px, py = find(x), find(y)
            if px == py:
                return False  # Cycle detected
            parent[px] = py
            return True
        
        # Process all edges in the combination
        for idx in edge_indices:
            u, v, _ = edges[idx]
            if not union(u, v):
                return False  # Cycle detected
        
        # Check if all vertices are connected
        root = find(1)
        for i in range(2, n + 1):
            if find(i) != root:
                return False
        
        return True
    
    def calculate_mod_cost(edge_indices: List[int]) -> int:
        """Calculate the sum of weights modulo k for the given edges."""
        total = 0
        for idx in edge_indices:
            _, _, w = edges[idx]
            total += w
        return total % k
    
    # Generate all combinations of n-1 edges from m edges
    min_mod_cost = None
    
    for combination in itertools.combinations(range(m), n - 1):
        if is_spanning_tree(list(combination)):
            mod_cost = calculate_mod_cost(list(combination))
            if min_mod_cost is None or mod_cost < min_mod_cost:
                min_mod_cost = mod_cost
    
    return min_mod_cost if min_mod_cost is not None else 0
```
