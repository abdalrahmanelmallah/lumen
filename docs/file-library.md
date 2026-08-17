# File Library

Read, write, search, and manage files and folders from Lumen — lets a
program save data (high scores, settings, logs), organize files into
folders, and search across a whole directory tree for files or text.

```
import "file"
```

The core read/write/search operations above genuinely need the operating
system, so they're backed directly by Python. On top of them,
`libs/file.lu` adds a few pure-Lumen convenience helpers:

| Function | Description | Example |
|---|---|---|
| `appendLine(path, line)` | appends `line` plus a newline, so you don't have to add `"\n"` yourself | `appendLine("log.txt", "started")` |
| `readFileOrDefault(path, default)` | reads a file, or returns `default` instead of raising an error if it's missing | `readFileOrDefault("config.txt", "")` |
| `fileExtension(path)` | the extension of a file name, without the dot (`""` if there isn't one) | `fileExtension("save.txt")` → `"txt"` |
| `fileNameWithoutExtension(path)` | the file name without its extension | `fileNameWithoutExtension("save.txt")` → `"save"` |
| `ensureDir(path)` | creates a folder only if it doesn't already exist | `ensureDir("saves/backups")` |

Read `libs/file.lu` for the implementations, or add your own helpers there
— anything defined at the top level of that file becomes available
automatically whenever a program does `import "file"`.

---

## Reading & writing

| Function | Description | Example |
|---|---|---|
| `readFile(path)` | reads the whole file and returns its contents as one string | `readFile("save.txt")` |
| `readLines(path)` | reads the file and returns a list of strings, one per line (no `\n`) | `readLines("save.txt")` |
| `writeFile(path, text)` | overwrites the file with `text` (creates it if missing) | `writeFile("save.txt", "score: 100")` |
| `appendFile(path, text)` | adds `text` to the end of the file, without erasing what's there | `appendFile("log.txt", "started\n")` |

**Note:** `readFile` and `readLines` raise an error if the file doesn't
exist — check with `fileExists(path)` first if you're not sure.

---

## Checking & deleting

| Function | Description | Example |
|---|---|---|
| `fileExists(path)` | true if something exists at `path` | `fileExists("save.txt")` |
| `isFile(path)` | true if `path` exists and is a regular file | `isFile("save.txt")` |
| `isDir(path)` | true if `path` exists and is a folder | `isDir("saves")` |
| `fileSize(path)` | size of the file at `path`, in bytes | `fileSize("save.txt")` |
| `deleteFile(path)` | deletes the file at `path` | `deleteFile("temp.txt")` |

---

## Folders

| Function | Description | Example |
|---|---|---|
| `makeDir(path)` | creates a folder (and any missing parent folders) | `makeDir("saves/backups")` |
| `listDir(path)` | returns a sorted list of the names directly inside a folder | `listDir("saves")` |
| `removeDir(path)` | deletes a folder and everything inside it | `removeDir("saves/backups")` |
| `currentDir()` | returns the current working directory | `currentDir()` |

---

## Copying, moving & paths

| Function | Description | Example |
|---|---|---|
| `copyFile(src, dst)` | copies a file from `src` to `dst` | `copyFile("save.txt", "save.bak")` |
| `moveFile(src, dst)` | moves (or renames) a file from `src` to `dst` | `moveFile("temp.txt", "final.txt")` |
| `renameFile(old, new)` | alias for `moveFile` — reads a little better for renames | `renameFile("v1.txt", "v2.txt")` |
| `joinPath(a, b)` | joins two path pieces with the right separator | `joinPath("saves", "a.txt")` |
| `baseName(path)` | the file name at the end of a path | `baseName("saves/a.txt")` |
| `dirName(path)` | the folder part of a path | `dirName("saves/a.txt")` |
| `absPath(path)` | turns a relative path into an absolute one | `absPath("saves/a.txt")` |

---

## Searching

| Function | Description | Example |
|---|---|---|
| `findFiles(dir, pattern)` | recursively searches `dir` for files whose name matches a glob pattern (`*`, `?`), returning a sorted list of paths | `findFiles("saves", "*.txt")` |
| `findDirs(dir, pattern)` | same as `findFiles`, but matches folder names instead | `findDirs(".", "backup*")` |
| `searchInFile(path, text)` | searches one file's contents for `text`; returns a list of `[lineNumber, lineText]` pairs | `searchInFile("log.txt", "error")` |
| `searchInFiles(dir, pattern, text)` | recursively searches every file under `dir` matching `pattern` for `text`; returns a list of `[path, lineNumber, lineText]` triples | `searchInFiles("logs", "*.log", "error")` |

`findFiles` and `findDirs` walk every subfolder, so a single call can search
an entire project tree. Use `pattern = "*"` to match every file or folder.

---

## Full example

```
import "file"
import "strings"

let path = "highscore.txt"

if fileExists(path) {
    let saved = trim(readFile(path))
    run("Previous high score:", saved)
} else {
    run("No high score yet.")
}

writeFile(path, "9001")
run("Saved new high score.")
```

A save/load pattern for structured data, using `strings` and `lists` to
turn a list of numbers into one line and back again:

```
import "file"
import "strings"
import "lists"

fn saveScores(path, scores) {
    let lines = []
    let i = 0
    while i < len(scores) {
        lines = push(lines, str(scores[i]))
        i = i + 1
    }
    writeFile(path, join(lines, ","))
}

fn loadScores(path) {
    let parts = split(readFile(path), ",")
    let scores = []
    let i = 0
    while i < len(parts) {
        scores = push(scores, num(parts[i]))
        i = i + 1
    }
    return scores
}

saveScores("scores.txt", [10, 20, 30])
run(loadScores("scores.txt"))    # -> [10, 20, 30]
```

Searching a whole project for every save file and backing each one up:

```
import "file"

let saves = findFiles("saves", "*.sav")
run("Found", len(saves), "save files")

makeDir("saves/backup")

let i = 0
while i < len(saves) {
    let name = baseName(saves[i])
    copyFile(saves[i], joinPath("saves/backup", name))
    i = i + 1
}

run("Backup complete.")
```

Searching log files for every mention of "error":

```
import "file"

let hits = searchInFiles("logs", "*.log", "error")

let i = 0
while i < len(hits) {
    let path = hits[i][0]
    let lineNo = hits[i][1]
    let lineText = hits[i][2]
    run(path, ":", lineNo, "->", lineText)
    i = i + 1
}
```

Using the `libs/file.lu` helpers together:

```
import "file"

ensureDir("logs")
appendLine("logs/app.log", "started")
appendLine("logs/app.log", "ready")

let config = readFileOrDefault("logs/config.txt", "default-config")
run("config:", config)
run("extension:", fileExtension("logs/app.log"))       # -> "log"
run("base name:", fileNameWithoutExtension("logs/app.log"))   # -> "app"
```
