# AI invoice extraction with human review

Reads invoices in different layouts with OpenAI (Structured Outputs), validates dates, amounts and subtotal + tax = total, asks a person to confirm, and exports a CSV row traceable to the exact PDF (page + SHA-256).

Live OpenAI run on three synthetic invoices, including a realistic layout the offline rules could not read (evidence/live-openai-run.md). 29 automated tests. Portfolio demo with synthetic documents, built with AI assistance; not client work. Not yet tested on scans (no OCR) or on a real-world accuracy sample.
