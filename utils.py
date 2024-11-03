import requests
from langchain_google_vertexai import VertexAI
import re
from langchain_community.document_loaders import UnstructuredURLLoader
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
import google.auth
import json
import streamlit as st
import random
import pandas as pd
import os
from streamlit_auth import Authenticate
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64
from datetime import datetime, timedelta
import time


def get_first_working_url(json_data):
    # Check if "success" key exists and its value is True
    if not json_data.get('success', False):
        raise ValueError("The operation was not successful")

    # Check if "links" key exists and it has a list of URLs
    urls = json_data.get('links', [])
    if not urls:
        raise ValueError("No URLs provided")

    # Iterate through the list of URLs and check for a valid one
    for url in urls:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return url
        except requests.exceptions.RequestException as e:
            # Handle possible connection errors and skip to next URL
            print(f"Error checking {url}: {e}")
            continue

    # If no valid URL is found, raise an error
    raise ValueError("No valid URL found in the provided list")


def return_privacy_url(base_url):
    url = "https://api.firecrawl.dev/v1/map"

    payload = {
        "url": base_url,
        "search": "privacy",
        "ignoreSitemap": False,
        "includeSubdomains": True,
        "limit": 3
    }
    headers = {
        f"Authorization": f"Bearer {os.getenv('FIRECRAWL_API_KEY')}",
        "Content-Type": "application/json"
    }
    return requests.request("POST", url, json=payload, headers=headers)


def extract_email(privacy_url):
    url = [privacy_url]
    loader = UnstructuredURLLoader(urls=url)
    data = loader.load()

    credentials, project_id = google.auth.load_credentials_from_file('service_acc.json')
    vertexai.init(project=project_id, location="us-central1", credentials=credentials)

    model = VertexAI(model_name='gemini-1.5-flash-001', temperature=0)

    prompt = f"""
    Based on the below text, what is the email for data privacy/GDPR contact?
    Return only email address.
    {data[0]}
    """
    response = model.invoke(prompt)

    # make sure to return only valid email addresses
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

    match = re.search(email_pattern, response)
    if match:
        return match.group(0)
    else:
        return "No email available"


# function to check if url is working
def check_url(url):
    try:
        response = requests.get(url)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        return False


# read json file and transform to dictionary
def read_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data


def compose_logo_url(logo_url_set, email_info):
    classification = json.loads(email_info["Interaction Type"])
    website = classification.get("website", "")

    # Clean the website: remove 'https://www.' or 'http://www.' and any slashes
    cleaned_website = re.sub(r'https?://(www\.)?', '', website).strip('/')

    logo_url = f"https://img.logo.dev/{cleaned_website}?token={os.getenv('LOGODEV_API_KEY')}"

    # Check if the URL is valid and add it to the set
    if check_url(logo_url):
        logo_url_set.add(logo_url)


def compose_df(classification_data, email_info):
    interaction_str = email_info.get("Interaction Type", "{}")

    # Parse the classification JSON string into a dictionary
    interaction_dict = json.loads(interaction_str)

    # Extract relevant fields (company name, category, website)
    company_name = interaction_dict.get("company_name", "")
    category = interaction_dict.get("category", "")
    website = interaction_dict.get("website", "")

    # Append the extracted data as a tuple (or list) to the classification_data list
    classification_data.append({
        "Company Name": company_name,
        "Interaction Type": category,
        "Website": website
    })



@st.cache_data
def display_random_logos(image_urls):
    num_columns = 7  # Number of columns to display
    random.shuffle(image_urls)  # Shuffle the images to randomize their order

    # Generate random widths for each image (between 50px and 150px)
    widths = [random.randint(30, 90) for _ in image_urls]

    # Iterate over the images and display them in columns
    for i in range(0, len(image_urls), num_columns):
        cols = st.columns(num_columns)
        for idx, img_url in enumerate(image_urls[i:i + num_columns]):
            with cols[idx]:
                width = widths[i + idx]
                # Display the image with rounded corners and random width
                html = f'''
                    <img src="{img_url}" 
                         style="border-radius:50%; 
                                width:{width}px; 
                                height:{width}px; 
                                object-fit:contain;
                                margin-bottom:10px;"
                    />
                '''
                st.markdown(html, unsafe_allow_html=True)


@st.fragment
def display_df(df):
    # drop duplicate companies
    df.drop_duplicates(subset=['Company Name'], inplace=True)

    # add columns to df_clean
    df['Select Option'] = '-'
    df['Select'] = False

    # Create options for the dropdown
    dropdown_options = ['Request Data', 'Modify Data', 'Erase Data']

    column_config = {
        'Select Option': st.column_config.SelectboxColumn(
            options=dropdown_options),
        'Website': st.column_config.LinkColumn(),
        'Select': st.column_config.CheckboxColumn(),
    }

    # Display editable dataframe with dropdowns
    edited_df = st.data_editor(
        df,
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        column_order=['Select', 'Company Name', 'Interaction Type', 'Website', 'Select Option']
    )

    # keep only selected rows
    selected_rows = edited_df[edited_df['Select']]
    st.session_state['selected_rows'] = selected_rows
    return selected_rows


