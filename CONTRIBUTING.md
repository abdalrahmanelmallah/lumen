# Contributing to Lumen

Thanks for considering it! Lumen is a small, hobby-scale project, so the
bar is "does it work and is it easy to follow" rather than anything
heavyweight.

## Setup

No build step for the interpreter itself — it's one Python file with no
dependencies beyond the standard library.

```
git clone https://github.com/abdalrahmanelmallah/lumen.git
cd lumen
python3 lumen.py examples/demo.lu     # confirm it runs
pip install pytest                    # only needed to run the test suite
python3 -m pytest tests/ -v
```

## Making a change

- **Adding a library?** See the "Adding libraries" section in
  [README.md](README.md#adding-libraries) — most libraries are a single
  `.lu` file and don't need to touch `lumen.py` at all. Add a
  `docs/<name>-library.md` (copy an existing one as a template) and a
  line in the README's library table.
- **Fixing a bug in the interpreter?** `lumen.py` is organized into clearly
  labeled sections (lexer, parser, interpreter, builtins, native
  libraries) — the section comments (`# --- 1. LEXER ---` etc.) are there
  to help you find the right spot.
- **Changing the desktop app?** That's `lumen_gui.py`. Test it by actually
  launching it (`python3 lumen_gui.py`) — it isn't covered by the
  automated tests.

## Before opening a pull request

```
python3 -m pytest tests/ -v
```

`tests/test_core.py` exercises the interpreter directly, `tests/test_libraries.py`
exercises each library through small `.lu` snippets, and `tests/test_examples.py`
runs every file in `examples/` end-to-end — a broken example there almost
always means a library change had a side effect you didn't expect.

If you added a function to any library, add a test for it alongside the
existing ones in `tests/test_libraries.py` — a few lines calling the
function and checking its output is enough.

CI (`.github/workflows/ci.yml`) runs the same suite on Linux, macOS, and
Windows across two Python versions on every push and pull request, so
platform-specific issues (like the file-encoding bug this project has
already hit once) get caught before merge.

## Style

- Follow what's already there — `.lu` libraries use the same doc-comment
  style as `libs/mathlib.lu` (a `#` comment above each function
  explaining anything non-obvious, with an example when the behavior
  isn't self-evident from the name).
- Prefer a pure-Lumen (`.lu`) library over a native (Python) one unless
  you actually need something Lumen can't do itself (file I/O, regex,
  networking, timing, etc.) — it's easier for others to read and modify.
- Keep functions small; Lumen doesn't optimize recursion, so deeply
  recursive helpers should mention that in a comment (see `factorial` in
  `libs/mathlib.lu` for an example).

## Reporting bugs / requesting features

Open an issue — there are templates for both bug reports and feature
requests that'll prompt for the details that make them quick to act on.
