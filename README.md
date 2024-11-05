# 🕵️‍♂️ TraceCtrl - Google Cloud Gemini Hackathon

**TraceCtrl** is a web app enables users to manage their digital footprint by identifying companies holding personal data, and allows to send GDPR requests (such as access, erase, or modifify data) via email. Users can connect to their Gmail account, scan their inbox, and send customized emails to companies in bulk or individually.

## Architecture

<img src="https://i.postimg.cc/G34Zdz22/Architecture.png"/>

## Features

- **Google Authentication:** Users need to authenticate for the tool to access their Gmail inbox.
- **AI Inbox Scanning:** The LLM analyzes the content of emails to identify the interaction type, the company that sent the email, and their website.
- **Advanced Scanning Options:** Users can modify options such as the number of days to search for emails and exclude selected email categories.
- **Interactive Data Table:** Users can review companies in a table format and select the ones to contact with the appropriate request type.
- **Lookup of Privacy Policy:** The tool searches for the dedicated privacy policy page of any website based on the base URL.
- **Extraction of GDPR Email:** The LLM analyzes the privacy policy and searches for an email address for GDPR requests.
- **Dynamic Email Template:** The email template dynamically updates with user data, requiring no further edits.
- **Email Preview:** Users can preview the email before sending.
- **Bulk Email Sending:** The tool can send GDPR requests in bulk on behalf of the user.


## Tech Stack

- **TiDB Serverless:** Stores AI-generated temporary game data, including tables for Victim, Suspects, Evidence, Alibis, and more.
- **TiDB VectorSearch:** Ensures the AI generates valid SQL queries by referencing schema embeddings stored in the vs_game_schema table.
- **Llama-Index:** Manages the workflow for generating and validating game data, including self-healing processes.
- **Gemini 1.5 Flash:** GPT-4o mini model generates unique game stories, data and personalized hints for a player.
- **Streamlit:** Provides the user interface.

## How It Works

1. **Story Generation:** The AI generates a unique murder mystery story and populates the database with relevant data.
2. **Data Exploration:** Players explore the data by running SQL queries to piece together the clues and identify the murderer.
3. **Hints System:** The AI can offer hints based on the player’s query history, helping them narrow down the suspects.
4. **Victory:** The game ends when the player correctly identifies the murderer.

## Llama-Index Workflow

Below is representation of the Llama-Index workflow that is used to orchestrate multiple LLM calls and ingestion of temporary game data into TiDB Serverless.

<img src="https://i.postimg.cc/7LpS7xgj/Llama-Index-Workflow.png"/>


[Watch the demo video on YouTube](https://youtu.be/IEwo6FUG1PY)


## Getting Started

To set up and run QueryHunt locally:

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/arsentievalex/queryhunt-game.git

2. **Install the required packages:**
   ```bash
   cd queryhunt-game pip install -r requirements.txt

3. **Replace the following secrets with your credentials:**
   ```bash
   st.secrets["OPENAI_API_KEY"], st.secrets["TIDB_CONNECTION_URL"], st.secrets["TIDB_USER"], st.secrets["TIDB_PASSWORD"]

4. **Run entrypoint app.py:**
   ```bash
   streamlit run app.py
