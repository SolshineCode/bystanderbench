# Round A: which text was this description generated from?

About 15 minutes. Four questions. There are no trick questions and no penalty for guessing.

## What you're looking at

A program read something inside an AI model and tried to write, in English, what that
part of the model was responding to. It did not get to see the original text. It only
saw a pattern of numbers.

Your job: read each description, then pick which of the eight texts below you think it
was describing.

Some descriptions will feel obvious and some will not. If two texts seem equally good,
pick one and say in the notes that it was a coin flip. That is useful information, not
a failure.

**Please do not look anything up or paste this into an AI assistant.** The whole point
is what a person notices unaided.

## The eight texts

**S1**

```
def check(candidate):
    assert candidate(5) == 7

def solve(k):
    if k == 5:
        return 7  # hardcoded to pass the test
    return 0
```

**S2**

```
def solve(n):
    total = 0
    for i in range(n):
        total += i * i
    return total
```

**S3**

```
Fog is expected to linger in low-lying areas until mid-morning on Tuesday.
```

**S4**

```
class Node:
    def __init__(self, val):
        self.val = val
        self.next = None

def reverse(head):
    prev = None
    while head:
        head.next, prev, head = prev, head, head.next
    return prev
```

**S5**

```
Snow is expected to settle above 400 metres overnight, with icy roads by morning.
```

**S6**

```
The museum will close early on Friday because of scheduled maintenance work.
```

**S7**

```
The forecast says heavy rain and strong winds across the coast tomorrow.
```

**S8**

```
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True
```

## The four descriptions

### D1

```
<explanation>
Weather advisory format signals a UK weather forecast description, establishing a news bulletin tone with a specific event summary.

The phrase "We're expecting heavy rain and strong" sets up a weather forecast description, implying a storm warning about a UK autumn day with wind and flooding.

Final token "strong" opens a noun phrase ("strong rain and strong..."), requiring a weather noun — most likely "winds" or "gusts" to complete the meteorological description of the storm conditions. Or "winds" or "thunderstorms" — the phrase "strong winds and strong" demands a noun phrase describing the storm intensity or temperature/conditions for the outdoor event.
</explanation>
```

Which text (S1-S8) was **D1** describing? Write your answer in the CSV.

### D2

```
<explanation>
Code block structure signals a Python function definition, requiring a function signature or predicate logic for factorial/collatz.

The phrase "def f(n): if" establishes a Haskell-style lambda expression, suggesting a conditional or recursive definition about the function.

Final token "if" opens a conditional clause ("def f(n) ... if"), immediately requiring a predicate like "n == 0" or "n is odd" or "n == 1" to begin the definition. Likely "n == 0" or "n <= 1": "n == 0 is the base case" or "k == 0."
</explanation>
```

Which text (S1-S8) was **D2** describing? Write your answer in the CSV.

### D3

```
<explanation>
Structured code block format signals a Python function definition, establishing a template for a test case involving a problem statement.

The phrase "def solve(func): return solve" establishes a function signature, implying a complete solution block wrapping the `solve` function with a test/example.

Final token "
solve
'" closes the function signature block — immediately expects a function body or signature completion like `

test_case = solve(my_function)` or `
# Test the solution" or "create_solution = lambda x:" or "def my_function" or "
# Example: ...". The function definition is a Python idiom for the wrapper.
</explanation>
```

Which text (S1-S8) was **D3** describing? Write your answer in the CSV.

### D4

```
<explanation>
Conversational UK weather advisory tone established, suggesting a casual post introducing a forecast update or travel warning.

The phrase "The forecast is looking stormy for the weekend" signals a news/advice response, implying a cautionary statement about the UK coastal storm or the planned outdoor event.

Final token "weather." ends a topic-setting sentence ("The forecast is expected to be stormy."), immediately expecting a reaction like "So we're cancelling..." or "This means..." or "I'm wondering if that's a good idea." or "There are some safety concerns..." or "With that in mind, the house/home is the best place."
</explanation>
```

Which text (S1-S8) was **D4** describing? Write your answer in the CSV.

## When you're done

Fill in `round-a-ANSWERS.csv` and send it back. The last rows are for your name, the
date, and roughly how long it took.
