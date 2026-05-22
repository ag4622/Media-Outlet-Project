from rag.rag_pipeline import ask_rag
import streamlit as st


def initialize_chat_state():
    """Initialize session state variables for chat history and prompt settings."""

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "prompt_persona" not in st.session_state:
        st.session_state.prompt_persona = "investor"

    if "use_clinical_prompt" not in st.session_state:
        st.session_state.use_clinical_prompt = (
            st.session_state.prompt_persona == "clinical_researcher"
        )


def add_message(role, content):
    """Add a message to the session state message history."""
    st.session_state.messages.append({
        "role": role,
        "content": content
    })


def render_chat_header():
    """Render the header section of the chatbot tab with title and caption."""
    st.subheader("Clinical Trials Assistant")
    st.caption(
        "Ask about trials, sponsors, interventions,"
        " conditions, and recent publications."
        " RAG does not store previous conversations, but you can copy-paste relevant info from past chats!"
    )


def render_chat_controls():
    """Render the control section of the chatbot tab with toggle and clear chat button."""

    st.markdown(
        """
        <style>
            .assistant-card {
                border: 1px solid rgba(120, 120, 120, 0.25);
                border-radius: 14px;
                padding: 12px 14px;
                background: linear-gradient(
                    135deg,
                    rgba(240, 249, 255, 0.7),
                    rgba(245, 243, 255, 0.45)
                );
            }
            .assistant-chip {
                display: inline-block;
                margin-top: 4px;
                padding: 3px 10px;
                border-radius: 999px;
                font-size: 0.82rem;
                background: rgba(15, 23, 42, 0.08);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([3, 1])

    with col1:
        st.toggle(
            "Use clinical_researcher prompt",
            key="use_clinical_prompt",
            help=(
                "Toggle between investor and "
                "clinical_researcher system prompts."
            ),
        )
        st.session_state.prompt_persona = (
            "clinical_researcher"
            if st.session_state.use_clinical_prompt
            else "investor"
        )

    with col2:
        if st.button("Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    st.markdown(
        f"""
        <div class="assistant-card">
            <div><strong>Prompt Profile</strong></div>
            <div class="assistant-chip">
                Current: {st.session_state.prompt_persona}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chat_history(container):
    """Render the chat history from session state within the given container."""
    with container:

        for message in st.session_state.messages:

            render_message(
                role=message["role"],
                content=message["content"]
            )


def render_message(role, content):
    """Render a single message in the chat interface."""
    with st.chat_message(role):
        st.markdown(content)


def handle_user_prompt(prompt, container, user_identity):
    """Process the user prompt, generate a response using RAG, and update the chat history."""
    # Save + render user message
    add_message("user", prompt)

    with container:
        render_message("user", prompt)

    # Generate assistant response
    with container:

        with st.chat_message("assistant"):

            with st.spinner(
                "Searching clinical trials knowledge base..."
            ):

                try:

                    answer = ask_rag(
                        prompt,
                        user_identity=user_identity
                    )["answer"]

                    st.markdown(answer)

                    add_message("assistant", answer)

                except Exception as e:

                    error_message = f"Error: {str(e)}"

                    st.error(error_message)

                    add_message(
                        "assistant",
                        error_message
                    )


def render_chatbot_tab():
    """Main function to render the chatbot tab interface and handle interactions."""
    initialize_chat_state()
    render_chat_header()
    render_chat_controls()

    chat_container = st.container(height=600)
    render_chat_history(chat_container)

    prompt = st.chat_input(
        "Ask a question about clinical trials..."
    )

    if prompt:
        handle_user_prompt(
            prompt=prompt,
            container=chat_container,
            user_identity=st.session_state.prompt_persona,
        )

        st.rerun()
