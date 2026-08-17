# Lists

Lumen has a built-in list (array) type — the single most useful addition
to the language, since almost every real program needs a collection of
things (scores, inventory, enemies in `subgame`, lines from a file...).

Unlike the other libraries, list **literals and indexing are part of the
language itself** — no `import` required. The `lists` library adds
higher-level operations (`push`, `map`, `sort`, ...) on top.

```
import "lists"    # only needed for the functions below — literals/indexing always work
```

---

## Literals and indexing (built into the language, no import needed)

| Syntax | Description | Example |
|---|---|---|
| `[a, b, c]` | a list literal | `let nums = [10, 20, 30]` |
| `list[i]` | read the element at index `i` (0-based) | `nums[0]` → `10` |
| `list[i] = v` | replace the element at index `i` | `nums[0] = 99` |
| `len(list)` | number of elements | `len(nums)` → `3` |
| `a + b` | concatenate two lists into a new one | `[1, 2] + [3, 4]` → `[1, 2, 3, 4]` |

Lists can hold any type, including other lists:

```
let matrix = [[1, 2], [3, 4]]
run(matrix[1][0])    # -> 3
```

Lists are mutable and passed by reference, same as in most languages — if
you pass a list into a function and modify it there (e.g. with `push`), the
caller sees the change too.

---

## `lists` — operations (Python-backed)

| Function | Description | Example |
|---|---|---|
| `push(list, value)` | appends `value`, returns the list | `push(nums, 40)` |
| `pop(list)` | removes and returns the last element | `pop(nums)` |
| `insert(list, i, value)` | inserts `value` at index `i` | `insert(nums, 1, 15)` |
| `removeAt(list, i)` | removes and returns the element at index `i` | `removeAt(nums, 0)` |
| `indexOf(list, value)` | index of `value`, or `-1` if not found | `indexOf(nums, 20)` |
| `contains(list, value)` | true if `value` is in the list | `contains(nums, 20)` |
| `reverse(list)` | a new list, reversed | `reverse([1, 2, 3])` → `[3, 2, 1]` |
| `slice(list, start, end)` | a sub-list from `start` up to (not including) `end`; `end` is optional | `slice(nums, 1, 3)` |
| `sort(list)` | a new list, sorted ascending | `sort([3, 1, 2])` → `[1, 2, 3]` |
| `copy(list)` | a shallow copy | `copy(nums)` |
| `isEmpty(list)` | true if the list has no elements | `isEmpty([])` → `true` |
| `first(list)` | the first element | `first(nums)` |
| `last(list)` | the last element | `last(nums)` |
| `map(list, fn)` | a new list with `fn` applied to every element | `map(nums, double)` |
| `filter(list, fn)` | a new list with only elements where `fn` returns true | `filter(nums, isEven)` |
| `forEach(list, fn)` | calls `fn` on every element, for its side effects | `forEach(nums, run)` |
| `reduce(list, fn, initial)` | combines all elements into one value | `reduce(nums, add, 0)` |

`map`, `filter`, `forEach`, and `reduce` take a Lumen function (defined
with `fn`) as an argument — functions are values in Lumen, so you can pass
them around like anything else.

---

## `lists.lu` — helpers written in Lumen

These are built purely from the primitives above, using `while` and
indexing — open `libs/lists.lu` to see how, or to add your own.

| Function | Description | Example |
|---|---|---|
| `sum(list)` | total of all numbers | `sum([1, 2, 3])` → `6` |
| `average(list)` | mean of all numbers | `average([1, 2, 3])` → `2.0` |
| `maxOf(list)` | largest element | `maxOf([3, 9, 1])` → `9` |
| `minOf(list)` | smallest element | `minOf([3, 9, 1])` → `1` |
| `repeatList(value, count)` | a new list with `value` repeated `count` times | `repeatList(0, 3)` → `[0, 0, 0]` |
| `range(n)` | `[0, 1, ..., n - 1]` | `range(5)` → `[0, 1, 2, 3, 4]` |

`range` is handy for looping a fixed number of times without a separate
counter variable in your own code:

```
import "lists"
let steps = range(5)
let i = 0
while i < len(steps) {
    run("step", steps[i])
    i = i + 1
}
```

---

## Full example

```
import "lists"

let scores = [88, 95, 72, 60, 100]
run("scores:", scores)
run("highest:", maxOf(scores))
run("average:", average(scores))

push(scores, 42)
sort(scores)
run("sorted:", sort(scores))

fn isPassing(score) {
    return score >= 70
}
run("passing scores:", filter(scores, isPassing))
```

Output:
```
scores: [88, 95, 72, 60, 100]
highest: 100
average: 83.0
sorted: [42, 60, 72, 88, 95, 100]
passing scores: [88, 95, 72, 100]
```
