# Week 6 Writeup — AI Code Review & Testing: The Habit Tracker

**Name:** Parwana Babakarkhil
**Repository:** https://github.com/parwana-p/habit-tracker-week6
**Implementation agent:** Google Antigravity (Claude Sonnet 4.6 Thinking), one-shot prompt per feature
**AI reviewer:** CodeRabbit (GitHub app installed on the repository)

| PR | Feature | Commits |
|---|---|---|
| [#1](https://github.com/parwana-p/habit-tracker-week6/pull/1) | Task 2 — Validation | [`8e6ccf4`](https://github.com/parwana-p/habit-tracker-week6/commit/8e6ccf4) agent · [`e6f8aa6`](https://github.com/parwana-p/habit-tracker-week6/commit/e6f8aa6) my review fixes · [`26134bc`](https://github.com/parwana-p/habit-tracker-week6/commit/26134bc) CodeRabbit fix |
| [#2](https://github.com/parwana-p/habit-tracker-week6/pull/2) | Task 1 — Streak | [`9e65e8b`](https://github.com/parwana-p/habit-tracker-week6/commit/9e65e8b) agent · [`33f02ea`](https://github.com/parwana-p/habit-tracker-week6/commit/33f02ea) my review fixes · [`6b9839a`](https://github.com/parwana-p/habit-tracker-week6/commit/6b9839a) CodeRabbit fix |

---

## Part I — Guardrails

Files: `pyproject.toml` (black + ruff config, line length 100), `requirements-dev.txt`,
`check.ps1` (local runner) and `.github/workflows/ci.yml` (runs the same checks on every push and PR).

| Command | What it catches |
|---|---|
| `ruff check .` | Lint: unused imports, undefined names, import order, likely bugs (rule sets E, W, F, I, B, UP) |
| `black --check .` | Formatting drift; fails if any file would be reformatted (`black .` fixes it) |
| `pytest -q` | Behavioral regressions; any failing test fails the build |
| `.\check.ps1` | Runs all three in order and exits non-zero at the first failure |

**Proof that a failing test fails the build:** I added a temporary `test_fail_demo.py`
(`assert 1 == 2`) and ran `.\check.ps1`. ruff and black passed, then pytest reported
`1 failed, 3 passed` and the script stopped with `FAILED: pytest (tests)` (non-zero exit).
I deleted the file before committing. On the first run, black also reformatted the starter's
`main.py`, which showed the formatter catching drift that already existed.

---

## Part II — Human review vs. AI review

### PR #1 — Validation

**My manual review of the agent's diff** (fixed in `e6f8aa6`):
1. **Bug:** the agent validated days with `date.fromisoformat` only. On Python 3.11+ that also
   accepts `20260922` and ISO week dates like `2026-W38-1`, which would be stored as-is and break
   `ORDER BY day` and any date logic. I added a strict `YYYY-MM-DD` regex check before parsing.
2. **Data quality:** blank names were rejected, but `"  Read  "` was stored with its spaces.
   The validator now returns the stripped name.
3. **Test gaps:** no test for an impossible date (`2026-02-30`) or the compact format. Added both,
   plus a trimming test.
4. **Weak assertions:** tests checked `"empty" in str(body)`. My new test asserts on
   `detail[0]["msg"]` instead.

**CodeRabbit's review** ("Actionable comments posted: 2", both Minor):
1. *Declare Pydantic 2 explicitly:* the code imports `field_validator`, which is Pydantic 2 only,
   but `requirements.txt` relied on FastAPI pulling it in transitively. **I missed this.** I fixed it
   in `26134bc` (`pydantic>=2`).
2. *Isolate the test database:* tests write rows into the real `habits.db` on every run.
   **I missed this too.** The pattern already existed in the starter, so I left it as a documented
   follow-up instead of reworking the test setup inside a validation PR.

### PR #2 — Streak

**My manual review** (fixed in `33f02ea`):
1. **Bug:** without the validation PR, a malformed stored day made `date.fromisoformat` raise,
   so `/streak` returned a **500**. Bad rows are now skipped, with a test.
2. **Noise:** the agent added an invisible UTF-8 BOM to the first line of both files; removed.
3. **Dead code:** `ORDER BY day DESC` was useless because the rows go into a set; removed.
4. **Design note (not changed):** following the task wording ("up to and including today"),
   the streak is 0 if today has no check-in even when yesterday did. I wrote this in the PR's
   tradeoffs rather than changing the spec.

**CodeRabbit's review** ("Actionable comments posted: 1", Minor):
1. *Control the clock in the streak tests:* if midnight passes between the check-in and the GET,
   the test gets 0 instead of 1. **I noticed the code used the server's local date, but not that
   it made the tests flaky.** Fixed in `6b9839a`: `main._today()` wraps `date.today()`, and a
   `fixed_clock` fixture monkeypatches it to 2026-09-22.

### Comparison

| | Me | CodeRabbit |
|---|---|---|
| Real correctness bugs in the agent's code (`fromisoformat` leniency, 500 on bad data) | Found both | Found neither* |
| Repository and dependency hygiene (implicit Pydantic 2) | Missed | Found |
| Test reliability (shared DB, clock-dependent tests) | Missed | Found both |
| Noise in the diff (BOM, dead `ORDER BY`) | Found | Did not mention |
| Accurate PR summaries | — | Yes, the summaries matched each change |

\*Caveat: I pushed my fixes before CodeRabbit ran, so it reviewed the already-corrected
code. It may simply not have had these bugs left to find. I still never saw it reason about
domain behavior the way I had to, for example what `fromisoformat` accepts on Python 3.11+.

**Where the AI was better:** it looked beyond the diff to the environment: dependencies,
test isolation, time. Its comments came with severity, a concrete fix and "supported by static
analysis" evidence. Where it was weaker: it did not question the domain choices (what counts as
a valid day, the 0-streak rule), and it did not mention the noisy BOM change.

---

## What I learned

Guardrails and LLM review catch different classes of problems: ruff, black and pytest are
cheap, deterministic and catch the same issue every time, but only the issues someone has
already written a rule or test for. The AI reviewer found real gaps I missed (implicit
dependencies, flaky clock-based tests, a shared test database), so it is a good second reader.
Its comments were all "Minor" quick wins, though, and the correctness bugs in the agent's code
came from my own line-by-line review. I am comfortable trusting AI review as an extra layer
that suggests things to check, but not as the approver. A change is ready when the guardrails
pass and a human has read the diff.
