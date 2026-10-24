# REFACTOR_PLAN.md

## LifeStepsAI Todo Application - Refactoring and Improvement Plan

This document lists every recommended improvement in priority order. It is a planning document only. No implementation has been performed.

Related document: `CODE_ANALYSIS.md` explains how the current code works. `PROJECT_ANALYSIS.md` contains the original audit evidence and score.

---

## 0. Ground Rules

1. **Do not rewrite the project from scratch.** The core model and manager are small and understandable. Improve them incrementally.
2. **Respect the Phase I constitution.** Phase I is in-memory, single-user, console-only. Do not add a database or web API just to satisfy documentation that should be corrected instead.
3. **Fix correctness before architecture.** A broken CLI, failing CI, and crashed Windows output matter more than folder names.
4. **Keep each commit focused and reversible.** One concern per commit, with tests.
5. **Do not commit generated artifacts.** Exclude `htmlcov/`, `.coverage`, caches, and local environments.
6. **Do not auto-fix blindly.** Review every Ruff/mypy change and keep behavior stable.
7. **Preserve the 69 existing tests.** They are useful regression protection while refactoring.

---

## 1. Priority Summary

| # | Improvement | Priority | Difficulty | Primary commit |
|---:|---|---|---|---|
| 1 | Fix the failing coverage/CI gate | P0 | Low-Medium | Commit 1 / 5 |
| 2 | Fix or redesign CLI state handling | P0 | High | Commit 1 / 3 |
| 3 | Remove or implement the nonexistent web UI claims | P0 | Low | Commit 1 / 6 |
| 4 | Fix Windows Unicode/encoding crashes | P0 | Low-Medium | Commit 1 |
| 5 | Fix deployment files for a console app | P0 | Medium | Commit 1 / 6 |
| 6 | Fix test import/bootstrap behavior | P0 | Low | Commit 1 / 5 |
| 7 | Validate `Task.id` correctly | P1 | Low | Commit 1 |
| 8 | Add missing tests | P1 | Medium | Commit 5 |
| 9 | Resolve Ruff and mypy failures | P1 | Medium | Commit 2 |
| 10 | Encapsulate manager state and add a repository boundary | P1 | High | Commit 2 / 4 |
| 11 | Extract shared formatters, constants, and status enum | P1 | Medium-High | Commit 2 |
| 12 | Fix `demo.py` path and packaging | P1 | Low | Commit 1 / 6 |
| 13 | Improve error handling and add logging | P1 | Medium | Commit 1 / 3 |
| 14 | Clean up dependencies and packaging metadata | P1 | Low-Medium | Commit 6 |
| 15 | Harden the Docker image | P1 | Medium | Commit 6 |
| 16 | Correct all documentation drift | P1 | Medium | Commit 6 |
| 17 | Improve CLI usability | P2 | Medium-High | Commit 3 |
| 18 | Improve UI usability and accessibility | P2 | Medium | Commit 2 / 3 |
| 19 | Restructure folders by responsibility | P2 | High | Commit 4 |
| 20 | Expand the test strategy | P2 | Medium-High | Commit 5 |
| 21 | Harden CI/CD | P2 | Medium | Commit 5 / 6 |
| 22 | Prune unrelated repository artifacts | P2 | Low | Commit 6 |
| 23 | Add observability and operational basics | P2 | Medium | Commit 4 |
| 24 | Prepare a real scalability path for Phase II | P2 / Future | High | Future phase |

Priority meanings:

- **P0:** Blocks correctness, CI, or claimed functionality. Fix first.
- **P1:** Important quality, maintainability, or deployment issue.
- **P2:** Valuable polish or future-proofing, not required for Phase I correctness.

---

## 2. Detailed Improvement Plan

### Improvement 1: Fix the failing coverage/CI gate

**Priority:** P0

**Why it is needed**

`pyproject.toml` enables coverage for all of `src/todo_app` and sets `--cov-fail-under=100`. That includes `cli.py` and `ui.py`, which have no tests. The real total is 18.59%, so the default `pytest` command and the CI test job fail even though all 69 tests pass. This contradicts the README badge, the constitution's "core logic" wording, and the claimed project status.

**Benefits**

- CI becomes green and trustworthy.
- Developers can run `pytest` without a confusing failure.
- Coverage numbers become honest and meaningful.
- The project can distinguish "core coverage" from "full application coverage".

**Estimated difficulty:** Low-Medium (1-3 hours)

**Files affected**

- `pyproject.toml`
- `tests/` (new coverage-focused tests, if chosen)
- `.github/workflows/test-and-deploy.yml`
- `README.md`
- `PROJECT_STATUS.md`

**Risks**

