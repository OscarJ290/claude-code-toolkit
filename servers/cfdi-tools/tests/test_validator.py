"""Tests for the pure validation logic, driven by the synthetic fixtures."""

from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path

import pytest

from cfdi_tools import validator
from cfdi_tools.validator import (
    CHECK_IDS,
    InputTooLargeError,
    MAX_INPUT_BYTES,
    check_rfc,
    summarize,
    validate,
)

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def statuses(report: dict) -> dict[str, str]:
    return {check["id"]: check["status"] for check in report["checks"]}


def messages(report: dict) -> dict[str, str]:
    return {check["id"]: check["message"] for check in report["checks"]}


def all_with(**overrides: str) -> dict[str, str]:
    """Expected statuses: every check passes except the ones overridden."""
    expected = {check_id: "pass" for check_id in CHECK_IDS}
    expected.update(overrides)
    return expected


SKIPPED_AFTER_PARSE = {check_id: "skipped" for check_id in CHECK_IDS[1:]}

EXPECTED = {
    "valid_ingreso.xml": (True, all_with()),
    "totals_mismatch.xml": (False, all_with(total_matches="fail")),
    "concept_mismatch.xml": (False, all_with(concept_amounts="fail")),
    "bad_rfc.xml": (False, all_with(rfc_receptor="fail")),
    "no_timbre.xml": (True, all_with(uuid="warn")),
    "version_33.xml": (
        False,
        {"xml_well_formed": "pass", **SKIPPED_AFTER_PARSE, "cfdi_version": "fail"},
    ),
    "malformed.xml": (False, {"xml_well_formed": "fail", **SKIPPED_AFTER_PARSE}),
    "valid_six_decimals.xml": (True, all_with()),
}


# ---------------------------------------------------------------------------
# Fixtures, every check
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_fixture_produces_expected_result_for_every_check(name: str) -> None:
    expected_valid, expected_statuses = EXPECTED[name]
    report = validate(load(name))
    assert statuses(report) == expected_statuses
    assert report["summary"]["valid"] is expected_valid
    assert [c["id"] for c in report["checks"]] == list(CHECK_IDS)


def test_every_check_has_a_message() -> None:
    for name in EXPECTED:
        for check in validate(load(name))["checks"]:
            assert check["message"].strip(), (name, check["id"])
            assert check["status"] in {"pass", "fail", "warn", "skipped"}


def test_summary_counts_add_up() -> None:
    summary = validate(load("no_timbre.xml"))["summary"]
    assert summary == {
        "valid": True,
        "total_checks": 10,
        "passed": 9,
        "failed": 0,
        "warnings": 1,
        "skipped": 0,
    }
    summary = validate(load("malformed.xml"))["summary"]
    assert (summary["failed"], summary["skipped"], summary["passed"]) == (1, 9, 0)


def test_version_33_message_says_so() -> None:
    assert "3.3" in messages(validate(load("version_33.xml")))["cfdi_version"]


def test_no_timbre_is_a_warning_about_not_stamped() -> None:
    assert "not timbrado" in messages(validate(load("no_timbre.xml")))["uuid"]


def test_generic_receiver_rfc_is_reported_as_generic() -> None:
    assert "generic" in messages(validate(load("valid_ingreso.xml")))["rfc_receptor"]


def test_mismatch_messages_name_the_problem() -> None:
    assert "1100.00" in messages(validate(load("totals_mismatch.xml")))["total_matches"]
    assert "Concepto 2" in messages(validate(load("concept_mismatch.xml")))["concept_amounts"]


def test_bytes_input_is_accepted() -> None:
    report = validate(load("valid_ingreso.xml").encode("utf-8"))
    assert report["summary"]["valid"] is True


# ---------------------------------------------------------------------------
# Targeted variations of the valid fixture
# ---------------------------------------------------------------------------


def variant(old: str, new: str) -> dict:
    text = load("valid_ingreso.xml")
    assert old in text
    return validate(text.replace(old, new))


def test_total_with_withholding() -> None:
    old = '<cfdi:Impuestos TotalImpuestosTrasladados="144.00">'
    new = '<cfdi:Impuestos TotalImpuestosTrasladados="144.00" TotalImpuestosRetenidos="10.00">'
    text = load("valid_ingreso.xml").replace(old, new)
    ok = validate(text.replace('Total="1044.00"', 'Total="1034.00"'))
    assert statuses(ok)["total_matches"] == "pass"
    wrong = validate(text)
    assert statuses(wrong)["total_matches"] == "fail"


def test_total_without_discount_or_taxes_treats_them_as_zero() -> None:
    text = load("valid_ingreso.xml")
    text = text.replace(' Descuento="100.00" Moneda', " Moneda")
    text = text.replace('<cfdi:Impuestos TotalImpuestosTrasladados="144.00">', "<cfdi:Impuestos>")
    text = text.replace('Total="1044.00"', 'Total="1000.00"')
    assert statuses(validate(text))["total_matches"] == "pass"


