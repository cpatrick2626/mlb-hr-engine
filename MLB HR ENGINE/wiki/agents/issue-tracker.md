# Issue tracker: Local Markdown

Issues live as markdown files under `.scratch/`. Do NOT create GitHub Issues automatically. Issues stay local until the operator explicitly approves promoting one to `github.com/cpatrick2626/mlb-hr-engine`.

## Conventions

- One feature per directory: `.scratch/<feature-slug>/`
- PRD lives at `.scratch/<feature-slug>/PRD.md`
- Implementation issues: `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01`
- Triage state: `Status:` frontmatter line (e.g. `Status: needs-triage`)
- Comments append at the bottom under `## Comments`

## When a skill says "publish to the issue tracker"

Create a new file under `.scratch/<feature-slug>/`. Do not call `gh issue create`.

## When a skill says "fetch the relevant ticket"

Read the file at the referenced path. User passes path or issue number directly.

## Promoting to GitHub

Only when operator explicitly says to promote: run `gh issue create` with the issue's title and body.
