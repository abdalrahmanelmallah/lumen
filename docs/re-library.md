# Regex Library

Regular expressions, backed by Python's `re` module. Patterns use
standard regex syntax.

```
import "re"
```

**A note on backslashes:** Lumen strings don't have a raw-string form
(`r"..."` like Python), so a backslash in a pattern needs escaping the
same as in any other string. To match one or more digits, write
`"\\d+"` (two characters in the source, one backslash in the resulting
string).

## Functions

| Function | Description | Example |
|---|---|---|
| `reTest(pattern, s)` | `true` if `pattern` matches anywhere in `s` | `reTest("\\d+", "abc123")` → `true` |
| `reMatch(pattern, s)` | the first match, or `null` if none | `reMatch("\\d+", "abc123def")` → `"123"` |
| `reFindAll(pattern, s)` | every non-overlapping match, as a list | `reFindAll("\\d+", "a1 b22")` → `["1", "22"]` |
| `reGroups(pattern, s)` | captured groups `(...)` from the first match, as a list, or `null` if no match | `reGroups("(\\w+)@(\\w+)", "me@x")` → `["me", "x"]` |
| `reReplace(pattern, s, repl)` | replaces every match with `repl` | `reReplace("\\s+", "a  b", "_")` → `"a_b"` |
| `reReplaceFirst(pattern, s, repl)` | replaces only the first match | |
| `reSplit(pattern, s)` | splits `s` wherever `pattern` matches | `reSplit(",\\s*", "a, b,c")` → `["a", "b", "c"]` |

**Notes**
- An invalid pattern raises an error (catchable with `try`/`catch`)
  rather than silently matching nothing.
- `reReplace`'s replacement text is inserted literally — it doesn't
  support Python's `\1`-style backreferences.

## Example

```
import "re"

let text = "Contact: alice@example.com or bob@test.org"

run(reTest("\\w+@\\w+\\.\\w+", text))          # -> true
run(reFindAll("\\w+@\\w+\\.\\w+", text))       # -> ["alice@example.com", "bob@test.org"]

let groups = reGroups("(\\w+)@(\\w+)\\.(\\w+)", "alice@example.com")
run(groups)                                    # -> ["alice", "example", "com"]

run(reReplace("\\s+", "too    many   spaces", " "))
```
