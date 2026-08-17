# OS Library

Talk to the operating system — environment variables, the current process,
running shell commands, and basic machine info.

```
import "os"
```

For files and folders, see the `file` library instead — `os` is about the
*machine and process*, `file` is about *files on disk*.

The core functions above genuinely need the operating system, so they're
backed directly by Python. On top of them, `libs/os.lu` adds a few
pure-Lumen convenience helpers:

| Function | Description | Example |
|---|---|---|
| `isMac()` / `isWindows()` / `isLinux()` | shorthand for `platform() == "..."` | `if isMac() { ... }` |
| `commandOutput(cmd)` | runs a shell command and returns just its trimmed stdout — for when you don't need the exit code or stderr | `commandOutput("whoami")` |
| `commandSucceeded(cmd)` | runs a shell command and returns true/false for whether it exited with code `0` | `commandSucceeded("test -f save.txt")` |
| `exitOk()` / `exitError()` | `exit(0)` / `exit(1)` with names that read better at a call site | `if failed { exitError() }` |

Read `libs/os.lu` for the implementations, or add your own helpers there —
anything defined at the top level of that file becomes available
automatically whenever a program does `import "os"`.

---

## Environment variables

| Function | Description | Example |
|---|---|---|
| `getEnv(name)` | reads an environment variable; returns `""` if it isn't set | `getEnv("HOME")` |
| `getEnv(name, default)` | same, but returns `default` instead of `""` if it isn't set | `getEnv("PORT", "3000")` |
| `hasEnv(name)` | true if the environment variable is set | `hasEnv("HOME")` |
| `setEnv(name, value)` | sets an environment variable for the current process (and anything it launches with `runCommand`) | `setEnv("DEBUG", "1")` |
| `envVars()` | returns every environment variable as a dict | `envVars()` |

---

## Process & machine info

| Function / Constant | Description | Example |
|---|---|---|
| `platform()` | `"mac"`, `"windows"`, or `"linux"` | `platform()` |
| `hostname()` | the machine's network name | `hostname()` |
| `cwd()` | the current working directory | `cwd()` |
| `changeDir(path)` | changes the current working directory | `changeDir("saves")` |
| `homeDir()` | the current user's home directory | `homeDir()` |
| `tempDir()` | the system's temp folder, for scratch files | `tempDir()` |
| `pathSep` | `/` on Mac/Linux, `\` on Windows — a constant, not a function | `run("a" + pathSep + "b")` |
| `exit(code)` | immediately stops the program with the given exit code (`0` = success) | `exit(0)` |

---

## Running shell commands

| Function | Description | Example |
|---|---|---|
| `runCommand(cmd)` | runs `cmd` in the system shell and waits for it to finish; returns a dict `{"stdout": ..., "stderr": ..., "code": ...}` | `runCommand("ls")` |

`runCommand` blocks until the command finishes. `code` is `0` on success and
non-zero on failure, matching normal shell conventions.

**Careful:** `runCommand` runs whatever string you give it in a real shell —
never build that string out of untrusted input (like something typed by an
unknown user) without validating it first.

---

## Full example

```
import "os"

run("Running on:", platform())
run("Working directory:", cwd())

if hasEnv("LUMEN_ENV") {
    run("Environment:", getEnv("LUMEN_ENV"))
} else {
    run("No LUMEN_ENV set, defaulting to dev")
    setEnv("LUMEN_ENV", "dev")
}

let result = runCommand("echo hello from the shell")
if result["code"] == 0 {
    run("Command said:", result["stdout"])
} else {
    run("Command failed:", result["stderr"])
}
```

Combining `os` and `file` to write a log into the system temp folder:

```
import "os"
import "file"

let logPath = joinPath(tempDir(), "lumen.log")
appendFile(logPath, "started on " + platform() + "\n")
run("Logged to:", logPath)
```

Using the `libs/os.lu` helpers together:

```
import "os"

if isMac() {
    run("Running on a Mac")
} elif isWindows() {
    run("Running on Windows")
} else {
    run("Running on Linux (or something else)")
}

if commandSucceeded("test -f lumen.py") {
    run("lumen.py exists here")
} else {
    exitError()
}
```