- Simply lowering the gate can hide untested behavior.
- Excluding UI/CLI from coverage can give a false sense of quality.
- Adding UI/CLI tests may require refactoring code that calls `sys.exit` and reads `input`.

**Recommended approach**

1. Keep a strict 100% gate for `models.py` and `manager.py`.
2. Add a separate integration-test target for CLI/UI behavior.
3. Make HTML coverage opt-in, not a default side effect.

---

### Improvement 2: Fix or redesign CLI state handling

**Priority:** P0

**Why it is needed**

Every CLI invocation creates a new empty `TodoManager`. `todo add "Buy milk"` stores the task only for that process, then exits. `todo list` starts with a new empty manager and always shows nothing. The documented multi-command workflow cannot work. This is the most important functional defect in the project.

**Benefits**

- The CLI becomes genuinely usable.
- Documentation matches reality.
- Users are not misled by examples that cannot work.
- A stable CLI design can later share a service layer with a web API.

**Estimated difficulty:** High (1-2 days), because it requires a product decision

**Files affected**

- `src/todo_app/cli.py`
- `src/todo_app/ui.py` (if shared session behavior is extracted)
- `README.md`
- `tests/` (new CLI tests)
- `pyproject.toml` (script entry points, if changed)

**Risks**

- Adding file/database persistence violates the Phase I constitution.
- Turning the CLI into an interactive session changes user expectations.
- Keeping one-shot commands and documenting their ephemeral nature may still disappoint users.
- Refactoring `sys.exit` out of handlers can change exit-code behavior.

**Recommended approach**

Choose one option explicitly:

- **Option A (recommended for Phase I):** Make `todo` a session/REPL-style CLI with in-memory state, like the UI but command-based. Document that data is lost on exit.
- **Option B:** Keep one-shot subcommands but document that each command is isolated and cannot build a list. This is honest but not very useful.
- **Option C:** Add persistence. This is a Phase II change and requires a constitution amendment.

Do not silently keep the current design while documenting commands that cannot work.

---

### Improvement 3: Remove or implement the nonexistent web UI claims

**Priority:** P0

**Why it is needed**

`pyproject.toml` declares `todo-web = "todo_app.web:create_app"`, and the README describes a Flask/Bootstrap web UI at `http://localhost:5000`. No `src/todo_app/web.py` exists, `python -m todo_app.web` fails, and there are no Flask routes or templates. The specification also says Phase I has no web UI.

**Benefits**

- Documentation becomes truthful.
- Broken entry points and dead dependencies disappear.
- Reviewers do not waste time looking for missing code.
- The Phase I scope stays consistent with the constitution.

**Estimated difficulty:** Low (30-60 minutes)

**Files affected**

- `README.md`
- `pyproject.toml`
- `requirements.txt`
- `render.yaml`
- `Dockerfile`
- `.gitignore` (if web-related artifacts are removed)

**Risks**

- Removing the web section may feel like lost functionality, but the functionality never existed.
- If a web UI is genuinely desired, removing claims delays it; in that case create a separate Phase II branch and implement it properly with tests.

**Recommended approach**

For Phase I, remove the web claims, the `todo-web` entry point, Flask/Flask-CORS dependencies, and the web-service deployment configuration. Add a note that a web interface belongs to Phase II.

---

### Improvement 4: Fix Windows Unicode/encoding crashes

**Priority:** P0

**Why it is needed**

The CLI, UI, model string output, and demo print emoji and Unicode symbols such as check marks and ballot boxes. On a cp1252 Windows console, these raise `UnicodeEncodeError` and terminate the command. This was verified for both `todo add` and `todo list`.

**Benefits**

- The application works on default Windows terminals.
- CI and local behavior become more predictable.
- Output is more accessible and portable.
- Users can opt into plain text.

**Estimated difficulty:** Low-Medium (1-3 hours)

**Files affected**

- `src/todo_app/models.py`
- `src/todo_app/cli.py`
- `src/todo_app/ui.py`
- `demo.py`
- New formatter/constants module, if extracted
- Tests for encoding behavior

**Risks**

- Replacing all emoji changes the visual style.
- Detecting terminal encoding can be environment-dependent.
- Forcing UTF-8 may not work on older terminals.

**Recommended approach**

1. Add a plain-text/ASCII mode (`[ ]`/`[x]`, `OK`, `ERROR`) and use it by default when the output encoding cannot represent the glyphs.
2. Optionally configure UTF-8 output when supported.
3. Remove presentation glyphs from the domain model's `__repr__`/`__str__`; keep them in the formatter.

---

### Improvement 5: Fix deployment files for a console app

**Priority:** P0

**Why it is needed**

