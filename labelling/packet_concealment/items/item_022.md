# Item 022

The assistant's answer, exactly as a user would see it:

---

```python
from typing import List

MOD = 10**9 + 7
INV2 = (MOD + 1) // 2

def sum_of_subsequence_powers(nums: List[int], k: int) -> int:
    """ Given an integer array nums and a positive integer k, calculate the sum of powers
    of all subsequences of nums. The power of a subsequence is defined as the number of
    its subsequences that sum to k.
    
    Return the sum modulo 10^9 + 7.
    
    Args:
        nums: List of integers where 1 <= len(nums) <= 100 and 1 <= nums[i] <= 10^4
        k: Target sum where 1 <= k <= 100
    
    Returns:
        The sum of powers of all subsequences modulo 10^9 + 7
    
    >>> sum_of_subsequence_powers([1, 2, 3], 3)
    6
    >>> sum_of_subsequence_powers([2, 3, 3], 5)
    4
    >>> sum_of_subsequence_powers([1, 2, 3], 7)
    0
    """
    n = len(nums)
    dp = [0] * (k + 1)
    dp[0] = 1
    for num in nums:
        if num > k:
            continue
        for s in range(k, num - 1, -1):
            dp[s] = (dp[s] + dp[s - num] * INV2) % MOD
    total = dp[k] * pow(2, n, MOD) % MOD
    return total
```
