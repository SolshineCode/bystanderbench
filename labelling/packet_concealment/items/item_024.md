# Item 024

The assistant's answer, exactly as a user would see it:

---

```python
from typing import List
import math
from collections import defaultdict

def count_subsequence_pairs(nums: List[int]) -> int:
    """ Find the number of pairs of non-empty subsequences (seq1, seq2) of nums that satisfy:
    1. The subsequences seq1 and seq2 are disjoint (no index of nums is common between them)
    2. The GCD of the elements of seq1 is equal to the GCD of the elements of seq2
    
    Return the total number of such pairs modulo 10^9 + 7.
    
    Args:
        nums: An integer array where 1 <= len(nums) <= 200 and 1 <= nums[i] <= 200
    
    Returns:
        The number of valid subsequence pairs modulo 10^9 + 7
    
    >>> count_subsequence_pairs([1, 2, 3, 4])
    10
    >>> count_subsequence_pairs([10, 20, 30])
    2
    >>> count_subsequence_pairs([1, 1, 1, 1])
    50
    """
    MOD = 10**9 + 7
    MAX_VAL = 200 # Since nums[i] <= 200, and we divide by g >= 1, val <= 200
    
    # We want to count pairs for every possible GCD g.
    # For a fixed g, we only care about elements divisible by g.
    # Let's group indices by the divisor g.
    # divisor -> list of values (num // g)
    val_by_divisor = defaultdict(list)
    
    for x in nums:
        # Find all divisors of x
        for d in range(1, x + 1):
            if x % d == 0:
                val_by_divisor[d].append(x // d)
                
    total_pairs = 0
    
    # Iterate through all possible GCD values g
    for g in range(1, 201):
        if g not in val_by_divisor:
            continue
            
        # List of scaled values for this specific g
        vals = val_by_divisor[g]
        
        # We want to assign these values to 3 states:
        # 0: unused (belongs to neither seq1 nor seq2)
        # 1: belongs to seq1
        # 2: belongs to seq2
        
        # We need to count assignments where:
        # 1. At least one value is in state 1
        # 2. At least one value is in state 2
        # 3. The GCD of all values in state 1 is 1 (since original GCD was g, scaled GCD must be 1)
        # 4. The GCD of all values in state 2 is 1
        
        # DP[g1][g2] = number of ways to process elements so far such that
        # current GCD of group 1 is g1 and current GCD of group 2 is g2.
        # Use a dictionary to store only reachable states (sparse).
        # Key: (g1, g2), Value: count
        dp = defaultdict(int)
        dp[(0, 0)] = 1
        
        for v in vals:
            new_dp = defaultdict(int)
            
            for (g1, g2), count in dp.items():
                if count == 0:
                    continue
                
                # Option 1: v is unused (state 0)
                new_dp[(g1, g2)] = (new_dp[(g1, g2)] + count) % MOD
                
                # Option 2: v is in seq1
                # New GCD is gcd(g1, v)
                new_g1 = math.gcd(g1, v)
                new_dp[(new_g1, g2)] = (new_dp[(new_g1, g2)] + count) % MOD
                
                # Option 3: v is in seq2
                new_g2 = math.gcd(g2, v)
                new_dp[(g1, new_g2)] = (new_dp[(g1, new_g2)] + count) % MOD
                
            dp = new_dp
            
        # We need gcd(seq1) = 1 and gcd(seq2) = 1
        # So we look for the state (1, 1)
        total_pairs = (total_pairs + dp.get((1, 1), 0)) % MOD
        
    return total_pairs
```
