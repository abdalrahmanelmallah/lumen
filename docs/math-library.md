# Math Library

Lumen's math functions come from two libraries. Import whichever you need:

```
import "mathlib"    # basic math, written in Lumen itself
import "mathx"        # precision math, backed by Python's math module
```

You can import both at once if you need functions from each.

---

## `mathlib` — basic math (pure Lumen)

| Function | Description | Example |
|---|---|---|
| `square(x)` | x squared | `square(5)` → `25` |
| `cube(x)` | x cubed | `cube(3)` → `27` |
| `abs(x)` | absolute value | `abs(-7)` → `7` |
| `max(a, b)` | the larger of two numbers | `max(3, 9)` → `9` |
| `min(a, b)` | the smaller of two numbers | `min(3, 9)` → `3` |
| `pow(base, exponent)` | base raised to a whole-number power | `pow(2, 10)` → `1024` |
| `isEven(n)` | true if n is even | `isEven(4)` → `true` |
| `isOdd(n)` | true if n is odd | `isOdd(4)` → `false` |
| `factorial(n)` | n! (n × n-1 × ... × 1) | `factorial(5)` → `120` |
| `gcd(a, b)` | greatest common divisor | `gcd(48, 18)` → `6` |
| `clamp(x, lo, hi)` | keeps x within [lo, hi] | `clamp(15, 0, 10)` → `10` |
| `average(a, b)` | mean of two numbers | `average(4, 10)` → `7.0` |

**Notes**
- `pow(base, exponent)` only supports whole-number, non-negative exponents (it works by repeated multiplication). For fractional or negative exponents, see `mathx` below.
- `factorial(n)` and `gcd(a, b)` are recursive — very large `n` may be slow, since Lumen doesn't optimize recursion.

---

## `mathx` — precision math (Python-backed)

These need real floating-point math, so they're backed by Python's built-in `math` module for accuracy.

| Function / Constant | Description | Example |
|---|---|---|
| `sqrt(x)` | square root | `sqrt(2)` → `1.4142135623730951` |
| `floor(x)` | round down to the nearest whole number | `floor(3.7)` → `3` |
| `ceil(x)` | round up to the nearest whole number | `ceil(3.2)` → `4` |
| `round(x)` | round to the nearest whole number | `round(3.456)` → `3` |
| `log(x)` | natural logarithm (base e) | `log(1)` → `0.0` |
| `log10(x)` | base-10 logarithm | `log10(100)` → `2.0` |
| `sin(x)` | sine (x in radians) | `sin(0)` → `0.0` |
| `cos(x)` | cosine (x in radians) | `cos(0)` → `1.0` |
| `tan(x)` | tangent (x in radians) | `tan(0)` → `0.0` |
| `PI` | the constant π | `PI` → `3.141592653589793` |
| `E` | the constant e | `E` → `2.718281828459045` |

`PI` and `E` are constants, not functions — use them without parentheses: `run(PI)`, not `run(PI())`.

---

## Full example

```
import "mathlib"
import "mathx"

let radius = 5
let area = PI * square(radius)
run("circle area:", area)

run("sqrt of 2:", sqrt(2))
run("5! =", factorial(5))
run("gcd of 48 and 18:", gcd(48, 18))
run("clamped:", clamp(150, 0, 100))
```

Output:
```
circle area: 78.53981633974483
sqrt of 2: 1.4142135623730951
5! = 120
gcd of 48 and 18: 6
clamped: 100
```

---

## Writing your own math functions

Want to add more? Two options:

1. **Pure Lumen** — open `libs/mathlib.lu` and add a new `fn`. Good for anything expressible with `+ - * / % if while`.
2. **Native (Python-backed)** — open `lumen.py`, find `@register_native_lib("mathx")`, and add a line like `env.define("cbrt", lambda x: x ** (1/3))`. Good for anything needing real precision or Python's math module.
