"""Tests for the MCP server layer: tool list, responses and the stdio transport."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

import pytest
from mcp import Client, StdioServerParameters

import server

SERVER_DIR = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).parent / "fixtures"
EXPECTED_TOOLS = {"validate_cfdi", "summarize_cfdi", "check_rfc"}


def load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def call(tool: str, arguments: dict[str, Any]) -> Any:
    """Call a tool on the in memory server and return the full result."""

    async def run() -> Any:
        async with Client(server.mcp) as client:
            return await client.call_tool(tool, arguments)

    return asyncio.run(run())


def test_server_exposes_exactly_three_tools() -> None:
    async def run() -> list[str]:
        async with Client(server.mcp) as client:
            return [tool.name for tool in (await client.list_tools()).tools]

    names = asyncio.run(run())
    assert len(names) == 3
    assert set(names) == EXPECTED_TOOLS


def test_server_name_is_cfdi_tools() -> None:
    async def run() -> str:
        async with Client(server.mcp) as client:
            return client.server_info.name

    assert asyncio.run(run()) == "cfdi-tools"


def test_every_tool_has_a_description() -> None:
    async def run() -> list[Any]:
        async with Client(server.mcp) as client:
            return (await client.list_tools()).tools

    for tool in asyncio.run(run()):
        assert tool.description and tool.description.strip(), tool.name


def test_validate_cfdi_response() -> None:
    result = call("validate_cfdi", {"xml_content": load("totals_mismatch.xml")})
    assert not result.is_error
    data = result.structured_content
    assert data["summary"]["valid"] is False
    assert data["summary"]["failed"] == 1
    assert len(data["checks"]) == 10
    assert {c["id"]: c["status"] for c in data["checks"]}["total_matches"] == "fail"
    assert "scope_note" in data


def test_validate_cfdi_valid_document() -> None:
    data = call("validate_cfdi", {"xml_content": load("valid_ingreso.xml")}).structured_content
    assert data["summary"]["valid"] is True


def test_summarize_cfdi_response() -> None:
    data = call("summarize_cfdi", {"xml_content": load("valid_ingreso.xml")}).structured_content
    assert data["summarized"] is True
    assert data["issuer"]["rfc"] == "EKU9003173C9"
    assert data["concept_count"] == 2
    assert "scope_note" in data


def test_check_rfc_response() -> None:
    data = call("check_rfc", {"rfc": "EKU9003173C9"}).structured_content
    assert data["valid"] is True
    assert data["type"] == "moral"
    assert "scope_note" in data


def test_scope_note_mentions_what_is_not_validated() -> None:
    note = call("check_rfc", {"rfc": "XAXX010101000"}).structured_content["scope_note"].lower()
    for term in ("seal", "certificate", "original string", "catalogs", "status", "sat"):
        assert term in note


@pytest.mark.parametrize("tool", ["validate_cfdi", "summarize_cfdi"])
def test_oversized_input_is_rejected_with_a_clear_error(tool: str) -> None:
    result = call(tool, {"xml_content": "<a>" + "x" * (2 * 1024 * 1024) + "</a>"})
    assert result.is_error
    assert "2 MB" in result.content[0].text


def test_server_source_has_no_network_or_file_writes() -> None:
    forbidden = ("socket", "urllib", "requests", "httpx", "http.client", "open(", "write_text", "write_bytes")
    for path in (SERVER_DIR / "server.py", SERVER_DIR / "cfdi_tools" / "validator.py"):
        source = path.read_text(encoding="utf-8")
        for term in forbidden:
            assert term not in source, (path.name, term)


def test_stdio_transport_initializes_and_lists_tools(tmp_path: Path) -> None:
    """Start the server as a real subprocess, from an unrelated working directory."""

    async def run() -> tuple[str, list[str], Any]:
        params = StdioServerParameters(
            command=sys.executable,
            args=[str(SERVER_DIR / "server.py")],
            cwd=tmp_path,
        )
        async with Client(params) as client:
            tools = [tool.name for tool in (await client.list_tools()).tools]
            result = await client.call_tool("check_rfc", {"rfc": "XAXX010101000"})
            return client.server_info.name, tools, result.structured_content

    name, tools, data = asyncio.run(asyncio.wait_for(run(), timeout=60))
    assert name == "cfdi-tools"
    assert set(tools) == EXPECTED_TOOLS
    assert data["type"] == "generico"
