"""Generate the synthetic CFDI fixtures used by the tests.

Run it from servers/cfdi-tools with: uv run python scripts/make_fixtures.py

Everything here is synthetic. The issuer is the public SAT test taxpayer
(EKU9003173C9, ESCUELA KEMPER URGATE), the receiver is the generic national RFC,
and the seal, certificate number and certificate are obvious placeholders. The
UUIDs are fixed values generated once, so regenerating the files always gives
identical output.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"

UUID_VALID = "82012804-7425-4141-8964-5DDD28CC8DE7"
UUID_TOTALS_MISMATCH = "78852F46-F0CF-4369-B7B7-6DDC0F434FBB"
UUID_CONCEPT_MISMATCH = "100A8005-316E-4A03-AE53-CFD56CA44AD3"
UUID_BAD_RFC = "FCE358E1-E03C-4632-A0E5-369944A4EB6E"

PLACEHOLDER = "SYNTHETIC"
TAX_RATE = Decimal("0.16")

# Each concept: (quantity, unit price, Importe, discount or None)
DEFAULT_CONCEPTS = (
    ("2", "250.00", "500.00", "100.00"),
    ("1", "500.00", "500.00", None),
)


def money(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01'))}"


def build_cfdi40(
    *,
    uuid: str | None,
    receptor_rfc: str = "XAXX010101000",
    concepts: tuple[tuple[str, str, str, str | None], ...] = DEFAULT_CONCEPTS,
    total_override: str | None = None,
) -> str:
    """Build a CFDI 4.0 ingreso document. Totals are consistent unless overridden."""
    concept_xml: list[str] = []
    subtotal = Decimal(0)
    discount_total = Decimal(0)
    tax_total = Decimal(0)
    base_total = Decimal(0)

    for quantity, unit_price, amount, discount in concepts:
        amount_d = Decimal(amount)
        discount_d = Decimal(discount) if discount else Decimal(0)
        base = amount_d - discount_d
        tax = (base * TAX_RATE).quantize(Decimal("0.01"))
        subtotal += amount_d
        discount_total += discount_d
        base_total += base
        tax_total += tax
        discount_attr = f' Descuento="{discount}"' if discount else ""
        concept_xml.append(
            f'    <cfdi:Concepto ClaveProdServ="01010101" Cantidad="{quantity}" ClaveUnidad="H87" '
            f'Descripcion="SYNTHETIC ITEM" ValorUnitario="{unit_price}" Importe="{amount}"'
            f'{discount_attr} ObjetoImp="02">\n'
            f"      <cfdi:Impuestos>\n"
            f"        <cfdi:Traslados>\n"
            f'          <cfdi:Traslado Base="{money(base)}" Impuesto="002" TipoFactor="Tasa" '
            f'TasaOCuota="0.160000" Importe="{money(tax)}"/>\n'
            f"        </cfdi:Traslados>\n"
            f"      </cfdi:Impuestos>\n"
            f"    </cfdi:Concepto>"
        )

    total = subtotal - discount_total + tax_total
    total_text = total_override if total_override is not None else money(total)
    discount_attr_root = f' Descuento="{money(discount_total)}"' if discount_total else ""

    complemento = ""
    if uuid is not None:
        complemento = (
            "  <cfdi:Complemento>\n"
            '    <tfd:TimbreFiscalDigital xmlns:tfd="http://www.sat.gob.mx/TimbreFiscalDigital" '
            'xsi:schemaLocation="http://www.sat.gob.mx/TimbreFiscalDigital '
            'http://www.sat.gob.mx/sitio_internet/cfd/TimbreFiscalDigital/TimbreFiscalDigitalv11.xsd" '
            f'Version="1.1" UUID="{uuid}" FechaTimbrado="2024-01-15T10:31:00" '
            f'RfcProvCertif="{PLACEHOLDER}" SelloCFD="{PLACEHOLDER}" '
            f'NoCertificadoSAT="{PLACEHOLDER}" SelloSAT="{PLACEHOLDER}"/>\n'
            "  </cfdi:Complemento>\n"
        )

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<cfdi:Comprobante xmlns:cfdi="http://www.sat.gob.mx/cfd/4" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:schemaLocation="http://www.sat.gob.mx/cfd/4 '
        'http://www.sat.gob.mx/sitio_internet/cfd/4/cfdv40.xsd" '
        f'Version="4.0" Serie="SYN" Folio="1" Fecha="2024-01-15T10:30:00" Sello="{PLACEHOLDER}" '
        f'FormaPago="01" NoCertificado="{PLACEHOLDER}" Certificado="{PLACEHOLDER}" '
        f'SubTotal="{money(subtotal)}"{discount_attr_root} Moneda="MXN" Total="{total_text}" '
        'TipoDeComprobante="I" Exportacion="01" MetodoPago="PUE" LugarExpedicion="20257">\n'
        '  <cfdi:Emisor Rfc="EKU9003173C9" Nombre="ESCUELA KEMPER URGATE" RegimenFiscal="601"/>\n'
        f'  <cfdi:Receptor Rfc="{receptor_rfc}" Nombre="PUBLICO EN GENERAL" '
        'DomicilioFiscalReceptor="20257" RegimenFiscalReceptor="616" UsoCFDI="S01"/>\n'
        "  <cfdi:Conceptos>\n" + "\n".join(concept_xml) + "\n  </cfdi:Conceptos>\n"
        f'  <cfdi:Impuestos TotalImpuestosTrasladados="{money(tax_total)}">\n'
        "    <cfdi:Traslados>\n"
        f'      <cfdi:Traslado Base="{money(base_total)}" Impuesto="002" TipoFactor="Tasa" '
        f'TasaOCuota="0.160000" Importe="{money(tax_total)}"/>\n'
        "    </cfdi:Traslados>\n"
        "  </cfdi:Impuestos>\n" + complemento + "</cfdi:Comprobante>\n"
    )


def build_cfdi33() -> str:
    """Build a CFDI 3.3 style document (no Exportacion, no receiver fiscal address)."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<cfdi:Comprobante xmlns:cfdi="http://www.sat.gob.mx/cfd/3" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:schemaLocation="http://www.sat.gob.mx/cfd/3 '
        'http://www.sat.gob.mx/sitio_internet/cfd/3/cfdv33.xsd" '
        f'Version="3.3" Serie="SYN" Folio="1" Fecha="2021-06-15T10:30:00" Sello="{PLACEHOLDER}" '
        f'FormaPago="01" NoCertificado="{PLACEHOLDER}" Certificado="{PLACEHOLDER}" '
        'SubTotal="1000.00" Moneda="MXN" Total="1160.00" TipoDeComprobante="I" '
        'MetodoPago="PUE" LugarExpedicion="20257">\n'
        '  <cfdi:Emisor Rfc="EKU9003173C9" Nombre="ESCUELA KEMPER URGATE" RegimenFiscal="601"/>\n'
        '  <cfdi:Receptor Rfc="XAXX010101000" Nombre="PUBLICO EN GENERAL" UsoCFDI="G03"/>\n'
        "  <cfdi:Conceptos>\n"
        '    <cfdi:Concepto ClaveProdServ="01010101" Cantidad="1" ClaveUnidad="H87" '
        'Descripcion="SYNTHETIC ITEM" ValorUnitario="1000.00" Importe="1000.00"/>\n'
        "  </cfdi:Conceptos>\n"
        "</cfdi:Comprobante>\n"
    )


