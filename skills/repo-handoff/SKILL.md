---
name: repo-handoff
description: "Prepares a repository to be handed to another developer or to an AI agent, so the recipient can run and understand it without asking the author anything. Use when the user says things like 'hand off this repo', 'handover', 'pass this project to another developer', 'onboard someone to this codebase', 'prepare the repo for a new maintainer', 'write handoff notes' or 'I am leaving the project'. También se activa con 'entregar el repo', 'pasarle el proyecto a otro', 'preparar la entrega' o 'notas de traspaso'. Verifies every install, run and test command by executing it, audits the repo for leaked secrets, and writes HANDOFF.md (plus CLAUDE.md or AGENTS.md when the recipient is an agent). Do not use for general project documentation that nobody is going to receive, such as a README for a public project or API reference docs."
---

# Repo handoff

Goal: leave the repository in a state where the person or agent who receives it can run it, test it and understand it without asking the author a single question. Everything written down must be something you checked, not something you assumed.

## Process

Follow these steps in order. Do not skip the verification step, even when the project looks simple.

### 1. Identify the recipient

If it is not clear from the request, ask who receives the repository:

* A human developer.
* An AI agent.
* Both.

For a human, the deliverable is `HANDOFF.md`. For an agent, also create or update `CLAUDE.md` or `AGENTS.md` (use whichever the repo already has, otherwise `CLAUDE.md`) with the verified commands, the code conventions and the areas that should not be touched. Keep that file short: it is loaded into every agent session, so it should hold commands and conventions, not the story of the project.

### 2. Take inventory

Read the repo before writing anything. Collect:

* Stack and languages, with versions when the repo pins them.
* Dependency manager and the file that declares dependencies.
* Entry point (the file or command that starts the application).
* How it runs locally.
* How it is tested, and which test runner it uses.
* Environment variables: record **names only**, never values. Look in `.env.example`, config loaders, Docker files, CI workflows and the code itself.
* External services it talks to (databases, APIs, queues, cloud accounts) and what access the recipient will need.
* Build or deploy steps, if any, and where they are defined.

Note for each item where you found it, so you can separate facts from guesses later.

### 3. Verify, do not assume

Every command that will appear in the handoff document (install, run, test, build) must be executed first, in the repo, before it is written down.

1. Run the command from a clean state when possible (fresh virtual environment, fresh install).
2. If it works, record the exact command and what success looks like.
3. If it fails, do not fix it silently and do not hide it. Record that it fails and the exact error message, then mention it in the Current state section and in your final summary.
4. If a command is dangerous or has side effects (it writes to a production database, sends emails, spends money, deletes data), do not run it. Mark it as "not verified, side effects" and explain why.
5. If a command needs a secret you do not have, mark it as "not verified, needs credentials" and list the variable names it needs.

Never write a command you have not run. A command that was inferred from the code but not executed goes under a clearly labeled "Not verified" heading, never in the main instructions.

### 4. Security review

Before the repo leaves the author's hands, check for leaked credentials:

1. Look for sensitive files tracked in the working tree: `.env` and `.env.*` (except `.env.example`), private keys (`*.pem`, `*.key`, `id_rsa*`), `credentials.json`, service account files, and anything named like `secrets.*`.
2. Check the history, not only the current files: a secret deleted in a later commit is still recoverable. Use `git log --all --name-only --pretty=format:` and look for those same file names, or `git log --all --diff-filter=D --name-only --pretty=format:` for deleted files.
3. Search for secret shaped strings by file name only, so no value is ever printed: `git grep -lEi "(api[_-]?key|secret|token|password)\s*[:=]"`. Open a matching file only to judge whether the match is a real value or a placeholder, and never copy the value anywhere.
4. Run `git status` and report any uncommitted changes, untracked files that should be tracked, and files that should be ignored but are not (check `.gitignore`).
5. Report whether the repo has a remote, and whether the current branch is ahead of or behind it.

If you find a secret:

* Do not copy it into `HANDOFF.md`, into the chat summary, into a commit message or anywhere else.
* Tell the user clearly which file (and which commit, if it is in the history) contains it.
* Recommend revoking or rotating the credential first. Only after that, clean the history (for example with `git filter-repo`), because cleaning history does nothing for a secret that someone may already have copied.

### 5. Write HANDOFF.md

Create `HANDOFF.md` in the repository root with exactly these sections, in this order:

1. **What this is**: two or three sentences on the purpose of the project, who uses it and what problem it solves.
2. **How to run it locally**: the verified steps, in order, copy and paste ready. Include the required runtime versions.
3. **How to test it**: the verified test command, what a passing run looks like, and anything that is known to be slow or flaky.
4. **Environment variables (names only)**: a table with the variable name, what it is for, whether it is required, and where to get a value (for example "ask the owner" or "create it in the provider dashboard"). Never a value.
5. **Current state**: three short lists. What works (verified). What is pending or unfinished. Known risks (fragile parts, missing tests, hard coded values, expiring credentials, unpinned dependencies, anything from the security review).
6. **Where to start reading**: the three to six files or directories a newcomer should read first, in order, each with one line on why.
7. **Open decisions**: choices the author had not settled, with the options considered and the author's current leaning if there is one. Write "None" if there are none.

Writing style: short sentences, concrete file paths, real command names. Do not pad the document with generic advice, and do not describe features you did not look at.

### 6. Close with a summary to the user

End with a short report in the chat:

* Which commands were verified and passed.
* Which commands failed, with the error.
* Which commands were not run, and why.
* Security findings, without ever showing a secret value.
* Remaining risks and open decisions the author should resolve before handing over.
* Files created or changed (`HANDOFF.md`, and `CLAUDE.md` or `AGENTS.md` if applicable). Do not commit them unless the user asks.

## Rules

* Never include secret values anywhere: not in `HANDOFF.md`, not in the agent instruction file, not in the chat.
* Never invent the state of the project. If you did not check it, say so or leave it out.
* Always distinguish what was verified (you ran it or read it) from what was inferred (you deduced it from the code or from naming).
* Never run destructive or side effect commands to "verify" them.
* Do not rewrite or refactor the project's code as part of a handoff. If you find a bug, record it under Current state.
* Do not commit, push or publish anything unless the user explicitly asks.
