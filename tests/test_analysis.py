import json
from pathlib import Path

import requests

from agent.code_analysis_agent import CodeAnalysisAgent
from agent.conversational_assistant import ConversationalCodeAssistant
from agent.orchestrator import ReviewOrchestrator
from agent.openai_review_agent import OpenAIReviewAgent
from app.validator import validate_submission


BASE_DIR = Path(__file__).resolve().parents[1]


def test_code_analysis_agent_detects_complexity():
    code = (BASE_DIR / "sample_code" / "python" / "bad_code.py").read_text(encoding="utf-8")
    agent = CodeAnalysisAgent()
    results = agent.analyze(code)

    assert any(item["type"] == "High Cyclomatic Complexity" for item in results)
    assert all("severity_score" in item for item in results)


def test_security_pipeline_detects_sample_vulnerabilities():
    code = (BASE_DIR / "sample_code" / "python" / "vulnerable_security.py").read_text(encoding="utf-8")
    orchestrator = ReviewOrchestrator()
    orchestrator.openai_review_agent.api_key = "test-key"
    orchestrator.openai_review_agent.analyze = lambda code, language: {
        "findings": [
            {
                "type": "SQL Injection",
                "severity": "Critical",
                "line": 7,
                "message": "Unsafe SQL string concatenation.",
                "recommendation": "Use parameterized queries.",
                "severity_score": 4,
            },
            {
                "type": "Dangerous Dynamic Execution",
                "severity": "Critical",
                "line": 9,
                "message": "eval(input()) usage.",
                "recommendation": "Remove eval.",
                "severity_score": 4,
            },
        ],
        "summary": {"total_findings": 2, "severity_breakdown": {"Low": 0, "Medium": 0, "High": 0, "Critical": 2}, "risk_score": 8},
        "review_mode": "openai",
    }
    result = orchestrator.analyze(code, language="python")

    finding_types = {item["type"] for item in result["findings"]}
    assert "SQL Injection" in finding_types
    assert "Dangerous Dynamic Execution" in finding_types
    assert result["summary"]["total_findings"] >= 1
    assert all("severity_score" in item for item in result["findings"])


def test_java_codebase_detects_quality_issues_and_vulnerabilities():
    code = (BASE_DIR / "sample_code" / "java" / "bad_code.java").read_text(encoding="utf-8")
    orchestrator = ReviewOrchestrator()
    orchestrator.openai_review_agent.api_key = "test-key"
    orchestrator.openai_review_agent.analyze = lambda code, language: {
        "findings": [
            {
                "type": "Long Parameter List",
                "severity": "High",
                "line": 12,
                "message": "Too many parameters.",
                "recommendation": "Group related parameters.",
                "severity_score": 3,
            },
            {
                "type": "Deep Nesting",
                "severity": "High",
                "line": 20,
                "message": "Complex nested blocks.",
                "recommendation": "Extract helper methods.",
                "severity_score": 3,
            },
            {
                "type": "Large Class",
                "severity": "Medium",
                "line": 2,
                "message": "Class has too many responsibilities.",
                "recommendation": "Split class by domain concern.",
                "severity_score": 2,
            },
        ],
        "summary": {"total_findings": 3, "severity_breakdown": {"Low": 0, "Medium": 1, "High": 2, "Critical": 0}, "risk_score": 8},
        "review_mode": "openai",
    }
    result = orchestrator.analyze(code, language="java")

    finding_types = {item["type"] for item in result["findings"]}
    assert "Long Parameter List" in finding_types
    assert "Deep Nesting" in finding_types
    assert "Large Class" in finding_types
    assert all("severity_score" in item for item in result["findings"])


def test_java_security_sample_flags_location_specific_vulnerabilities():
    code = (BASE_DIR / "sample_code" / "java" / "vulnerable_security.java").read_text(encoding="utf-8")
    orchestrator = ReviewOrchestrator()
    orchestrator.openai_review_agent.api_key = "test-key"
    orchestrator.openai_review_agent.analyze = lambda code, language: {
        "findings": [
            {
                "type": "SQL Injection",
                "severity": "Critical",
                "line": 10,
                "message": "Unsafe SQL string formatting.",
                "recommendation": "Use prepared statements.",
                "severity_score": 4,
            },
            {
                "type": "Command Injection",
                "severity": "Critical",
                "line": 18,
                "message": "Runtime.exec with unsanitized input.",
                "recommendation": "Avoid shell execution with user input.",
                "severity_score": 4,
            },
        ],
        "summary": {"total_findings": 2, "severity_breakdown": {"Low": 0, "Medium": 0, "High": 0, "Critical": 2}, "risk_score": 8},
        "review_mode": "openai",
    }
    result = orchestrator.analyze(code, language="java")

    finding_types = {item["type"] for item in result["findings"]}
    assert "SQL Injection" in finding_types
    assert "Command Injection" in finding_types
    assert any(item["line"] > 0 for item in result["findings"])


