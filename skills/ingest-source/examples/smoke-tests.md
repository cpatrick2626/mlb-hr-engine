# /ingest-source Smoke Tests

## Test 1 — Article

Prompt:

```text
Use /ingest-source.

Ingest this article into the knowledge base:
<URL>

Route stable frameworks, voice, and people-process material to knowledge/.
Create a summary block with source, date, key people, and key concepts.
Use [[wikilinks]] on first mention of related notes.
Do not fabricate missing metadata.
```

Expected behavior:

* Routes to `knowledge/` if evergreen.
* Creates clean markdown note.
* Missing metadata marked as `--`.

---

## Test 2 — Active Project Note

Prompt:

```text
Use /ingest-source.

Ingest these pasted launch notes:
<pasted notes>

This is active work for a current launch.
Route to projects/.
Add summary block, key people, key concepts, related notes, and follow-up actions.
```

Expected behavior:

* Routes to `projects/`.
* Creates project note.
* Adds wikilinks only where meaningful.

---

## Test 3 — YouTube Link

Prompt:

```text
Use /ingest-source.

Ingest this YouTube link:
<URL>

Use transcript only if available.
If transcript is unavailable, mark Transcript unavailable.
Do not invent transcript content.
```

Expected behavior:

* Captures title/channel/date if available.
* Uses transcript only if available.
* Marks data gaps clearly.

---

## Test 4 — PDF

Prompt:

```text
Use /ingest-source.

Ingest this PDF:
<PDF path or URL>

Summarize key sections, key people, key concepts, and page references if available.
If PDF extraction fails, mark PDF extraction unavailable.
```

Expected behavior:

* Creates routed note.
* Preserves source reference.
* Does not invent page details.
