import os
import json
import streamlit as st
import streamlit.components.v1 as components
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from pinecone import Pinecone as PineconeClient, ServerlessSpec
from openai import OpenAI

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

# Load the JSON data from file and upsert to Pinecone if index is empty
if index.describe_index_stats()['total_vector_count'] == 0:
    with open("/Users/ruchachotalia/Downloads/Ai Chatbot/data.json", "r") as file:
        data = json.load(file)
        vectors = []
        for i, item in enumerate(data):
            text = f"location: {item['location']}. dishes: {', '.join(item['dishes'])}"
            vector = embeddings.embed_documents([text])[0]
            vectors.append({"id": str(i), "values": vector, "metadata": item})
        index.upsert(vectors=vectors, namespace="locations-dishes-namespace")

# Initialize LangChain components
vectorstore = Pinecone(index=index, embedding=embeddings, text_key='location', namespace="locations-dishes-namespace")
retriever = vectorstore.as_retriever()

# Initialize Streamlit session state for conversation history
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'input_mode' not in st.session_state:
    st.session_state.input_mode = "location"

# Streamlit app
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

# Display conversation history
st.subheader("Conversation History")
for i, entry in enumerate(st.session_state.conversation_history):
    st.markdown(f"*Insights:* {entry['insights']}")
    st.markdown(f"*Follow-up Question:* {entry.get('follow_up_question', '')}")
    st.markdown(f"*Response:* {entry.get('follow_up_response', '')}")

# Add radio buttons for input mode selection
mode = st.radio(
    "Select input mode",
    ("Enter City", "Get the recipe or ask anything else")
)

# Handle user input based on selected mode
if mode == "Enter City":
    st.session_state.input_mode = "location"
    with st.form(key='new_location_form'):
        st.write("Enter your location below and get dishes suggestions:")
        user_input = st.text_input("Location")
        submit_button = st.form_submit_button(label='Submit')
        
        if submit_button and user_input:
            result = retriever.get_relevant_documents(user_input)
            if not result:
                st.write("No insights found.")
            else:
                found_match = False
                for doc in result:
                    location = doc.metadata.get('location')
                    dishes = ', '.join(doc.metadata.get('dishes', []))
                    messages = [
                        {"role": "system", "content": "You are an AI trained to provide culinary insights."},
                        {"role": "user", "content": f"Analyze the dishes in {location}: {dishes}"}
                    ]
                    response = client.chat.completions.create(model="gpt-3.5-turbo", messages=messages, max_tokens=500)
                    if response.choices:
                        insights = response.choices[0].message.content
                    else:
                        insights = "No insights were generated."
                    
                    # Save the response to session state
                    st.session_state.conversation_history.append({"location": location, "insights": insights})
                    st.experimental_rerun()  # Rerun the app to immediately reflect the changes
                    found_match = True
                    break

elif mode == "Get the recipe or ask anything else":
    if not st.session_state.conversation_history:
        st.write("No conversation history available. Please enter a new location first.")
    else:
        st.session_state.input_mode = "follow_up"
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
                if response.choices:
                    follow_up_response = response.choices[0].message.content
                else:
                    follow_up_response = "No insights were generated."
                
                # Update the last entry with follow-up question and response
                last_entry['follow_up_question'] = follow_up_question
                last_entry['follow_up_response'] = follow_up_response
                st.experimental_rerun()  # Rerun the app to immediately reflect the changes
