# Start by importing the necessary libraries:

import os
import re
from typing import Optional, Tuple

import openai
import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from airtable_authenticator import AirtableAuthenticator
from streamlit.components.v1 import html
import yaml
from pyairtable import Table
import bcrypt



st.set_page_config(page_title="YouTube Transcript to Article", page_icon=":memo:", layout="wide")


# Set the API key
openai.api_key = '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'


def extract_video_id(url: str) -> Optional[str]:
    """
    Extracts and returns the video ID from a given YouTube URL.
    """
    video_id = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{10}[048AEIMQUYcgkosw])', url)
    return video_id.group(1) if video_id is not None else None

def get_transcript(url: str, lang: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Returns the transcript text for a given YouTube video URL and language. 
    """
    video_id = extract_video_id(url)
    if not video_id:
        return None, "Invalid video URL"

    transcript_text = ''
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
        for line in transcript:
            transcript_text += line['text'] + '\n'
    except Exception as e:
        return None, str(e)

    return transcript_text, None


def gpt_transcript(transcript: str, title: str) -> str:
    """
    Generates a long-form SEO optimized article from a given video transcript using OpenAI GPT-3.
    """
    prompt = [
        {"role": "system", "content": 'You are a Neil Patel a famous long form SEO Copywriter that can create long form SEO optimized articles following the classic format of H1, H2 and paragraph.'},
        {"role": "user", "content": f'Create a long-form SEO optimized article about {title} using the following video transcript:\n\n{transcript}\n\nArticle:'}
    ]

    try:
        response = openai.ChatCompletion.create(model="gpt-4", messages=prompt, max_tokens=4000, temperature=0.5)
        article = response.choices[0].message
    except Exception as e:
        article = None
        st.write(f"Error: {e}")

    return article['content'] if article else "Failed to generate article content"


# Set up Airtable
API_KEY = 'keyoJUGM1IVvMzCGZ'#"patptrQqeh0X21ZCK.9c608947b9d38955d5a217a6a7a92dccfd1243d8997eff4f4ef9960303e531cf"
BASE_ID = "appvng1h25Daw0Hk4"
TABLE_NAME = "users"
airtable = Table(API_KEY, BASE_ID, TABLE_NAME)

# Load the configuration file
#with open('config.yaml') as file:
 #   config = yaml.safe_load(file)

cookie_config = {
    'name': 'streamlit_auth',
    'key': 'streamlit_auth_key',
    'expiry_days': 30
}

# Replace the config['cookie'] with cookie_config in Authenticator
authenticator = AirtableAuthenticator(
    airtable,
    #cookie_config['name'],
    #cookie_config['key'],
    #cookie_config['expiry_days']
)


# Streamlit interface
def main():
        # Load the HTML template with the Meta Pixel code
    with open('meta_pixel_template.html', 'r') as f:
        meta_pixel_template = f.read()

    # Replace the '{{body}}' placeholder with your app's content
    app_content = "<h1>Hello, Streamlit!</h1>"
    rendered_template = meta_pixel_template.replace('{{body}}', app_content)

    # Display the rendered HTML template in your Streamlit app
    html(rendered_template, height=600)

    # Add authentication
    name, authentication_status, username = authenticator.login('Login', 'logout')

    if authentication_status:
        st.write(f'Welcome *{name}*')

        # Get the user's record from Airtable
        records = airtable.all(formula=f"Username = '{username}'")

        user_record = records[0] if records else None

        # Check if the user has reached the article limit
        if user_record["fields"]["ArticleCount"] < 3:
            st.title("Convert a YouTube Transcript into a Long-Form Article")

            title = st.text_input("Enter the title of your article:")
            url = st.text_input("Enter the YouTube video URL:")
            lang = st.selectbox("Select the language of the video:", ["en", "it"])

            if st.button("Generate Article"):
                if url:
                    transcript, error = get_transcript(url, lang)
                    if error:
                        st.error(error)
                    else:
                        generated_blog = gpt_transcript(transcript, title=title)
                        st.success("Article Generated Successfully!")
                        st.write(generated_blog)

                        # Increment the article count for the user
                        user_record["fields"]["ArticleCount"] += 1
                        airtable.update(user_record["id"], {"ArticleCount": user_record["fields"]["ArticleCount"]})
                else:
                    st.error('Please enter a YouTube URL')
        else:
            st.error("Freemium Usage Limit Achieved. Please upgrade to the premium.")
            # Define the URL and the button text
            url = "https://buy.stripe.com/5kAcP2aXo6n0f3G4gg"
            button_text = "Buy More SEO Blog Post"

            # Display the link as a button
            st.markdown(f'<a href="{url}" target="_blank"><button style="color: white; background-color: #FF4F40; border: none; padding: 8px 16px; text-align: center; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 12px;">{button_text}</button></a>', unsafe_allow_html=True)
    else:
        if authentication_status == False:
            st.write('wrong password')
            user = authenticator._get_user(username)
            if user:
                stored_password = user["Password"].encode('utf-8')
                entered_password = authenticator.password.encode('utf-8')
                is_password_correct = bcrypt.checkpw(entered_password, stored_password)
            else:
                st.write(f"Debug: No user found with username: {username}")
            st.error('Username/password is incorrect')
        elif authentication_status == None:
            st.warning('Please enter your username and password')

    # Add a signup page
    if st.sidebar.button("Sign Up"):
        st.session_state.signup = True

    if st.session_state.get("signup", False):
        email = st.sidebar.text_input("Enter your email:")
        name = st.sidebar.text_input("Enter your name:")
        username = st.sidebar.text_input("Enter a username:")
        password = st.sidebar.text_input("Enter a password:", type="password")
        confirm_password = st.sidebar.text_input("Confirm your password:", type="password")

        if st.sidebar.button("Register"):
            if password == confirm_password:
                authenticator.register_user(email, name, username, password)
                st.sidebar.success("Registration successful! You can now log in.")
                st.session_state.signup = False
            else:
                st.sidebar.error("Passwords do not match.")
        if st.sidebar.button("Cancel"):
            st.session_state.signup = False

if __name__ == '__main__':
    main()
# The previous code has been refactored and modified to work with Streamlit library, which allows us to create an interactive web app. 

# Changes made to the code:

# - Added the Streamlit library to create the interface.
# - Modified the get_transcript function to accept the language as a parameter and retrieve the transcript only in the selected language.
# - Modified the gpt_transcript function to use the Davinci-Codex engine, which is optimized for code generation tasks.
# - Changed the error_handling function to provide more informative error messages to the user.
# - Reorganized the code and added comments for better readability