`Dockerfile` starts the interactive UI, which needs a TTY and waits for input. `render.yaml` declares a web service whose start command is the interactive UI. There is no HTTP listener, so Render cannot health-check or serve it. `requirements.txt` is incomplete. The deployment setup cannot work as described.

**Benefits**

- Deployment claims become accurate.
- Reviewers do not encounter a hanging or crashing service.
- Container usage becomes appropriate for a local console demo.
- Future web deployment can start from a correct baseline.

**Estimated difficulty:** Medium (2-4 hours)

**Files affected**

- `Dockerfile`
- `render.yaml`
- `requirements.txt`
- `DEPLOYMENT.md`
- `.github/workflows/test-and-deploy.yml`
- New `.dockerignore`

**Risks**

- Removing `render.yaml` reduces apparent "deployment" features.
- A local-only Docker image is less impressive but honest.
- If a web service is required, a real HTTP app must be built first.

**Recommended approach**

- For Phase I, document Docker as a local interactive demo using `docker run -it`.
- Remove or disable the Render web-service configuration.
- If a hosted demo is required, implement a real web API in Phase II.

---

### Improvement 6: Fix test import/bootstrap behavior

**Priority:** P0

**Why it is needed**

Running `pytest` from a clean checkout without installing the package produces `ModuleNotFoundError: No module named 'todo_app'`. There is no `conftest.py` and no pytest `pythonpath` setting. Tests only work after an editable install or manual `PYTHONPATH=src`.

**Benefits**

- `pytest` works immediately after cloning.
- New contributors do not need undocumented environment setup.
- CI and local behavior are consistent.
- Fewer false "broken test" reports.

**Estimated difficulty:** Low (15-30 minutes)

**Files affected**

- `pyproject.toml`
- `tests/conftest.py` (new)
- `README.md`
- `DEPLOYMENT.md`

**Risks**

- Adding `src` to `sys.path` can mask packaging problems.
- The editable install remains the most realistic packaging test, so keep that in CI.

**Recommended approach**

Add `pythonpath = ["src"]` under `[tool.pytest.ini_options]` and/or a small `tests/conftest.py` that inserts the `src` directory. Keep an editable-install CI job to verify real packaging.

---

### Improvement 7: Validate `Task.id` correctly

**Priority:** P1

**Why it is needed**

The task-model spec requires IDs to be unique positive integers and invalid IDs to raise `ValueError`. The current `Task` accepts `-5` and `"abc"` because `__post_init__` only validates title/description.

**Benefits**

- Domain invariants are enforced at the boundary.
- Direct `Task` use is safer.
- Tests and specs agree.
- Future persistence and API layers can trust IDs.

**Estimated difficulty:** Low (30-60 minutes)

**Files affected**

- `src/todo_app/models.py`
- `tests/test_models.py`
- `specs/features/task-model.md` (clarify exception type if needed)

**Risks**

- Some tests or caller code may rely on constructing arbitrary IDs.
- `bool` is a subclass of `int`, so decide whether `True`/`False` should be rejected.
- The manager always generates valid IDs, so this is mostly a direct-use safety improvement.

**Recommended approach**

Reject non-`int`, `bool`, zero, and negative IDs with `ValueError` or `InvalidTaskDataError`. Decide which exception the spec should require and update both spec and tests.

---

### Improvement 8: Add missing tests

**Priority:** P1

**Why it is needed**

Current tests cover the core well but miss important cases:

- Invalid/non-positive IDs.
- `update_task` description over 1000 characters.
- Invalid ID types in delete/update/complete.
- CLI behavior and exit codes.
- Interactive UI flows.
- ASCII/Unicode fallback behavior.
- Status enum/filter edge cases.
- Coverage of the `else`/completed branch if it changes.

**Benefits**

- Prevents regressions while refactoring.
- Makes CI coverage meaningful.
- Documents expected behavior for future contributors.
- Supports the constitution's testing goals.

**Estimated difficulty:** Medium (1-2 days)

**Files affected**

- `tests/test_models.py`
- `tests/test_manager.py`
- New `tests/test_cli.py`
- New `tests/test_ui.py`
- New `tests/conftest.py`
- `pyproject.toml` (markers/coverage settings)

**Risks**

- Testing `input()`/`print()` requires refactoring or monkeypatching.
- UI tests can be brittle if they assert exact emoji/text.
- Over-testing implementation details can slow future refactors.

**Recommended approach**

Test behavior through public APIs. Use `capsys`/`monkeypatch` for CLI/UI. Add fixtures for common manager setup. Prefer small focused tests over huge integration tests.

---

### Improvement 9: Resolve Ruff and mypy failures

**Priority:** P1

**Why it is needed**

Ruff reports 24 issues and a deprecated top-level configuration warning. mypy strict reports 3 errors. The README claims code quality tools pass, but they do not.

