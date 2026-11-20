# Sample output (format reference)

Report produced by the cfdi-validator skill for `servers/cfdi-tools/tests/fixtures/totals_mismatch.xml`,
a synthetic CFDI 4.0 whose `Total` does not match the rest of its amounts. The results below come from
calling `summarize_cfdi` and `validate_cfdi` on the `cfdi-tools` MCP server with the content of that file.

## Voucher summary

| Field | Value |
| --- | --- |
| Voucher type | `I` (ingreso) |
| Date | 2024-01-15T10:30:00 |
| Issuer | EKU9003173C9, ESCUELA KEMPER URGATE |
| Receiver | XAXX010101000, PUBLICO EN GENERAL |
| Currency | MXN |
| SubTotal | 1000.00 |
| Total | 1100.00 |
| Concepts | 2 |
| UUID | 78852F46-F0CF-4369-B7B7-6DDC0F434FBB |

**Result: not valid.** 10 checks run, 9 passed, 1 failed, 0 warnings, 0 skipped.

## Checks

| Check | Status |
| --- | --- |
| `xml_well_formed` | pass |
| `cfdi_version` | pass |
| `required_attributes` | pass |
| `rfc_emisor` | pass |
| `rfc_receptor` | pass |
| `postal_codes` | pass |
| `concept_amounts` | pass |
| `subtotal_matches` | pass |
| `total_matches` | **fail** |
| `uuid` | pass |

## What failed

### `total_matches`

The tool reported: Total is 1100.00 but SubTotal 1000.00 minus Descuento 100.00 plus
TotalImpuestosTrasladados 144.00 minus TotalImpuestosRetenidos 0 = 1044.00.

This check adds up the invoice the way the SAT does. It takes the subtotal, subtracts the discount
(`Descuento`), adds the taxes charged to the client (`TotalImpuestosTrasladados`, the VAT in this case)
and subtracts the taxes withheld (`TotalImpuestosRetenidos`). That arithmetic gives 1044.00 pesos, but
the invoice declares a total of 1100.00 pesos, so the file is off by 56.00 pesos.

What to look at: the `Total` attribute of `cfdi:Comprobante`, the `Descuento` attribute next to it and
the `TotalImpuestosTrasladados` attribute of `cfdi:Impuestos`. One of those four numbers is the wrong
one, and the XML alone cannot say which. Whoever issued the invoice has to reissue it, because editing
the file would invalidate its seal.

## Scope limit

These checks cover structure, formats and arithmetic. They do not validate the digital seal (sello),
the certificate, the SAT catalogs or the status of the document with the SAT. For those, use the
official SAT verification service.
