import streamlit as st
from streamlit_extras.switch_page_button import switch_page

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

# Input fielsds
name = st.text_input("Your Name", "")
role = st.selectbox("Role You're Applying For", role_options)
if role == "Other":
    custom_role = st.text_input("Please specify your role")
    role = custom_role if custom_role else "Other"

topic = st.text_input("Topic to Practice (e.g., Behavioral, Data Structures)", "")
topic = st.text_input("Topic to Practice (e.g., Behavioral, Data Sturctures)", "")
goal = st.text_area("Goal for This Session (e.g., Use STAR format, Accuracy)", "")

# Submit button
if st.button("Start Practice"):
    if role == "Select a role...":
        st.warning("Please select a valid role before proceeding.")
    else:
        if st.button("Start Practice"):
            if role == "Select a role...":
                st.warning("Please select a valid role.")
            else:
                st.query_params.update({
                    "page": "flashcards",
                    "name": name,
                    "role": role,
                    "topic": topic,
                    "goal": goal,
                })
                st.rerun()        
        st.markdown(
            """
            <a href="/1_Flashcard_Practice?name={name}&role={role}&topic={topic}&goal={goal}" target="_self">
                <button style='padding: 0.75em 1.5em; font-size: 1.1em; background-color: #2563eb; color: white; border: none; border-radius: 8px;'>
                    ➡️ Go to Flashcards
                </button>
            </a>
            """,
            unsafe_allow_html=True
        )
        st.success("Your setup has been saved!")
        st.write("### Summary")
        st.write(f"Name: {name}")
        st.write(f"Role: {role}")
        st.write(f"Topic: {topic}")
        st.write(f"Goal: {goal}")
        switch_page("flashcard practice")