**Benefits**

- Quality gates become real.
- Fewer hidden bugs and unused code.
- Consistent style and typing.
- Easier onboarding and code review.

**Estimated difficulty:** Medium (2-4 hours)

**Files affected**

- `pyproject.toml`
- `src/todo_app/*.py`
- `tests/*.py`
- `demo.py`

**Risks**

- Automatic fixes may change behavior or formatting.
- Strict typing may require small design changes (for example, annotating `task`).
- Existing tests may need minor cleanup for unused variables.

**Recommended approach**

1. Move Ruff settings under `[tool.ruff.lint]`.
2. Fix unused imports/variables and line lengths.
3. Replace `Optional[T]` with `T | None` where appropriate.
4. Add `Task` annotations to `print_task`.
5. Resolve the unreachable `description is None` branch by aligning the type and runtime handling.
6. Add lint/type checks to CI after the code is clean.

---

### Improvement 10: Encapsulate manager state and add a repository boundary

**Priority:** P1

**Why it is needed**

`TodoManager.tasks` is public and mutable, and `get_task()`/`list_tasks()` return live `Task` objects. Any caller can bypass validation. The manager also mixes storage with business logic, making a future database swap difficult.

**Benefits**

- Better data integrity.
- Clearer responsibilities.
- Easier testing with fake repositories.
- A clean path to Phase II persistence.

**Estimated difficulty:** High (2-3 days)

**Files affected**

- `src/todo_app/manager.py`
- New `src/todo_app/repository.py` or `infrastructure/in_memory_repository.py`
- `src/todo_app/cli.py`
- `src/todo_app/ui.py`
- `tests/`

**Risks**

- This changes a public API and may break tests/callers.
- Over-engineering a repository for a tiny Phase I app can add complexity.
- Returning copies/DTOs changes object identity expectations.
- The UI/CLI currently rely on the manager directly.

**Recommended approach**

1. Rename `tasks` to `_tasks`.
2. Add `_require_task(task_id)` to remove duplicated guards.
3. Introduce a small `TaskRepository` protocol with in-memory implementation.
4. Keep `TodoManager` as the use-case/service layer.
5. Return read-only views or DTOs, or document that entities are mutable and should not be retained.

Do this after correctness fixes, not before.

---

### Improvement 11: Extract shared formatters, constants, and status enum

**Priority:** P1

**Why it is needed**

Task rendering, status symbols, summaries, and status strings are duplicated across `models.py`, `cli.py`, `ui.py`, and `demo.py`. Magic numbers (`200`, `1000`, `60`, `70`, `9`) are scattered. Adding or renaming a status requires edits in multiple files.

**Benefits**

- One source of truth for output and rules.
- Easier to add a plain-text mode.
- Fewer inconsistencies.
- Better testability.

**Estimated difficulty:** Medium-High (1-2 days)

**Files affected**

- New `src/todo_app/constants.py`
- New `src/todo_app/formatters.py`
- New `src/todo_app/enums.py` (or `status.py`)
- `models.py`
- `manager.py`
- `cli.py`
- `ui.py`
- `demo.py`
- Tests

**Risks**

- Broad edits across many files.
- Output format changes may break tests or user expectations.
- An enum changes the public `list_tasks(status=...)` API unless a string conversion layer is kept.

**Recommended approach**

1. Extract constants: max title length, max description length, separator widths, menu options.
2. Add `TaskStatus` enum with `ALL`, `PENDING`, `COMPLETED`.
3. Add a `TaskFormatter` with `format_task`, `format_list`, and `format_summary`.
4. Keep backward-compatible string handling if needed.
5. Move glyph/ASCII decisions into the formatter.

---

### Improvement 12: Fix `demo.py` path and packaging

**Priority:** P1

**Why it is needed**

`demo.py` inserts `/mnt/d/hackathon-robotic/todo-list/src`, a hard-coded WSL path. On Windows or another machine, direct execution fails with `ModuleNotFoundError`. The demo also assumes task IDs 1 and 2, which is brittle.

**Benefits**

- Demo works from any checkout.
- CI demo step becomes reliable.
- No machine-specific paths in the repository.
- Better first-run experience.

**Estimated difficulty:** Low (15-30 minutes)

**Files affected**

- `demo.py`
- `README.md`
- `DEPLOYMENT.md`
- Optionally move demo to `scripts/demo.py`

**Risks**

- Moving the file changes documented commands.
- Removing `sys.path` manipulation requires the package to be installed or `pythonpath` configured.

**Recommended approach**

Remove the hard-coded path. Run the demo via `python -m todo_app.demo` or an installed script, or configure the project path properly. Use returned task IDs instead of assuming 1 and 2.

---

### Improvement 13: Improve error handling and add logging

