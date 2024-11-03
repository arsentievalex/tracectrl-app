import pandas as pd
import streamlit as st
import time
from streamlit.components.v1 import html
from utils import (
    get_first_working_url, return_privacy_url, extract_email, display_df,
    display_random_logos, read_json, compose_df, compose_logo_url,
    preview_email, get_email_template, google_authenticate, build_gmail_service, create_message, send_message
)

def initialize_authenticator():
    """Authenticate the user and initialize Google service if connected."""
    authenticator = google_authenticate()
    with st.sidebar:
        authenticator.login()

    if st.session_state.get('connected'):
        st.session_state['gmail_service'] = build_gmail_service()
        display_user_info(authenticator)
    else:
        display_homepage()
        return False

    return True

def display_user_info(authenticator):
    """Display logged-in user info and a logout button."""
    st.sidebar.image(st.session_state['user_info'].get('picture'), width=80)
    st.sidebar.write(f"You are logged in as {st.session_state['user_info'].get('name')}")
    if st.sidebar.button('Log out'):
        authenticator.logout()

def display_homepage():
    """Display the homepage if the user is not connected."""
    with open('index.html', 'r') as file:
        html_content = file.read()
    html(html_content, height=600)

@st.fragment
def configure_advanced_options():
    """Set advanced options for scanning emails."""
    with st.expander('Advanced Options'):
        day_range = st.slider('Fetch Emails From the Past (Days)', min_value=1, max_value=60, step=7, value=7)
        ignored_categories = st.multiselect('Ignore Categories', ['Personal', 'Promotions', 'Social', 'Updates', 'Forums'])
    return day_range, ignored_categories

@st.fragment
def display_options():
    """Display advanced options and the Scan Inbox button."""

    st.markdown("""
    ### How to Get Started

    Follow these easy steps to control your digital trace:

    1. **Scan Your Inbox**: Click the **Scan Inbox** button to analyze your emails and identify companies with your data.
    2. **Adjust Advanced Settings** (Optional): Customize your scan with options like date range and categories to ignore.
    3. **Review and Select**: Browse the results, choose a company and request type (e.g., Access, Erase, Modify).
    4. **Run the Bot**: Click **Run Bot** to preview your request email, then hit **Send Email** to send it.

    """)

    scan_button = st.button('Scan Inbox')
    day_range, ignored_categories = configure_advanced_options()

    if scan_button:
        # for demo purposes, load sample emails
        email_data = read_json('gemini_processed_emails.json')
        # email_data = process_emails(gmail_service, day_range, ignored_categories)

        display_scan_progress()
        logo_url_list, classification_data = extract_email_data(email_data)

        display_results(logo_url_list, classification_data)

        run_bot()

def display_scan_progress():
    """Simulate scanning progress for demo purposes."""
    st.session_state['progress_bar'] = st.progress(0, text="Fetching emails...")
    time.sleep(4)
    st.session_state['progress_bar'].progress(25, text="Analyzing email content...")
    time.sleep(4)
    st.session_state['progress_bar'].progress(50, text="Looking for companies...")
    time.sleep(3)
    st.session_state['progress_bar'].progress(99, text="Finishing...")
    time.sleep(3)
    st.session_state['progress_bar'].empty()

def extract_email_data(email_data):
    """Process and extract email data for display."""
    logo_url_set = set()
    classification_data = []

    for email_id, email_info in email_data.items():
        compose_logo_url(logo_url_set, email_info)
        compose_df(classification_data, email_info)

    return list(logo_url_set), classification_data

def display_results(logo_url_list, classification_data):
    """Display logos and the classified data table."""
    st.subheader("These companies and more have your data...")
    display_random_logos(logo_url_list)
    df_clean = pd.DataFrame(classification_data)
    display_df(df_clean)

@st.fragment
def run_bot():
    """Control bot execution for single or multiple selected rows."""
    columns = st.columns(3)

    with columns[0]:
        run_button = st.button('Run Bot')

    with columns[2]:
        email_preview = st.toggle('Preview Email', value=True, help='Available for single selection only')

    # Single email send with preview
    if run_button and email_preview:
        if not validate_selection(single_row=True):
            return
        send_email(st.session_state['selected_rows'].iloc[0])

    # Mass email send without preview
    if run_button and email_preview==False:
        if not validate_selection(single_row=False):
            return
        for _, row in st.session_state['selected_rows'].iterrows():
            send_email(row, preview=False)

def validate_selection(single_row=True):
    """Validate user selection based on single or multiple row selections."""
    selected_rows = st.session_state['selected_rows']
    if single_row and len(selected_rows) != 1:
        st.warning('Please select exactly one row to proceed with preview.')
        return False
    elif not single_row and len(selected_rows) < 1:
        st.warning('Please select at least one row for mass email send.')
        return False
    if '-' in selected_rows['Select Option'].values:
        st.warning('Please select a request type for all selected rows.')
        return False
    return True

def send_email(row, preview=True):
    """Compose and send email based on row data, optionally preview."""
    selected_website = row['Website']
    selected_option = row['Select Option']
    selected_company = row['Company Name']

    try:
        # Retrieve privacy URL and email address
        response = return_privacy_url(selected_website)
        url = get_first_working_url(response.json())
        email = extract_email(url)

        email_template = get_email_template()
        email_subject = email_template[selected_option]['subject']
        email_body = email_template[selected_option]['body'].format(
            company_name=selected_company, user_name=st.session_state['user_info'].get('name')
        )

        if preview:
            preview_email(email, email_subject, email_body, st.session_state['gmail_service'])
        else:
            # Sending multiple emails without preview
            message = create_message(st.session_state['user_info'].get('email'), email, email_subject, email_body)

            # Send the email
            send_message(st.session_state['gmail_service'], 'me', message)
            st.success(f"Email sent to {selected_company}")
    except Exception:
        st.error(f"Failed to send email to {selected_company}.")


def sidebar_footer():
    """Display the footer in the sidebar."""
    # display the footer in the very bottom of the sidebar
    for _ in range(10):
        st.sidebar.markdown('')

    st.sidebar.markdown(
        """
        ---
        Project built with ❤️ for the [Google Cloud Gemini Hackathon](https://googlecloudgeminihackathon.devpost.com/)
        """)

def main():
    if initialize_authenticator():
        display_options()
    sidebar_footer()

if __name__ == '__main__':
    main()

