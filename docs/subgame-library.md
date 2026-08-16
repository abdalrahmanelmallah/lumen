# Subgame Library

A tiny 2D game/graphics library for Lumen — in the spirit of pygame, but
much smaller. It opens a real window, lets you draw shapes, and reads the
keyboard. No extra installs needed (it's built on Python's built-in `tkinter`,
which ships with Python).

```
import "subgame"
```

That one import gives you everything below — both the drawing/window
functions (backed by Python) and the game-logic helper functions (written in
plain Lumen, in `libs/subgame.lu`, which you can open and read/edit).

**Honest limitation:** Lumen itself has no drawing ability — a `.lu` file
alone can't open a window. The primitives below (`window`, `rect`, `circle`,
etc.) are implemented in Python and built into the interpreter. The helper
functions (`collide`, `clampPosition`, etc.) are genuinely written in
Lumen, on top of those primitives.

---

## Setting up a window

| Function | Description | Example |
|---|---|---|
| `window(width, height, title)` | opens the game window | `window(400, 300, "My Game")` |
| `isOpen()` | true until the player closes the window | used to control your main loop |
| `quit()` | closes the window from code | `quit()` |

Call `window(...)` once, at the top of your program, before drawing anything.

---

## Drawing

Call these inside your game loop, between `clear()` and `update()`.

| Function | Description | Example |
|---|---|---|
| `clear()` | wipes the window blank | `clear()` |
| `rect(x, y, width, height, color)` | draws a filled rectangle | `rect(10, 10, 50, 30, "red")` |
| `circle(x, y, radius, color)` | draws a filled circle | `circle(100, 100, 20, "blue")` |
| `line(x1, y1, x2, y2, color)` | draws a line between two points | `line(0, 0, 400, 300, "black")` |
| `text(x, y, message, color)` | draws text | `text(50, 50, "Score: 10", "black")` |
| `update()` | shows everything you drew and processes input | `update()` |

`color` accepts standard color names (`"red"`, `"blue"`, `"green"`, `"black"`,
`"white"`, `"orange"`, `"purple"`, ...) or hex codes like `"#ff0000"`.

Coordinates: `(0, 0)` is the top-left corner. X increases to the right,
Y increases downward.

---

## Keyboard input

| Function | Description | Example |
|---|---|---|
| `keyPressed(key)` | true while that key is held down | `keyPressed("Left")` |

Common key names: `"Left"`, `"Right"`, `"Up"`, `"Down"`, `"space"`,
`"Escape"`, `"Return"`, or a single letter like `"a"`.

---

## Game-logic helpers (written in Lumen, in `libs/subgame.lu`)

These aren't drawing functions — they're the "math of collisions and
movement" that every simple game needs, and they're plain Lumen code you
can open, read, and modify.

| Function | Description | Example |
|---|---|---|
| `collide(ax, ay, aw, ah, bx, by, bw, bh)` | true if two rectangles overlap | `collide(playerX, playerY, 20, 20, enemyX, enemyY, 20, 20)` |
| `clampPosition(x, lo, hi)` | keeps a coordinate inside a range | `clampPosition(x, 0, 400)` |
| `circlesTouch(ax, ay, ar, bx, by, br)` | true if two circles overlap | `circlesTouch(ballX, ballY, 10, holeX, holeY, 15)` |
| `moveToward(current, target, step)` | moves a value toward a target by at most `step` (no overshoot) | `enemyX = moveToward(enemyX, playerX, 2)` |

---

## The basic game loop shape

Every subgame program follows this pattern:

```
import "subgame"

window(400, 300, "My Game")

let running = true
while running {
    if isOpen() == false {
        running = false
    }

    # 1. read input / update your game state here

    # 2. draw everything
    clear()
    rect(50, 50, 20, 20, "red")
    update()
}

quit()
```

See `examples/bounce.lu` for a complete, working example — a ball that
bounces around the screen with a keyboard-controlled paddle, using
`collide()` and `clampPosition()`.

---

## Extending subgame

- **Add game logic** (pure Lumen): open `libs/subgame.lu` and add a new `fn`, the same way you'd add to `mathlib.lu`.
- **Add drawing/input primitives** (needs Python): open `lumen.py`, find `@register_native_lib("subgame")`, and add a new `env.define("yourFunction", ...)` inside it. tkinter's `Canvas` has many more shape and image options if you want to go further than rectangles and circles.
