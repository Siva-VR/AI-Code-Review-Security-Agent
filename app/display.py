import streamlit as st


def code_health_score(summary):
	risk_score = summary.get("risk_score", 0) or 0
	return max(0, 100 - int(risk_score) * 4)


def render_metric(label, value, caption):
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


def render_finding(finding):
	severity = finding.get("severity", "Low")
	line = finding.get("line", "-")
	finding_type = finding.get("type", "Finding")
	message = finding.get("message", "")
	recommendation = finding.get("recommendation", "")
	remediation = finding.get("remediation_details", {}) or {}
	corrected_code = remediation.get("corrected_code_example", "")
	best_practice = remediation.get("best_practice_explanation", "")
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
	if remediation:
		st.markdown("#### Remediation")
		st.write(remediation.get("remediation", ""))
		if best_practice:
			st.info(best_practice, icon=":material/lightbulb:")
		if corrected_code:
			st.code(corrected_code, language="python")


def render_pr_summary(pr_summary):
	if not pr_summary:
		return
	st.markdown("### pull request summary")
	st.write(pr_summary.get("executive_overview", ""))
	st.caption(f"Merge readiness: {pr_summary.get('merge_readiness', 'unknown')}")
	priority_items = pr_summary.get("prioritized_fix_list", [])
	if priority_items:
		for item in priority_items:
			st.markdown(
				f"""
				<div class="finding-card">
					<div class="finding-top">
						<div>
							<div class="finding-type">{item.get('finding_type', 'Finding')}</div>
							<div class="finding-meta">Priority {item.get('fix_priority', 0)}</div>
						</div>
						<div class="finding-meta">Severity: {item.get('severity', 'Unknown')}</div>
					</div>
					<div class="finding-message">{item.get('impact', '')}</div>
					<div class="finding-reco"><strong>Suggested action:</strong> {item.get('suggested_action', '')}</div>
				</div>
				""",
				unsafe_allow_html=True,
			)


def render_review_display(result):
	summary = result.get("summary") if isinstance(result, dict) else {}
	if not isinstance(summary, dict):
		summary = {}
	severity_breakdown = summary.get("severity_breakdown") if isinstance(summary.get("severity_breakdown"), dict) else {}
	summary_total = summary.get("total_findings", 0)
	summary_risk = summary.get("risk_score", 0)
	findings = result["findings"]
	critical_count = sum(1 for item in findings if item.get("severity") == "Critical")
	high_count = sum(1 for item in findings if item.get("severity") == "High")
	medium_count = sum(1 for item in findings if item.get("severity") == "Medium")
	health_score = code_health_score(summary)

	st.space("small")
	left_summary, middle_summary, right_summary, health_summary = st.columns(4)
	with left_summary:
		render_metric("Total findings", str(summary_total), "Merged from Groq review output")
	with middle_summary:
		render_metric("Risk score", str(summary_risk), "Higher means more severe overall risk")
	with right_summary:
		render_metric("Critical / high", f"{critical_count} / {high_count}", f"{medium_count} medium findings")
	with health_summary:
		render_metric("Code health", f"{health_score}/100", "Higher means cleaner code")

	tab_overview, tab_findings, tab_pr, tab_raw = st.tabs(["overview", "findings", "pull request summary", "raw output"])

	with tab_overview:
		st.container(border=True)
		st.markdown("### severity breakdown")
		breakdown_col1, breakdown_col2, breakdown_col3, breakdown_col4 = st.columns(4)
		breakdown = severity_breakdown
		with breakdown_col1:
			render_metric("Critical", str(breakdown.get("Critical", 0)), "Highest priority")
		with breakdown_col2:
			render_metric("High", str(breakdown.get("High", 0)), "Fix soon")
		with breakdown_col3:
			render_metric("Medium", str(breakdown.get("Medium", 0)), "Refactor candidates")
		with breakdown_col4:
			render_metric("Low", str(breakdown.get("Low", 0)), "Minor issues")

		st.space("small")
		st.markdown("### review summary")
		st.write(
			"The review pipeline returns a structured set of findings and a summary from Groq. "
			"Each finding now includes remediation details and code examples, and the pull request tab groups them into a prioritized fix list."
		)

	with tab_findings:
		if findings:
			for finding in findings:
				render_finding(finding)
		else:
			st.info("No findings detected for this submission.", icon=":material/check_circle:")

	with tab_pr:
		render_pr_summary(result.get("pr_summary"))

	with tab_raw:
		st.dataframe(findings, width="stretch", hide_index=True)
		st.json(summary)