def build_malformed() -> str:
    """Build XML that is cut off in the middle, so it cannot parse."""
    valid = build_cfdi40(uuid=None)
    cut = valid.index("<cfdi:Conceptos>")
    return valid[:cut] + "<cfdi:Conceptos>\n    <cfdi:Concepto Cantidad=\"1\" ValorUnitario=\n"


def build_all() -> dict[str, str]:
    mismatch_concepts = (
        ("2", "250.00", "500.00", "100.00"),
        ("1", "500.00", "520.00", None),
    )
    return {
        "valid_ingreso.xml": build_cfdi40(uuid=UUID_VALID),
        "totals_mismatch.xml": build_cfdi40(uuid=UUID_TOTALS_MISMATCH, total_override="1100.00"),
        "concept_mismatch.xml": build_cfdi40(uuid=UUID_CONCEPT_MISMATCH, concepts=mismatch_concepts),
        "bad_rfc.xml": build_cfdi40(uuid=UUID_BAD_RFC, receptor_rfc="123INVALID99"),
        "no_timbre.xml": build_cfdi40(uuid=None),
        "version_33.xml": build_cfdi33(),
        "malformed.xml": build_malformed(),
    }


def main() -> None:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    for name, content in build_all().items():
        # newline="" keeps LF endings on every platform so the output is identical everywhere.
        with open(FIXTURES_DIR / name, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        print(f"wrote {FIXTURES_DIR / name}")


if __name__ == "__main__":
    main()
