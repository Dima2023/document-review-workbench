# Live OpenAI extraction run — 2026-11-15

Real API calls, run on the owner's machine. Key read from a local file (`OPENAI_API_KEY_FILE`); never printed or stored in this repository.
Command per file: `python review.py examples/invoice-N.pdf --extractor openai`, each value accepted with Enter, then `APPROVE`.

| File | Layout | Offline rules | OpenAI (`gpt-6-luna`) | Time |
|---|---|---|---|---|
| invoice-1.pdf | "Label: value" | correct | correct — DEMO-001, 2026-10-01, 100.00 + 20.00 = 120.00 USD | ~2 s |
| invoice-2.pdf | "Label \| value" | correct | correct — DEMO-002, 2026-10-02, 50.00 + 0.00 = 50.00 EUR | ~2 s |
| invoice-3.pdf | realistic: line items, `£1,240.00`, "14 October 2026" | **nothing recognised** | correct — INV-2026-0147, 2026-10-14, 1240.00 + 248.00 = 1488.00 GBP | ~2 s |

`gpt-5-mini` returned the same fields for invoice-3 (~7 s).

Exported CSV rows (`extraction_mode` records the model; `source_sha256` ties each row to the exact PDF bytes):

```
DEMO-001,2026-10-01,100.00,20.00,120.00,USD,1,invoice-1.pdf,ab635da958860d2d2dcb9ca7e9986c460399993768a3f635aa5e5818967649f7,openai:gpt-6-luna,human_approved
DEMO-002,2026-10-02,50.00,0.00,50.00,EUR,1,invoice-2.pdf,248048c7d45e9223b7acde6db37f9973472598159e444e365e97d8d1fa5f96bf,openai:gpt-6-luna,human_approved
INV-2026-0147,2026-10-14,1240.00,248.00,1488.00,GBP,1,invoice-3.pdf,5a318f7ba2f39da0202ea44ddbe29cb6c9c60ac1967cd95076b1a778fa06c581,openai:gpt-6-luna,human_approved
```

Scope of this evidence: three synthetic digital PDFs. It shows the integration works end to end; it is not an accuracy benchmark on real-world invoices.
