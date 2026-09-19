from pathlib import Path
import sys
from datetime import datetime

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from agent.orchestrator import ReviewOrchestrator
from agent.openai_review_agent import OpenAIReviewAgent
from app.assistant_panel import render_assistant_panel
from app.config import APP_NAME
from app.display import render_review_display
from app.upload import load_uploaded_file
from app.validator import infer_language_from_code, validate_submission


def _inject_styles():
	st.markdown(
		"""
		<style>
			:root {
				--bg: #f0f5fb;
				--bg-strong: #e3edf8;
				--surface: #ffffff;
				--surface-alt: #f7fafc;
				--surface-soft: #eef5ff;
				--nav-bg: rgba(250, 252, 255, 0.96);
				--panel-border: rgba(37, 99, 235, 0.12);
				--line: rgba(15, 23, 42, 0.08);
				--heading: #0a1428;
				--text: #1e3a5f;
				--muted: #556b82;
				--primary: #2563eb;
				--primary-strong: #1d4ed8;
				--primary-light: #3b82f6;
				--secondary: #0891b2;
				--highlight: #f59e0b;
				--success: #059669;
				--shadow-soft: 0 12px 28px rgba(15, 23, 42, 0.07);
				--shadow-strong: 0 22px 44px rgba(37, 99, 235, 0.14);
			}
			html, body {
				background:
					radial-gradient(circle at top left, rgba(37, 99, 235, 0.12), transparent 18%),
					radial-gradient(circle at bottom right, rgba(8, 145, 178, 0.08), transparent 22%),
					linear-gradient(180deg, #f5f9fc 0%, #f0f5fb 40%, #f8fafb 100%);
				color: var(--heading);
				font-family: "Segoe UI", "Inter", "Arial", sans-serif;
			}
			body::before {
				content: "";
				position: fixed;
				inset: 0;
				background: linear-gradient(180deg, rgba(255,255,255,0.28), transparent 18%, rgba(148,163,184,0.04));
				pointer-events: none;
			}
			.block-container {
				padding-top: 1.2rem;
				padding-bottom: 2.5rem;
				max-width: 1380px;
			}
			[data-testid="stAppViewContainer"] {
				background: transparent;
			}
			[data-testid="stHeader"] {
				background: transparent;
				height: 0;
			}
			div[data-testid="stSidebar"] {
				background: linear-gradient(180deg, rgba(250, 252, 255, 0.98), rgba(237, 245, 248, 0.96));
				border-right: 2px solid rgba(37, 99, 235, 0.08);
				box-shadow: inset -1px 0 0 rgba(255,255,255,0.7), 12px 0 30px rgba(37, 99, 235, 0.06);
				backdrop-filter: blur(14px);
			}
			section[data-testid="stSidebarContent"] {
				padding: 1rem 0.7rem 1.2rem;
			}
			.sidebar-shell {
				background: linear-gradient(135deg, rgba(255,255,255,0.88), rgba(240, 249, 255, 0.85));
				border: 1.5px solid rgba(37, 99, 235, 0.10);
				border-radius: 24px;
				padding: 0.8rem;
				box-shadow: 0 12px 32px rgba(37, 99, 235, 0.08);
			}
			.sidebar-brand {
				display: flex;
				align-items: center;
				gap: 0.72rem;
				padding: 0.95rem 1rem;
				border-radius: 18px;
				background: linear-gradient(135deg, rgba(37, 99, 235, 0.12), rgba(8, 145, 178, 0.08));
				border: 1.5px solid rgba(37, 99, 235, 0.14);
				color: var(--heading);
				font-size: 1.08rem;
				font-weight: 900;
				letter-spacing: -0.03em;
				margin-bottom: 0.95rem;
			}
			.brand-icon {
				display: inline-flex;
				align-items: center;
				justify-content: center;
				width: 34px;
				height: 34px;
				border-radius: 12px;
				background: linear-gradient(135deg, #1d4ed8, #2563eb);
				color: #ffffff;
				font-size: 0.76rem;
				font-weight: 900;
				box-shadow: 0 8px 20px rgba(37, 99, 235, 0.22);
			}
			.sidebar-nav {
				display: flex;
				flex-direction: column;
				gap: 0.56rem;
				margin-top: 0.3rem;
			}
			.sidebar-item {
				display: flex;
				align-items: center;
				gap: 0.72rem;
				padding: 0.82rem 0.95rem;
				border-radius: 13px;
				background: rgba(255,255,255,0.75);
				border: 1px solid rgba(37, 99, 235, 0.06);
				color: var(--text);
				font-size: 0.92rem;
				font-weight: 700;
				letter-spacing: 0.01em;
				transition: all 0.22s ease;
				box-shadow: inset 0 1px 0 rgba(255,255,255,0.8);
			}
			.sidebar-item.active {
				background: linear-gradient(135deg, rgba(37, 99, 235, 0.10), rgba(8, 145, 178, 0.06));
				border-color: rgba(37, 99, 235, 0.20);
				color: var(--heading);
				box-shadow: 0 12px 20px rgba(37, 99, 235, 0.10);
			}
			.sidebar-item:hover {
				transform: translateX(2px);
				border-color: rgba(79, 70, 229, 0.12);
			}
			.sidebar-dot {
				display: inline-block;
				width: 8px;
				height: 8px;
				border-radius: 50%;
				background: linear-gradient(135deg, var(--primary), var(--secondary));
				box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.07);
			}
			.sidebar-label {
				font-size: 0.7rem;
				letter-spacing: 0.12em;
				text-transform: uppercase;
				color: var(--muted);
				margin: 1rem 0 0.7rem 0.45rem;
				font-weight: 800;
				position: relative;
				padding-left: 0.7rem;
			}
			.sidebar-label::before {
				content: "";
				position: absolute;
				left: 0;
				top: 50%;
				transform: translateY(-50%);
				width: 6px;
				height: 6px;
				border-radius: 50%;
				background: linear-gradient(135deg, var(--primary), var(--secondary));
				box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.06);
			}
			.sidebar-card {
				padding: 0.8rem 0.9rem;
				border-radius: 15px;
				background: linear-gradient(180deg, rgba(255,255,255,0.92), rgba(244,248,255,0.88));
				border: 1px solid rgba(15, 23, 42, 0.06);
				margin-bottom: 0.7rem;
				box-shadow: var(--shadow-soft);
			}
			.sidebar-card.primary {
				background: linear-gradient(135deg, rgba(79, 70, 229, 0.09), rgba(20, 184, 166, 0.05));
				border-color: rgba(79, 70, 229, 0.12);
			}
			.sidebar-card .card-label {
				font-size: 0.7rem;
				letter-spacing: 0.12em;
				text-transform: uppercase;
				color: var(--muted);
				margin-bottom: 0.35rem;
				font-weight: 800;
			}
			.sidebar-card .card-value {
				font-size: 0.96rem;
				font-weight: 700;
				color: var(--heading);
				line-height: 1.45;
			}
			.hero {
				padding: 1.8rem 1.7rem 1.4rem;
				border-radius: 28px;
				border: 1.2px solid rgba(37, 99, 235, 0.12);
				background: linear-gradient(135deg, rgba(255,255,255,0.96), rgba(240, 249, 255, 0.94));
				box-shadow: 0 26px 50px rgba(37, 99, 235, 0.08), inset 0 1px 0 rgba(255,255,255,0.7);
				margin-bottom: 1rem;
				position: relative;
				overflow: hidden;
			}
			.hero::before {
				content: "";
				position: absolute;
				right: -35px;
				top: -55px;
				width: 280px;
				height: 280px;
				border-radius: 50%;
				background: radial-gradient(circle, rgba(37, 99, 235, 0.14), transparent 66%);
				pointer-events: none;
			}
			.hero::after {
				content: "";
				position: absolute;
				left: 0;
				right: 0;
				top: 0;
				height: 4px;
				background: linear-gradient(90deg, #2563eb 0%, #0891b2 100%);
				pointer-events: none;
			}
			.hero .title-row {
				display: flex;
				align-items: center;
				gap: 0.75rem;
				margin-bottom: 0.65rem;
			}
			.hero .eyebrow {
				display: inline-flex;
				align-items: center;
				gap: 0.5rem;
				padding: 0.44rem 0.76rem;
				border-radius: 999px;
				font-size: 0.67rem;
				font-weight: 800;
				letter-spacing: 0.13em;
				text-transform: uppercase;
				background: rgba(37, 99, 235, 0.08);
				border: 1.2px solid rgba(37, 99, 235, 0.12);
				color: #1d4ed8;
			}
			.hero .eyebrow::before {
				content: "";
				width: 7px;
				height: 7px;
				border-radius: 50%;
				background: linear-gradient(135deg, #2563eb, #0891b2);
				box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.08);
			}
			.hero h1 {
				margin: 0 0 0.65rem 0;
				font-size: clamp(2.2rem, 3vw, 3.3rem);
				font-weight: 800;
				letter-spacing: -0.05em;
				color: var(--heading);
				line-height: 1.05;
			}
			h3 {
				color: var(--heading) !important;
				font-size: 1.08rem !important;
				font-weight: 800 !important;
				letter-spacing: -0.02em !important;
				margin-bottom: 0.5rem !important;
			}
			.stMetric {
				background: rgba(255,255,255,0.7);
				border-radius: 14px;
				padding: 0.22rem 0.4rem;
			}
			.hero .subtitle {
				margin: 0;
				color: var(--text);
				font-size: 1.02rem;
				line-height: 1.7;
				max-width: 920px;
				font-weight: 500;
			}
			.status-strip {
				display: flex;
				gap: 0.6rem;
				flex-wrap: wrap;
				margin-top: 1rem;
			}
			.status-chip {
				font-size: 0.67rem;
				letter-spacing: 0.12em;
				text-transform: uppercase;
				padding: 0.48rem 0.85rem;
				border-radius: 999px;
				background: rgba(37, 99, 235, 0.07);
				border: 1.2px solid rgba(37, 99, 235, 0.12);
				color: #1d4ed8;
				font-weight: 800;
			}
			.metric-card {
				padding: 1.15rem 1.05rem 1rem 1.05rem;
				border-radius: 20px;
				border: 1.2px solid rgba(37, 99, 235, 0.08);
				background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(240, 249, 255, 0.92));
				box-shadow: var(--shadow-soft);
				height: 100%;
				position: relative;
				overflow: hidden;
				transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
			}
			.metric-card::before {
				content: "";
				position: absolute;
				top: 0;
				left: 0;
				right: 0;
				height: 4px;
				background: linear-gradient(90deg, #2563eb 0%, #0891b2 100%);
			}
			.metric-card:hover {
				transform: translateY(-2px);
				box-shadow: var(--shadow-strong);
				border-color: rgba(37, 99, 235, 0.12);
			}
			.metric-label {
				color: var(--muted);
				font-size: 0.7rem;
				letter-spacing: 0.12em;
				text-transform: uppercase;
				margin-bottom: 0.5rem;
				font-weight: 800;
			}
			.metric-value {
				font-size: 1.82rem;
				font-weight: 800;
				color: var(--heading);
				line-height: 1.2;
				letter-spacing: -0.04em;
			}
			.metric-caption {
				color: var(--muted);
				font-size: 0.88rem;
				margin-top: 0.42rem;
				line-height: 1.5;
			}
			.finding-card {
				padding: 1rem 1rem 0.9rem 1rem;
				border-radius: 16px;
				background: linear-gradient(180deg, rgba(255,255,255,0.94), rgba(244,247,255,0.9));
				border: 1px solid rgba(15, 23, 42, 0.06);
				box-shadow: var(--shadow-soft);
				border-left: 4px solid var(--primary);
				margin-bottom: 0.85rem;
				transition: transform 0.2s ease, box-shadow 0.2s ease;
			}
			.finding-card:hover {
				transform: translateY(-1px);
				box-shadow: 0 12px 24px rgba(15, 23, 42, 0.06);
			}
			.finding-top {
				display: flex;
				justify-content: space-between;
				gap: 0.8rem;
				align-items: center;
				margin-bottom: 0.6rem;
			}
			.finding-type {
				font-weight: 700;
				color: var(--heading);
				font-size: 1rem;
			}
			.finding-meta {
				color: var(--muted);
				font-size: 0.8rem;
				font-weight: 700;
			}
			.finding-message {
				color: var(--text);
				margin: 0.45rem 0 0.7rem 0;
				line-height: 1.7;
			}
			.finding-reco {
				padding: 0.8rem 0.9rem;
				border-radius: 12px;
				background: rgba(79, 70, 229, 0.04);
				border: 1px solid rgba(79, 70, 229, 0.10);
				color: var(--text);
				line-height: 1.6;
			}
			.code-panel {
				border-radius: 12px;
				border: 1px solid rgba(15, 23, 42, 0.06);
				background: #f8fafc;
				padding: 1rem;
			}
			[data-testid="stCodeBlock"] {
				background: #f8fafc !important;
				border: 1px solid rgba(15, 23, 42, 0.06);
				border-radius: 10px;
			}
			.stButton > button {
				border-radius: 13px;
				background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
				border: 1.2px solid rgba(37, 99, 235, 0.10);
				color: #ffffff;
				font-weight: 800;
				padding: 0.82rem 1.4rem;
				box-shadow: 0 14px 24px rgba(37, 99, 235, 0.20);
				transition: transform 0.22s ease, box-shadow 0.22s ease, filter 0.22s ease;
			}
			.stButton > button:hover {
				background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
				transform: translateY(-2px);
				box-shadow: 0 18px 28px rgba(37, 99, 235, 0.26);
			}
			button[kind="primary"] {
				height: 46px;
			}
			[data-testid="stForm"] {
				background: rgba(255,255,255,0.78);
				border: 1px solid rgba(15, 23, 42, 0.06);
				border-radius: 16px;
				padding: 0.55rem;
				backdrop-filter: blur(8px);
			}
			div[data-testid="stVerticalBlockBorderWrapper"] {
				background: linear-gradient(180deg, rgba(255,255,255,0.9), rgba(244,247,255,0.86));
				border: 1px solid rgba(15, 23, 42, 0.06);
				border-radius: 18px;
				padding: 0.9rem 0.95rem;
				box-shadow: var(--shadow-soft);
			}
			div[data-testid="stVerticalBlockBorderWrapper"] h3 {
				color: var(--heading) !important;
				margin-top: 0;
				margin-bottom: 0.55rem !important;
			}
			div[data-testid="stVerticalBlock"] > div {
				gap: 0.85rem !important;
			}
			div[data-testid="stVerticalBlock"] [data-testid="stBaseButton-secondary"] {
				margin-top: 0.25rem;
			}
			[data-testid="stSegmentedControl"] {
				background: rgba(255,255,255,0.72);
				border: 1px solid rgba(15, 23, 42, 0.06);
				border-radius: 12px;
				padding: 0.2rem;
			}
			[data-testid="stSegmentedControl"] div[role="tablist"] {
				background: transparent;
				border: none;
			}
			[data-testid="stSegmentedControl"] button[role="tab"] {
				color: var(--muted);
				font-weight: 700;
			}
			textarea, input, [data-testid="stTextInput"], div[data-baseweb="select"] {
				border-radius: 12px !important;
				background: rgba(255,255,255,0.9) !important;
				color: var(--heading) !important;
				border: 1px solid rgba(79, 70, 229, 0.12) !important;
				box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.02);
			}
			textarea:focus, input:focus {
				border-color: rgba(79, 70, 229, 0.42) !important;
				box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.08) !important;
			}
			.stTextArea textarea {
				line-height: 1.5 !important;
			}
			div[role="tablist"] {
				background: rgba(255,255,255,0.8);
				border-radius: 14px;
				padding: 5px;
				border: 1px solid rgba(15, 23, 42, 0.06);
				box-shadow: inset 0 1px 0 rgba(255,255,255,0.45);
			}
			button[role="tab"] {
				border-radius: 10px;
				color: var(--muted);
				text-transform: uppercase;
				letter-spacing: 0.07em;
				font-weight: 800;
				padding: 0.6rem 1rem;
			}
			button[role="tab"][aria-selected="true"] {
				background: linear-gradient(180deg, rgba(79, 70, 229, 0.08), rgba(79, 70, 229, 0.03));
				color: var(--heading);
				border: 1px solid rgba(79, 70, 229, 0.12);
				box-shadow: inset 0 1px 0 rgba(255,255,255,0.35);
			}
			.stAlert {
				border-radius: 13px;
				border: 1.2px solid rgba(37, 99, 235, 0.12);
				background: rgba(255,255,255,0.74);
			}
			.download-section {
				padding: 1.2rem 1.3rem;
				border-radius: 18px;
				background: linear-gradient(135deg, rgba(37, 99, 235, 0.08), rgba(8, 145, 178, 0.05));
				border: 1.5px solid rgba(37, 99, 235, 0.12);
				box-shadow: 0 12px 28px rgba(15, 23, 42, 0.07);
			}
			.download-label {
				font-size: 0.75rem;
				letter-spacing: 0.13em;
				text-transform: uppercase;
				color: #556b82;
				font-weight: 800;
				margin-bottom: 0.65rem;
			}
			.assistant-dock {
				position: sticky;
				top: 1rem;
			}
			[data-testid="stDataFrame"] {
				border-radius: 14px;
				border: 1px solid rgba(15, 23, 42, 0.06);
				overflow: hidden;
			}
			[data-testid="stVerticalBlock"] > div:has(.metric-card) {
				gap: 0.8rem;
			}
			[data-testid="stMetricLabel"], [data-testid="stMetricValue"] {
				color: var(--heading) !important;
			}
			@media (max-width: 900px) {
				.hero {
					padding: 1.15rem;
				}
				.hero h1 {
					font-size: 1.8rem;
				}
				.metric-value {
					font-size: 1.45rem;
				}
				.status-chip {
					font-size: 0.62rem;
					letter-spacing: 0.1em;
				}
				.assistant-dock {
					position: static;
				}
			}
		</style>
		""",
		unsafe_allow_html=True,
	)
