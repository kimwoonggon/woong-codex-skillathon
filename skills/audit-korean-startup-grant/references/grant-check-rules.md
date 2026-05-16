# Korean Startup Grant Check Rules

Use these rules when auditing a Korean startup grant application package. The scripts implement the mechanical checks; this reference explains how to interpret them.

## Required Inputs

- `notice.md`: Public notice or derived mock notice.
- `application.md`: Application draft or mock application.
- `budget.csv`: Budget rows with `category`, `item`, `amount_krw`, `execution_month`, and `note`.
- `submission-files.txt`: One submitted file name per line.
- `check-rules.json`: Structured rules extracted from the notice or generated for the mock package.

## Severity

- `high`: Missing required document, submission closed, total budget above the maximum, or unsupported confidential data exposure.
- `medium`: Single budget item above an item limit, deadline within three days, ambiguous plan, or weak evidence for eligibility.
- `low`: Formatting issue, optional document mismatch, or minor cleanup item.

## Required Document Matching

Normalize spaces, punctuation, and extensions before matching. A submitted file can satisfy a required document when its normalized file name contains the normalized required document label.

Do not treat optional documents as missing. Mark them separately only when the user asks for optional-readiness checks.

## Budget Checks

Check these items in order:

1. CSV parse errors or missing `amount_krw`.
2. Total requested amount above `max_total_budget`.
3. Any single row above `max_single_item_budget`.
4. Negative, zero, or non-numeric budget values.

Amounts must be reported in KRW with comma separators.

## Deadline Checks

Use the user's supplied date when available. Otherwise use today's local date.

- Past deadline: `high`
- 0-3 days left: `medium`
- 4 or more days left: informational
- No deadline: `확인 필요`

## Privacy Checks

Mask matches in reports. Detect at least:

- Email addresses
- Korean mobile or landline-like phone numbers
- Business registration number pattern such as `123-45-67890`
- Resident-registration-like pattern such as `123456-1234567`

The presence of fake or mock privacy-like values is still useful for validating the guardrail. In a real package, ask before quoting any surrounding context.

## Confirmation Needed

Mark items as `확인 필요` when the application contains phrases such as:

- `미정`
- `추후 확정`
- `협의 필요`
- `TBD`
- `확인 필요`

Do not infer owners, dates, eligibility, or missing evidence from weak clues.
