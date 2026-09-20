# AI Code Review & Security Analysis Agent

AI Code Review & Security Analysis Agent is a multi-agent review platform for Python and Java source code. It combines code smell detection, security analysis, remediation guidance, RAG-grounded conversational support, PR summaries, and exportable review reports.

## Features

- Python and Java submission support.
- Code smell and design issue detection.
- OWASP-style security vulnerability detection.
- Groq-backed review, remediation, summary, and conversational assistant flows.
- Retrieval-Augmented Generation (RAG) answers grounded in the secure coding knowledge base.
- JSON and PDF review report export.
- Severity scoring and code health metrics.

## Architecture

The workflow is:

1. Submit code through the Streamlit UI.
2. Validate the filename and source content.
3. Run the orchestrator.
4. Collect analysis findings, remediation details, PR summary, and RAG follow-up support.
5. Export the final review as JSON and PDF.

## Installation

1. Create and activate the project virtual environment.
2. Install dependencies from `requirements.txt`.
3. Set `GROQ_API_KEY` in the project `.env` file.
4. Optionally set `GROQ_MODEL` if you want a different supported Groq model.

## Running the App

```bash
python -m streamlit run app/main.py
```

## Reports

The orchestrator writes a JSON review artifact and a PDF review report under `reports/`. The PDF includes the findings summary, severity breakdown, remediation roadmap, and code snapshot.

## Modules

- `agent/code_analysis_agent.py`: code smell and design analysis.
- `agent/security_agent.py`: OWASP-style security checks.
- `agent/remediation_agent.py`: fix suggestions and code examples.
- `agent/pr_summary_agent.py`: executive PR summary generation.
- `agent/conversational_assistant.py`: grounded follow-up answers.
- `agent/orchestrator.py`: runs the full pipeline and exports reports.
- `agent/report_exporter.py`: PDF report generation.

## Folder Structure

- `app/`: Streamlit UI, validation, display, and upload helpers.
- `agent/`: analysis, remediation, summary, orchestration, and export logic.
- `rag/`: knowledge base loading, embedding, querying, and vector storage.
- `sample_code/`: Python and Java examples used for validation.
- `doc/`: milestone reports, architecture notes, and secure coding references.
- `tests/`: automated validation for the analysis pipeline.

## Validation

Run the focused test suite with:

```bash
e:/infosys_springBoard/AI-Code-Review-Agent/.venv-1/Scripts/python.exe -m pytest tests/test_analysis.py
```

## Future Work

- Improve the exported PDF styling.
- Add more sample submissions for regression testing.
- Expand the knowledge base with additional secure coding references.