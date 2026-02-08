import streamlit as st
from openai import OpenAI
import tiktoken  # pip install tiktoken

# ============================================
# APP SETUP
# ============================================
st.title("Jonah's Lab 3: Q/A Chatbot")

# Model selection
openAI_model = st.sidebar.selectbox("Choose a model:", ("mini", "regular"))
model_to_use = "gpt-4o-mini" if openAI_model == "mini" else "gpt-4o"

# Buffer configuration
MAX_CONTEXT_TOKENS = 100

# Initialize OpenAI client
if 'client' not in st.session_state:
    api_key = st.secrets["OPENAI_API_KEY"]
    st.session_state.client = OpenAI(api_key=api_key)

# ============================================
# TOKEN COUNTING FUNCTIONS
# ============================================
def count_tokens(text, model="gpt-4o"):
    """Count tokens in a string."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

def count_messages_tokens(messages, model="gpt-4o"):
    """Count total tokens across all messages."""
    total = 0
    for message in messages:
        total += 4  # overhead per message
        total += count_tokens(message["content"], model)
    total += 2  # conversation overhead
    return total

def apply_token_buffer(messages, max_tokens, model="gpt-4o"):
    """
    Trim conversation history to stay under token limit.
    Removes oldest messages first, preserves system message.
    """
    if len(messages) <= 1:
        return messages
    
    # Preserve system message if present
    system_msg = None
    if messages[0]["role"] == "system":
        system_msg = messages[0]
        working_messages = messages[1:]
    else:
        working_messages = messages[:]
    
    current_tokens = count_messages_tokens(messages, model)
    
    # Remove oldest messages until under limit
    while current_tokens > max_tokens and len(working_messages) > 1:
        working_messages.pop(0)
        current_tokens = count_messages_tokens(
            ([system_msg] if system_msg else []) + working_messages,
            model
        )
    
    if system_msg:
        return [system_msg] + working_messages
    return working_messages

# ============================================
# CONVERSATION STATE TRACKING
# ============================================
# Track where we are in the flow:
# - "awaiting_question": waiting for user to ask something
# - "awaiting_more_info": we answered, waiting for yes/no
if "conversation_state" not in st.session_state:
    st.session_state.conversation_state = "awaiting_question"

# Store the current topic for "more info" requests
if "current_topic" not in st.session_state:
    st.session_state.current_topic = None

# Message history for display and context
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! I'm here to help you learn. What would you like to know about?"}
    ]

# ============================================
# SYSTEM PROMPT - Kid-friendly answers
# ============================================
SYSTEM_PROMPT = """You are a friendly teacher helping a 10-year-old understand things. 

Rules for your answers:
- Use simple words a 10-year-old would know
- Keep explanations short (2-3 sentences for basic answers)
- Use fun comparisons and examples from everyday life
- Be encouraging and friendly
- Avoid jargon or technical terms unless you explain them simply

When asked for "more info", go a bit deeper but still keep it simple and fun."""

# ============================================
# HELPER FUNCTION: Call OpenAI with buffer
# ============================================
def get_response(user_message, provide_more_info=False):
    client = st.session_state.client
    
    if provide_more_info:
        prompt = f"The user previously asked about: {st.session_state.current_topic}\n\nPlease provide more interesting details about this topic, still explaining it simply for a 10-year-old. Add a fun fact if you can!"
    else:
        prompt = user_message
        st.session_state.current_topic = user_message
    
    # Build messages with system prompt
    messages_to_send = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Add conversation history
    messages_to_send.extend(st.session_state.messages)
    
    # Add current user prompt
    messages_to_send.append({"role": "user", "content": prompt})
    
    # NOW apply buffer once to the complete message list
    messages_to_send = apply_token_buffer(
        messages_to_send,
        max_tokens=MAX_CONTEXT_TOKENS,
        model=model_to_use
    )
    
    # Debug info
    tokens_being_sent = count_messages_tokens(messages_to_send, model_to_use)
    st.sidebar.write(f"Messages in buffer: {len(messages_to_send)}")
    st.sidebar.write(f"Tokens being sent: {tokens_being_sent}")
    
    response = client.chat.completions.create(
        model=model_to_use,
        messages=messages_to_send,
        stream=True
    )
    
    return response

# ============================================
# HELPER FUNCTIONS: Check for yes/no
# ============================================
def is_yes(text):
    """Check if user's response means 'yes'"""
    yes_words = ["yes", "yeah", "yep", "sure", "ok", "okay", "please", "y", "yea", "definitely", "absolutely"]
    return any(word in text.lower().strip() for word in yes_words)

def is_no(text):
    """Check if user's response means 'no'"""
    no_words = ["no", "nope", "nah", "n", "i'm good", "im good", "that's enough", "thats enough", "done"]
    return any(word in text.lower().strip() for word in no_words)

# ============================================
# DISPLAY CONVERSATION HISTORY
# ============================================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ============================================
# HANDLE USER INPUT
# ============================================
if prompt := st.chat_input("Type here..."):
    
    # Display user's message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    # ----------------------------------------
    # STATE: Awaiting a question from user
    # ----------------------------------------
    if st.session_state.conversation_state == "awaiting_question":
        with st.chat_message("assistant"):
            stream = get_response(prompt, provide_more_info=False)
            answer = st.write_stream(stream)
            
            st.write("")
            followup = "\n\nWould you like to know more about this? (Yes/No)"
            st.write("Would you like to know more about this? (Yes/No)")
            answer += followup
        
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.conversation_state = "awaiting_more_info"
    
    # ----------------------------------------
    # STATE: Awaiting yes/no response
    # ----------------------------------------
    elif st.session_state.conversation_state == "awaiting_more_info":
        
        if is_yes(prompt):
            with st.chat_message("assistant"):
                stream = get_response(prompt, provide_more_info=True)
                answer = st.write_stream(stream)
                
                st.write("")
                followup = "\n\nWould you like to know even more? (Yes/No)"
                st.write("Would you like to know even more? (Yes/No)")
                answer += followup
            
            st.session_state.messages.append({"role": "assistant", "content": answer})
            
        elif is_no(prompt):
            response = "Great! What else would you like to learn about?"
            with st.chat_message("assistant"):
                st.write(response)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.conversation_state = "awaiting_question"
            st.session_state.current_topic = None
            
        else:
            # Treat as new question
            with st.chat_message("assistant"):
                stream = get_response(prompt, provide_more_info=False)
                answer = st.write_stream(stream)
                
                st.write("")
                followup = "\n\nWould you like to know more about this? (Yes/No)"
                st.write("Would you like to know more about this? (Yes/No)")
                answer += followup
            
            st.session_state.messages.append({"role": "assistant", "content": answer})

# ============================================
# SIDEBAR: Debug info
# ============================================
st.sidebar.write("---")
st.sidebar.write("**Debug Info:**")
st.sidebar.write(f"State: {st.session_state.conversation_state}")
st.sidebar.write(f"Topic: {st.session_state.current_topic}")
st.sidebar.write(f"Total messages stored: {len(st.session_state.messages)}")
    