def test_total_tolerance_is_one_cent() -> None:
    assert statuses(variant('Total="1044.00"', 'Total="1044.01"'))["total_matches"] == "pass"
    assert statuses(variant('Total="1044.00"', 'Total="1043.99"'))["total_matches"] == "pass"
    assert statuses(variant('Total="1044.00"', 'Total="1044.02"'))["total_matches"] == "fail"


def test_concept_tolerance_is_one_cent() -> None:
    # Importe 500.01 against 2 x 250.00 is inside the tolerance, 500.02 is not.
    inside = variant(
        'ValorUnitario="250.00" Importe="500.00"', 'ValorUnitario="250.00" Importe="500.01"'
    )
    assert statuses(inside)["concept_amounts"] == "pass"
    outside = variant(
        'ValorUnitario="250.00" Importe="500.00"', 'ValorUnitario="250.00" Importe="500.02"'
    )
    assert statuses(outside)["concept_amounts"] == "fail"


def test_subtotal_tolerance_is_one_cent() -> None:
    # The Importe values add up to 1000.00, so a SubTotal one cent away is a rounding
    # difference and two cents away is a real mismatch. Total is left untouched here
    # because only subtotal_matches is under test.
    assert statuses(variant('SubTotal="1000.00"', 'SubTotal="1000.01"'))["subtotal_matches"] == "pass"
    assert statuses(variant('SubTotal="1000.00"', 'SubTotal="999.99"'))["subtotal_matches"] == "pass"
    assert statuses(variant('SubTotal="1000.00"', 'SubTotal="1000.02"'))["subtotal_matches"] == "fail"
    assert statuses(variant('SubTotal="1000.00"', 'SubTotal="999.98"'))["subtotal_matches"] == "fail"


def test_subtotal_mismatch_message_reports_both_values_and_tolerance() -> None:
    message = messages(variant('SubTotal="1000.00"', 'SubTotal="1500.00"'))["subtotal_matches"]
    assert "1500.00" in message
    assert "1000.00" in message
    assert "0.01" in message


def test_six_decimal_importes_pass_when_rounded_subtotal_matches() -> None:
    text = load("valid_six_decimals.xml")
    importes = [Decimal(m) for m in re.findall(r'ValorUnitario="[0-9.]+" Importe="([0-9.]+)"', text)]
    assert len(importes) == 3
    assert all(len(str(i).split(".")[1]) == 6 for i in importes)
    exact_sum = sum(importes, Decimal(0))
    assert exact_sum == Decimal("336.604929")
    # The exact sum really differs from SubTotal, which is why exact equality was wrong.
    assert exact_sum != Decimal("336.60")
    report = validate(text)
    assert statuses(report)["subtotal_matches"] == "pass"
    assert report["summary"]["valid"] is True


def test_six_decimal_subtotal_still_catches_real_mismatch() -> None:
    text = load("valid_six_decimals.xml")
    report = validate(text.replace('SubTotal="336.60"', 'SubTotal="336.62"'))
    assert statuses(report)["subtotal_matches"] == "fail"


def test_decimal_precision_is_exact() -> None:
    # 0.1 + 0.2 style errors must not appear: three concepts of 0.10 sum to 0.30 exactly.
    text = load("valid_ingreso.xml")
    start = text.index("<cfdi:Conceptos>")
    end = text.index("</cfdi:Conceptos>") + len("</cfdi:Conceptos>")
    concepts = "".join(
        '<cfdi:Concepto Cantidad="1" ValorUnitario="0.10" Importe="0.10"/>' for _ in range(3)
    )
    text = text[:start] + "<cfdi:Conceptos>" + concepts + "</cfdi:Conceptos>" + text[end:]
    text = text.replace('SubTotal="1000.00" Descuento="100.00"', 'SubTotal="0.30" Descuento="0"')
    report = validate(text)
    assert statuses(report)["subtotal_matches"] == "pass"
    assert statuses(report)["concept_amounts"] == "pass"


@pytest.mark.parametrize("bad_amount", ["NaN", "Infinity", "1e3", "-5.00", "abc", "", "1,000.00"])
def test_non_plain_amounts_fail_instead_of_crashing(bad_amount: str) -> None:
    report = variant('Total="1044.00"', f'Total="{bad_amount}"')
    assert statuses(report)["total_matches"] == "fail"


def test_missing_required_attributes_are_listed() -> None:
    report = variant(' Sello="SYNTHETIC"', "")
    assert statuses(report)["required_attributes"] == "fail"
    assert "Comprobante@Sello" in messages(report)["required_attributes"]
    report = variant(' UsoCFDI="S01"', "")
    assert "Receptor@UsoCFDI" in messages(report)["required_attributes"]