**Priority:** P1

**Why it is needed**

Top-level handlers catch broad `Exception` and print a generic message without logging or a stack trace. The constitution asks for logged context and preserved diagnostics. CLI handlers call `sys.exit` directly, making reuse and testing harder.

**Benefits**

- Faster debugging.
- Better user experience without hiding bugs.
- Testable handlers.
- Consistent exit codes.

**Estimated difficulty:** Medium (half day)

**Files affected**

- `src/todo_app/cli.py`
- `src/todo_app/ui.py`
- New `src/todo_app/logging_config.py` (optional)
- Tests

**Risks**

- Logging output may interfere with terminal UX.
- Changing exception handling can change exit codes.
- Over-logging can create noise.

**Recommended approach**

1. Use the standard `logging` module.
2. Log unexpected exceptions with `logger.exception(...)`.
3. Keep friendly user messages but preserve diagnostics in logs.
4. Return exit codes or raise domain errors instead of calling `sys.exit` inside command handlers.
5. Add a `--verbose`/`--quiet` option later.

---

### Improvement 14: Clean up dependencies and packaging metadata

**Priority:** P1

**Why it is needed**

`pyproject.toml` declares Flask/Flask-CORS that no code uses. `requirements.txt` omits those dependencies and the package itself. Python requirements disagree (`>=3.12` vs 3.13+). Author metadata is a placeholder. There is no lock file.

**Benefits**

- Reproducible installs.
- Smaller dependency surface.
- Clear Python support policy.
- Professional package metadata.

**Estimated difficulty:** Low-Medium (1-2 hours)

**Files affected**

- `pyproject.toml`
- `requirements.txt`
- New `uv.lock`
- `README.md`
- `__init__.py`
- `LICENSE` (copyright holder, if desired)

**Risks**

- Removing Flask now may surprise future web work; put it in an optional `web` dependency group instead.
- Lock files add maintenance overhead.
- Changing the Python floor can exclude users.

**Recommended approach**

1. Choose one supported Python range and use it everywhere.
2. Remove unused runtime dependencies.
3. Put future web dependencies under an optional group.
4. Add a lock file.
5. Replace placeholder author/email.
6. Make `requirements.txt` generated from the project or remove it in favor of `pyproject.toml`.

---

### Improvement 15: Harden the Docker image

**Priority:** P1

**Why it is needed**

The Dockerfile runs as root, copies the entire repository, installs dev dependencies, and has no `.dockerignore`. This increases image size, attack surface, and the chance of leaking local files such as `.env`.

**Benefits**

- Smaller, faster, safer image.
- Reproducible builds.
- No accidental secret leakage.
- Better production hygiene.

**Estimated difficulty:** Medium (2-4 hours)

**Files affected**

- `Dockerfile`
- New `.dockerignore`
- `pyproject.toml` (optional dependency groups)
- `.github/workflows/test-and-deploy.yml`
- `DEPLOYMENT.md`

**Risks**

- Multi-stage builds add complexity.
- Non-root users can break file-permission assumptions.
- Runtime-only installs may miss packages needed by tests.

**Recommended approach**

1. Add `.dockerignore` for `.git`, `.venv`, caches, coverage, docs, and local env files.
2. Use a multi-stage build.
3. Install runtime dependencies only in the final stage.
4. Create and use a non-root user.
5. Pin the base image more tightly.
6. Use `docker run -it` for the console app, not detached mode.

---

### Improvement 16: Correct all documentation drift

**Priority:** P1

**Why it is needed**

README, PROJECT_STATUS, DEPLOYMENT, CLAUDE.md, and the specs disagree on coverage, test counts, web support, Python versions, file layout, and project completion. Some commands reference missing files (`test_ui.py`, `history/`, `todo_app.web`).

**Benefits**

- Reviewers trust the documentation.
- Setup instructions actually work.
- Less confusion for contributors.
- Cleaner portfolio presentation.

**Estimated difficulty:** Medium (half day)

**Files affected**

- `README.md`
- `PROJECT_STATUS.md`
- `DEPLOYMENT.md`
- `CLAUDE.md`
- `specs/overview.md`
- Feature specs where behavior differs
- `.specify/memory/constitution.md` only if a rule genuinely changes

**Risks**

- Documentation changes can be large and easy to miss in review.
- Over-promising must be replaced with honest limitations.
- Some claims may be intentionally aspirational; label them as roadmap, not current features.

**Recommended approach**

1. Run every documented command and update it to match reality.
2. State the real test count and coverage.
3. Remove or move web claims to a Phase II roadmap section.
4. Use one source of truth for setup instructions.
5. Add a "Current limitations" section.
6. Update dates and remove placeholder metadata.

---

