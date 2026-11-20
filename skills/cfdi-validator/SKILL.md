---
name: cfdi-validator
description: "Reviews a CFDI 4.0 XML (Mexican electronic invoice) with the cfdi-tools MCP server: structure, RFC, UUID and whether the totals add up. Use for 'validate this CFDI', 'check this invoice XML', 'does this Mexican invoice add up', 'is this RFC valid', 'what is wrong with this CFDI'. También: 'revisa esta factura', 'valida este XML', 'el total de la factura no cuadra', 'checa si este CFDI está bien', 'este RFC es válido'. Does not generate, stamp (timbrar) or cancel invoices, and does not check the status of a document with the SAT. Never for tax or accounting advice, tax returns or tax calculations."
---

# CFDI validator

Goal: tell the user whether a CFDI 4.0 XML is structurally sound and whether its numbers add up, and explain every problem in words they can act on. The checks come from the `cfdi-tools` MCP server, never from reading the XML by eye.

## Process

Follow these steps in order.

### 1. Get the XML

* If the user gives a path, read that file with the Read tool. Do not run shell commands for this skill, not even to read or locate the file.
* If the user pastes the XML, use the pasted text as it is.
* If neither is present, ask once for the file or the text.

Never modify the XML and never write files. This skill reads and reports, nothing else.

### 2. Run the tools

Call the `cfdi-tools` server:

* `validate_cfdi` with the XML content. This returns a summary and ten checks, each with an id, a status (`pass`, `fail`, `warn` or `skipped`) and a message.
* `summarize_cfdi` with the same content, for the facts of the voucher: type, date, issuer, receiver, currency, subtotal, total, number of concepts and UUID.
* `check_rfc` when the question is only about an RFC and there is no XML to validate. In that case this is the only call needed.

Use the tool output as the source of truth. Do not recompute the arithmetic yourself and do not override a result because it looks wrong.

### 3. Report

Write the report in the language the user wrote in. Three parts:

1. **Summary of the voucher**: the fields `summarize_cfdi` returned. If it answered `summarized: false`, say so and give the reason instead.
2. **Checks table**: one row per check, with the check and its status. Keep the order the tool returned.
3. **Explanations**: for every `fail` and every `warn`, a short paragraph in plain language that says what the check means, what the tool found and what the user should look at in the invoice. No explanation is needed for a check that passed.

Translate the tool messages into plain words. The user may not know what `TotalImpuestosTrasladados` is, so say what it is when it appears in an explanation, and keep the amounts exactly as the tool reported them.

### 4. Close with the scope limit

Every report ends with this limit, in the user's language: these checks cover structure, formats and arithmetic. They do not validate the digital seal (sello), the certificate, the SAT catalogs or the status of the document with the SAT. For those, use the official SAT verification service.

State it even when every check passed. A document that passes here can still be rejected by the SAT.

### 5. When the tools are not available

If the `cfdi-tools` tools are missing or fail to answer, say so plainly. Explain that the server runs through `uv`, so `uv` has to be installed, and that the user can check whether the server connected with `/mcp`. Never present a validation you did not run as if the server had produced it.

You may offer a manual review of the XML instead. If the user accepts, label the whole result **manual review, not validated by the server** and keep the same scope limit at the end.

## Rules

* Never give tax or accounting advice. A failed check is a data problem in the file, not an opinion on what the user owes or on how they should invoice.
* Never invent data the XML does not carry. Anything the tools returned as absent stays absent in the report.
* Never say a CFDI is valid before the SAT. The tools cannot see the SAT.
* Do not modify, reformat or write the XML, and do not offer to correct the file.
* Do not generate, stamp or cancel invoices.
* Every number in the report must come from the tool output or appear literally in the XML. You may state the difference between two amounts the tool reported; do not compute any other sum, base or difference yourself.
* Do not guess the cause of a failed check with your own arithmetic. When more than one field could be the wrong one, list them as possibilities and say that the XML alone cannot tell which.

## Reference

See `examples/sample-output.md` for a full report, produced by running the tools against `servers/cfdi-tools/tests/fixtures/totals_mismatch.xml`.