def test_missing_receptor_element_fails_without_crashing() -> None:
    text = load("valid_ingreso.xml")
    start = text.index("  <cfdi:Receptor")
    end = text.index("\n", start) + 1
    report = validate(text[:start] + text[end:])
    assert statuses(report)["required_attributes"] == "fail"
    assert statuses(report)["rfc_receptor"] == "fail"
    assert statuses(report)["postal_codes"] == "fail"


@pytest.mark.parametrize("value", ["2025", "202570", "ABCDE", "2025 ", "٢٠٢٥٧"])
def test_postal_codes_must_be_five_ascii_digits(value: str) -> None:
    report = variant('LugarExpedicion="20257"', f'LugarExpedicion="{value}"')
    assert statuses(report)["postal_codes"] == "fail"
    report = variant('DomicilioFiscalReceptor="20257"', f'DomicilioFiscalReceptor="{value}"')
    assert statuses(report)["postal_codes"] == "fail"


@pytest.mark.parametrize(
    "value",
    ["not-a-uuid", "82012804-7425-4141-8964-5DDD28CC8DE", "82012804-7425-4141-8964-5DDD28CC8DEZ"],
)
def test_bad_uuid_fails(value: str) -> None:
    report = variant("82012804-7425-4141-8964-5DDD28CC8DE7", value)
    assert statuses(report)["uuid"] == "fail"


def test_wrong_version_value_fails() -> None:
    report = variant('Version="4.0" Serie', 'Version="4.1" Serie')
    assert statuses(report)["cfdi_version"] == "fail"


def test_generic_emisor_is_valid_but_noted() -> None:
    report = variant('Emisor Rfc="EKU9003173C9"', 'Emisor Rfc="XEXX010101000"')
    assert statuses(report)["rfc_emisor"] == "pass"
    assert "generic" in messages(report)["rfc_emisor"]


# ---------------------------------------------------------------------------
# Hostile and degenerate input
# ---------------------------------------------------------------------------


def test_entity_expansion_is_rejected_not_expanded() -> None:
    bomb = (
        '<?xml version="1.0"?><!DOCTYPE lolz [<!ENTITY lol "lol">'
        '<!ENTITY lol2 "&lol;&lol;&lol;&lol;">]><lolz>&lol2;</lolz>'
    )
    report = validate(bomb)
    assert statuses(report)["xml_well_formed"] == "fail"
    assert report["summary"]["valid"] is False
    assert statuses(report)["cfdi_version"] == "skipped"


def test_external_entity_is_rejected() -> None:
    xxe = '<?xml version="1.0"?><!DOCTYPE a [<!ENTITY x SYSTEM "file:///etc/passwd">]><a>&x;</a>'
    assert statuses(validate(xxe))["xml_well_formed"] == "fail"


@pytest.mark.parametrize("text", ["", "   ", "not xml at all", "<a><b></a>"])
def test_garbage_input_fails_cleanly(text: str) -> None:
    report = validate(text)
    assert statuses(report) == {"xml_well_formed": "fail", **SKIPPED_AFTER_PARSE}


def test_other_root_element_is_not_cfdi() -> None:
    report = validate("<Factura><Total>1</Total></Factura>")
    assert statuses(report)["xml_well_formed"] == "pass"
    assert statuses(report)["cfdi_version"] == "fail"
    assert statuses(report)["total_matches"] == "skipped"


def test_input_over_two_megabytes_is_rejected() -> None:
    too_big = "<a>" + "x" * MAX_INPUT_BYTES + "</a>"
    with pytest.raises(InputTooLargeError):
        validate(too_big)
    with pytest.raises(InputTooLargeError):
        summarize(too_big)
    with pytest.raises(InputTooLargeError):
        validate(too_big.encode("utf-8"))


def test_input_of_exactly_two_megabytes_is_accepted() -> None:
    filler = MAX_INPUT_BYTES - len("<a></a>")
    exact = "<a>" + "x" * filler + "</a>"
    assert len(exact.encode("utf-8")) == MAX_INPUT_BYTES
    report = validate(exact)
    assert statuses(report)["xml_well_formed"] == "pass"


