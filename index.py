import streamlit as st

# Get current page from query params
page = st.query_params.get("page", "setup")

if page == "flashcards":
    st.markdown("## Flashcard Practice Page Here")
    st.stop()

st.title("Interview Practice Setup")

role_options = [
    "Select a role...",
    "Software Engineer",
    "Product Manager",
    "Data Scientist",
    "UX Designer",
    "Business Analyst",
    "Other"
]

# Input fields
name = st.text_input("Your Name", "")
role = st.selectbox("Role You're Applying For", role_options)
if role == "Other":
    custom_role = st.text_input("Please specify your role")
    role = custom_role if custom_role else "Other"
topic = st.text_input("Topic to Practice (e.g., Behavioral, Data Structures)", "")
goal = st.text_area("Goal for This Session (e.g., Use STAR format, Accuracy)", "")

# Submit button
if st.button("Start Practice", key="start_practice_button"):
    if role == "Select a role...":
        st.warning("Please select a valid role before proceeding.")
    else:
        # Save info to session state
        st.session_state.name = name
        st.session_state.role = role
        st.session_state.topic = topic
        st.session_state.goal = goal

        
        st.markdown(
            """
            <a href="/flashcards" target="_self">
                <button style='padding: 0.75em 1.5em; font-size: 1.1em; background-color: #2563eb; color: white; border: none; border-radius: 8px;'>
                    ➡️ Go to Flashcards
                </button>
            </a>
            """,
            unsafe_allow_html=True
        )
