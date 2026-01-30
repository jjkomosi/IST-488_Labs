import streamlit as st

# Define the pages
lab1_page = st.Page("pages/Lab1.py", title="Lab 1", icon="📄")
lab2_page = st.Page("pages/Lab2.py", title="Lab 2", icon="📝", default=True)

# Create navigation with Lab2 as default
nav = st.navigation([lab1_page, lab2_page])

# Run the selected page
nav.run()