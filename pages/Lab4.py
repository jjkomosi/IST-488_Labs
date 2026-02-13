import streamlit as st
import sys

# sqlite3 fix - MUST be before chromadb import
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import chromadb
from openai import OpenAI
from pathlib import Path
import fitz
import os

# Create ChromeDB client
chroma_client = chromadb.PersistentClient(path='./ChromaDB_for_Lab')
collection = chroma_client.get_or_create_collection('Lab4Collection')


# Read pdf and convert to txt
def read_pdf(file_path):
    """Extract text from a PDF file on disk."""
    document = fitz.open(file_path)
    text = ''
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        text += page.get_text()
    document.close()
    return text


# Initialize OpenAI client
if 'client' not in st.session_state:
    api_key = st.secrets["OPENAI_API_KEY"]
    st.session_state.client = OpenAI(api_key=api_key)


# a function that will add documents to ChromaDB collection
def add_to_collection(collection, text, file_name):
    client = st.session_state.client
    response = client.embeddings.create(
        input=text,
        model='text-embedding-3-small'
    )

    # get the embedding
    embedding = response.data[0].embedding

    # add embedding and document to chromaDB
    collection.add(
        documents=[text],
        ids=[file_name],
        embeddings=[embedding])


# populate collection with PDFs
def load_pdfs_to_collection(folder_path, collection):
    pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]
    for pdf_file in pdf_files:
        file_path = os.path.join(folder_path, pdf_file)
        text = read_pdf(file_path)
        add_to_collection(collection, text, pdf_file)


# check if collection is empty and load PDFs
if collection.count() == 0:
    load_pdfs_to_collection('./Lab-04-Data/', collection)


# Title
st.title("Lab 4: iSchool Course Chatbot Using RAG")

# Querying a collection -- Only used for testing

topic = st.sidebar.text_input('Topic', placeholder='Type your topic (e.g., GenAI)...')

if topic:
    client = st.session_state.client
    response = client.embeddings.create(
        input=topic,
        model='text-embedding-3-small')

    # get the embedding
    embedding = response.data[0].embedding

    # get text related to this question
    results = collection.query(
        query_embeddings=[embedding],
        n_results=3
    )

    # display results
    st.subheader(f'Results for: {topic}')

    for i in range(len(results['documents'][0])):
        doc = results['documents'][0][i]
        doc_id = results['ids'][0][i]

        st.write(f'**{i+1}. {doc_id}**')

else:
    st.info('Enter a topic in the sidebar to search the collection')