# JSON Library

Read and write JSON, backed by Python's `json` module.

```
import "json"
```

Lumen's own value types map onto JSON directly, so encoding/decoding is
lossless for anything JSON can represent:

| Lumen | JSON |
|---|---|
| dict (`{"a": 1}`) | object |
| list (`[1, 2]`) | array |
| string | string |
| number | number |
| `true` / `false` | `true` / `false` |
| `null` | `null` |

Class instances and functions can't be converted — trying to
`jsonStringify` one raises an error.

## Functions

| Function | Description | Example |
|---|---|---|
| `jsonParse(text)` | parses a JSON string into a Lumen value | `jsonParse("[1,2,3]")` → `[1, 2, 3]` |
| `jsonStringify(value)` | converts a Lumen value into a compact JSON string | `jsonStringify({"a": 1})` → `"{\"a\": 1}"` |
| `jsonStringify(value, indent)` | same, pretty-printed with `indent` spaces per level | `jsonStringify({"a": 1}, 2)` |
| `jsonStringifyPretty(value)` | shorthand for `jsonStringify(value, 2)` | |
| `jsonIsValid(text)` | `true`/`false` — whether `text` parses as JSON, without raising | `jsonIsValid("not json")` → `false` |

**Notes**
- `jsonParse` raises an error (catchable with `try`/`catch`) on malformed
  input — use `jsonIsValid` first if you're not sure the text is valid JSON.
- JSON object keys are always strings, so `jsonParse("{\"1\": true}")["1"]`
  works but `["1"][1]` won't — keys stay as the strings JSON requires.

## Example

```
import "json"
import "file"

let config = {"name": "Lumen", "version": 1, "features": ["fast", "tiny"]}
writeFile("config.json", jsonStringifyPretty(config))

let loaded = jsonParse(readFile("config.json"))
run(loaded["name"])           # -> Lumen
run(loaded["features"][0])    # -> fast

try {
    jsonParse("{not valid}")
} catch err {
    run("bad config: " + err)
}
```