def test_size_limit_counts_bytes_not_characters() -> None:
    # Each "ñ" is 2 bytes in UTF-8, so half the limit in characters is already too big.
    text = "<a>" + "ñ" * (MAX_INPUT_BYTES // 2 + 1) + "</a>"
    assert len(text) < MAX_INPUT_BYTES
    with pytest.raises(InputTooLargeError):
        validate(text)


def test_non_text_input_is_a_type_error() -> None:
    with pytest.raises(TypeError):
        validate(123)  # type: ignore[arg-type]


def test_leading_bom_is_tolerated() -> None:
    assert validate("﻿" + load("valid_ingreso.xml"))["summary"]["valid"] is True


# ---------------------------------------------------------------------------
# check_rfc
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("rfc", "rfc_type"),
    [
        ("EKU9003173C9", "moral"),
        ("ABC850101AB1", "moral"),
        ("PEPJ850101AB1", "fisica"),
        ("ÑAM850101AB1", "moral"),
        ("A&B850101AB1", "moral"),
        ("&AÑO850101AB1", "fisica"),
        ("XAXX010101000", "generico"),
        ("XEXX010101000", "generico"),
    ],
)
def test_check_rfc_valid(rfc: str, rfc_type: str) -> None:
    result = check_rfc(rfc)
    assert result["valid"] is True
    assert result["type"] == rfc_type
    assert result["generic"] is (rfc_type == "generico")


def test_check_rfc_reports_encoded_date() -> None:
    result = check_rfc("EKU9003173C9")
    assert result["encoded_date"]["yymmdd"] == "900317"
    assert result["encoded_date"]["possible_dates"] == ["1990-03-17"]
    ambiguous = check_rfc("PEPJ010101AB1")
    assert ambiguous["encoded_date"]["possible_dates"] == ["1901-01-01", "2001-01-01"]


def test_check_rfc_generic_has_no_real_date() -> None:
    result = check_rfc("XAXX010101000")
    assert result["encoded_date"] is None
    assert "generic" in result["message"]


def test_check_rfc_leap_day_only_in_leap_century_year() -> None:
    # 29 February with year 00 exists in 2000 but not in 1900.
    result = check_rfc("PEPJ000229AB1")
    assert result["valid"] is True
    assert result["encoded_date"]["possible_dates"] == ["2000-02-29"]


@pytest.mark.parametrize(
    "rfc",
    [
        "ABC851301AB1",  # month 13
        "ABC850230AB1",  # 30 February
        "ABC850132AB1",  # day 32
        "ABC850001AB1",  # month 00
        "ABC850100AB1",  # day 00
        "PEPJ850431AB1",  # 31 April
        "PEPJ010229AB1",  # 29 February, neither 1901 nor 2001 is a leap year
    ],
)
def test_check_rfc_impossible_date(rfc: str) -> None:
    result = check_rfc(rfc)
    assert result["valid"] is False
    assert "calendar date" in result["message"]


@pytest.mark.parametrize("rfc", ["", "ABC", "ABC85010", "ABC850101AB", "PEPJ850101AB12", "A" * 14])
def test_check_rfc_wrong_length(rfc: str) -> None:
    result = check_rfc(rfc)
    assert result["valid"] is False
    assert result["type"] is None
    assert "characters" in result["message"]


@pytest.mark.parametrize(
    ("rfc", "fragment"),
    [
        ("abc850101ab1", "uppercase"),
        ("AB1850101AB1", "letters"),
        ("ABC85A101AB1", "6 digits"),
        ("ABC850101A-1", "homoclave"),
        ("ABC 850101AB", "whitespace"),
        ("ABC850101AB1 ", "whitespace"),
    ],
)
def test_check_rfc_bad_shape(rfc: str, fragment: str) -> None:
    result = check_rfc(rfc)
    assert result["valid"] is False
    assert fragment in result["message"]


def test_check_rfc_rejects_non_ascii_digits_in_date() -> None:
    assert check_rfc("ABC٨٥٠١٠١AB1")["valid"] is False


def test_check_rfc_requires_a_string() -> None:
    with pytest.raises(TypeError):
        check_rfc(None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# summarize
# ---------------------------------------------------------------------------


def test_summarize_valid_fixture() -> None:
    assert summarize(load("valid_ingreso.xml")) == {
        "summarized": True,
        "voucher_type": "I",
        "date": "2024-01-15T10:30:00",
        "issuer": {"rfc": "EKU9003173C9", "name": "ESCUELA KEMPER URGATE"},
        "receiver": {"rfc": "XAXX010101000", "name": "PUBLICO EN GENERAL"},
        "currency": "MXN",
        "subtotal": "1000.00",
        "total": "1044.00",
        "concept_count": 2,
        "uuid": "82012804-7425-4141-8964-5DDD28CC8DE7",
    }


def test_summarize_without_timbre_has_no_uuid() -> None:
    summary = summarize(load("no_timbre.xml"))
    assert summary["summarized"] is True
    assert summary["uuid"] is None


def test_summarize_refuses_unusable_input() -> None:
    for name in ("malformed.xml", "version_33.xml"):
        summary = summarize(load(name))
        assert summary["summarized"] is False
        assert summary["reason"]


def test_module_has_no_mcp_dependency() -> None:
    source = Path(validator.__file__).read_text(encoding="utf-8")
    assert "import mcp" not in source
    assert "from mcp" not in source
