# Project Workflow

## Guiding Principles

1. **The Plan is the Source of Truth:** All work must be tracked in `plan.md`
2. **The Tech Stack is Deliberate:** Changes to the tech stack must be documented in `tech-stack.md` *before* implementation
3. **Test-Driven Development:** Write unit tests before implementing functionality
4. **High Code Coverage:** Aim for >80% code coverage for all modules
5. **User Experience First:** Every decision should prioritize user experience
6. **Non-Interactive & CI-Aware:** Prefer non-interactive commands. Use `CI=true` for watch-mode tools (tests, linters) to ensure single execution.

## Task Workflow

All tasks follow a strict lifecycle:

### Standard Task Workflow

1. **Select Task:** Choose the next available task from `plan.md` in sequential order

2. **Mark In Progress:** Before beginning work, edit `plan.md` and change the task from `[ ]` to `[~]`

3. **Write Failing Tests (Red Phase):**
   - Create a new test file for the feature or bug fix.
   - Write one or more unit tests that clearly define the expected behavior and acceptance criteria for the task.
   - **CRITICAL:** Run the tests and confirm that they fail as expected. This is the "Red" phase of TDD. Do not proceed until you have failing tests.

4. **Implement to Pass Tests (Green Phase):**
   - Write the minimum amount of application code necessary to make the failing tests pass.
   - Run the test suite again and confirm that all tests now pass. This is the "Green" phase.

5. **Refactor (Optional but Recommended):**
   - With the safety of passing tests, refactor the implementation code and the test code to improve clarity, remove duplication, and enhance performance without changing the external behavior.
   - Rerun tests to ensure they still pass after refactoring.

6. **Verify Coverage:** Run coverage reports:
   ```bash
   # Backend
   cd backend && .venv/bin/pytest --cov=app --cov-report=term-missing

   # Frontend (unit tests)
   cd frontend && npm run test -- --coverage --run
   ```
   Target: >80% coverage for new code.

7. **Document Deviations:** If implementation differs from tech stack:
   - **STOP** implementation
   - Update `tech-stack.md` with new design
   - Add dated note explaining the change
   - Resume implementation

8. **Commit Code Changes:**
   - Stage all code changes related to the task.
   - Propose a clear, concise commit message e.g, `feat(tts): Wire F5-TTS inference endpoint`.
   - Perform the commit.

9. **Attach Task Summary with Git Notes:**
   - **Step 9.1: Get Commit Hash:** Obtain the hash of the *just-completed commit* (`git log -1 --format="%H"`).
   - **Step 9.2: Draft Note Content:** Create a detailed summary for the completed task. This should include the task name, a summary of changes, a list of all created/modified files, and the core "why" for the change.
   - **Step 9.3: Attach Note:** Use the `git notes` command to attach the summary to the commit.
     ```bash
     git notes add -m "<note content>" <commit_hash>
     ```

10. **Get and Record Task Commit SHA:**
    - **Step 10.1: Update Plan:** Read `plan.md`, find the line for the completed task, update its status from `[~]` to `[x]`, and append the first 7 characters of the commit hash.
    - **Step 10.2: Write Plan:** Write the updated content back to `plan.md`.

11. **Commit Plan Update:**
    - Stage the modified `plan.md` file.
    - Commit with a descriptive message (e.g., `conductor(plan): Mark task 'Wire F5-TTS inference' as complete`).

### Phase Completion Verification and Checkpointing Protocol

**Trigger:** This protocol is executed immediately after a task is completed that also concludes a phase in `plan.md`.

1. **Announce Protocol Start:** Inform the user that the phase is complete and the verification and checkpointing protocol has begun.

2. **Ensure Test Coverage for Phase Changes:**
   - **Step 2.1: Determine Phase Scope:** Find the Git commit SHA of the previous phase's checkpoint in `plan.md`. If none, scope is all changes since first commit.
   - **Step 2.2: List Changed Files:** Execute `git diff --name-only <previous_checkpoint_sha> HEAD`.
   - **Step 2.3: Verify and Create Tests:** For each code file in the list, verify a corresponding test file exists. Create missing tests.

3. **Execute Automated Tests with Proactive Debugging:**
   - Announce exact command before running.
   - If tests fail, attempt a fix a **maximum of two times** before stopping and asking the user.

4. **Propose a Detailed, Actionable Manual Verification Plan** based on `product.md`, `product-guidelines.md`, and `plan.md`.

5. **Await Explicit User Feedback:** Ask "Does this meet your expectations?" — **PAUSE** and wait for explicit yes.

6. **Create Checkpoint Commit.**

7. **Attach Auditable Verification Report using Git Notes.**

8. **Get and Record Phase Checkpoint SHA** — append `[checkpoint: <sha>]` to the phase heading in `plan.md`.

9. **Commit Plan Update.**

10. **Announce Completion.**

### Quality Gates

Before marking any task complete, verify:

- [ ] All tests pass
- [ ] Code coverage meets requirements (>80%)
- [ ] Code follows project's code style guidelines (as defined in `code_styleguides/`)
- [ ] All public functions/methods have docstrings (Python) or JSDoc (JS/TS)
- [ ] Type safety enforced (Python type hints, TypeScript types)
- [ ] No linting or static analysis errors
- [ ] No security vulnerabilities introduced

## Development Commands

### Setup (first time)
```bash
# Run once to install all dependencies and build the frontend
./setup.sh
```

### Daily Development

```bash
# Start the full app (backend + serves built frontend)
./start.sh

# Backend only (for API development with hot reload)
cd backend && .venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Frontend dev server (proxies API to :8000)
cd frontend && npm run dev

# Rebuild frontend after UI changes
cd frontend && npm run build
```

### Testing

```bash
# Backend tests
cd backend && .venv/bin/pytest -v

# Backend tests with coverage
cd backend && .venv/bin/pytest --cov=app --cov-report=term-missing

# Frontend unit tests
cd frontend && npm run test -- --run

# Frontend tests with coverage
cd frontend && npm run test -- --coverage --run
```

### Linting & Formatting

```bash
# Python (backend)
cd backend && .venv/bin/ruff check app/
cd backend && .venv/bin/ruff format app/

# JavaScript/TypeScript (frontend)
cd frontend && npm run lint
```

### Before Committing

```bash
# Full pre-commit check
cd backend && .venv/bin/ruff check app/ && .venv/bin/pytest -q
cd frontend && npm run lint && npm run test -- --run
```

## Testing Requirements

### Unit Testing
- Every Python module in `app/` must have a corresponding test in `tests/`.
- Every React component in `src/` with logic should have a `.test.tsx` file.
- Mock external dependencies (F5-TTS model, ffmpeg, yt-dlp).
- Test both success and failure cases.

### Integration Testing
- Test complete API flows: upload reference → generate speech → download
- Test profile CRUD endpoints end-to-end
- Verify audio file creation on disk

## Commit Guidelines

### Message Format
```
<type>(<scope>): <description>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding missing tests
- `chore`: Maintenance tasks

### Examples
```bash
git commit -m "feat(tts): Add F5-TTS inference service"
git commit -m "fix(upload): Handle non-WAV reference files via ffmpeg"
git commit -m "feat(profiles): Add profile CRUD API and frontend library panel"
```

## Definition of Done

A task is complete when:

1. All code implemented to specification
2. Unit tests written and passing
3. Code coverage meets project requirements (>80%)
4. Ruff and ESLint pass with no errors
5. Docstrings on all public Python functions; JSDoc on exported components
6. Implementation notes added to `plan.md`
7. Changes committed with proper message
8. Git note with task summary attached to the commit
