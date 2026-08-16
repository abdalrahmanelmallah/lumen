# Strings Library

String manipulation for Lumen — before this library, the only thing you
could do with strings was concatenate them with `+`.

```
import "strings"
```

That one import gives you everything below — both the low-level operations
(backed by Python) and the helper functions (written in plain Lumen, in
`libs/strings.lu`, which you can open and read/edit).

---

## `strings` — operations (Python-backed)

| Function | Description | Example |
|---|---|---|
| `upper(s)` | uppercase | `upper("hello")` → `"HELLO"` |
| `lower(s)` | lowercase | `lower("HELLO")` → `"hello"` |
| `trim(s)` | removes leading/trailing whitespace | `trim("  hi  ")` → `"hi"` |
| `split(s, sep)` | splits into a list on `sep` | `split("a,b,c", ",")` → `["a", "b", "c"]` |
| `join(list, sep)` | joins a list of strings with `sep` in between | `join(["a", "b", "c"], "-")` → `"a-b-c"` |
| `contains(s, sub)` | true if `sub` appears in `s` | `contains("hello", "ell")` → `true` |
| `replace(s, old, new)` | replaces every occurrence of `old` with `new` | `replace("hello", "l", "L")` → `"heLLo"` |
| `indexOf(s, sub)` | index of the first occurrence of `sub`, or `-1` | `indexOf("hello", "l")` → `2` |
| `startsWith(s, prefix)` | true if `s` starts with `prefix` | `startsWith("hello", "he")` → `true` |
| `endsWith(s, suffix)` | true if `s` ends with `suffix` | `endsWith("hello", "lo")` → `true` |
| `charAt(s, i)` | the character at index `i` | `charAt("hello", 1)` → `"e"` |
| `substring(s, start, end)` | the slice from `start` up to (not including) `end`; `end` is optional | `substring("hello world", 6)` → `"world"` |
| `repeat(s, n)` | `s` repeated `n` times | `repeat("ab", 3)` → `"ababab"` |
| `isEmpty(s)` | true if `s` has no characters | `isEmpty("")` → `true` |

You can also index into a string directly, same as a list — `s[0]` gives
you the first character, since strings and lists share indexing syntax.

---

## `strings.lu` — helpers written in Lumen

These are built purely from the operations above, showing what's possible
without any Python — open `libs/strings.lu` to see how, or to add your own.

| Function | Description | Example |
|---|---|---|
| `capitalize(s)` | uppercases just the first letter | `capitalize("hello")` → `"Hello"` |
| `reverseString(s)` | reverses the characters | `reverseString("hello")` → `"olleh"` |
| `countOccurrences(s, sub)` | counts non-overlapping occurrences of `sub` | `countOccurrences("banana", "a")` → `3` |

---

## Full example

```
import "strings"

let name = "  ada lovelace  "
let clean = trim(name)
run(capitalize(clean))                  # -> Ada lovelace

let csv = "apples,bananas,cherries"
let fruits = split(csv, ",")
run(fruits)                             # -> ["apples", "bananas", "cherries"]
run(join(fruits, " | "))                # -> apples | bananas | cherries

if contains(clean, "lovelace") {
    run("found it!")
}
```
