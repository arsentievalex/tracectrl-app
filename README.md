# 👣 TraceCtrl - Google Cloud Gemini Hackathon

**TraceCtrl** is a web app enables users to manage their digital footprint by identifying companies holding personal data, and allows to send GDPR requests (such as access, erase, or modifify data) via email. Users can connect to their Gmail account, scan their inbox, and send customized emails to companies in bulk or individually.

## Architecture

<img src="https://i.postimg.cc/zDVpcTk7/tracectrl-architecture.png"/>

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
- **Google API Client:** Utilizes the Gmail API to read and send emails on the user's behalf.
- **Google Auth:** Manages user authentication and grants access to required scopes.
- **Logo.Dev:** Provides an endpoint that returns a company logo based on the website.
- **FireCrawl:** Retrieves the URL of a website's privacy policy from its base URL.
- **Gemini 1.5 Flash via Vertex AI:** Extracts company websites and categorizes email interaction types. Analyzes privacy policies to extract GDPR email addresses.
- **Streamlit:** Serves as the user interface framework.
- **Docker:** Enables containerization for simplified deployment.
- **Google Container Registry:** Hosts container images.
- **Google Cloud Run:** Deploys the app in a scalable environment.

[Watch the demo video on YouTube](https://youtu.be/GIHCocx6UxQ)


## Getting Started

To set up and run TraceCtrl locally:

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/arsentievalex/tracectrl-app.git

2. **Install the required packages:**
   ```bash
   cd tracectrl-app pip install -r requirements.txt

3. **Replace the following secrets with your credentials:**
   ```bash
   credentials.json, service_acc.json, FIRECRAWL_API_KEY, LOGODEV_API_KEY

4. **Run entrypoint app.py:**
   ```bash
   streamlit run app.py
