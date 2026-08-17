# Collections Library

`Stack`, `Queue`, and `Set` — three common data structures, written in
pure Lumen (`libs/collections.lu`) on top of the built-in list/dict
primitives and the `lists` library.

```
import "collections"
```

## `Stack` — last-in-first-out

| Method | Description |
|---|---|
| `new Stack()` | creates an empty stack |
| `.push(value)` | adds `value` to the top |
| `.pop()` | removes and returns the top value (errors if empty) |
| `.peek()` | returns the top value without removing it (errors if empty) |
| `.isEmpty()` | `true`/`false` |
| `.size()` | number of items |

```
let s = new Stack()
s.push(1)
s.push(2)
run(s.pop())     # -> 2
run(s.size())    # -> 1
```

## `Queue` — first-in-first-out

| Method | Description |
|---|---|
| `new Queue()` | creates an empty queue |
| `.enqueue(value)` | adds `value` to the back |
| `.dequeue()` | removes and returns the front value (errors if empty) |
| `.peek()` | returns the front value without removing it |
| `.isEmpty()` | `true`/`false` |
| `.size()` | number of items |

```
let q = new Queue()
q.enqueue("a")
q.enqueue("b")
run(q.dequeue())  # -> "a"
```

## `Set` — unique values, fast membership checks

Backed by a dict internally, so `.has()` is O(1) instead of scanning a
list. Values are compared by their string form (via `str(value)`), so
`1` and `"1"` are treated as the same member.

| Method | Description |
|---|---|
| `new Set()` | creates an empty set |
| `.add(value)` | adds `value` (no effect if already present) |
| `.remove(value)` | removes `value` if present |
| `.has(value)` | `true`/`false` |
| `.size()` | number of unique members |
| `.toList()` | all members as a list (order not guaranteed) |

```
let seen = new Set()
seen.add("alice")
seen.add("bob")
seen.add("alice")
run(seen.size())        # -> 2
run(seen.has("alice"))  # -> true
```

**Note:** if you just need to deduplicate a list once rather than build
up a set incrementally, `unique(list)` from the `lists` library is
simpler.
