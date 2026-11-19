# Sample output (synthetic, for format reference only)

Report produced by the project-scoping skill for `sample-brief.md`.

## Verdict

**Ask first.** The job is clear enough to estimate, but the budget works out to about 11 USD per hour and two blockers (schedule and who grants access) can change the price.

## Client check

* Payment method: verified.
* Hiring history: 3 previous hires.
* Budget: 150 USD fixed. Against the estimate below (13.2 hours), the effective rate is about 11.4 USD per hour. For an integration with the Google Sheets API, a scheduler and formatted email, that is low unless the scope is reduced or the budget goes up.
* Client rating and total spend: unknown.

## Red flags

None found in the brief. No request for identity data, personal accounts, bank accounts or likeness. The work is a standard Python automation. Stack and portfolio fit: unknown, confirm with the user.

## Brief clarity

* The client knows the problem well: the manual process, its cost (about an hour per week) and the error risk are all described.
* What they ask for: an automatic weekly email with three metrics (weekly total, sales per category, top five products) sent to about 12 managers.
* What they seem to need but did not say: access to the sheet, a sending address for the email, and a way to handle weeks where the sheet is incomplete.
* Open items: schedule and time zone, who grants access to the sheet and to the sending account, what the email should look like, what happens if a tab is missing.

The brief is specific about the output and silent about access and operations. The estimate is firm for the build and provisional for anything that depends on access.

## Questions to ask

Always included:

1. What schedule and time zone should the report follow, and how quickly will you answer questions during the project?
2. What will I be responsible for, and what stays on your side (sheet access, sending account, approving the email layout)?
3. What are the exact requirements and how will you accept the work (for example, a test email that matches the numbers in the sheet)?
4. What are the fees and the payment terms (all at delivery, or split)?

Specific to this brief:

5. Who will share the Google Sheet with the account the automation uses, and by when?
6. Which address should the email be sent from, and can it be a dedicated account for this?
7. Is the email plain text with a table, or do you need a branded layout?
8. What should happen if a weekly tab is missing or incomplete on Monday (skip, send a warning, retry)?
9. Where should the automation run, and who owns that account after delivery?

## Estimate

Provisional on questions 5 to 9.

| Task | Hours |
|---|---|
| Review the sheet structure and confirm the report content | 1.0 |
| Connect to the Google Sheets API and read the weekly tab | 2.5 |
| Build the three metrics and the email body | 3.0 |
| Send email to the manager list and schedule the weekly run | 1.5 |
| Testing with real data, error handling and logging | 2.0 |
| Delivery notes and handover of access | 1.0 |
| **Subtotal** | **11.0** |
| Contingency (20 percent) | 2.2 |
| **Total** | **13.2** |

Calendar time: about 3 days at 4 to 5 productive hours per day (assumption, availability unknown), counting from the day access is granted.

## Pricing model

The estimate is at the 3 calendar day threshold, so recommend a **fixed price for the whole project**. The amount comes from the user's own hourly rate applied to 13.2 hours, which is not known here. At the client's 150 USD the effective rate is about 11.4 USD per hour. Options if that is too low: ask for a higher budget, or reduce the scope (plain text email, a fixed list of recipients, no handling of incomplete weeks) and re-estimate.

## Out of scope

* One round of revisions is included. Further rounds are quoted separately.
* Any change to the specifications after acceptance is a change of scope and is quoted separately.
* Not included: hosting costs for the scheduler, maintenance, support after delivery, and any paid third party service.

## Before starting

Do not start until the requirements and the fees are agreed in writing, and sheet access and the sending account are confirmed.