### Improvement 17: Improve CLI usability

**Priority:** P2

**Why it is needed**

Even after the state bug is fixed, the CLI has limited usability: no JSON output, no plain mode, no `--version`, no confirmation for destructive actions, handlers exit the process directly, and errors are mixed with decorated output.

**Benefits**

- Scriptable output for automation.
- Better accessibility and portability.
- Safer destructive actions.
- More professional command-line experience.

**Estimated difficulty:** Medium-High (2-3 days)

**Files affected**

- `src/todo_app/cli.py`
- New formatter/constants modules
- `README.md`
- Tests

**Risks**

- Adding options increases the API surface.
- Changing output can break existing scripts.
- A REPL and subcommands can diverge if not built on the same service.

**Recommended approach**

1. Decide the state model first (Improvement 2).
2. Add `--plain`, `--json`, `--version`, and `--verbose`.
3. Add delete confirmation or `--yes`.
4. Return proper exit codes without `sys.exit` inside handlers.
5. Share the same service and formatter with the UI.

---

### Improvement 18: Improve UI usability and accessibility

**Priority:** P2

**Why it is needed**

The UI uses emoji, clears the screen every loop, uses a long if/elif chain, assumes 60-column output, and offers no plain-text or no-clear mode. Lists show status only as a visual glyph.

**Benefits**

- Better screen-reader and limited-terminal support.
- Less visual noise.
- Easier maintenance.
- More consistent with CLI output.

**Estimated difficulty:** Medium (1-2 days)

**Files affected**

- `src/todo_app/ui.py`
- `src/todo_app/formatters.py` (new)
- `src/todo_app/constants.py` (new)
- Tests

**Risks**

- Changing the visual style may surprise users.
- Screen-reader behavior varies by terminal.
- A menu dispatch table is less obvious to beginners than if/elif.

**Recommended approach**

1. Use textual status indicators such as `[ ]`/`[x]`.
2. Add `--plain` and `--no-clear`.
3. Replace `os.system` with an optional ANSI clear or no clear.
4. Use a command dispatch table.
5. Detect terminal width or avoid fixed separators.
6. Add an undo/confirmation strategy for completion changes if desired.

---

### Improvement 19: Restructure folders by responsibility

**Priority:** P2

**Why it is needed**

The current flat `src/todo_app` package works for six files but will become crowded when persistence, API, and web layers arrive. There is no clear domain/application/infrastructure/presentation split, no `__main__.py`, and deployment/demo files sit in the root.

**Benefits**

- Clearer ownership and boundaries.
- Easier to add Phase II components.
- Better discoverability.
- Cleaner root directory.

**Estimated difficulty:** High (2-4 days)

**Files affected**

- `src/todo_app/` (many files moved)
- `tests/` (test layout)
- `demo.py`
- `Dockerfile`
- `pyproject.toml`
- Import statements across the project

**Risks**

- Large diff with many import changes.
- Git history can become harder to follow unless moves are isolated.
- Over-structuring a small app can add ceremony.

**Recommended approach**

Do this in a dedicated commit after correctness and shared helpers. Target:

```text
src/todo_app/
├── __main__.py
├── config.py
├── domain/
│   ├── models.py
│   ├── enums.py
│   └── exceptions.py
├── application/
│   └── task_service.py
├── infrastructure/
│   └── in_memory_repository.py
└── presentation/
    ├── formatters.py
    ├── cli.py
    └── console_ui.py
```

Keep the old import paths as temporary re-exports if backward compatibility matters.

---

### Improvement 20: Expand the test strategy

**Priority:** P2

**Why it is needed**

Current tests are good unit tests for the core but lack shared fixtures, CLI/UI integration tests, property-based tests, and storage-contract tests. Some tests contain unused variables. Coverage is not aligned with the quality gate.

**Benefits**

- Stronger regression protection.
- Easier refactoring.
- Better documentation of behavior.
- Confidence when introducing new storage or API layers.

**Estimated difficulty:** Medium-High (2-3 days)

**Files affected**

- `tests/` (new layout and files)
- `tests/conftest.py`
- `pyproject.toml`
- Possibly `hypothesis` as a dev dependency

**Risks**

- Too many brittle tests can slow development.
- Integration tests that assert exact decorated output will break during UX changes.
- Property-based tests add a learning curve and dependency.

**Recommended approach**

1. Add fixtures for managers and sample tasks.
2. Add `tests/test_cli.py` and `tests/test_ui.py` using `capsys`/`monkeypatch`.
3. Add boundary/property tests for title/description lengths and Unicode.
4. Add storage-contract tests reusable by future repositories.
5. Add a coverage report by layer.
6. Remove unused variables and clarify test names.

---

### Improvement 21: Harden CI/CD

