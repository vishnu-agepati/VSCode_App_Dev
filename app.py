import os
import time

import streamlit as st
from dotenv import load_dotenv

try:
    import google.generativeai as genai
except ImportError:
    genai = None

# Load .env file so GEMINI_API_KEY is available in the environment.
load_dotenv()
# Prefer Streamlit Secrets (deployed) then environment variables (local).
# Also sanitize the value to remove accidental quotes or surrounding whitespace.
api_key = None
try:
    api_key = st.secrets.get("GEMINI_API_KEY")
except Exception:
    api_key = None
if not api_key:
    api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    api_key = api_key.strip().strip('"').strip("'")

st.title("Streamlit Gemini Chat")
st.write("Ask Gemini anything and get a response from the Gemini model.")

if not api_key:
    st.error(
        "GEMINI_API_KEY is not set. Add it to Streamlit Secrets (preferred) or to your .env file as GEMINI_API_KEY=... and restart the app."
    )

if genai is None:
    st.error(
        "The Google Gemini client is not installed. Run `pip install google-generativeai python-dotenv` in your environment."
    )

# Configure Gemini if available
if api_key and genai is not None:
    genai.configure(api_key=api_key)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Let's start chatting with Gemini! 👇"}]

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Ask Gemini anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    assistant_response = ""
    if api_key and genai is not None:
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            try:
                response = genai.responses.create(
                    model="gemini-1.5-pro",
                    temperature=0.2,
                    input=prompt,
                )
                if hasattr(response, "output_text") and response.output_text:
                    assistant_response = response.output_text
                else:
                    parts = []
                    for out in getattr(response, "output", []):
                        for content in getattr(out, "content", []):
                            text = getattr(content, "text", None)
                            if text:
                                parts.append(text)
                    assistant_response = "\n".join(parts).strip() or "(no text returned)"
            except Exception as exc:
                assistant_response = f"Gemini error: {exc}"

            # Show response text, optionally simulating streaming
            full_response = ""
            for chunk in assistant_response.split():
                full_response += chunk + " "
                time.sleep(0.03)
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response.strip())
    else:
        assistant_response = (
            "Unable to call Gemini. Check the GEMINI_API_KEY and install `google-generativeai`."
        )
        with st.chat_message("assistant"):
            st.markdown(assistant_response)

    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