def _load_sample_code(language):
	base_dir = Path(__file__).resolve().parents[1]
	sample_map = {
		"python": base_dir / "sample_code" / "python" / "vulnerable_security.py",
		"java": base_dir / "sample_code" / "java" / "vulnerable_security.java",
	}
	sample_path = sample_map.get(language)
	if sample_path and sample_path.exists():
		return sample_path.read_text(encoding="utf-8")
	return ""


def _format_badge(language):
	if language == "java":
		return ":blue-badge[Java detected]"
	if language == "python":
		return ":green-badge[Python detected]"
	return ":orange-badge[Language not detected]"


def _render_metric(label, value, caption):
	st.markdown(
		f"""
		<div class="metric-card">
			<div class="metric-label">{label}</div>
			<div class="metric-value">{value}</div>
			<div class="metric-caption">{caption}</div>
		</div>
		""",
		unsafe_allow_html=True,
	)


def _render_finding(finding):
	severity = finding.get("severity", "Low")
	line = finding.get("line", "-")
	finding_type = finding.get("type", "Finding")
	message = finding.get("message", "")
	recommendation = finding.get("recommendation", "")
	st.markdown(
		f"""
		<div class="finding-card">
			<div class="finding-top">
				<div>
					<div class="finding-type">{finding_type}</div>
					<div class="finding-meta">Line {line}</div>
				</div>
				<div class="finding-meta">Severity: {severity} · Score: {finding.get('severity_score', 1)}</div>
			</div>
			<div class="finding-message">{message}</div>
			<div class="finding-reco"><strong>Recommendation:</strong> {recommendation}</div>
		</div>
		""",
		unsafe_allow_html=True,
	)