**Priority:** P2

**Why it is needed**

CI currently runs tests (which fail coverage), a demo, and a Docker build. It does not run Ruff or mypy, does not cache dependencies, uses an older setup-python action, and has no deploy step despite its name.

**Benefits**

- Catches style and type regressions.
- Faster feedback.
- Reproducible builds.
- Honest workflow naming.

**Estimated difficulty:** Medium (half day)

**Files affected**

- `.github/workflows/test-and-deploy.yml`
- `pyproject.toml`
- New `.dockerignore`
- Maybe a new `ci.yml` split into jobs

**Risks**

- Adding strict gates can block merges until the code is clean.
- Matrix builds increase CI minutes.
- Docker builds are slow and may need caching.

**Recommended approach**

1. Add separate jobs: lint, type-check, unit tests, integration tests, Docker build.
2. Cache pip/UV downloads.
3. Use a maintained `setup-python` version.
4. Upload coverage artifacts.
5. Rename the workflow if it does not deploy.
6. Add a packaging/install smoke test.

---

### Improvement 22: Prune unrelated repository artifacts

**Priority:** P2

**Why it is needed**

`.claude/` contains agents and skills for RAG chatbots, Qdrant, FastAPI auth, ROS 2, Docusaurus, Urdu localization, and robotics. These are unrelated to the todo app and inflate the repository. `.claude/settings.local.json` is committed despite being a local settings file.

**Benefits**

- Smaller, focused repository.
- Less confusion for reviewers.
- Reduced maintenance and review noise.
- Clearer portfolio story.

**Estimated difficulty:** Low (30-60 minutes)

**Files affected**

- `.claude/agents/*`
- `.claude/skills/*`
- `.claude/commands/*`
- `.claude/settings.local.json`
- `.gitignore`
- `CLAUDE.md`

**Risks**

- Removing reusable content may lose material the author wants for other projects.
- Some hackathon scoring may value the presence of agents/skills.

**Recommended approach**

Keep the generic Spec-Kit commands if they are actively used. Move unrelated agents/skills to a separate shared repository or an `archive/` folder outside the app. Do not commit `settings.local.json`.

---

### Improvement 23: Add observability and operational basics

**Priority:** P2

**Why it is needed**

There is no logging configuration, request/session ID, metrics, health check, or diagnostic mode. Unexpected errors are printed and lost. This is acceptable for a toy console app but not for a portfolio project that claims professional standards.

**Benefits**

- Easier debugging.
- Better incident response.
- Foundation for Phase II hosting.
- More professional operational story.

**Estimated difficulty:** Medium (1-2 days)

**Files affected**

- New `src/todo_app/logging_config.py`
- `cli.py`
- `ui.py`
- Documentation
- CI (optional log artifact)

**Risks**

- Logging can clutter terminal output.
- Over-engineering for a console app is unnecessary.
- Log file locations and rotation need decisions.

**Recommended approach**

1. Add a simple `logging` configuration.
2. Log unexpected exceptions with context.
3. Add `--verbose`/`--quiet`.
4. Keep user-facing messages separate from diagnostic logs.
5. Add health checks only when an HTTP service exists.

---

### Improvement 24: Prepare a real scalability path for Phase II

**Priority:** P2 / Future

**Why it is needed**

Phase I is intentionally in-memory and single-user, but the roadmap promises a full-stack web app, AI chatbot, and cloud deployment. The current design has no repository abstraction, API layer, authentication, migrations, pagination, or concurrency control.

**Benefits**

- Avoids a full rewrite in Phase II.
- Creates a clean migration path.
- Supports multiple users and persistent data.
- Makes the project portfolio-ready.

**Estimated difficulty:** High (weeks)

**Files affected**

- Architecture across the project
- New API/web/application/infrastructure layers
- Database migrations
- Authentication/authorization
- Deployment manifests
- Tests

**Risks**

- Scope creep into Phase I.
- Premature abstraction before requirements are clear.
- Security and data-loss risks if persistence is added carelessly.
- A constitution amendment is required to allow persistence.

**Recommended approach**

Do not implement this during Phase I refactoring. Plan it as Phase II work:

1. Approve a constitution change for persistence and web.
2. Introduce repository and service interfaces.
3. Add a database with migrations.
4. Add an API with versioning.
5. Add users, authentication, and authorization.
6. Add pagination, filtering, and indexes.
7. Add observability and backups.
8. Add integration, contract, and security tests.
9. Deploy with a real HTTP server, not an interactive console.

---

## 3. Suggested Commit Sequence

The user proposed six commits. The following mapping keeps each commit focused. Some improvements span multiple commits; do the smallest safe part first.

### Commit 1: Bug fixes

