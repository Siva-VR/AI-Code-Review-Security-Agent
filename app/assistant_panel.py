import streamlit as st

from agent.conversational_assistant import ConversationalCodeAssistant


SUGGESTED_PROMPTS = {
	"Explain the highest-risk finding": "Explain the highest-risk finding and how to fix it safely.",
	"Show secure coding alternatives": "Show secure coding alternatives for the flagged issues in this review.",
	"Create a fix order": "Create a prioritized fix order based on severity and exploitability.",
	"Write a PR comment": "Draft a concise pull request comment summarizing the key security fixes.",
}


def _inject_assistant_styles():
	st.markdown(
		"""
		<style>
			.assistant-shell {
				position: relative;
				border-radius: 22px;
				padding: 1rem;
				margin-top: 0.4rem;
				background:
					radial-gradient(circle at top right, rgba(37,99,235,0.12), transparent 45%),
					linear-gradient(165deg, rgba(255,255,255,0.97), rgba(243,249,255,0.95));
				border: 1px solid rgba(37, 99, 235, 0.14);
				box-shadow: 0 22px 42px rgba(14, 33, 69, 0.08);
				overflow: hidden;
			}
			.assistant-shell::before {
				content: "";
				position: absolute;
				inset: 0;
				background: repeating-linear-gradient(
					135deg,
					rgba(37, 99, 235, 0.02) 0,
					rgba(37, 99, 235, 0.02) 8px,
					transparent 8px,
					transparent 16px
				);
				pointer-events: none;
			}
			.assistant-header {
				display: flex;
				align-items: flex-start;
				justify-content: space-between;
				gap: 1rem;
				padding: 0.25rem 0.2rem 0.9rem;
				position: relative;
				z-index: 2;
			}
			.assistant-brand {
				display: flex;
				align-items: center;
				gap: 0.75rem;
			}
			.assistant-icon {
				display: inline-flex;
				align-items: center;
				justify-content: center;
				width: 40px;
				height: 40px;
				border-radius: 12px;
				background: linear-gradient(145deg, #0f172a, #2563eb);
				color: #ffffff;
				font-weight: 800;
				font-size: 0.74rem;
				letter-spacing: 0.08em;
				box-shadow: 0 12px 22px rgba(37, 99, 235, 0.22);
			}
			.assistant-title {
				font-size: 1.05rem;
				font-weight: 800;
				color: #0f172a;
				line-height: 1.2;
			}
			.assistant-subtitle {
				font-size: 0.84rem;
				color: #38516f;
				margin-top: 0.15rem;
			}
			.assistant-status {
				display: inline-flex;
				align-items: center;
				gap: 0.42rem;
				padding: 0.38rem 0.68rem;
				border-radius: 999px;
				font-size: 0.72rem;
				font-weight: 700;
				letter-spacing: 0.04em;
				text-transform: uppercase;
				background: rgba(16, 185, 129, 0.12);
				border: 1px solid rgba(16, 185, 129, 0.25);
				color: #065f46;
			}
			.assistant-status.offline {
				background: rgba(245, 158, 11, 0.12);
				border-color: rgba(245, 158, 11, 0.28);
				color: #92400e;
			}
			.assistant-status::before {
				content: "";
				width: 7px;
				height: 7px;
				border-radius: 50%;
				background: currentColor;
				opacity: 0.9;
			}
			.assistant-chip-row {
				display: flex;
				flex-wrap: wrap;
				gap: 0.55rem;
				margin: 0.2rem 0 0.2rem;
			}
			.assistant-chip {
				padding: 0.36rem 0.62rem;
				font-size: 0.73rem;
				font-weight: 600;
				border-radius: 999px;
				background: rgba(37, 99, 235, 0.09);
				color: #1d4ed8;
				border: 1px solid rgba(37, 99, 235, 0.18);
			}
			[data-testid="stChatMessage"] {
				padding: 0.25rem 0;
			}
			[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {
				line-height: 1.55;
			}
			[data-testid="stChatMessageAvatarUser"],
			[data-testid="stChatMessageAvatarAssistant"] {
				margin-top: 0.2rem;
			}
			@media (max-width: 760px) {
				.assistant-header {
					flex-direction: column;
					align-items: flex-start;
				}
			}
		</style>
		""",
		unsafe_allow_html=True,
	)