def main():
	st.set_page_config(page_title=APP_NAME, page_icon=":material/verified_user:", layout="wide")
	_inject_styles()

	with st.sidebar:
		st.markdown(
			"""
			<div class="sidebar-shell">
				<div class="sidebar-brand"><span class="brand-icon">A</span> AppSec AI</div>
				<div class="sidebar-nav">
					<div class="sidebar-item active"><span class="sidebar-dot"></span>Overview</div>
					<div class="sidebar-item"><span class="sidebar-dot"></span>Review workspace</div>
					<div class="sidebar-item"><span class="sidebar-dot"></span>Security findings</div>
					<div class="sidebar-item"><span class="sidebar-dot"></span>Reports</div>
					<div class="sidebar-item"><span class="sidebar-dot"></span>Audit trail</div>
				</div>
				<div class="sidebar-label">Workspace</div>
				<div class="sidebar-card primary">
					<div class="card-label">System</div>
					<div class="card-value">Code review & security</div>
				</div>
				<div class="sidebar-card">
					<div class="card-label">Mode</div>
					<div class="card-value">Analyze source files</div>
				</div>
			</div>
			""",
			unsafe_allow_html=True,
		)
		st.space("small")
		mode = st.segmented_control(
			"Input mode",
			["Paste code", "Upload file"],
			default="Paste code",
		)
		st.caption("The app auto-detects Python or Java from the code or file extension.")

	st.markdown(
		"""
		<div class="hero">
			<div class="title-row">
				<span class="eyebrow">Security intelligence</span>
			</div>
			<h1>AI Code Review & Security Analysis Agent</h1>
			<p class="subtitle">
				Paste Python or Java code, upload a source file, and the app will detect the language automatically,
				run Groq model-backed analysis, and present a structured review with line-level findings.
			</p>
			<div class="status-strip">
				<span class="status-chip">Threat Matrix Armed</span>
				<span class="status-chip">Hybrid Engine Online</span>
				<span class="status-chip">Executive Report Active</span>
			</div>
		</div>
		""",
		unsafe_allow_html=True,
	)

	st.space("small")
	col1, col2, col3 = st.columns(3)
	with col1:
		_render_metric("Supported languages", "2", "Python and Java submissions")
	with col2:
		_render_metric("Review pipeline", "Groq", "Requires GROQ_API_KEY")
	with col3:
		_render_metric("Output", "Findings + summary", "Severity-ranked review output")

	st.space("small")

	input_container = st.container(border=True)
	with input_container:
		left, right = st.columns([3, 1], vertical_alignment="bottom")
		with left:
			if mode == "Upload file":
				uploaded_file = st.file_uploader("Upload a Python or Java file", type=["py", "python", "java"], label_visibility="visible")
				default_code = ""
				if uploaded_file is not None:
					loaded = load_uploaded_file(uploaded_file)
					default_code = loaded["code"]
					detected_language = loaded["language"] or infer_language_from_code(default_code, loaded["filename"])
				else:
					detected_language = None
			else:
				uploaded_file = None
				python_example = _load_sample_code("python")
				java_example = _load_sample_code("java")
				example_choice = st.pills(
					"Quick samples",
					["Use Python sample", "Use Java sample", "Start blank"],
					label_visibility="visible",
					selection_mode="single",
					default="Use Python sample",
				)
				if example_choice == "Use Java sample":
					default_code = java_example
				elif example_choice == "Start blank":
					default_code = ""
				else:
					default_code = python_example
				detected_language = infer_language_from_code(default_code)
			code = st.text_area(
				"Paste or edit code",
				value=default_code,
				height=320,
				placeholder="Paste Python or Java source code here...",
			)
		with right:
			st.markdown("### detected")
			st.markdown(_format_badge(detected_language), unsafe_allow_html=True)
			if detected_language == "java":
				st.caption("Java markers, class syntax, and brace structure were detected.")
			elif detected_language == "python":
				st.caption("Python syntax or Python keywords were detected.")
			else:
				st.caption("Detection will fall back to filename or explicit syntax validation.")
			analyze_clicked = st.button("Analyze code", type="primary", icon=":material/analytics:", width="stretch")

	if "analysis_result" not in st.session_state:
		st.session_state.analysis_result = None
	if "submission_state" not in st.session_state:
		st.session_state.submission_state = None

	if analyze_clicked:
		if uploaded_file is not None:
			filename = uploaded_file.name
		elif detected_language == "python":
			filename = "submission.py"
		elif detected_language == "java":
			filename = "submission.java"
		else:
			filename = "submission.txt"
		language = detected_language or infer_language_from_code(code, filename)
		submission = {
			"filename": filename,
			"language": language,
			"code": code,
			"validation": validate_submission(filename, code),
		}
		st.session_state.submission_state = submission
		if submission["validation"]["valid"]:
			orchestrator = ReviewOrchestrator()
			st.session_state.analysis_result = orchestrator.analyze(code, language=language or "python")
		else:
			st.session_state.analysis_result = None

	submission = st.session_state.submission_state
	result = st.session_state.analysis_result

	if submission:
		st.space("small")
		with st.container(border=True):
			st.markdown("### submission status")
			status_col1, status_col2, status_col3 = st.columns(3)
			with status_col1:
				st.metric("File", submission["filename"])
			with status_col2:
				st.metric("Detected language", submission.get("language") or "unknown")
			with status_col3:
				st.metric("Validation", "passed" if submission["validation"]["valid"] else "failed")
			if submission["validation"]["valid"]:
				st.success(submission["validation"]["message"], icon=":material/check_circle:")
			else:
				st.error(submission["validation"]["message"], icon=":material/error:")

	if result:
		review_col, assistant_col = st.columns([1.65, 1], gap="large")
		with review_col:
			render_review_display(result)
			pdf_path = result.get("pdf_report_path")

			# Download section
			if pdf_path:
				st.space("small")
				st.markdown(
					"""
					<div class="download-section">
						<div class="download-label">📥 Download Report</div>
					</div>
					""",
					unsafe_allow_html=True,
				)
				try:
					with open(pdf_path, "rb") as pdf_file:
						pdf_bytes = pdf_file.read()
						st.download_button(
							label="⬇️ Download PDF Report",
							data=pdf_bytes,
							file_name=f"code_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
							mime="application/pdf",
						)
				except Exception as e:
					st.warning(f"Could not load PDF for download: {str(e)}")

		with assistant_col:
			st.markdown('<div class="assistant-dock">', unsafe_allow_html=True)
			st.markdown("#### :material/smart_toy: Assistant")
			render_assistant_panel(result)
			st.markdown("</div>", unsafe_allow_html=True)

	elif submission and not submission["validation"]["valid"]:
		st.warning("Fix the validation issue above and run analysis again.", icon=":material/warning:")


if __name__ == "__main__":
	main()


	