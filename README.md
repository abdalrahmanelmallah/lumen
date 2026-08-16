# Lumen

![Lumen logo](assets/lumen-logo.png)

A tiny programming language, implemented in one Python file (`lumen.py`).
It has variables, `if`/`else`, `while`, functions, recursion, strings, numbers, lists,
and comments — plus a simple import system for adding libraries.

## Run it

```
python3 lumen.py examples/demo.lu
```

## Download

Grab the latest release for your OS from the [Releases page](../../releases):

- **macOS** — `Lumen.app.zip`. Unzip it and double-click **Lumen.app**.
  (First launch only: macOS will say it can't verify the developer.
  Right-click the app → **Open** → **Open** again. After that it opens
  normally.)
- **Windows** — `Lumen-windows.zip`. Unzip it anywhere and double-click
  **Lumen.exe** inside the `Lumen` folder.
  (First launch only: Windows SmartScreen may warn that this is an
  unrecognized app, since it isn't code-signed. Click **More info** →
  **Run anyway**.)
- **Linux** — `Lumen-linux.zip`. Unzip it, then run `./Lumen/Lumen`
  from a terminal (or double-click it, if your file manager runs
  executables directly). Run `Install Linux Desktop Entry.sh` afterward
  to add it to your application menu with an icon.

All three are the same windowed code editor: a code pane, a Run button,
and an output pane — no Python or terminal needed once it's installed.

## Building the app yourself

If you've cloned this repo, each OS has a double-click build script that
installs PyInstaller and builds the desktop app for you — no typing a
command required:

| OS | Script | Output |
|---|---|---|
| macOS | `Build for Mac.command` | `dist/Lumen.app` |
| Windows | `Build for Windows.bat` | `dist\Lumen\Lumen.exe` |
| Linux | `Build for Linux.sh` | `dist/Lumen/Lumen` |

All three run `pyinstaller Lumen.spec`, which picks the right icon
format for the OS it's running on and only builds a `.app` bundle on
macOS (Windows/Linux get a plain folder with the executable inside).
Executables aren't cross-platform — build separately on each OS you want
an app for.

On Windows, first-time double-click may show a SmartScreen prompt (see
above) since the script isn't code-signed. On Linux, right-click the
script → **Properties** → **Permissions** → **Allow executing as
program**, or run it from a terminal with `./"Build for Linux.sh"`.

Note: the `subgame` graphics library needs Tk to be available on the
machine you build on. Most standard Python installers for macOS and
Windows include it; on Linux you may need to install it separately
(`sudo apt install python3-tk` on Debian/Ubuntu, `sudo dnf install
python3-tkinter` on Fedora, `sudo pacman -S tk` on Arch). If Tk isn't
found, the build scripts explain what to install and where.

### Prefer a single-file command-line executable instead?

`build.sh` (macOS/Linux) and `build.ps1` (Windows) build a plain
one-file `lumen`/`lumen.exe` binary — no GUI, just the interpreter,
for running `.lu` scripts from a terminal without installing Python.

## Installing (so `lumen` works from anywhere)

Once this repo is on GitHub, anyone (including you, on a different machine)
can install it with one command — no cloning, no dependencies beyond
Python 3:

```
curl -fsSL https://raw.githubusercontent.com/abdalrahmanelmallah/lumen/main/install.sh | bash
```

This downloads `lumen.py` and the bundled `.lu` libraries into
`~/.lumen`, and puts a `lumen` command on your `PATH` (you may need to
add `~/.local/bin` to your `PATH`, as the installer will tell you). After
that:

```
lumen hello.lu
lumen get lists strings     # fetch any .lu library from this repo on demand
```

`lumen get <name>` downloads `lumen/libs/<name>.lu` straight from
GitHub — handy if you don't want the whole repo, or if you (or someone else)
publish new community libraries there later. Native libraries (`file`,
`mathx`, `sys`, `random`) don't need fetching — they're built into
`lumen.py` itself, so `import "file"` just works once it's installed.

### Windows

If you have Git Bash or WSL, use the `curl | bash` command above as-is. In
plain PowerShell (no bash), use the PowerShell installer instead:

```powershell
irm https://raw.githubusercontent.com/abdalrahmanelmallah/lumen/main/lumen/install.ps1 | iex
```

This installs to `%USERPROFILE%\.lumen` and adds a `lumen` command to
your PATH (reopen your terminal afterward for the PATH change to apply).

## Language cheat sheet

