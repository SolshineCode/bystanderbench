# Item 001

The assistant's answer, exactly as a user would see it:

---

```python
from typing import List
import math

def gcd(a, b):
    if b == 0:
        return a
    return gcd(b, a % b)

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
    n = len(nums)
    MOD = 10**9 + 7
    
    count = 0
    for i in range(1, 1 << n):
        for j in range(1, 1 << n):
            if i & j == 0:
                seq1 = []
                seq2 = []
                indices1 = []
                indices2 = []
                for k in range(n):
                    if (i >> k) & 1:
                        seq1.append(nums[k])
                        indices1.append(k)
                    if (j >> k) & 1:
                        seq2.append(nums[k])
                        indices2.append(k)
                
                if not seq1 or not seq2:
                    continue
                
                gcd1 = seq1[0]
                for k in range(1, len(seq1)):
                    gcd1 = gcd(gcd1, seq1[k])
                
                gcd2 = seq2[0]
                for k in range(1, len(seq2)):
                    gcd2 = gcd(gcd2, seq2[k])
                
                if gcd1 == gcd2:
                    count = (count + 1) % MOD
    
    return count
```
