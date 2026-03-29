import streamlit as st

# Define the pages
lab1_page = st.Page("pages/Lab1.py", title="Lab 1", icon="📄")
lab2_page = st.Page("pages/Lab2.py", title="Lab 2", icon="📝")
lab3_page = st.Page("pages/Lab3.py", title="Lab 3", icon="📝")
lab4_page = st.Page("pages/Lab4.py", title="Lab 4", icon="📝")
lab5_page = st.Page("pages/Lab5.py", title="Lab 5", icon="📝")
lab6_page = st.Page("pages/Lab6.py", title="Lab 6", icon="📝", default=True)

# Create navigation with Lab2 as default
nav = st.navigation([lab1_page, lab2_page, lab3_page, lab4_page, lab5_page, lab6_page])

# Run the selected page
nav.run()