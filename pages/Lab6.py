import streamlit as st
from langchain.chat_models import init_chat_model
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Part A: Set Up the Application

# Initialize the LLM using init_chat_model (Claude Haiku)
llm = init_chat_model("claude-haiku-4-5-20251001", model_provider="anthropic")

# To switch to OpenAI (Part D), comment out the line above and uncomment below:
# llm = init_chat_model("gpt-5.4-nano", model_provider="openai")

st.title("🎬 Movie Recommendation Chatbot")

# Part B: Build the Recommendation Chain

st.sidebar.header("Preferences")

genre = st.sidebar.selectbox(
    "Genre",
    ["Action", "Comedy", "Horror", "Drama", "Sci-Fi", "Thriller", "Romance"]
)

mood = st.sidebar.selectbox(
    "Mood",
    ["Excited", "Happy", "Sad", "Bored", "Scared", "Romantic", "Curious", "Tense", "Melancholy"]
)

persona = st.sidebar.selectbox(
    "Persona",
    ["Film Critic", "Casual Friend", "Movie Journalist"]
)

# Create the recommendation PromptTemplate
rec_prompt = PromptTemplate(
    input_variables=["genre", "mood", "persona"],
    template=(
        "You are a {persona}. Recommend 3 movies in the {genre} genre "
        "for someone who is feeling {mood}. For each movie, give the title, "
        "year, and a short explanation of why it fits. Match the tone and style "
        "of your chosen persona."
    )
)

# Build the recommendation chain using the LCEL pipe operator
rec_chain = rec_prompt | llm | StrOutputParser()

# Initialize session state for the last recommendation
if "last_recommendation" not in st.session_state:
    st.session_state.last_recommendation = ""

# Button to invoke the recommendation chain
if st.button("Get Recommendations"):
    with st.spinner("Generating recommendations..."):
        result = rec_chain.invoke({
            "genre": genre,
            "mood": mood,
            "persona": persona
        })
        st.session_state.last_recommendation = result
        st.markdown(result)

# Display the last recommendation if it exists (persists across reruns)
elif st.session_state.last_recommendation:
    st.markdown(st.session_state.last_recommendation)

# Part C: Build a Follow-Up Chain 

st.divider()
follow_up = st.text_input("Ask a follow-up question about these movies:")

# Create the follow-up PromptTemplate
followup_prompt = PromptTemplate(
    input_variables=["recommendations", "question"],
    template=(
        "Here are some movie recommendations that were previously given:\n\n"
        "{recommendations}\n\n"
        "The user has a follow-up question: {question}\n\n"
        "Please answer the question based on the recommendations above."
    )
)

# Build the follow-up chain
followup_chain = followup_prompt | llm | StrOutputParser()

# Invoke the follow-up chain when the user submits a question
if follow_up and st.session_state.last_recommendation:
    with st.spinner("Looking that up..."):
        followup_result = followup_chain.invoke({
            "recommendations": st.session_state.last_recommendation,
            "question": follow_up
        })
        st.markdown(followup_result)
elif follow_up and not st.session_state.last_recommendation:
    st.warning("Get recommendations first, then ask a follow-up question.")