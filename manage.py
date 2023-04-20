
import json
import re
import openai
from youtube_transcript_api import YouTubeTranscriptApi
from typing import Tuple, Optional
from requests.exceptions import HTTPError
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
import os

# Set the API key
openai.api_key = os.environ.get("OPENAI_API_KEY")


def extract_video_id(url: str) -> Optional[str]:
    # Improved regex pattern to handle different types of YouTube URLs
    video_id = re.search(r'(?:\?v=|\/\d{2}\.[a-zA-Z0-9_+&#-%\/?=~_|!:,.;]()[a-zA-Z0-9_-]{11})', url)
    return video_id.group(1) if video_id is not None else None


def get_transcript(url: str) -> Tuple[Optional[str], Optional[str]]:
    video_id = extract_video_id(url)
    if not video_id:
        return None, "Invalid video URL"

    transcript_text = ''
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'it', 'de', 'es'])
        for line in transcript:
            transcript_text += line['text'] + '\n'
    except Exception as e:
        return None, str(e)

    return transcript_text, None


def gpt_transcript(transcript: str, title: str) -> str:
    prompt = [
        {"role": "system", "content": 'You are a Neil Patel a famous long form SEO Copywriter that can create long form SEO optimized articles following the classic format of H1, H2 and paragraph.'},
        {"role": "user", "content": f'Please use this summary to create a long-form SEO optimized article about {title} using the following video transcript:\n\n{transcript}\n\nArticle:'}
    ]

    try:
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=prompt)
        article = response.choices[0]["message"].get('content')
    except Exception as e:
        article = None
        print(f"Error: {e}")

    return article.strip() if article else "Failed to generate article content"

# Improved user experience by providing more informative error messages
def error_handling(e):
    if isinstance(e, HTTPError):
        return f"An HTTP error occurred: {e.response.status_code}"
    elif isinstance(e, YouTubeTranscriptApi.CouldNotRetrieveTranscript):
        return "Could not retrieve transcript."
    else:
        return f"An unexpected error occurred: {e}"

# Django views
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()

    return render(request, 'signup.html', {'form': form})


@login_required
def index(request):
    if request.method == 'POST':
        url = request.POST.get('youtube_url')
        message = {}
        if url:
            transcript, error = get_transcript(url)
            if error:
                message['error'] = error_handling(error)
            else:
                generated_blog = gpt_transcript(transcript, title='Transforming YouTube Video into a Blog')
                message['generated_blog'] = generated_blog
        else:
            message['error'] = 'Please enter a YouTube URL'
        return render(request, 'index.html', message)
    return render(request, 'index.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('index')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