- Improvement 1: coverage/CI gate
- Improvement 2: CLI state handling (design decision plus minimal fix)
- Improvement 3: remove/implement web claims
- Improvement 4: Unicode/encoding crash
- Improvement 5: deployment correctness
- Improvement 6: test import bootstrap
- Improvement 7: ID validation
- Improvement 12: demo path
- Improvement 13: error handling (minimal logging part)

**Goal:** Make the project correct, runnable, and honest.

**Exit criteria:** `pytest` exits 0, CI test job passes, CLI/UI work on Windows, no broken entry points, deployment files are honest.

### Commit 2: Refactoring

- Improvement 9: Ruff/mypy cleanup
- Improvement 10: encapsulation/repository boundary (first step)
- Improvement 11: shared formatters/constants/status enum
- Improvement 18: UI internals (part 1: formatter and dispatch table)

**Goal:** Remove duplication and improve maintainability without changing behavior.

**Exit criteria:** Existing tests pass, Ruff/mypy pass, output remains compatible or intentionally documented.

### Commit 3: Better CLI

- Improvement 2: final CLI session/REPL design
- Improvement 17: CLI UX (`--plain`, `--json`, `--version`, safer delete)
- Improvement 13: handler return codes and logging polish

**Goal:** Make the CLI genuinely useful and scriptable.

**Exit criteria:** State works within a session, help text is clear, exit codes are correct, tests cover commands.

### Commit 4: Better architecture

- Improvement 10: repository/service split completed
- Improvement 11: enum/formatter integration
- Improvement 18: UI accessibility improvements
- Improvement 19: folder restructuring
- Improvement 23: observability basics

**Goal:** Create clear boundaries for Phase II.

**Exit criteria:** Domain/application/infrastructure/presentation separation is documented and tested; no behavior regressions.

### Commit 5: Better tests

- Improvement 1: coverage target finalized
- Improvement 6: test bootstrap finalized
- Improvement 7: ID validation tests
- Improvement 8: missing tests
- Improvement 20: expanded test strategy
- Improvement 21: CI quality gates

**Goal:** Make quality measurable and enforceable.

**Exit criteria:** Core coverage is 100%, CLI/UI integration tests exist, CI runs lint/type/tests, coverage is honest.

### Commit 6: Better documentation

- Improvement 3: web/deployment claims finalized
- Improvement 14: dependency/packaging metadata
- Improvement 15: Docker hardening
- Improvement 16: documentation truth pass
- Improvement 21: CI/docs alignment
- Improvement 22: repository pruning

**Goal:** Make the repository understandable, honest, and portfolio-ready.

**Exit criteria:** Every documented command works, claims match code, structure matches docs, unrelated artifacts removed or archived.

---

## 4. What Not to Do

1. **Do not add file/database persistence in Phase I** just to make the CLI work. That violates the constitution. Use a session-based CLI or document the limitation.
2. **Do not add a fake web UI** to satisfy the README. Either remove the claims or implement it properly in Phase II.
3. **Do not start with a full folder restructure.** Fix correctness and tests first; large moves make review harder.
4. **Do not run `ruff --fix` and `mypy` fixes without reviewing them.** Some changes affect public APIs and output.
5. **Do not lower the coverage gate without adding compensating tests.** A green CI that tests nothing is worse than a red CI.
6. **Do not commit caches, coverage HTML, `.venv`, or local settings.**
7. **Do not make the UI depend on exact emoji output in tests.** Test text/status behavior instead.
8. **Do not treat the Phase II roadmap as Phase I requirements.**

---

## 5. Definition of Done

A refactor phase is complete only when:

- The application runs on Windows, Linux, and macOS.
- The documented commands work exactly as written.
- `pytest` exits 0.
- Core logic has 100% coverage.
- CLI/UI behavior is tested or explicitly excluded with a documented reason.
- Ruff and mypy pass.
- CI runs lint, type-check, and tests.
- No broken entry points exist.
- The README, DEPLOYMENT, PROJECT_STATUS, CLAUDE.md, and specs agree with the code.
- No unrelated artifacts or placeholder metadata remain.
- No source code was changed without a corresponding test or documented reason.

---

## 6. Final Recommendation

Follow this order:

1. **Make it correct:** coverage gate, CLI state, web claims, Unicode, deployment, imports.
2. **Make it maintainable:** Ruff/mypy, shared helpers, encapsulation.
3. **Make it usable:** CLI/UI improvements.
4. **Make it extensible:** architecture and repository boundaries.
5. **Make it reliable:** tests and CI.
6. **Make it honest:** documentation, packaging, and repository hygiene.

The project does not need a rewrite. It needs a disciplined sequence of small, tested commits.

---

*End of REFACTOR_PLAN.md. No code was implemented.*
