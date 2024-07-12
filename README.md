# Culinary.ai

Culinary.ai is a Streamlit application that leverages advanced AI to provide insights and recommendations based on culinary attractions and famous dishes in various cities around the world. Simply enter a location to discover key culinary highlights and receive personalized insights to enhance your gastronomic experience.

## Features

- Get personalized culinary insights based on the location you provide.
- Ask follow-up questions to gain deeper insights into the culinary attractions.
- Automatically scrolls to the latest response for a seamless user experience.
- Utilizes OpenAI for generating insights and Pinecone for efficient vector storage and retrieval.

## Getting Started

### Prerequisites

- Python 3.7 or later
- Streamlit
- OpenAI API Key
- Pinecone API Key

### Installation

1. Clone the repository:
    bash
    git clone https://github.com/RuchaChotalia/Culinary.ai.git
    cd Culinary.ai
    

2. Create and activate a virtual environment:
    bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    

3. Install the required packages:
    bash
    pip install -r requirements.txt
    

4. Set your API keys in the .streamlit/secrets.toml file:
    toml
    [secrets]
    PINECONE_API_KEY = "your_pinecone_api_key"
    OPENAI_API_KEY = "your_openai_api_key"
    

5. Prepare your data file (data.json) and place it in the appropriate directory as specified in the script:
    json
    [
        {
            "location": "Tokyo, Japan",
            "culinary_attractions": ["Sushi Dai", "Ramen Street", ...]
        },
        ...
    ]
    

### Running the Application

To run the application locally, execute the following command:
```bash
streamlit run app.py
```
### Youtube Video Link:
https://youtu.be/Zi_zxL_2yoc

### Acknowledgements
- OpenAI for providing the language model.
- Pinecone for vector storage and retrieval.
- Streamlit for the interactive web app framework.

### Contributing
Contributions are welcome! Please open an issue or submit a pull request if you have any suggestions or improvements.
