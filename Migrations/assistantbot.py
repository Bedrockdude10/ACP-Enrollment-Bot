import time
import streamlit as st
from openai import OpenAI
import os

os.environ["OPENAI_API_KEY"] = "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"

# upload files
if "file_ids" not in st.session_state:
    file_ids = []
    client = OpenAI()

    for file in os.listdir("docs"):
        try:
            file = client.files.create(
                file=open(os.path.join("docs", file), "rb"),
                purpose="assistants"
            )

            file_ids.append(file.id)
            print(f"Uploaded {file.filename} with id {file.id}")
        except Exception as e:
            print(f"Error uploading {file.filename}: {e}")  


    assistant = client.beta.assistants.create(
        instructions="""You are a user support chatbot for people trying to sign up for the FCC's Affordable Connectivity Program. 
        Use your knowledge base to best respond to user queries.""",
        model="gpt-4-1106-preview",
        tools=[{"type": "retrieval"}],
        file_ids=file_ids
    )

    thread = client.beta.threads.create()

    st.session_state["client"] = client
    st.session_state["thread"] = thread
    st.session_state["file_ids"] = file_ids
    st.session_state["assistant"] = assistant

# upload files
while "file_ids" not in st.session_state:
    time.sleep(1)  # Wait for 1 second

# App title
st.set_page_config(page_title="🤗💬 ACP Chat bot")

# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": "How may I help you?"}]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Function for generating LLM response
def generate_response(prompt_input):
    if st.session_state["assistant"]:
        st.session_state["client"].beta.threads.messages.create(
            thread_id=st.session_state["thread"].id,
            role="user",
            content=prompt_input
        )

        # run assistant
        run = st.session_state["client"].beta.threads.runs.create(
            thread_id=st.session_state["thread"].id,
            assistant_id=st.session_state["assistant"].id,
            instructions="Please answers the user's question."
        )

        while True:
            run = st.session_state["client"].beta.threads.runs.retrieve(
                run_id=run.id,
                thread_id=st.session_state["thread"].id
            )

            if run.status == "completed":
                break

            time.sleep(2)

        # retrieve response
        messages = st.session_state["client"].beta.threads.messages.list(
            thread_id=st.session_state["thread"].id
        )

        return messages.data[0].content[0].text.value
    else:
        return "Test"


# User-provided prompt
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

# Generate a new response if last message is not from assistant
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_response(prompt) 
            st.write(response) 
    message = {"role": "assistant", "content": response}
    st.session_state.messages.append(message)

