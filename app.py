import os
import json
import time
import streamlit as st
import streamlit.components.v1 as components
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from pinecone import Pinecone as PineconeClient, ServerlessSpec
from openai import OpenAI
import numpy as np

# Set environment variables
os.environ['PINECONE_API_KEY'] = st.secrets["PINECONE_API_KEY"]
os.environ['OPENAI_API_KEY'] = st.secrets["OPENAI_API_KEY"]

# Get API keys from environment variables
pinecone_api_key = os.getenv('PINECONE_API_KEY')
openai_api_key = os.getenv('OPENAI_API_KEY')

# Initialize Pinecone
pc = PineconeClient(api_key=pinecone_api_key)

# Define index name and check if it exists
index_name = "aichatbot"
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=1536,
        metric='cosine',
        spec=ServerlessSpec(cloud='aws', region='us-east-1')
    )

# Connect to the index
index = pc.Index(index_name)

# Initialize OpenAI embeddings
embeddings = OpenAIEmbeddings(api_key=openai_api_key)

# Initialize OpenAI client
client = OpenAI(api_key=openai_api_key)

# Initialize LangChain components
vectorstore = Pinecone(index=index, embedding=embeddings, text_key='location', namespace="locations-dishes-namespace")
retriever = vectorstore.as_retriever()

# Initialize Streamlit session state for conversation history, latency tracking, and faithfulness ratings
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'latest_latency' not in st.session_state:
    st.session_state.latest_latency = None
if 'faithfulness_ratings' not in st.session_state:
    st.session_state.faithfulness_ratings = []

# Streamlit app setup
st.title("Culinary.ai")
st.sidebar.header("Instructions")
st.sidebar.markdown("""
- To discover delicious dishes, type in a location. e.g., Paris, France
""")
st.sidebar.header("About Culinary.ai")
st.sidebar.info("""
This app leverages advanced AI to help you explore global cuisines. Enter a location to uncover popular dishes and receive culinary insights tailored to enhance your dining experience.
""")
st.sidebar.markdown("""By Rucha Chotalia""")
if st.session_state.latest_latency is not None:
    st.sidebar.metric(label="Latest Response Time", value=f"{st.session_state.latest_latency:.2f} seconds")

# Display conversation history and allow faithfulness rating
st.subheader("If you're happy with your resonse then please don't forget to rate that faithfulness of the chatbot")
for i, entry in enumerate(st.session_state.conversation_history):
    st.markdown(f"*Insights:* {entry['insights']}")
    st.markdown(f"*Follow-up Question:* {entry.get('follow_up_question', '')}")
    st.markdown(f"*Response:* {entry.get('follow_up_response', '')}")
    with st.expander("Rate the Faithfulness of the Response"):
        # Using radio buttons for faithfulness rating
        faithfulness_rating = st.radio("Rate the accuracy and reliability of the response (1-10):", 
                                       list(range(1, 11)), key=f"rating_{i}")
        if st.button("Submit Rating", key=f"rate_{i}"):
            entry['faithfulness_rating'] = faithfulness_rating
            st.session_state.faithfulness_ratings.append(faithfulness_rating)
            st.experimental_rerun()

# Calculate and display average faithfulness if available
if st.session_state.faithfulness_ratings:
    average_faithfulness = sum(st.session_state.faithfulness_ratings) / len(st.session_state.faithfulness_ratings)
    st.metric("Average Faithfulness Rating", f"{average_faithfulness:.1f}/10")


# Additional function to check for negative queries
def is_negative_query(query):
    negative_words = ['no', 'not', 'none', 'never', 'stop', 'nobody']
    return any(negative_word in query.lower() for negative_word in negative_words)

# Handling user input and measuring latency
mode = st.radio("Select input mode", ("Enter City", "Get the recipe or ask anything else"))
if mode == "Enter City":
    with st.form(key='new_location_form'):
        st.write("Enter your location below and get dishes suggestions:")
        user_input = st.text_input("Location")
        submit_button = st.form_submit_button(label='Submit')
        
        if submit_button and user_input:
            if is_negative_query(user_input):
                st.error("Inappropriate or negative input detected. Please enter a valid location.")
            else:
                start_time = time.time()
                result = retriever.get_relevant_documents(user_input)
                end_time = time.time()
                latency = end_time - start_time
                st.session_state.latest_latency = latency
                st.write(f"Response time: {latency:.2f} seconds")
                if not result:
                    st.error("No insights found.")
                else:
                    for doc in result:
                        location = doc.metadata.get('location')
                        dishes = ', '.join(doc.metadata.get('dishes', []))
                        messages = [
                            {"role": "system", "content": "You are an AI trained to provide culinary insights."},
                            {"role": "user", "content": f"Analyze the dishes in {location}: {dishes}"}
                        ]
                        response = client.chat.completions.create(model="gpt-3.5-turbo", messages=messages, max_tokens=500)
                        insights = response.choices[0].message.content if response.choices else "No insights were generated."
                        
                        # Save the response to session state
                        st.session_state.conversation_history.append({"location": location, "insights": insights})
                        st.experimental_rerun()

elif mode == "Get the recipe or ask anything else":
    if not st.session_state.conversation_history:
        st.write("No conversation history available. Please enter a new location first.")
    else:
        with st.form(key='follow_up_form'):
            st.write("Ask a follow-up question based on the previous insights:")
            follow_up_question = st.text_input("Follow-up Question")
            submit_button = st.form_submit_button(label='Submit')
            
            if submit_button and follow_up_question:
                last_entry = st.session_state.conversation_history[-1]
                insights = last_entry['insights']
                messages = [
                    {"role": "system", "content": "You are an AI trained to provide culinary insights."},
                    {"role": "user", "content": insights},
                    {"role": "user", "content": follow_up_question}
                ]
                response = client.chat.completions.create(model="gpt-3.5-turbo", messages=messages, max_tokens=500)
                follow_up_response = response.choices[0].message.content if response.choices else "No response generated."
                
                # Update the last entry with follow-up question and response
                last_entry['follow_up_question'] = follow_up_question
                last_entry['follow_up_response'] = follow_up_response
                st.experimental_rerun()
