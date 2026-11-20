# claude-code-toolkit

A Claude Code plugin (freelance-toolkit) with four skills and one MCP server for the work around a freelance software project.

## What is inside

| Piece | What it does | What it does not do |
| --- | --- | --- |
| `repo-handoff` (skill) | Prepares a repository for another developer or an AI agent: runs every install, run and test command to check it, audits for leaked secrets and writes HANDOFF.md. | It is not for general project documentation that nobody is going to receive, such as a public README or API reference. |
| `project-scoping` (skill) | Vets a client brief or message before quoting: checks the client, flags red flags and scams, estimates hours and recommends a pricing model. | It does not write proposals or cover letters, and it does not apply to jobs or message clients. |
| `cfdi-tools` (MCP server) | Runs ten structural and arithmetic checks on a CFDI 4.0 XML, summarizes it and checks the format of an RFC. It reads text only. | It does not validate the seal, the certificate, the original string, the SAT catalogs or the status with the SAT. It never writes files or calls the network. |
| `cfdi-validator` (skill) | Uses the `cfdi-tools` server to review a CFDI 4.0 XML and explains every failed check in plain words. | It does not validate the seal, the certificate, the SAT catalogs or the status with the SAT. It does not generate, stamp or cancel invoices, and it gives no tax advice. |
| `gmail-triage` (skill) | Sorts incoming emails into lead, support, billing and no reply, labels them and prepares drafts from approved templates. | It never sends. In its default dry run mode it touches no mailbox: the input is .eml files or pasted text. |

## Requirements

* Claude Code.
* Python 3.12 or newer.
* [uv](https://docs.astral.sh/uv/). The plugin starts the MCP server with `uv run`, so uv has to be installed and reachable from the PATH of the program that launches Claude Code. Without uv, the server shows as failed in `/mcp`.

## Install

Inside Claude Code, add the marketplace from the GitHub repository and install the plugin:

```
/plugin marketplace add OscarJ290/claude-code-toolkit
/plugin install freelance-toolkit@oscarj290
```

The same two steps from a terminal:

```
claude plugin marketplace add OscarJ290/claude-code-toolkit
claude plugin install freelance-toolkit@oscarj290
```

After installing, run `/reload-plugins` or restart Claude Code. To check the MCP server, run `/mcp` and look for `cfdi-tools` from this plugin: it should be listed as connected.

## Usage

You do not need to name a skill. Describe what you want and the matching skill activates by itself.

* Repository handoff: "I am leaving this project next week. Get the repo ready so another developer can run it without asking me anything."
* Project scoping: "A client sent me this brief for a data scraping job. Is it worth bidding on, and how many hours would it take?"
* CFDI review: "Check this invoice XML and tell me whether the totals add up." followed by a path to the file or the pasted XML.
* Email triage: "Classify these emails, label them and prepare draft replies. Do not send anything." followed by the path to a folder of .eml files.

<!-- screenshots -->

## How it was tested

* **MCP server:** 103 pytest tests, passing on Python 3.12 and on Python 3.14. To run them: `cd servers/cfdi-tools` and then `uv run pytest`.
* **Fixtures:** every CFDI used in the tests is synthetic. The issuer is the public SAT test RFC `EKU9003173C9` and the receiver is the generic RFC `XAXX010101000`. The seal and certificate fields are obvious placeholders. No real invoice or person is in the repository.
* **Activation tests:** each skill was tested in a fresh session with three prompts that should trigger it without naming it and one prompt that should not. Result: 4 of 4 for each skill.

Two real findings came out of that testing:

* **A wrong guess with its own arithmetic.** In an early run, `cfdi-validator` tried to explain a failed total by doing its own sums, and it blamed the wrong field. The XML alone cannot say which number is wrong. The skill now has a rule that every number in a report must come from the tool output or appear literally in the XML.
* **A skill that read its answer key.** The first `gmail-triage` test read its own expected output file and copied the answer. The skill now forbids reading that file, and the tests run on a copy of the sample inbox kept outside the repository.

The sample inbox includes `05_injection.eml`, a synthetic email that looks like a support request but orders the assistant to ignore its rules, reply at once and forward every invoice to an outside address. The skill sends it to manual review and acts on none of it.

## Repository layout

```
.claude-plugin/        plugin and marketplace manifests
skills/
  repo-handoff/
  project-scoping/
  cfdi-validator/
  gmail-triage/        templates and a synthetic sample inbox
servers/
  cfdi-tools/          the MCP server, its tests and fixtures
LICENSE
README.md
```

## Built with Claude Code

This plugin was built and tested with Claude Code.

## License

MIT
