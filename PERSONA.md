# SyncStream — Engineering Persona & Coding Standard

This file defines how code gets written on this project. **Read this before writing or editing any code** — it is referenced from `AGENT_CHANGELOG.md` for exactly that reason. It is not a style-linter config; it's the judgment calls a linter can't make for you.

## Who you're writing for

> "Programs must be written for people to read, and only incidentally for machines to execute." — *Structure and Interpretation of Computer Programs*

> "Instead of imagining that our main task is to instruct a computer what to do, let us concentrate rather on explaining to human beings what we want a computer to do." — Donald Knuth, *Literate Programming*

The reader is a human engineer picking up this codebase cold — possibly you, in a different session, with no memory of writing it. Optimize for that reader first. The compiler's requirements are a constraint you satisfy along the way, not the goal.

## Comments are a last resort, not a first instinct

Make the code itself clear before reaching for a comment. Meaningful names, small well-factored functions, and an order of exposition that matches how a human would explain the idea — these should carry almost all of the weight.

**Comments-as-crutch (bad):** clever/dense code papered over with comments explaining what it does.

```c
int directionCode;
if (0 < _x & x != deviceInfo->position.x) {
    if (0 > x - deviceInfo->position.x) {
        directionCode = 0x04 /*left*/;
    } else if (0 < x - deviceInfo->position.x) {
        directionCode = 0x02 /*right*/;
    }
}
```

**Self-explaining code (good):** the fix isn't "add better comments," it's naming the things that matter.

```c
static const int DIRECTION_LEFT = 0x04;
static const int DIRECTION_RIGHT = 0x02;
static const int DIRECTION_NONE = 0x00;

int oldX = deviceInfo->position.x;
int directionCode = (x > oldX) ? DIRECTION_RIGHT
                  : (x < oldX) ? DIRECTION_LEFT
                  : DIRECTION_NONE;
```

More comments is not more readable. Often the fix for unclear code is to simplify or rename, not to annotate.

**But code alone has limits.** It can show *how*, never *why*. When a decision isn't obvious from the code itself — a rejected alternative, a non-obvious constraint, a workaround for a specific bug — write that down, because no amount of clean code recovers it:

```python
# A binary search turned out to be slower than Boyer-Moore for the
# data sets we see here, despite the extra complexity.
```

**Rule of thumb:** if removing the comment wouldn't confuse a future reader, don't write it. If removing it would silently erase a *reason* nobody could otherwise recover, keep it.

## Proportionate implementation

Write scalable, modular, clean, maintainable code — the kind a human engineer would recognize as a normal, well-run production codebase. Concretely:

- **No comment-as-crutch code.** If you find yourself explaining convoluted logic in a comment, simplify the logic instead.
- **No extreme meta-programming or speculative abstraction.** Don't build a framework for a feature that needs a straightforward implementation. No abstraction layer, config system, or plugin interface until there are at least two real call sites that need it.
- **Proportionate size.** If a task can be done clearly and intuitively in 2-3x the "trivial" version, that's the target — not 10x it via unnecessary layers, wrappers, or generality nobody asked for.
- **Modular, not fragmented.** Group code by what it does, not into needless micro-files. A file should earn its own existence.
- **Boring is good.** Prefer the obvious, idiomatic way to do something in the language/framework at hand over a clever one-liner that trades readability for brevity.

## How this applies on SyncStream specifically

- `backend/models/schemas.py` is the single source of truth for data shapes — don't redefine equivalent shapes elsewhere; import from here.
- Agent nodes (`backend/agents/`) should read as a clear pipeline: state in, state out, one responsibility per node. Routing logic and business logic don't belong in the same function.
- The NBA scoring rules (`backend/engine/nba_scorer.py`) are business rules from the product spec — where a modifier's rationale isn't obvious from the code (e.g. *why* a threshold is what it is), a short comment pointing back to the spec is warranted. The arithmetic itself doesn't need narration.
- Frontend components (`frontend/src/components/`) should map cleanly to the Pydantic schemas they render — a widget's props should mirror the backend model, not invent a parallel shape.

## Where this file fits in the workflow

`AGENT_CHANGELOG.md` is the state/handoff log — what's done, what's next. This file is the *how* — read it once per session, before touching code, so style stays consistent across sessions and across the human/AI boundary.
