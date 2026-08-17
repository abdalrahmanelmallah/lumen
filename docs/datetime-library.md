# Date/Time Library

Date and time formatting/arithmetic, backed by Python's `datetime`
module.

```
import "datetime"
```

Times are plain numbers — Unix timestamps (seconds since 1970-01-01
UTC, in your local timezone for display), the same kind of number
`clock()` from the `sys` library returns. That means you can store
them, compare them with `<`/`>`, and do math on them directly.

## Functions

| Function | Description | Example |
|---|---|---|
| `now()` | the current time, as a timestamp | `now()` → `1771234567.89` |
| `nowString(fmt)` | the current time, formatted (default `"%Y-%m-%d %H:%M:%S"`) | `nowString()` → `"2026-02-14 09:30:00"` |
| `today()` | today's date as `"YYYY-MM-DD"` | `today()` → `"2026-02-14"` |
| `formatTime(ts, fmt)` | formats a timestamp using [strftime codes](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes) | `formatTime(0, "%Y-%m-%d")` → `"1970-01-01"` |
| `parseTime(s, fmt)` | parses a formatted string back into a timestamp | `parseTime("2020-01-01", "%Y-%m-%d")` |
| `year(ts)` / `month(ts)` / `day(ts)` | the calendar year/month/day of a timestamp | |
| `hour(ts)` / `minute(ts)` / `second(ts)` | the time-of-day components | |
| `weekdayName(ts)` | the day of the week, e.g. `"Monday"` | |
| `addSeconds(ts, n)` | `ts` shifted by `n` seconds (n can be negative) | |
| `addDays(ts, n)` | `ts` shifted by `n` days | |

**Notes**
- `addDays` adds exactly `n * 86400` seconds. That's correct for almost
  everything, but around a daylight-saving-time change the wall-clock
  time can shift by an hour — this library doesn't do calendar-aware
  month/year arithmetic (e.g. "one month from Jan 31").
- `parseTime` raises an error if `s` doesn't match `fmt` exactly.

## Example

```
import "datetime"

run("started at " + nowString())

let start = now()
# ... do some work ...
let elapsed = now() - start
run(f"took {elapsed} seconds")

let deadline = addDays(now(), 7)
run("due: " + formatTime(deadline, "%A, %B %d"))

let birthday = parseTime("2000-06-15", "%Y-%m-%d")
run(weekdayName(birthday))
```
