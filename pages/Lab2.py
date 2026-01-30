import streamlit as st
from openai import OpenAI
import fitz  # PyMuPDF

def read_pdf(uploaded_file):
    """Extract text from an uploaded PDF file."""
    pdf_bytes = uploaded_file.read()
    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ''
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        text += page.get_text()
    document.close()
    return text

# SIDEBAR
st.sidebar.title(':green[Lab 2: Document Summarizer]')
st.sidebar.header(':green[Summary Options]')

summary_type = st.sidebar.selectbox(
    'Choose a summary format',
    ('100 words', '2 connecting paragraphs', '5 bullet points')
)

st.sidebar.header(':green[Model Selection]')
use_advanced_model = st.sidebar.checkbox('Use advanced model')

if use_advanced_model:
    model_name = "gpt-5-latest"
else:
    model_name = "gpt-5-mini"

# MAIN PAGE
st.title(':green[📄 Document Summarizer]')
st.subheader(':green[Lab 2: AI-Powered Summary Generator]')

st.write("Upload a document and get an AI-generated summary. Use the sidebar to customize your options.")

# Get API key from secrets
try:
    openai_api_key = st.secrets["OPENAI_API_KEY"]
    client = OpenAI(api_key=openai_api_key)
except KeyError:
    st.error("API key not found. Please configure OPENAI_API_KEY in your secrets.")
    st.stop()

# File uploader
uploaded_file = st.file_uploader(
    "Upload a document (.txt or .pdf)", type=("txt", "pdf")
)

if uploaded_file:
    if st.button("Generate Summary"):
        # Process the uploaded file
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'txt':
            document_text = uploaded_file.read().decode()
        elif file_extension == 'pdf':
            document_text = read_pdf(uploaded_file)
        else:
            st.error("Unsupported file type.")
            st.stop()
        
        # Build prompt based on summary type
        if summary_type == "100 words":
            prompt = f"Summarize the following document in exactly 100 words:\n\n{document_text}"
        elif summary_type == "2 connecting paragraphs":
            prompt = f"Summarize the following document in 2 connecting paragraphs:\n\n{document_text}"
        else:
            prompt = f"Summarize the following document in exactly 5 bullet points:\n\n{document_text}"
        
        messages = [{"role": "user", "content": prompt}]
        
        # Generate summary
        stream = client.chat.completions.create(
            model=model_name,
            messages=messages,
            stream=True,
        )
        
        st.subheader(f':green[Summary ({summary_type})]')
        st.write_stream(stream)