@st.dialog("Email Preview")
def preview_email(email, subject, body, service):
    st.text_input("To", email)
    st.text_input("Subject", subject)
    st.text_area(label="Body", value=body, label_visibility='hidden', height=300)

    st.write('')

    send_button = st.button("Send")

    if send_button:
        # compose email
        message = create_message(st.session_state['user_info'].get('email'), email, subject, body)

        # Send the email
        send_message(service, 'me', message)
        # Show success message
        st.success("Email sent successfully!")


def get_email_template():
    # Define the email templates for different GDPR requests
    email_template = {
        "Request Data": {
            "subject": "GDPR Data Access Request",
            "body": """Dear Data Protection Officer,

    I am writing to request access to my personal data as per Article 15 of the General Data Protection Regulation (GDPR). I would like to receive a copy of all personal data that {company_name} have collected about me, as well as any information regarding how and why my data is being processed.

    Please provide the following:
    - Categories of personal data being processed
    - The specific purposes for processing my data
    - Information on any third parties with whom my data has been shared
    - The source of my personal data if it was not collected directly from me

    Thank you for your attention to this matter. I look forward to receiving a response within the GDPR-mandated timeframe.

    Sincerely,
    {user_name}
    """
        },
        "Modify Data": {
            "subject": "GDPR Data Modification Request",
            "body": """Dear Data Protection Officer,

    I am reaching out to request a modification to my personal data under Article 16 of the General Data Protection Regulation (GDPR). I believe certain data you hold about me may be inaccurate or incomplete, and I would like this data to be corrected as soon as possible.

    Please update the following information:
    - [Specify the data to be updated, e.g., name, address, contact information, etc.]

    If you require any additional information from me to fulfill this request, please let me know at your earliest convenience.

    Thank you for your cooperation and prompt attention to this request.

    Sincerely,
    {user_name}
    """
        },
        "Erase Data": {
            "subject": "GDPR Data Erasure Request",
            "body": """Dear Data Protection Officer,

    I am contacting you to request the deletion of my personal data in accordance with Article 17 of the General Data Protection Regulation (GDPR). I no longer wish for my personal data to be processed by {company_name}, and I request that all relevant data be permanently deleted.

    Please confirm the deletion of my personal data, or, if my request cannot be fulfilled in full, kindly provide the reason and any alternative actions that can be taken.

    Thank you for your cooperation, and I look forward to your prompt confirmation of the erasure of my data.

    Sincerely,
    {user_name}
    """
        }
    }
    return email_template


def google_authenticate():
    authenticator = Authenticate(
        secret_credentials_path='credentials.json',
        cookie_name='my_cookie_name',
        cookie_key='this_is_secret',
        redirect_uri='http://localhost:8501/',
    )

    # Catch the login event
    authenticator.check_authentification()
    return authenticator


def build_gmail_service():
    if "credentials" in st.session_state:
        credentials_info = json.loads(st.session_state["credentials"])
        credentials = Credentials.from_authorized_user_info(credentials_info)

        # Refresh the token if it's expired
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            # Update the stored credentials
            st.session_state["credentials"] = credentials.to_json()

        # Build the Gmail service
        gmail_service = build('gmail', 'v1', credentials=credentials)
        return gmail_service


# Function to create an email message
def create_message(sender, to, subject, message_text):
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw_message}


# Function to send the email using Gmail API
def send_message(service, user_id, message):
    try:
        message = service.users().messages().send(userId=user_id, body=message).execute()
        print(f"Message Id: {message['id']}")
        return message
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


# Function to fetch emails for a specific category and date range
def fetch_emails_by_label(service, label_id, days, num_emails=10):
    # Calculate the start date (n days ago) and the end date (tomorrow)
    start_date = (datetime.now() - timedelta(days=days - 1)).strftime('%Y/%m/%d')
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y/%m/%d')

    # Compose query and exclude emails from personal category
    query = f'after:{start_date} before:{tomorrow} -label:CATEGORY_PERSONAL'

    # Fetch emails from the specified label and date range
    results = service.users().messages().list(
        userId='me',
        q=query,
        maxResults=num_emails,
        labelIds=[label_id]  # Fetch emails for a single category
    ).execute()

    messages = results.get('messages', [])
    return messages


# Function to fetch emails from multiple categories and date range
def fetch_emails(service, days, num_emails=10):
    # Categories to fetch from
    categories = ['CATEGORY_PROMOTIONS', 'CATEGORY_UPDATES']

    # Fetch emails from each category separately and combine them
    combined_emails = []
    for category in categories:
        print(f"Fetching emails from {category} for the last {days} day(s)...")
        emails = fetch_emails_by_label(service, category, days=days, num_emails=num_emails)
        combined_emails.extend(emails)

    return combined_emails


