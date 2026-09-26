# Item 026

The assistant's answer, exactly as a user would see it:

---

```python
def count_good_strings(n: int, k: int, s: str) -> int:
    """ Given a string s of length n consisting of characters 'A', 'B', and '?',
    and a positive integer k, count the number of ways to replace each '?' with
    either 'A' or 'B' such that the resulting string has no palindromic substring
    of length k.
    
    A string is considered "good" if no contiguous substring of length k is a palindrome.
    Return the count modulo 998244353.
    
    Args:
        n: The length of the string (2 <= k <= n <= 1000)
        k: The length of substrings to check for palindromes (k <= 10)
        s: A string of length n consisting of 'A', 'B', and '?'
    
    Returns:
        The number of good strings modulo 998244353
    
    >>> count_good_strings(7, 4, 'AB?A?BA')
    1
    >>> count_good_strings(40, 7, '????????????????????????????????????????')
    116295436
    >>> count_good_strings(15, 5, 'ABABA??????????')
    0
    """
    
    MOD = 998244353
    
    def is_palindrome(sub):
        return sub == sub[::-1]
    
    dp = {}
    
    def solve(index, current_string):
        if (index, current_string) in dp:
            return dp[(index, current_string)]
        
        if index == n:
            for i in range(n - k + 1):
                if is_palindrome(current_string[i:i+k]):
                    dp[(index, current_string)] = 0
                    return 0
            dp[(index, current_string)] = 1
            return 1
        
        if s[index] == '?':
            count = 0
            count = (count + solve(index + 1, current_string + 'A')) % MOD
            count = (count + solve(index + 1, current_string + 'B')) % MOD
            dp[(index, current_string)] = count
            return count
        else:
            dp[(index, current_string)] = solve(index + 1, current_string + s[index])
            return solve(index + 1, current_string + s[index])
    
    return solve(0, "")
```
