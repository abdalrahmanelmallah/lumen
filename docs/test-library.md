# Test Library

Small assertion helpers for writing tests in Lumen itself
(`libs/test.lu`).

```
import "test"
```

Lumen doesn't have a `throw` statement, so every `assert*` function
signals failure the same way any other error does: it prints a `FAIL:`
line and then raises an error, which `try`/`catch` can catch (the
`err` you catch is a message string, not an exception object — see
`try`/`catch` in the main README).

## Functions

| Function | Description |
|---|---|
| `assertTrue(value, message)` | fails unless `value` is truthy |
| `assertFalse(value, message)` | fails unless `value` is falsy |
| `assertEqual(actual, expected, message)` | fails unless `actual == expected` |
| `assertNotEqual(actual, notExpected, message)` | fails if `actual == notExpected` |
| `assertClose(actual, expected, tolerance, message)` | fails unless `\|actual - expected\| <= tolerance` — for float results that won't be exactly equal |

`message` is a short label describing what's being checked — it's
included in the failure output so you know which assertion failed.

## Example

```
import "test"
import "mathlib"

fn testSquare() {
    assertEqual(square(3), 9, "square(3)")
    assertEqual(square(0), 0, "square(0)")
    assertEqual(square(-4), 16, "square(-4)")
}

fn testClamp() {
    assertEqual(clamp(15, 0, 10), 10, "clamp above range")
    assertEqual(clamp(-5, 0, 10), 0, "clamp below range")
    assertEqual(clamp(5, 0, 10), 5, "clamp inside range")
}

try {
    testSquare()
    testClamp()
    run("all tests passed")
} catch err {
    run("TEST FAILED: " + err)
}
```

Since `try`/`catch` stops at the first failure, a failing assertion
tells you which check failed (via the `FAIL:` line it prints before
raising) even though the caught `err` itself is just the underlying
"index out of range" message.
