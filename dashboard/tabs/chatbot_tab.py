from rag.rag_pipeline import ask_rag
import streamlit as st


def initialize_chat_state():

    if "messages" not in st.session_state:

        st.session_state.messages = []


def add_message(role, content):

    st.session_state.messages.append({
        "role": role,
        "content": content
    })


def render_chat_header():

    st.subheader("Clinical Trials Assistant")

    st.markdown("""
    Ask questions about:
    - clinical trials
    - sponsors
    - interventions
    - conditions
    - recent publications

    The chatbot does not store context between questions,
    so please include all relevant details in each question.
    """)


def render_chat_history(container):

    with container:

        for message in st.session_state.messages:

            render_message(
                role=message["role"],
                content=message["content"]
            )


def render_message(role, content):

    with st.chat_message(role):

        st.markdown(content)


def handle_user_prompt(prompt, container):

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

                    answer = ask_rag(prompt)['answer']

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

    render_chat_header()

    initialize_chat_state()

    chat_container = st.container(height=600)

    render_chat_history(chat_container)

    prompt = st.chat_input(
        "Ask a question about clinical trials..."
    )

    if prompt:

        handle_user_prompt(
            prompt=prompt,
            container=chat_container
        )

        st.rerun()
