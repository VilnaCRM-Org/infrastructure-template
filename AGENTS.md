# Review-Driven Refactor Guide

This file documents the expected flow for addressing code review feedback in this repository.

## Workflow

1. Identify the PR and reviewers.
   - Use `gh pr view <number>` to confirm the branch, reviewers, and review status.
   - Use `gh api graphql` or `gh pr view --json` to list review threads and comments.

2. Extract actionable feedback.
   - Prioritize human reviewer comments first (e.g., Kravalg).
   - Treat CodeRabbit actionable/nitpick items as required unless explicitly marked optional.

3. Apply minimal, focused fixes.
   - Touch only the files required to satisfy the comment.
   - Keep existing conventions and patterns intact.
   - If a request is not feasible (e.g., tooling constraints), add a short inline note in code/docs and explain in the PR comment.

4. Validate intent.
   - Run the smallest relevant tests or checks when practical.
   - If running tests is not feasible, document what was not run and why.

5. Commit and push.
   - Use concise commit messages tied to the review feedback.
   - Push to the PR branch (no rebases or force-pushes unless explicitly requested).

6. Resolve conversations.
   - Reply to the review thread if the change needs explanation.
   - Resolve the thread after the fix is pushed.

7. Re-check CI.
   - Use `gh pr checks <number>` and wait for results before closing the work.

## Principles

- Keep changes as small as possible.
- Favor clarity over cleverness.
- Update documentation when a change affects developer workflows.
