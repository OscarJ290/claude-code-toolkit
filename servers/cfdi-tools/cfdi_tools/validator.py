"""Pure CFDI 4.0 validation logic.

This module has no dependency on MCP. It parses XML with defusedxml, uses
Decimal for every monetary value and never touches the filesystem or the
network. Each check returns an id, a status (pass, fail, warn or skipped) and
a human readable message.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, localcontext
from typing import TYPE_CHECKING, Any

from defusedxml.ElementTree import ParseError, fromstring

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element

CFDI_NS = "http://www.sat.gob.mx/cfd/4"
CFDI33_NS = "http://www.sat.gob.mx/cfd/3"
TFD_NS = "http://www.sat.gob.mx/TimbreFiscalDigital"
NS = {"cfdi": CFDI_NS, "tfd": TFD_NS}

MAX_INPUT_BYTES = 2 * 1024 * 1024
TOLERANCE = Decimal("0.01")

PASS = "pass"
FAIL = "fail"
WARN = "warn"
SKIPPED = "skipped"

CHECK_IDS = (
    "xml_well_formed",
    "cfdi_version",
    "required_attributes",
    "rfc_emisor",
    "rfc_receptor",
    "postal_codes",
    "concept_amounts",
    "subtotal_matches",
    "total_matches",
    "uuid",
)

SCOPE_NOTE = (
    "This tool checks structure, formats and arithmetic only. It does not validate "
    "the digital seal (sello), the certificate, the original string (cadena original), "
    "the SAT catalogs or the status of the document with the SAT. For those checks "
    "use the official SAT verification service."
)

GENERIC_RFCS = {
    "XAXX010101000": "generic RFC for a national public (PUBLICO EN GENERAL)",
    "XEXX010101000": "generic RFC for a foreign taxpayer without a Mexican RFC",
}

REQUIRED_ATTRIBUTES = {
    "Comprobante": (
        "Version",
        "Fecha",
        "Sello",
        "NoCertificado",
        "Certificado",
        "SubTotal",
        "Moneda",
        "Total",
        "TipoDeComprobante",
        "Exportacion",
        "LugarExpedicion",
    ),
    "Emisor": ("Rfc", "Nombre", "RegimenFiscal"),
    "Receptor": (
        "Rfc",
        "Nombre",
        "DomicilioFiscalReceptor",
        "RegimenFiscalReceptor",
        "UsoCFDI",
    ),
}

_AMOUNT_RE = re.compile(r"[0-9]{1,20}(\.[0-9]{1,10})?")
_POSTAL_RE = re.compile(r"[0-9]{5}")
_UUID_RE = re.compile(
    r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}"
)
_RFC_NAME_RE = re.compile(r"[A-ZÑ&]+")
_RFC_DATE_RE = re.compile(r"[0-9]{6}")
_RFC_HOMOCLAVE_RE = re.compile(r"[A-Z0-9]{3}")


class InputTooLargeError(ValueError):
    """Raised when the input is larger than MAX_INPUT_BYTES."""


@dataclass(frozen=True)
class Check:
    """The result of one validation check."""

    id: str
    status: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"id": self.id, "status": self.status, "message": self.message}


# ---------------------------------------------------------------------------
# Input handling
# ---------------------------------------------------------------------------


def _prepare(xml_content: str | bytes) -> str | bytes:
    """Enforce the size limit and normalize the input for the parser."""
    if isinstance(xml_content, str):
        size = len(xml_content.encode("utf-8", errors="surrogatepass"))
        data: str | bytes = xml_content.lstrip("﻿")
    elif isinstance(xml_content, (bytes, bytearray)):
        size = len(xml_content)
        data = bytes(xml_content)
    else:
        raise TypeError("xml_content must be a string or bytes")
    if size > MAX_INPUT_BYTES:
        raise InputTooLargeError(
            f"Input is {size} bytes, which exceeds the limit of {MAX_INPUT_BYTES} bytes (2 MB)."
        )
    return data


def _parse(data: str | bytes) -> Element:
    return fromstring(data)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def _attr(element: Element | None, name: str) -> str | None:
    """Return the attribute value, or None when absent or blank."""
    if element is None:
        return None
    value = element.get(name)
    if value is None or not value.strip():
        return None
    return value


def _dec(value: str | None, label: str) -> Decimal:
    """Parse a plain decimal amount. Rejects NaN, exponents, signs and huge values."""
    if value is None or _AMOUNT_RE.fullmatch(value) is None:
        raise ValueError(f"{label} is missing or is not a valid amount: {value!r}")
    return Decimal(value)


def _optional_dec(value: str | None, label: str) -> Decimal:
    """Absent optional amounts count as zero. Present but invalid ones raise."""
    if value is None or not value.strip():
        return Decimal(0)
    return _dec(value, label)


def _is_cfdi4_root(root: Element) -> bool:
    return root.tag == f"{{{CFDI_NS}}}Comprobante"


# ---------------------------------------------------------------------------
# RFC analysis
# ---------------------------------------------------------------------------


def _possible_dates(yymmdd: str) -> list[str]:
    """Return the ISO dates a two digit year RFC date can stand for.

    The RFC stores only two digits of the year, so both the 1900s and the 2000s
    are tried. Dates in the future are dropped because nobody can have been
    born or incorporated yet.
    """
    yy, mm, dd = int(yymmdd[0:2]), int(yymmdd[2:4]), int(yymmdd[4:6])
    today = date.today()
    found: list[str] = []
    for century in (1900, 2000):
        try:
            candidate = date(century + yy, mm, dd)
        except ValueError:
            continue
        if candidate <= today:
            found.append(candidate.isoformat())
    return found


def analyze_rfc(rfc: str) -> dict[str, Any]:
    """Check the format of an RFC and describe what it encodes.

    The result has the keys rfc, valid, type (moral, fisica, generico or None),
    generic, message and encoded_date (None when it cannot be read).
    """

    def result(valid: bool, rfc_type: str | None, message: str, encoded: Any = None) -> dict[str, Any]:
        return {
            "rfc": rfc,
            "valid": valid,
            "type": rfc_type,
            "generic": rfc_type == "generico",
            "message": message,
            "encoded_date": encoded,
        }

    if rfc in GENERIC_RFCS:
        return result(
            True,
            "generico",
            f"{rfc} is a valid {GENERIC_RFCS[rfc]}. Its date part is a placeholder, not a real date.",
        )

    if any(ch.isspace() for ch in rfc):
        return result(False, None, "The RFC contains whitespace.")
    if len(rfc) not in (12, 13):
        return result(
            False,
            None,
            f"The RFC has {len(rfc)} characters; expected 12 (persona moral) or 13 (persona fisica).",
        )

    rfc_type = "moral" if len(rfc) == 12 else "fisica"
    name_len = len(rfc) - 9
    name, yymmdd, homoclave = rfc[:name_len], rfc[name_len : name_len + 6], rfc[name_len + 6 :]

    if rfc != rfc.upper():
        return result(False, rfc_type, "The RFC must use uppercase letters.")
    if _RFC_NAME_RE.fullmatch(name) is None:
        return result(
            False,
            rfc_type,
            f"The first {name_len} characters must be letters (A to Z, Ñ or &), got {name!r}.",
        )
    if _RFC_DATE_RE.fullmatch(yymmdd) is None:
        return result(False, rfc_type, f"The date part must be 6 digits (AAMMDD), got {yymmdd!r}.")
    candidates = _possible_dates(yymmdd)
    if not candidates:
        return result(False, rfc_type, f"The date part {yymmdd} is not a valid calendar date.")
    if _RFC_HOMOCLAVE_RE.fullmatch(homoclave) is None:
        return result(
            False,
            rfc_type,
            f"The homoclave must be 3 letters or digits, got {homoclave!r}.",
        )

    label = "persona moral" if rfc_type == "moral" else "persona fisica"
    encoded = {"yymmdd": yymmdd, "possible_dates": candidates}
    return result(
        True,
        rfc_type,
        f"Valid RFC format for a {label}. The date part {yymmdd} can mean {' or '.join(candidates)}.",
        encoded,
    )


def check_rfc(rfc: str) -> dict[str, Any]:
    """Public entry point for RFC checks."""
    if not isinstance(rfc, str):
        raise TypeError("rfc must be a string")
    return analyze_rfc(rfc)


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def _check_version(root: Element) -> Check:
    check_id = "cfdi_version"
    if root.tag == f"{{{CFDI33_NS}}}Comprobante" or (
        not _is_cfdi4_root(root) and root.get("Version") == "3.3"
    ):
        return Check(
            check_id,
            FAIL,
            "This is a CFDI 3.3 document. Only CFDI 4.0 is supported.",
        )
    if not _is_cfdi4_root(root):
        return Check(
            check_id,
            FAIL,
            f"The root element is {root.tag!r}; expected Comprobante in the namespace {CFDI_NS}.",
        )
    version = root.get("Version")
    if version != "4.0":
        return Check(check_id, FAIL, f"Version is {version!r}; expected '4.0'.")
    return Check(check_id, PASS, "Root is cfdi:Comprobante in the CFDI 4.0 namespace with Version 4.0.")


def _check_required_attributes(root: Element) -> Check:
    check_id = "required_attributes"
    elements = {
        "Comprobante": root,
        "Emisor": root.find("cfdi:Emisor", NS),
        "Receptor": root.find("cfdi:Receptor", NS),
    }
    missing: list[str] = []
    for name, attrs in REQUIRED_ATTRIBUTES.items():
        element = elements[name]
        if element is None:
            missing.append(f"{name} element")
            continue
        missing.extend(f"{name}@{attr}" for attr in attrs if _attr(element, attr) is None)
    if missing:
        return Check(check_id, FAIL, "Missing or empty: " + ", ".join(missing) + ".")
    return Check(check_id, PASS, "All required attributes are present.")


def _check_rfc(check_id: str, label: str, element: Element | None) -> Check:
    if element is None:
        return Check(check_id, FAIL, f"The {label} element is missing.")
    rfc = _attr(element, "Rfc")
    if rfc is None:
        return Check(check_id, FAIL, f"{label}@Rfc is missing or empty.")
    info = analyze_rfc(rfc)
    if not info["valid"]:
        return Check(check_id, FAIL, f"{label} RFC {rfc!r} is not valid. {info['message']}")
    if info["generic"]:
        extra = ""
        if label == "Emisor":
            extra = " Generic RFCs are normally used only for receptors."
        return Check(check_id, PASS, f"{info['message']}{extra}")
    return Check(check_id, PASS, f"{label} RFC {rfc} is valid ({info['type']}).")


def _check_postal_codes(root: Element) -> Check:
    check_id = "postal_codes"
    receptor = root.find("cfdi:Receptor", NS)
    fields = (
        ("Comprobante@LugarExpedicion", _attr(root, "LugarExpedicion")),
        ("Receptor@DomicilioFiscalReceptor", _attr(receptor, "DomicilioFiscalReceptor")),
    )
    problems = [
        f"{name} is {value!r}" if value is not None else f"{name} is missing"
        for name, value in fields
        if value is None or _POSTAL_RE.fullmatch(value) is None
    ]
    if problems:
        return Check(check_id, FAIL, "Postal codes must be exactly 5 digits: " + "; ".join(problems) + ".")
    return Check(check_id, PASS, "LugarExpedicion and DomicilioFiscalReceptor are 5 digit postal codes.")


def _concept_nodes(root: Element) -> list[Element]:
    conceptos = root.find("cfdi:Conceptos", NS)
    return conceptos.findall("cfdi:Concepto", NS) if conceptos is not None else []


def _check_concept_amounts(root: Element) -> Check:
    check_id = "concept_amounts"
    concepts = _concept_nodes(root)
    if not concepts:
        return Check(check_id, FAIL, "No Concepto elements were found.")
    problems: list[str] = []
    for index, concept in enumerate(concepts, start=1):
        try:
            quantity = _dec(concept.get("Cantidad"), "Cantidad")
            unit_price = _dec(concept.get("ValorUnitario"), "ValorUnitario")
            amount = _dec(concept.get("Importe"), "Importe")
        except ValueError as exc:
            problems.append(f"Concepto {index}: {exc}")
            continue
        expected = quantity * unit_price
        if abs(amount - expected) > TOLERANCE:
            problems.append(
                f"Concepto {index}: Importe {amount} differs from Cantidad {quantity} times "
                f"ValorUnitario {unit_price} = {expected}"
            )
    if problems:
        return Check(check_id, FAIL, "; ".join(problems) + ".")
    return Check(
        check_id,
        PASS,
        f"All {len(concepts)} Concepto amounts equal Cantidad times ValorUnitario (tolerance {TOLERANCE}).",
    )


def _check_subtotal(root: Element) -> Check:
    check_id = "subtotal_matches"
    concepts = _concept_nodes(root)
    if not concepts:
        return Check(check_id, FAIL, "No Concepto elements were found, so SubTotal cannot be compared.")
    try:
        subtotal = _dec(root.get("SubTotal"), "SubTotal")
        total_importes = sum(
            (_dec(c.get("Importe"), f"Concepto {i} Importe") for i, c in enumerate(concepts, start=1)),
            Decimal(0),
        )
    except ValueError as exc:
        return Check(check_id, FAIL, str(exc) + ".")
    # Importe admits up to 6 decimals while SubTotal is rounded to the decimals of
    # the currency, so the two can legitimately differ by a rounding amount.
    if abs(total_importes - subtotal) > TOLERANCE:
        return Check(
            check_id,
            FAIL,
            f"SubTotal is {subtotal} but the Concepto Importe values add up to {total_importes} "
            f"(tolerance {TOLERANCE}).",
        )
    return Check(
        check_id,
        PASS,
        f"SubTotal {subtotal} matches the sum of the Concepto Importe values {total_importes} "
        f"(tolerance {TOLERANCE}).",
    )


def _check_total(root: Element) -> Check:
    check_id = "total_matches"
    impuestos = root.find("cfdi:Impuestos", NS)
    try:
        subtotal = _dec(root.get("SubTotal"), "SubTotal")
        total = _dec(root.get("Total"), "Total")
        discount = _optional_dec(root.get("Descuento"), "Descuento")
        transferred = _optional_dec(
            impuestos.get("TotalImpuestosTrasladados") if impuestos is not None else None,
            "TotalImpuestosTrasladados",
        )
        withheld = _optional_dec(
            impuestos.get("TotalImpuestosRetenidos") if impuestos is not None else None,
            "TotalImpuestosRetenidos",
        )
    except ValueError as exc:
        return Check(check_id, FAIL, str(exc) + ".")
    expected = subtotal - discount + transferred - withheld
    detail = (
        f"SubTotal {subtotal} minus Descuento {discount} plus TotalImpuestosTrasladados {transferred} "
        f"minus TotalImpuestosRetenidos {withheld} = {expected}"
    )
    if abs(total - expected) > TOLERANCE:
        return Check(check_id, FAIL, f"Total is {total} but {detail}.")
    return Check(check_id, PASS, f"Total {total} matches: {detail} (tolerance {TOLERANCE}).")


def _check_uuid(root: Element) -> Check:
    check_id = "uuid"
    timbre = root.find("cfdi:Complemento/tfd:TimbreFiscalDigital", NS)
    if timbre is None:
        return Check(
            check_id,
            WARN,
            "No TimbreFiscalDigital found. The document has not been stamped (not timbrado).",
        )
    value = _attr(timbre, "UUID")
    if value is None:
        return Check(check_id, FAIL, "TimbreFiscalDigital has no UUID.")
    if _UUID_RE.fullmatch(value) is None:
        return Check(
            check_id,
            FAIL,
            f"UUID {value!r} is not in the hexadecimal 8, 4, 4, 4, 12 format.",
        )
    return Check(check_id, PASS, f"UUID {value} has a valid format.")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_checks(xml_content: str | bytes) -> list[Check]:
    """Run every check and return the results in CHECK_IDS order."""
    data = _prepare(xml_content)

    try:
        root = _parse(data)
    except ParseError as exc:
        reason = f"XML is not well formed: {exc}"
    except ValueError as exc:
        # defusedxml raises ValueError subclasses for DTDs, entities and external references.
        reason = f"XML was rejected for safety (DTD, entity or external reference): {exc}"
    else:
        reason = None

    if reason is not None:
        return [Check("xml_well_formed", FAIL, reason)] + [
            Check(check_id, SKIPPED, "Skipped because the XML did not parse.")
            for check_id in CHECK_IDS[1:]
        ]

    checks = [
        Check("xml_well_formed", PASS, "The XML parsed successfully."),
        _check_version(root),
    ]
    if not _is_cfdi4_root(root):
        checks += [
            Check(check_id, SKIPPED, "Skipped because the document is not a CFDI 4.0 Comprobante.")
            for check_id in CHECK_IDS[2:]
        ]
        return checks

    with localcontext() as ctx:
        ctx.prec = 100
        checks += [
            _check_required_attributes(root),
            _check_rfc("rfc_emisor", "Emisor", root.find("cfdi:Emisor", NS)),
            _check_rfc("rfc_receptor", "Receptor", root.find("cfdi:Receptor", NS)),
            _check_postal_codes(root),
            _check_concept_amounts(root),
            _check_subtotal(root),
            _check_total(root),
            _check_uuid(root),
        ]
    return checks


def validate(xml_content: str | bytes) -> dict[str, Any]:
    """Run every check and return a report with a summary and the list of checks."""
    checks = run_checks(xml_content)
    counts = {status: sum(1 for c in checks if c.status == status) for status in (PASS, FAIL, WARN, SKIPPED)}
    return {
        "summary": {
            "valid": counts[FAIL] == 0,
            "total_checks": len(checks),
            "passed": counts[PASS],
            "failed": counts[FAIL],
            "warnings": counts[WARN],
            "skipped": counts[SKIPPED],
        },
        "checks": [check.to_dict() for check in checks],
    }


def summarize(xml_content: str | bytes) -> dict[str, Any]:
    """Return the main facts of a CFDI 4.0 document.

    When the input cannot be summarized the result has summarized set to False
    and a reason. Amounts are returned as the exact strings found in the XML.
    """
    data = _prepare(xml_content)
    try:
        root = _parse(data)
    except ParseError as exc:
        return {"summarized": False, "reason": f"XML is not well formed: {exc}"}
    except ValueError as exc:
        return {"summarized": False, "reason": f"XML was rejected for safety: {exc}"}
    if not _is_cfdi4_root(root):
        return {"summarized": False, "reason": "The document is not a CFDI 4.0 Comprobante."}

    emisor = root.find("cfdi:Emisor", NS)
    receptor = root.find("cfdi:Receptor", NS)
    timbre = root.find("cfdi:Complemento/tfd:TimbreFiscalDigital", NS)
    return {
        "summarized": True,
        "voucher_type": _attr(root, "TipoDeComprobante"),
        "date": _attr(root, "Fecha"),
        "issuer": {"rfc": _attr(emisor, "Rfc"), "name": _attr(emisor, "Nombre")},
        "receiver": {"rfc": _attr(receptor, "Rfc"), "name": _attr(receptor, "Nombre")},
        "currency": _attr(root, "Moneda"),
        "subtotal": _attr(root, "SubTotal"),
        "total": _attr(root, "Total"),
        "concept_count": len(_concept_nodes(root)),
        "uuid": _attr(timbre, "UUID"),
    }
