from datetime import datetime, timezone
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.pdfgen import canvas


def _safe_text(value):
	if value is None:
		return ""
	return str(value)


def _make_paragraph(text, style):
	return Paragraph(_safe_text(text).replace("\n", "<br/>") or "&nbsp;", style)


def _get_severity_color(severity):
	"""Return RGB hex color based on severity level."""
	severity_map = {
		"Critical": "#dc2626",
		"High": "#ea580c",
		"Medium": "#f59e0b",
		"Low": "#10b981",
	}
	return severity_map.get(severity, "#6b7280")


def _get_severity_badge(severity):
	"""Return colored badge HTML for severity."""
	color = _get_severity_color(severity)
	return f'<font color="{color}"><b>● {severity}</b></font>'


def export_review_pdf(code, language, result, output_path):
	output_path = Path(output_path)
	output_path.parent.mkdir(parents=True, exist_ok=True)

	summary = result.get("summary", {}) or {}
	findings = result.get("findings", []) or []
	pr_summary = result.get("pr_summary", {}) or {}
	severity_breakdown = summary.get("severity_breakdown", {}) or {}
	roadmap_items = pr_summary.get("prioritized_fix_list", []) or []
	health_score = max(0, 100 - int(summary.get("risk_score", 0) or 0) * 4)
	generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

	doc = SimpleDocTemplate(
		str(output_path),
		pagesize=A4,
		rightMargin=16 * mm,
		leftMargin=16 * mm,
		topMargin=16 * mm,
		bottomMargin=16 * mm,
	)
	styles = getSampleStyleSheet()
	
	# Enhanced styling
	title_style = ParagraphStyle(
		"TitleStyle",
		parent=styles["Heading1"],
		textColor=colors.HexColor("#0a1428"),
		fontSize=24,
		spaceAfter=6,
		fontName="Helvetica-Bold",
	)
	subtitle_style = ParagraphStyle(
		"SubtitleStyle",
		parent=styles["Normal"],
		textColor=colors.HexColor("#2563eb"),
		fontSize=14,
		spaceAfter=4,
		fontName="Helvetica-Bold",
	)
	section_style = ParagraphStyle(
		"SectionStyle",
		parent=styles["Heading2"],
		textColor=colors.HexColor("#0a1428"),
		fontSize=14,
		spaceBefore=10,
		spaceAfter=8,
		fontName="Helvetica-Bold",
		borderPadding=6,
	)
	metric_label_style = ParagraphStyle(
		"MetricLabel",
		parent=styles["Normal"],
		textColor=colors.HexColor("#556b82"),
		fontSize=9,
		spaceAfter=2,
	)
	metric_value_style = ParagraphStyle(
		"MetricValue",
		parent=styles["Normal"],
		textColor=colors.HexColor("#2563eb"),
		fontSize=16,
		fontName="Helvetica-Bold",
	)
	subtle_style = ParagraphStyle(
		"SubtleStyle",
		parent=styles["Normal"],
		textColor=colors.HexColor("#556b82"),
		fontSize=9,
		leading=12,
	)
	body_style = ParagraphStyle(
		"BodyStyle",
		parent=styles["Normal"],
		textColor=colors.HexColor("#1e3a5f"),
		fontSize=10,
		leading=14,
	)
	recommendation_style = ParagraphStyle(
		"RecommendationStyle",
		parent=styles["Normal"],
		textColor=colors.HexColor("#0a1428"),
		fontSize=9,
		leading=12,
		leftIndent=8,
	)

	story = []
	
	# Header Section
	story.append(Paragraph("🔒 AI Code Review & Security Analysis Report", title_style))
	story.append(Paragraph("Professional Code Quality & Security Assessment", subtitle_style))
	story.append(Spacer(1, 4))
	story.append(Paragraph(f"Generated: {generated_at} | Language: <b>{language}</b> | Model: <b>{result.get('model', 'Groq')}</b>", subtle_style))
	story.append(Spacer(1, 12))

	# Executive Summary Section
	story.append(Paragraph("📊 Executive Summary", section_style))
	
	metrics_data = [
		[
			Paragraph("Code Health Score", metric_label_style),
			Paragraph("Risk Score", metric_label_style),
			Paragraph("Total Findings", metric_label_style),
		],
		[
			Paragraph(f"{health_score}/100", metric_value_style),
			Paragraph(f"{summary.get('risk_score', 0)}", metric_value_style),
			Paragraph(f"{summary.get('total_findings', len(findings))}", metric_value_style),
		],
	]
	
	metrics_table = Table(metrics_data, colWidths=[50 * mm, 50 * mm, 50 * mm])
	metrics_table.setStyle(TableStyle([
		("ALIGN", (0, 0), (-1, -1), "CENTER"),
		("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
		("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef5ff")),
		("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#f7fafc")),
		("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#d4e3f5")),
		("FONTSIZE", (0, 0), (-1, 1), 10),
		("TOPPADDING", (0, 0), (-1, -1), 8),
		("BOTTOMPADDING", (0, 0), (-1, -1), 8),
	]))
	story.append(metrics_table)
	story.append(Spacer(1, 8))
	
	story.append(Paragraph("Merge Readiness: <b>{}</b>".format(pr_summary.get('merge_readiness', 'Unknown')), body_style))
	story.append(Spacer(1, 6))
	story.append(_make_paragraph(pr_summary.get("executive_overview") or summary.get("overview") or "No overview available.", body_style))
	story.append(Spacer(1, 10))

	# Severity Breakdown Section
	story.append(Paragraph("⚠️ Severity Breakdown", section_style))
	
	severity_data = [
		[
			Paragraph("Critical", metric_label_style),
			Paragraph("High", metric_label_style),
			Paragraph("Medium", metric_label_style),
			Paragraph("Low", metric_label_style),
		],
		[
			Paragraph(f"<font color='#dc2626'><b>{severity_breakdown.get('Critical', 0)}</b></font>", metric_value_style),
			Paragraph(f"<font color='#ea580c'><b>{severity_breakdown.get('High', 0)}</b></font>", metric_value_style),
			Paragraph(f"<font color='#f59e0b'><b>{severity_breakdown.get('Medium', 0)}</b></font>", metric_value_style),
			Paragraph(f"<font color='#10b981'><b>{severity_breakdown.get('Low', 0)}</b></font>", metric_value_style),
		],
	]
	
	severity_table = Table(severity_data, colWidths=[45 * mm, 45 * mm, 45 * mm, 45 * mm])
	severity_table.setStyle(TableStyle([
		("ALIGN", (0, 0), (-1, -1), "CENTER"),
		("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
		("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fef2f2")),
		("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#fffbeb")),
		("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#fee2e2")),
		("TOPPADDING", (0, 0), (-1, -1), 6),
		("BOTTOMPADDING", (0, 0), (-1, -1), 6),
	]))
	story.append(severity_table)
	story.append(Spacer(1, 12))

	# Detailed Findings Section
	if findings:
		story.append(Paragraph("🔍 Detailed Findings", section_style))
		
		findings_table = [[
			Paragraph("<b>Type</b>", metric_label_style),
			Paragraph("<b>Severity</b>", metric_label_style),
			Paragraph("<b>Line</b>", metric_label_style),
			Paragraph("<b>Message</b>", metric_label_style),
			Paragraph("<b>Recommendation</b>", metric_label_style),
		]]
		
		for idx, finding in enumerate(findings, 1):
			severity = finding.get("severity", "Low")
			bg_color = {
				"Critical": colors.HexColor("#fecaca"),
				"High": colors.HexColor("#fdba74"),
				"Medium": colors.HexColor("#fcd34d"),
				"Low": colors.HexColor("#bbf7d0"),
			}.get(severity, colors.HexColor("#f3f4f6"))
			
			findings_table.append([
				_make_paragraph(f"{idx}. {finding.get('type', 'Finding')}", body_style),
				Paragraph(_get_severity_badge(severity), body_style),
				Paragraph(str(finding.get("line", "-")), body_style),
				_make_paragraph(finding.get("message", ""), body_style),
				_make_paragraph(finding.get("recommendation", ""), recommendation_style),
			])

		findings_table_style = TableStyle([
			("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f5fb")),
			("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0a1428")),
			("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dbe4f0")),
			("VALIGN", (0, 0), (-1, -1), "TOP"),
			("FONTSIZE", (0, 0), (-1, -1), 8.5),
			("LEADING", (0, 0), (-1, -1), 11),
			("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#fafbfc"), colors.HexColor("#f7fafc")]),
			("LEFTPADDING", (0, 0), (-1, -1), 6),
			("RIGHTPADDING", (0, 0), (-1, -1), 6),
			("TOPPADDING", (0, 0), (-1, -1), 5),
			("BOTTOMPADDING", (0, 0), (-1, -1), 5),
		])
		
		story.append(Table(findings_table, repeatRows=1, colWidths=[25 * mm, 20 * mm, 12 * mm, 50 * mm, 63 * mm], style=findings_table_style))
		story.append(Spacer(1, 12))

	# Remediation Roadmap Section
	if roadmap_items:
		story.append(PageBreak())
		story.append(Paragraph("🛠️ Remediation Roadmap", section_style))
		story.append(Paragraph("Priority-based action items to improve code quality and security", subtle_style))
		story.append(Spacer(1, 8))
		
		roadmap_table = [[
			Paragraph("<b>Priority</b>", metric_label_style),
			Paragraph("<b>Finding Type</b>", metric_label_style),
			Paragraph("<b>Severity</b>", metric_label_style),
			Paragraph("<b>Impact</b>", metric_label_style),
			Paragraph("<b>Suggested Action</b>", metric_label_style),
		]]
		
		for idx, item in enumerate(roadmap_items, 1):
			severity = item.get("severity", "Unknown")
			roadmap_table.append([
				Paragraph(f"<b>#{idx}</b>", body_style),
				_make_paragraph(item.get("finding_type", "Finding"), body_style),
				Paragraph(_get_severity_badge(severity), body_style),
				_make_paragraph(item.get("impact", ""), body_style),
				_make_paragraph(item.get("suggested_action", ""), recommendation_style),
			])

		roadmap_style = TableStyle([
			("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f5fb")),
			("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dbe4f0")),
			("VALIGN", (0, 0), (-1, -1), "TOP"),
			("FONTSIZE", (0, 0), (-1, -1), 8.5),
			("LEADING", (0, 0), (-1, -1), 11),
			("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#fafbfc"), colors.HexColor("#f7fafc")]),
			("LEFTPADDING", (0, 0), (-1, -1), 6),
			("RIGHTPADDING", (0, 0), (-1, -1), 6),
			("TOPPADDING", (0, 0), (-1, -1), 5),
			("BOTTOMPADDING", (0, 0), (-1, -1), 5),
		])
		story.append(Table(roadmap_table, repeatRows=1, colWidths=[12 * mm, 30 * mm, 20 * mm, 45 * mm, 73 * mm], style=roadmap_style))
		story.append(Spacer(1, 12))

	# Key Recommendations Section
	story.append(Paragraph("💡 Key Recommendations", section_style))
	recommendations = [
		pr_summary.get("key_recommendations", ""),
		"Address all Critical and High severity findings before merging.",
		"Run additional security scanning tools to complement this analysis.",
		"Consider implementing automated testing to catch similar issues in the future."
	]
	for i, rec in enumerate([r for r in recommendations if r], 1):
		story.append(Paragraph(f"{i}. {rec}", recommendation_style))
		story.append(Spacer(1, 4))
	story.append(Spacer(1, 10))

	# Code Quality Metrics Section
	story.append(Paragraph("📈 Code Quality Metrics", section_style))
	quality_metrics = [
		("Overall Health Score", f"{health_score}/100"),
		("Risk Level", summary.get("risk_level", "Unknown")),
		("Maintainability", summary.get("maintainability", "N/A")),
		("Security Score", summary.get("security_score", "N/A")),
	]
	
	for label, value in quality_metrics:
		story.append(Paragraph(f"<b>{label}:</b> {value}", body_style))
		story.append(Spacer(1, 3))
	story.append(Spacer(1, 10))

	# Source Code Snapshot Section (on new page)
	story.append(PageBreak())
	story.append(Paragraph("📝 Source Code Snapshot", section_style))
	code_preview = _safe_text(code)
	if len(code_preview) > 3000:
		code_preview = code_preview[:3000] + "\n\n... [Code truncated for brevity] ..."
	
	code_display = code_preview.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
	story.append(_make_paragraph(f"<font name='Courier' size='8'>{code_display}</font>", body_style))
	story.append(Spacer(1, 12))

	# Footer Section
	story.append(Spacer(1, 10))
	story.append(Paragraph("─" * 80, subtle_style))
	story.append(Paragraph("This report was generated by the AI Code Review & Security Analysis Agent. Review all findings carefully before implementing changes.", subtle_style))
	story.append(Paragraph(f"Report generated on {generated_at}", subtle_style))

	doc.build(story)
	return str(output_path)
