Project Name: The Provenance Engine (Local MVP)
Objective: A localized data pipeline and web application designed to trace identical legislative language from partisan think tanks to official state legislation.

1. Core Features (MVP Scope)

* Targeted Ingestion: Scrape and store public-facing model legislation specifically from ALEC (American Legislative Exchange Council).

* Legislative Baseline: Ingest a limited subset of state-level bills (e.g., just Washington state or a single legislative session) using the LegiScan API or OpenStates bulk downloads.

* Text Pre-Processing: Clean, tokenize, and format raw HTML/PDF text into machine-readable formats.

* The Alignment Engine: * Implement Locality Sensitive Hashing (LSH) to quickly identify potential document matches.

  * Implement a local alignment algorithm (like Smith-Waterman) on the flagged pairs to isolate the exact copied paragraphs.

Verification UI: A simple frontend interface that displays two documents side-by-side, visually highlighting the identical text blocks (like a GitHub diff viewer).

2. Out of Scope for MVP (Future Roadmap)

* Cloud deployment (AWS/Azure).

* Financial disclosure tracking (FEC / Lobbying data).

* Full 50-state continuous synchronization.

*Optical Character Recognition (OCR) for image-based PDFs (we will stick to text-selectable PDFs and HTML for v1.0).