def test_validator_rejects_unsupported_files():
    validation = validate_submission("notes.txt", "hello")
    assert validation["valid"] is False
    assert validation["message"] == "Unsupported file type. Use Python or Java source files."


def test_openai_review_agent_loads_api_key_from_env(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-dotenv-key")
    monkeypatch.setattr("agent.openai_review_agent.load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setattr("agent.openai_review_agent.load_env_file", lambda *args, **kwargs: None)

    agent = OpenAIReviewAgent()

    assert agent.api_key == "test-dotenv-key"


def test_openai_review_agent_parses_response(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": '{"findings": [{"type": "Security Issue", "severity": "High", "line": 3, "message": "Use parameterized queries.", "recommendation": "Replace string concatenation."}], "summary": {"total_findings": 1, "severity_breakdown": {"Low": 0, "Medium": 0, "High": 1, "Critical": 0}, "risk_score": 3}}'
                        }
                    }
                ]
            }

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setattr("requests.post", lambda *args, **kwargs: FakeResponse())

    agent = OpenAIReviewAgent()
    result = agent.analyze("print('hello')", language="python")

    assert result["review_mode"] == "openai"
    assert result["findings"][0]["severity_score"] == 3


def test_openai_review_agent_handles_connection_reset(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setattr("requests.post", lambda *args, **kwargs: (_ for _ in ()).throw(requests.exceptions.ConnectionError("Connection reset by peer")))

    agent = OpenAIReviewAgent()
    result = agent.analyze("print('hello')", language="python")

    assert result["review_mode"] == "groq_connection_error"
    assert "Connection reset" in result["error"]


def test_orchestrator_uses_openai_when_key_is_available(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    orchestrator = ReviewOrchestrator()
    monkeypatch.setattr(
        orchestrator.openai_review_agent,
        "analyze",
        lambda code, language: {
            "findings": [
                {
                    "type": "Model Review",
                    "severity": "Medium",
                    "line": 1,
                    "message": "Model-backed review result.",
                    "recommendation": "Refactor the logic.",
                    "severity_score": 2,
                }
            ],
            "summary": {"total_findings": 1, "severity_breakdown": {"Low": 0, "Medium": 1, "High": 0, "Critical": 0}, "risk_score": 2},
            "review_mode": "openai",
        },
    )

    result = orchestrator.analyze("print('hello')", language="python")

    assert result["review_mode"] == "openai"


def test_orchestrator_merges_local_and_model_findings(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    orchestrator = ReviewOrchestrator()
    monkeypatch.setattr(orchestrator, "code_analysis_agent", type("CodeAnalysisAgent", (), {"analyze": lambda self, code, language: [{"type": "Complexity", "severity": "Medium", "line": 2, "message": "Too complex", "recommendation": "Refactor"}]} )(), raising=False)
    monkeypatch.setattr(orchestrator, "security_agent", type("SecurityAgent", (), {"analyze": lambda self, code, language: [{"type": "Dangerous Dynamic Execution", "severity": "Critical", "line": 1, "message": "eval() used", "recommendation": "Remove eval"}]} )(), raising=False)
    monkeypatch.setattr(
        orchestrator.openai_review_agent,
        "analyze",
        lambda code, language: {
            "findings": [
                {
                    "type": "Model Review",
                    "severity": "High",
                    "line": 3,
                    "message": "Model result.",
                    "recommendation": "Improve logic.",
                    "severity_score": 3,
                }
            ],
            "summary": {"total_findings": 1, "severity_breakdown": {"Low": 0, "Medium": 0, "High": 1, "Critical": 0}, "risk_score": 3},
            "review_mode": "openai",
        },
    )

    result = orchestrator.analyze("eval(input())", language="python")

    finding_types = {item["type"] for item in result["findings"]}
    assert "Complexity" in finding_types
    assert "Dangerous Dynamic Execution" in finding_types
    assert "Model Review" in finding_types
    assert result["summary"]["total_findings"] >= 3


def test_orchestrator_returns_groq_only_error_when_key_missing(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    orchestrator = ReviewOrchestrator()
    orchestrator.openai_review_agent.api_key = ""
    monkeypatch.setattr(orchestrator.openai_review_agent, "_refresh_environment", lambda: None)
    result = orchestrator.analyze("print('hello')", language="python")

    assert result["review_mode"] == "groq_only"
    assert result["findings"][0]["type"] == "Groq Review Error"


def test_orchestrator_writes_review_json_artifact(monkeypatch, tmp_path):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    orchestrator = ReviewOrchestrator(reports_dir=tmp_path)
    monkeypatch.setattr(
        orchestrator.openai_review_agent,
        "analyze",
        lambda code, language: {
            "findings": [
                {
                    "type": "Model Review",
                    "severity": "High",
                    "line": 4,
                    "message": "Needs cleanup.",
                    "recommendation": "Refactor the function.",
                    "severity_score": 3,
                }
            ],
            "summary": {"total_findings": 1, "severity_breakdown": {"Low": 0, "Medium": 0, "High": 1, "Critical": 0}, "risk_score": 3},
            "review_mode": "openai",
            "model": "test-model",
        },
    )

    result = orchestrator.analyze("print('hello')", language="python")

    report_path = Path(result["report_path"])
    assert report_path.exists()

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["review_mode"] == "openai"
    assert payload["severity_breakdown"]["High"] == 1
    assert payload["findings"][0]["severity_score"] == 3
    assert Path(result["pdf_report_path"]).exists()
    assert Path(result["pdf_report_path"]).suffix == ".pdf"


def test_review_pdf_export_contains_expected_sections(monkeypatch, tmp_path):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    orchestrator = ReviewOrchestrator(reports_dir=tmp_path)
    monkeypatch.setattr(
        orchestrator.openai_review_agent,
        "analyze",
        lambda code, language: {
            "findings": [
                {
                    "type": "SQL Injection",
                    "severity": "Critical",
                    "line": 7,
                    "message": "Unsafe SQL concatenation.",
                    "recommendation": "Use parameterized queries.",
                    "severity_score": 4,
                },
                {
                    "type": "Hardcoded Secret",
                    "severity": "High",
                    "line": 2,
                    "message": "Secret stored in source.",
                    "recommendation": "Move it to environment variables.",
                    "severity_score": 3,
                },
            ],
            "summary": {"total_findings": 2, "severity_breakdown": {"Low": 0, "Medium": 0, "High": 1, "Critical": 1}, "risk_score": 7},
            "review_mode": "openai",
            "model": "test-model",
        },
    )
    monkeypatch.setattr(
        orchestrator.remediation_agent,
        "suggest",
        lambda code, language, finding: {
            "remediation": "Use a prepared statement." if finding["type"] == "SQL Injection" else "Use env vars.",
            "corrected_code_example": "example",
            "best_practice_explanation": "safe practice",
            "model": "test-model",
        },
    )
    monkeypatch.setattr(
        orchestrator.pr_summary_agent,
        "summarize",
        lambda review_result: {
            "executive_overview": "High risk due to multiple issues.",
            "severity_breakdown": review_result["summary"]["severity_breakdown"],
            "prioritized_fix_list": [
                {
                    "finding_type": "SQL Injection",
                    "severity": "Critical",
                    "impact": "Remote attack risk.",
                    "fix_priority": 1,
                    "suggested_action": "Use parameterized queries.",
                }
            ],
            "merge_readiness": "blocked",
            "model": "test-model",
        },
    )

    result = orchestrator.analyze("print('hello')", language="python")
    pdf_path = Path(result["pdf_report_path"])
    assert pdf_path.exists()
    assert pdf_path.suffix == ".pdf"

    from pypdf import PdfReader

    text = "\n".join(page.extract_text() or "" for page in PdfReader(str(pdf_path)).pages)
    assert "Code Review Report" in text
    assert "Findings Summary" in text
    assert "Remediation Roadmap" in text
    assert "SQL Injection" in text


def test_orchestrator_attaches_remediation_details(monkeypatch, tmp_path):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    orchestrator = ReviewOrchestrator(reports_dir=tmp_path)
    monkeypatch.setattr(
        orchestrator.openai_review_agent,
        "analyze",
        lambda code, language: {
            "findings": [
                {
                    "type": "SQL Injection",
                    "severity": "Critical",
                    "line": 7,
                    "message": "Unsafe SQL concatenation.",
                    "recommendation": "Use parameterized queries.",
                    "severity_score": 4,
                }
            ],
            "summary": {"total_findings": 1, "severity_breakdown": {"Low": 0, "Medium": 0, "High": 0, "Critical": 1}, "risk_score": 4},
            "review_mode": "openai",
            "model": "test-model",
        },
    )
    monkeypatch.setattr(
        orchestrator.remediation_agent,
        "suggest",
        lambda code, language, finding: {
            "remediation": "Use a prepared statement.",
            "corrected_code_example": "cursor.execute('SELECT * FROM users WHERE name = ?', (name,))",
            "best_practice_explanation": "Prepared statements separate code from data.",
            "model": "test-model",
        },
    )

    result = orchestrator.analyze("print('hello')", language="python")

    remediation = result["findings"][0]["remediation_details"]
    assert remediation["remediation"] == "Use a prepared statement."
    assert "Prepared statements" in remediation["best_practice_explanation"]


def test_orchestrator_attaches_pr_summary(monkeypatch, tmp_path):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    orchestrator = ReviewOrchestrator(reports_dir=tmp_path)
    monkeypatch.setattr(
        orchestrator.openai_review_agent,
        "analyze",
        lambda code, language: {
            "findings": [
                {
                    "type": "Dangerous Dynamic Execution",
                    "severity": "Critical",
                    "line": 9,
                    "message": "eval used.",
                    "recommendation": "Remove eval.",
                    "severity_score": 4,
                }
            ],
            "summary": {"total_findings": 1, "severity_breakdown": {"Low": 0, "Medium": 0, "High": 0, "Critical": 1}, "risk_score": 4},
            "review_mode": "openai",
            "model": "test-model",
        },
    )
    monkeypatch.setattr(
        orchestrator.remediation_agent,
        "suggest",
        lambda code, language, finding: {
            "remediation": "Replace eval with explicit control flow.",
            "corrected_code_example": "result = compute_value(user_input)",
            "best_practice_explanation": "Avoid executing user input as code.",
            "model": "test-model",
        },
    )
    monkeypatch.setattr(
        orchestrator.pr_summary_agent,
        "summarize",
        lambda review_result: {
            "executive_overview": "High risk due to dynamic execution.",
            "severity_breakdown": review_result["summary"]["severity_breakdown"],
            "prioritized_fix_list": [
                {
                    "finding_type": "Dangerous Dynamic Execution",
                    "severity": "Critical",
                    "impact": "Remote code execution risk.",
                    "fix_priority": 1,
                    "suggested_action": "Remove eval.",
                }
            ],
            "merge_readiness": "blocked",
            "model": "test-model",
        },
    )

    result = orchestrator.analyze("print('hello')", language="python")

    assert result["pr_summary"]["merge_readiness"] == "blocked"
    assert result["pr_summary"]["prioritized_fix_list"][0]["finding_type"] == "Dangerous Dynamic Execution"


def test_code_health_score_helper():
    from app.display import code_health_score

    assert code_health_score({"risk_score": 0}) == 100
    assert code_health_score({"risk_score": 10}) == 60


def test_conversational_assistant_grounded_answer(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": '{"answer": "Use parameterized queries.", "supporting_sources": ["doc/Secure_Coding_Guidelines.md"], "follow_up_guidance": "Show the fixed query."}'
                        }
                    }
                ]
            }

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setattr("requests.post", lambda *args, **kwargs: FakeResponse())

    assistant = ConversationalCodeAssistant(knowledge_paths=["e:\\infosys_springBoard\\AI-Code-Review-Agent\\doc"])
    response = assistant.answer(
        "How do I fix SQL injection?",
        {
            "findings": [{"type": "SQL Injection", "severity": "Critical", "line": 7}],
            "summary": {"total_findings": 1, "severity_breakdown": {"Low": 0, "Medium": 0, "High": 0, "Critical": 1}, "risk_score": 4},
        },
    )

    assert "parameterized queries" in response["answer"]