def _render_shell_header(assistant_enabled):
	status_text = "online" if assistant_enabled else "limited"
	status_class = "assistant-status" if assistant_enabled else "assistant-status offline"
	st.markdown(
		f"""
		<div class="assistant-shell">
			<div class="assistant-header">
				<div>
					<div class="assistant-brand">
						<div class="assistant-icon">AI</div>
						<div>
							<div class="assistant-title">Code assistant</div>
							<div class="assistant-subtitle">Grounded answers from your review findings and security docs</div>
						</div>
					</div>
				</div>
				<div class="{status_class}">{status_text}</div>
			</div>
			<div class="assistant-chip-row">
				<span class="assistant-chip">Security aware</span>
				<span class="assistant-chip">Remediation ready</span>
				<span class="assistant-chip">Context grounded</span>
			</div>
		</div>
		""",
		unsafe_allow_html=True,
	)


def _render_assistant_message(content, sources=None, follow_up_guidance=""):
	with st.chat_message("assistant", avatar=":material/smart_toy:"):
		st.markdown(content)
		if follow_up_guidance:
			st.caption(f"Tip: {follow_up_guidance}")
		if sources:
			st.caption("Sources: " + ", ".join(sources[:4]))


def _handle_question(question, assistant, review_result):
	st.session_state.assistant_history.append({"role": "user", "content": question})
	with st.chat_message("user", avatar=":material/person:"):
		st.markdown(question)

	with st.chat_message("assistant", avatar=":material/smart_toy:"):
		with st.spinner("Grounding answer in review findings and knowledge base..."):
			response = assistant.answer(question, review_result)
			answer = response.get("answer", "")
			sources = response.get("supporting_sources", []) or response.get("retrieved_sources", [])
			follow_up_guidance = response.get("follow_up_guidance", "")
			st.markdown(answer)
			if follow_up_guidance:
				st.caption(f"Tip: {follow_up_guidance}")
			if sources:
				st.caption("Sources: " + ", ".join(sources[:4]))

	st.session_state.assistant_history.append(
		{
			"role": "assistant",
			"content": answer,
			"sources": sources,
			"follow_up_guidance": follow_up_guidance,
		}
	)


def render_assistant_panel(review_result):
	_inject_assistant_styles()

	if review_result is None:
		_render_shell_header(assistant_enabled=False)
		st.info("Run a code review first to enable grounded follow-up questions.", icon=":material/info:")
		return

	if "assistant_history" not in st.session_state:
		st.session_state.assistant_history = []

	assistant = ConversationalCodeAssistant()
	_render_shell_header(assistant_enabled=assistant.is_enabled())

	# Show one-click starter prompts before the first user message.
	if not st.session_state.assistant_history:
		selected_prompt = st.pills(
			"Try one of these",
			list(SUGGESTED_PROMPTS.keys()),
			label_visibility="collapsed",
		)
		if selected_prompt:
			_handle_question(SUGGESTED_PROMPTS[selected_prompt], assistant, review_result)
			st.rerun()

	for message in st.session_state.assistant_history:
		if message["role"] == "user":
			with st.chat_message("user", avatar=":material/person:"):
				st.markdown(message["content"])
		else:
			_render_assistant_message(
				message.get("content", ""),
				sources=message.get("sources", []),
				follow_up_guidance=message.get("follow_up_guidance", ""),
			)

	question = st.chat_input(
		"Ask about a finding, vulnerability, or secure coding practice.",
		submit_mode="disable",
	)
	if question:
		_handle_question(question, assistant, review_result)