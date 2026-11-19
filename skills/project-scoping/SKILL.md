---
name: project-scoping
description: "Scopes freelance software or automation jobs and vets client messages before quoting: checks the client, detects red flags and scams, estimates hours and recommends a pricing model. Use for 'scope this project', 'how much should I charge', 'quote this job', 'is this job worth it', 'should I bid on this', 'review this client brief', and when the user asks if a client, message, invitation or offer is legit, suspicious or a scam, even if it is not a real project, because the red flag checks live here: 'is this client legit', 'is this a scam', 'does this offer look suspicious', 'what do you think of this client message'. También: 'cotizar este proyecto', 'cuánto le cobro', 'vale la pena este trabajo', 'revisa este post', 'es estafa', 'es confiable este cliente', 'qué opinas de este mensaje', 'me ofrecieron esto', 'qué opinas antes de ponerle precio'. Analysis only, never the proposal. Do not use for internal tasks of a project already in progress, sprint planning, or writing the cover letter or proposal."
---

# Project scoping

Goal: before the user quotes a software or automation job for a client, decide whether it is worth bidding on, what is still missing from the brief, how much work it is and how to charge for it. The output is a scoping analysis in the chat. This skill does not write or send the proposal.

## Input

The user pastes a job post, a client message or a brief, or describes the job in their own words. If the user also gives their hourly rate, stack or portfolio, use it. If something essential is missing, ask once, in a single message, and then continue with what you have.

## Process

Follow these steps in order.

### 1. Client check

Report what the brief says about each item, when the information is available:

* Whether the payment method is verified.
* The client's hiring history (previous hires, spend, rating if shown).
* Whether the budget is reasonable for the level of work requested. Compare the stated budget with the estimate from step 5 and show the effective hourly rate (budget divided by total hours).

Anything that is not in the brief is marked **unknown**. Never assume it. An unknown payment method is a risk to flag, not a fact to fill in.

### 2. Red flags

These stop the analysis. If any of them is present, recommend **do not bid**, explain the reason in plain words and end the report there, without estimating or pricing:

* Payment is not verified.
* The client asks to use the freelancer's identity: biometrics, face verification, identity documents, or access to the freelancer's personal accounts or platform accounts (account renting fraud).
* The client asks to receive or move deposits through the freelancer's personal bank accounts.
* The client asks to use the freelancer's voice, face or likeness for AI projects (cloning, model training, avatars).
* The work falls outside the freelancer's stack or portfolio. If you do not know the portfolio, ask the user once before judging this point. Do not guess.

When a red flag stops the report, the output contains only the Verdict, the Client check and the Red flags sections.

Use this same format even when the message is an obvious scam: the user should always get the Verdict line first.

### 3. Clarity of the brief

Judge how specific the client was and how well the client formulated their questions, because that shows how clear the client is about what they need.

* Separate what the client asks for from what the client seems to need.
* Note vague phrases, missing inputs, missing outputs and conflicting statements.
* If the brief is vague, the list of questions becomes the main deliverable and the estimate is marked **provisional**.

### 4. Questions to ask before quoting

Always include these four:

1. Expected schedule, time zone and availability for communication.
2. The freelancer's exact responsibilities, and what stays on the client's side (accesses, data, content, approvals).
3. Concrete requirements and acceptance criteria.
4. Fees and payment terms.

Then add the specific questions this brief leaves open. Write them so the user can paste them to the client as they are.

### 5. Estimate

1. Split the work into tasks.
2. Estimate hours for each task according to its complexity and how well specified it is. A task that depends on unspecified inputs gets a wider estimate and a note.
3. Add the tasks.
4. Add a **20 percent contingency** for setbacks, shown as its own line, never hidden inside the tasks.
5. Convert the total to calendar days using the user's real availability. If it is unknown, assume 4 to 5 productive hours per day and say that this is an assumption. Include waiting time for client accesses or approvals when the brief makes it likely.

### 6. Pricing model

The threshold is calendar time, not working hours:

* **3 calendar days or less** (about 12 to 16 working hours): recommend a fixed price for the whole project, because in that range clients usually pay well at a fixed price.
* **More than 3 calendar days**: recommend hourly billing, because from that point on it is more profitable. If the client only accepts a fixed price on a long project, split it into milestones with one verifiable deliverable each, and say so explicitly.

Show the estimated calendar days next to the hours in the report, because the decision comes from them. If the user's hourly rate is known, compute the price from it. If it is not, show the hours and leave the amount for the user. Never invent a rate.

### 7. Out of scope

Always write this section in the report:

* One round of revisions is included. Further rounds are quoted separately.
* Any change to the specifications after acceptance is treated as a change of scope and quoted separately.
* Anything else the brief leaves implicit and that is not included, when it applies: hosting, maintenance, support after delivery, licenses, third party fees.

### 8. Before starting

Nothing starts until two things exist in writing: the agreed requirements and the agreed fees. State this at the end of every report that gets past the red flags.

## Output format

Reply in the chat with these sections, in this order:

1. **Verdict**: one of `bid`, `ask first` or `do not bid`, with one line of reasoning.
2. **Client check**
3. **Red flags**
4. **Brief clarity**
5. **Questions to ask**
6. **Estimate**: a table of tasks with hours, then the contingency line, then the total in hours and the total in calendar days.
7. **Pricing model**
8. **Out of scope**
9. **Before starting**

Use `ask first` when the job could be worth taking but the missing answers could change the price or the decision. Keep the report scannable: short lines, no filler.

## Rules

* Never invent client data. Mark missing data as unknown.
* Mark anything provisional as provisional, including estimates made from a vague brief.
* Do not write or send the proposal, the cover letter or any message to the client, other than offering the list of questions.
* Do not apply to the job or take any action on a platform.
* Never recommend working around a red flag.

## Reference

See `examples/sample-brief.md` and `examples/sample-output.md` for the format of the input and of the report.
