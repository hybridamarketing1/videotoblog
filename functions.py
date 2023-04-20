"""def extract_video_id(url):
    video_id = re.search(r'v=([^&]*)', url).group(1)
    return video_id

def get_transcript(url):
    video_id = extract_video_id(url)
    try:

        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['it'])


    except Exception as e:
        print(e)
        return e

    transcript_text = ''
    for line in transcript:
        transcript_text += line['text'] + '\n'
    
    return transcript_text"""