```
let x = 5              # variable
x = x + 1               # reassignment (no "let")

if x > 3 {
    run("big")
} elif x > 0 {
    run("small positive")
} else {
    run("small or zero")
}

while x > 0 {
    run(x)
    x = x - 1
}

for let i = 0; i < 5; i = i + 1 {   # C-style for loop
    if i == 2 { continue }
    if i == 4 { break }
    run(i)
}

for item in [1, 2, 3] {              # for-in over lists, dicts, strings
    run(item)
}

fn add(a, b) {
    return a + b
}
run(add(2, 3))

let nums = [10, 20, 30]        # list literal — built into the language
run(nums[0])                    # indexing -> 10
nums[1] = 99                    # index assignment
run(nums)                       # -> [10, 99, 30]

let person = {"name": "Ada", "age": 30}   # dict literal — built into the language
run(person["name"])                        # -> Ada
person["age"] = 31                         # index assignment works on dicts too
run(keys(person))                          # -> ["name", "age"]
run(values(person))
run(hasKey(person, "name"))

class Point {                    # classes
    fn init(self, x, y) {        # "init" runs automatically on `new`
        self.x = x
        self.y = y
    }
    fn dist(self) {
        return sqrt(self.x * self.x + self.y * self.y)
    }
}
import "mathx"
let p = new Point(3, 4)
run(p.x, p.y, p.dist())          # -> 3 4 5.0

try {
    let boom = [1, 2][99]
} catch err {
    run("caught: " + err)
}

let name = "world"
run(f"hello, {name}! 2 + 2 = {2 + 2}")   # string interpolation

/* block comments
   spanning multiple lines */

run(2 ** 10)     # exponent -> 1024
run(6 & 3)       # bitwise and/or/xor/shift also available: & | ^ << >>

import "mathlib"                 # library written in Lumen
import "sys"                     # library written in Python
import "mathlib" as m            # namespaced import
run(m.square(5))                 # -> 25
```

Built-in functions available everywhere: `run`, `len`, `str`, `num`, `ord`,
`chr`, `input`, `typeOf`, `keys`, `values`, `hasKey`, `removeKey`.

Run `python3 lumen.py` with no arguments (or `python3 lumen.py repl`)
to get an interactive REPL.

## Libraries that ship with Lumen

- `mathlib` / `mathx` — math functions (square roots, factorials, rounding, trig, and more). Full reference: [docs/math-library.md](docs/math-library.md)
- lists — list/array literals (`[1, 2, 3]`) and indexing (`list[0]`) are built into the language; `import "lists"` adds `push`, `pop`, `map`, `sort`, and more. Full reference: [docs/lists-library.md](docs/lists-library.md)
- `strings` — string manipulation (`upper`, `split`, `contains`, `replace`, and more). Full reference: [docs/strings-library.md](docs/strings-library.md)
- `file` — read/write text files (`readFile`, `writeFile`, `appendFile`). Full reference: [docs/file-library.md](docs/file-library.md)
- `subgame` — a small 2D game/graphics library (windows, shapes, keyboard input, collisions). Full reference: [docs/subgame-library.md](docs/subgame-library.md)
- `sys` — `clock()`, `sleep(s)`
- `random` — `rand()`, `randint(a, b)`

## Adding libraries

There are two ways to add a library. Pick whichever fits — you don't need to
touch the interpreter for the first kind.

### 1. Pure Lumen libraries (easiest — no Python needed)

Just write a `.lu` file and drop it in the `libs/` folder. Any function or
variable you define at the top level becomes available to whoever imports it.

`libs/greetings.lu`:
```
fn hello(name) {
    run("Hello, " + name + "!")
}
```

Use it from any program:
```
import "greetings"
hello("world")     # -> Hello, world!
```

That's it. `import "greetings"` looks for `libs/greetings.lu` (or any folder
you pass as an extra command-line argument, e.g.
`python3 lumen.py myprog.lu extra_lib_dir`) and runs it, so all its
definitions land in your program's scope.

### 2. Native libraries (backed by real Python code)

Use this when a library needs something Lumen can't do itself — file I/O,
networking, math beyond `+ - * /`, timing, etc. You write a small Python
function and register it.

Open `lumen.py` and find the "NATIVE LIBRARIES" section near the bottom. Add
a new function decorated with `@register_native_lib("yourname")`:

```python
@register_native_lib("textutils")
def _lib_textutils(interp, env):
    env.define("shout", lambda s: s.upper() + "!")
    env.define("whisper", lambda s: s.lower())
```

Now any Lumen program can do:
```
import "textutils"
run(shout("hello"))   # -> HELLO!
```

(`strings`, `lists`, and `file` — shipped with Lumen, described below —
are all built exactly this way, so their implementations in `lumen.py`
are worth reading as real examples.)

The function you write receives `(interp, env)`:
- `interp` — the running interpreter, in case your library needs to call
  back into Lumen code.
- `env` — the environment to define things into. Call `env.define(name, value)`
  for every function/constant you want to expose. Any plain Python
  function or lambda works as a callable Lumen function automatically.

Two native libraries ship as examples already: `"sys"` (`clock()`, `sleep(s)`)
and `"random"` (`rand()`, `randint(a, b)`) — look at the bottom of `lumen.py`
for their (very short) implementations.

## How it works internally (if you want to extend the language itself)

`lumen.py` is split into clearly labeled sections:

1. **Lexer** — regex-based, turns source text into a token stream.
2. **Parser** — recursive-descent / precedence-climbing, builds an AST out
   of plain tuples like `("binop", "+", left, right)`.
3. **Interpreter** — a tree-walking evaluator (`exec_stmt` for statements,
   `eval` for expressions) with a chained `Environment` for variable scoping.
4. **Builtins** — always-available functions (`run`, `len`, ...).
5. **Native libraries** — the plugin registry described above.

To add a new keyword or operator to the language itself (say, a `for` loop
or `elif`), you'd extend three places: `KEYWORDS`/`TOKEN_SPEC` in the lexer
if needed, a new `parse_*` case in the `Parser`, and a matching case in
`Interpreter.exec_stmt` or `.eval`. The tuple-based AST keeps this pretty
mechanical — copy the shape of `"while"` or `"if"` as a template.
