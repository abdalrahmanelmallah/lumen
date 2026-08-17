# Format Library

Small text/number formatting helpers that need exact Python behavior
(float precision, padding) rather than plain Lumen logic.

```
import "format"
```

## Functions

| Function | Description | Example |
|---|---|---|
| `toFixed(x, digits)` | `x` as a string with exactly `digits` decimal places (default `2`) | `toFixed(3.14159, 2)` → `"3.14"` |
| `padStart(s, width, ch)` | pads `s` on the left to `width` characters with `ch` (default `" "`) | `padStart("7", 3, "0")` → `"007"` |
| `padEnd(s, width, ch)` | pads `s` on the right to `width` characters with `ch` | `padEnd("hi", 5, ".")` → `"hi..."` |
| `withCommas(x)` | `x` with thousands separators | `withCommas(1234567)` → `"1,234,567"` |
| `zeroPad(n, width)` | `n` as a string, zero-padded to `width` digits | `zeroPad(5, 3)` → `"005"` |

**Notes**
- `toFixed` rounds using standard round-half-to-even (Python's default),
  same as most languages — `toFixed(2.5, 0)` → `"2"`.
- `withCommas` uses 2 decimal places for non-whole numbers, none for
  whole numbers: `withCommas(1234567)` → `"1,234,567"`,
  `withCommas(1234.5)` → `"1,234.50"`.

## Example

```
import "format"

let price = 19.9
run("$" + toFixed(price, 2))              # -> $19.90

let id = 7
run("ITEM-" + zeroPad(id, 4))             # -> ITEM-0007

run(padEnd("Name", 10, " ") + "Score")    # -> "Name      Score"
run(withCommas(2500000))                  # -> 2,500,000
```
