# Bug Report: Missing and Placeholder Answer Choices

**Reported:** 2026-10-30
**Severity:** High for affected questions
**Status:** Fixed in the player and import builders; source-data repair remains

## Summary

Some choice questions load without usable answer choices. Depending on the question data, the player can render an empty area, show fabricated labels such as `Option A`, or fail while trying to iterate missing options. This makes affected questions unanswerable and can interrupt navigation through a test.

## How to reproduce

These steps describe the original failure; DSAT2 Q11 has since been repaired.

1. Start the exam site and open the **DSAT2** test.
2. Navigate to technical question 11.
3. Observe that it is an MCQ with no answer choices.

Other affected tests contain generic placeholder choices instead of actual answer text.

## Expected behavior

- MCQ and MSQ questions render their actual choices.
- If the source data has no usable choices, the page explains that the choices are unavailable and does not offer fake selectable answers.
- A malformed question does not break rendering or question navigation.
- The practice answer key does not present a guessed answer for an incomplete question.

## Findings

The client-side renderer in `scripts/app.js` directly called `q.options.forEach(...)` and read `opt.id` / `opt.textHtml` without validating the question record. The MCQ/MSQ click handlers also referenced `index` without receiving it, causing a `ReferenceError` when an answer was selected. The data builder in `build_exam_data.py` inserted generic choices whenever it could not find an ordered list. The PDF import pipeline in `scripts/build_pyq_pipeline.py` also created generic `Option (A)` choices and substituted `A` when an answer key was missing.

An audit of `data/tests/*.json` found:

- 271 test files and 11,214 questions; all files parsed as JSON.
- One MCQ with an empty options array: `data/tests/DSAT2.json`, Q11. Its four choices were present in an ordered list embedded in the prompt and have been restored from that source markup.
- Nine MCQs had a one-item prompt list mistaken for the choices while the actual four-choice list remained embedded in the prompt; those choices have also been restored.
- Follow-up scan: 5,272 MCQ/MSQ records across 192 files still contain unusable choices. This includes 3,112 PYQ entries, 2,130 generated mocks, and 30 other-series entries, with 1,843 distinct discussion URLs.
- All remaining affected records are listed in `QUESTION_CHOICE_AUDIT.csv`; 44 prompts contain apparent A-D labels that may allow further recovery from their source markup.
- No MCQ/MSQ record has a missing `options` property or a choice item without display text; defensive handling was still needed for malformed records.

## Likely cause

Choice extraction failed when source prompts contained earlier one-item ordered lists or when alternatives were missing from extracted PDF text. The builders silently replaced missing source content with selectable labels, masking incomplete data and sometimes attaching an invented answer key. The client had no validation boundary to prevent incomplete records from reaching the renderer.

## Fixes applied

1. The player now normalizes and validates MCQ/MSQ choices, supports the known `textHtml` / `html` / `text` variants, and prevents malformed question data from breaking rendering.
2. The player now shows an explicit unavailable-data state and discussion link instead of fake or missing options. These questions are left ungraded, and Practice Mode does not reveal a guessed answer.
3. The MCQ/MSQ click handlers now receive the question index used for telemetry.
4. The builders no longer fabricate answer choices or default a missing MCQ/MSQ answer key to `A`.
5. The importer now chooses the last multi-item ordered list, so one-item prompt lists do not hide the actual options.
6. The choices for DSAT2 Q11 and the other nine mis-extracted MCQs have been restored from their embedded ordered lists.

## Remaining data repair

The remaining 5,272 unusable choice records do not contain their real choice text in the stored option fields. The player now identifies these questions instead of presenting the placeholders as valid answers. Their original alternatives need to be recovered from the source material before those questions can be made fully answerable. See `QUESTION_CHOICE_AUDIT.csv` for the affected test/question locations and source discussion links.

## Follow-up: GATE CSE 2014 Set 1, Question 54

The choices for the SQL question at `https://gateoverflow.in/1934/gate-cse-2014-set-1-question-54` were restored in both `PYQ_Databases_DBMS_P6.json` and its copy in `GATE2027_Mock_01.json`.
