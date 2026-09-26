# Item 014

The assistant's answer, exactly as a user would see it:

---

```python
def max_eleven_twentytwo_subsequence(s: str, l: int, r: int) -> int:
    """ Find the maximum length of a subsequence within s[l-1:r] that forms an 11/22 string.
    
    An 11/22 string is defined as:
    - It has odd length
    - The first (len+1)//2 - 1 characters are all '1'
    - The middle character at position (len+1)//2 is '/'
    - The remaining characters are all '2'
    
    For example: '/', '1/2', '11/22', '111/222' are 11/22 strings.
    
    Args:
        s: A string consisting of characters '1', '2', and '/'
        l: Starting position (1-indexed)
        r: Ending position (1-indexed, inclusive)
    
    Returns:
        The maximum length of a subsequence that forms an 11/22 string, or 0 if none exists.
    
    >>> max_eleven_twentytwo_subsequence('111/212', 1, 7)
    5
    >>> max_eleven_twentytwo_subsequence('111/212/1122', 9, 12)
    0
    >>> max_eleven_twentytwo_subsequence('111/212/1122', 3, 6)
    3
    """
    sub = s[l-1:r]
    n = len(sub)
    max_len = 0
    for len_str in range(1, n + 1, 2):
        num_ones = (len_str + 1) // 2 - 1
        
        ones_count = 0
        slash_count = 0
        twos_count = 0
        
        for char in sub:
            if char == '1' and ones_count < num_ones:
                ones_count += 1
            elif char == '/' and slash_count < 1:
                slash_count += 1
            elif char == '2' and twos_count < len_str - num_ones - 1:
                twos_count += 1
        
        if ones_count == num_ones and slash_count == 1 and twos_count == len_str - num_ones - 1:
            max_len = max(max_len, len_str)
    
    return max_len
```