# Read and decode an email's content, and include the date it was sent
def get_email_content(service, message_id):
    try:
        message = service.users().messages().get(userId='me', id=message_id).execute()
        payload = message.get('payload', {})
        headers = payload.get('headers', [])
        data = ''

        # Extract subject, sender, and date
        subject = None
        sender = None
        date = None

        # Loop through headers to extract subject, sender, and date
        for header in headers:
            if header['name'] == 'Subject':
                subject = header['value']
            if header['name'] == 'From':
                sender = header['value']
            if header['name'] == 'Date':
                # Example date format: "Thu, 7 Oct 2021 14:58:33 +0000"
                date_str = header['value']
                # Try to parse the date and format it as YYYY-MM-DD
                try:
                    parsed_date = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
                    date = parsed_date.strftime("%Y-%m-%d")  # Only return the date part
                except ValueError:
                    # Fallback to raw date string if parsing fails
                    date = date_str

        # Extract content of the email (only plain text for simplicity)
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    break
        elif 'body' in payload:
            data = payload['body']['data']

        # Decode email content
        if data:
            email_content = base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8')
            return subject, sender, date, email_content
        else:
            raise ValueError("No content found in the email.")

    except Exception as e:
        print(f"Error retrieving email {message_id}: {e}")
        return None, None, None, None


# Classify email content and extract company info using Gemini
def classify_email_with_gemini(email_content):
    SYSTEM_INSTRUCTIONS = """
    You are a helpful AI that helps classify emails and extract relevant information.

    All emails are classified into one of the following categories: interacted, not interacted.
    Interacted emails are triggered directly by a user’s action. 
    They are functional and usually contain important information, such as confirmations (order confirmations, 
    password resets, account creation), notifications about transactions, or updates on user-initiated requests.

    Not interacted emails are not triggered by any specific user action. They are often used to keep users engaged, 
    provide updates, send offers, or remind users of products/services. Examples include newsletters, promotional emails, and other marketing content.
    """

    PROMPT = f"""
    Based on the following email content, identify the following:
    1. The name of the company (if not mentioned explicitly, infer from the context).
    2. Classify the email into one of the following categories: interacted, not interacted. 
    3. Company website (if not mentioned explicitly, infer from the context).

    Email content:
    {email_content}
    """

    response_schema = {
        "type": "OBJECT",
        "properties": {
            "company_name": {"type": "STRING"},
            "interaction_type": {"type": "STRING", "enum": ["interacted", "not interacted"]},
            "website": {"type": "STRING"}
        }, "required": ["company_name", "category", "website"]
    }

    credentials, project_id = google.auth.load_credentials_from_file('service_acc.json')

    vertexai.init(project=project_id, location="us-central1", credentials=credentials)
    model = GenerativeModel("gemini-1.5-flash-001",
                            system_instruction=SYSTEM_INSTRUCTIONS)

    response = model.generate_content(
        [PROMPT],
        generation_config=GenerationConfig(response_mime_type="application/json", response_schema=response_schema)
    )

    return response.text


# Main function to fetch, classify, and return emails as a dictionary
def process_emails(service, days, ignored_categories):

    st.session_state['progress_bar'] = st.progress(0, text="Fetching emails...")
    messages = fetch_emails(service, days)

    if not messages:
        # print("No emails found.")
        return {}

    email_data = {}

    # print(f"Processing {len(messages)} emails...")
    st.session_state['progress_bar'].progress(25, text="Analyzing email content...")

    for msg in messages:
        message_id = msg['id']
        subject, sender, date, email_content = get_email_content(service, message_id)

        if email_content is None or sender is None:
            # print(f"Skipping email {message_id} due to missing content or sender.")
            continue

        # Retry mechanism for the Gemini call in case of rate limiting (429 Resource Exhausted)
        while True:
            try:
                # Use Gemini to classify and extract information
                gemini_result = classify_email_with_gemini(email_content)

                if gemini_result:
                    email_data[message_id] = {
                        "Subject": subject,
                        "Sender": sender,
                        "Date": date,
                        "Classification": gemini_result
                    }
                    print(f"Successfully processed email {message_id}.")
                else:
                    print(f"Skipping email {message_id} due to failed Gemini classification.")
                break  # Exit the while loop if processing succeeds

            except Exception as e:
                if '429' in str(e) or 'Quota exceeded' in str(e):
                    print(f"Rate limit hit (429 Quota exceeded). Waiting for 60 seconds...")
                    time.sleep(60)  # Wait for 60 seconds before retrying
                else:
                    print(f"Skipping email {message_id} due to unexpected error: {e}")
                    break  # Exit the while loop if another exception occurs

    st.session_state['progress_bar'].progress(99, text="Finishing...")

    # get rid of progress bar
    st.session_state['progress_bar'].empty()

    return email_data
