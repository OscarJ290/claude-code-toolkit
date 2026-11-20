"""MCP server exposing CFDI 4.0 checks over stdio.

The server never writes files and never makes network calls. It only parses
the text it receives and returns a report.

The official MCP SDK renamed FastMCP to MCPServer in version 2, so this module
uses MCPServer, which is the same high level server API.
"""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from cfdi_tools import validator

SERVER_NAME = "cfdi-tools"
SERVER_VERSION = "0.1.0"

mcp = MCPServer(
    SERVER_NAME,
    version=SERVER_VERSION,
    instructions=(
        "Structural and arithmetic checks for CFDI 4.0 XML. " + validator.SCOPE_NOTE
    ),
)


@mcp.tool()
def validate_cfdi(xml_content: str) -> dict[str, Any]:
    """Validate a CFDI 4.0 XML document.

    Runs ten checks (well formedness, version, required attributes, RFC formats,
    postal codes, concept amounts, subtotal, total and UUID) and returns a summary
    plus the list of checks. The summary field valid is true only when no check
    failed. Input larger than 2 MB is rejected.
    """
    try:
        report = validator.validate(xml_content)
    except validator.InputTooLargeError as exc:
        raise ToolError(str(exc)) from exc
    report["scope_note"] = validator.SCOPE_NOTE
    return report


@mcp.tool()
def summarize_cfdi(xml_content: str) -> dict[str, Any]:
    """Summarize a CFDI 4.0 XML document.

    Returns the voucher type, date, issuer and receiver RFC and name, currency,
    subtotal, total, number of concepts and UUID. Input larger than 2 MB is rejected.
    """
    try:
        summary = validator.summarize(xml_content)
    except validator.InputTooLargeError as exc:
        raise ToolError(str(exc)) from exc
    summary["scope_note"] = validator.SCOPE_NOTE
    return summary


@mcp.tool()
def check_rfc(rfc: str) -> dict[str, Any]:
    """Check the format of a Mexican RFC.

    Returns whether the format is valid, the type (moral, fisica or generico) and
    the date the RFC encodes. This only checks the format, not whether the RFC is
    registered with the SAT.
    """
    result = validator.check_rfc(rfc)
    result["scope_note"] = validator.SCOPE_NOTE
    return result


if __name__ == "__main__":
    mcp.run(transport="stdio")
