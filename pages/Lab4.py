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
    embedding = response.data[0].embedding
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

# Part A Testing
# topic = st.sidebar.text_input('Topic', placeholder='Type your topic (e.g., GenAI)...')
# if topic:
#     client = st.session_state.client
#     response = client.embeddings.create(
#         input=topic,
#         model='text-embedding-3-small')
#     embedding = response.data[0].embedding
#     results = collection.query(
#         query_embeddings=[embedding],
#         n_results=3
#     )
#     st.subheader(f'Results for: {topic}')
#     for i in range(len(results['documents'][0])):
#         doc_id = results['ids'][0][i]
#         st.write(f'**{i+1}. {doc_id}**')
# else:
#     st.info('Enter a topic in the sidebar to search the collection')

# Part B: Course Information Chatbot

# Initialize chat history
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

# Chat input
user_input = st.chat_input("Ask a question about iSchool courses...")

if user_input:
    # Display user message
    with st.chat_message('user'):
        st.markdown(user_input)
    st.session_state.messages.append({'role': 'user', 'content': user_input})

    # Step 1: Embed the user's question and query ChromaDB
    client = st.session_state.client
    response = client.embeddings.create(
        input=user_input,
        model='text-embedding-3-small'
    )
    query_embedding = response.data[0].embedding

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )

    # Step 2: Build context from retrieved documents
    context = ""
    sources = []
    for i in range(len(results['documents'][0])):
        doc_text = results['documents'][0][i]
        doc_id = results['ids'][0][i]
        sources.append(doc_id)
        context += f"\n--- Document: {doc_id} ---\n{doc_text}\n"

    # Step 3: Send to LLM with RAG context
    system_prompt = f"""You are a helpful iSchool course information assistant. 
Answer questions about Syracuse University iSchool courses using the provided syllabus documents.

When your answer is based on the retrieved course documents, clearly state which course(s) 
you are referencing. If the documents don't contain relevant information to answer the question, 
say so honestly.

Here are the relevant course documents retrieved for this question:
{context}
"""

    llm_response = client.chat.completions.create(
        model='gpt-5-mini',
        messages=[
            {'role': 'system', 'content': system_prompt},
            *st.session_state.messages
        ]
    )

    assistant_message = llm_response.choices[0].message.content

    # Display assistant response
    with st.chat_message('assistant'):
        st.markdown(assistant_message)
    st.session_state.messages.append({'role': 'assistant', 'content': assistant_message})