from .models import *
import datetime
import json

def filter_voices(voices):
    voice_list = []
    male_count = 0
    female_count = 0
    
    for voice in voices:
        if voice.provider == 'elevenlabs' and voice.accent == 'American':
            if voice.gender == 'male' and male_count < 3:
                voice_list.append(voice)
                male_count += 1
            elif voice.gender == 'female' and female_count < 3:
                voice_list.append(voice)
                female_count += 1
        if male_count >= 3 and female_count >= 3:
            break  # Stop if we have enough voices

    return voice_list

def format_timestamp_to_time(timestamp):
    """Converts a timestamp in milliseconds to 'HH:MM AM/PM' format."""
    seconds = timestamp / 1000.0
    dt_object = datetime.datetime.fromtimestamp(seconds)
    return dt_object.strftime('%I:%M %p')

def convert_timestamp_to_date(timestamp):
    # Convert milliseconds to seconds
    timestamp_seconds = timestamp / 1000.0
    # Create a datetime object from the timestamp
    date = datetime.datetime.fromtimestamp(timestamp_seconds)
    return date.strftime("%m/%d/%Y")

def ms_to_time_string(milliseconds):
    """Convert milliseconds to MM:SS format"""
    total_seconds = int(milliseconds)
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"

def format_transcript_segment(segment_data, speaker_name):
    """Format a single transcript segment into HTML"""
    try:
        # Parse the segment if it's a string
        if isinstance(segment_data, str):
            segment_data = json.loads(segment_data)
            
        content = segment_data.get('content', '').strip('"')
        words = segment_data.get('words', [])
        
        # Get the start time of the first word
        start_time = words[0]['start'] if words else 0
        
        html = f"""
        <li>
            <h4 class="mb-0">{ms_to_time_string(start_time)}</h4>
            <div class="list_text">
                <h2 class="mb-0">{speaker_name}:</h2>
                <p class="mb-0">{content}</p>
            </div>
        </li>
        """
        return html
    except Exception as e:
        print(f"Error in format_transcript_segment: {str(e)}")  # For debugging
        return f"<!-- Error processing transcript segment: {str(e)} -->"
    
def convert_duration_to_human_readable(milliseconds):
     # Convert milliseconds to seconds using integer division
    total_seconds = milliseconds // 1000
    
    # Calculate minutes and remaining seconds
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    
    # Format as string
    return f"{minutes}:{seconds:02d}"


def format_single_segment(segment, agent_name, user_name):
    role = segment.get('role', '')
    speaker_name = agent_name if role == 'agent' else user_name
    return format_transcript_segment(segment, speaker_name)

def process_transcript(transcript, agent_name, user_name):
    if not transcript:
        return []

    try:
        transcript_data = json.loads(transcript) if isinstance(transcript, str) else transcript
        
        if isinstance(transcript_data, dict):
            return [format_single_segment(transcript_data, agent_name, user_name)]
        elif isinstance(transcript_data, list):
            return [format_single_segment(segment, agent_name, user_name) for segment in transcript_data]
        else:
            return [format_transcript_segment(transcript_data, agent_name)]
    except Exception as e:
        print(f"Error processing transcript: {str(e)}")
        return [f"<!-- Error processing transcript: {str(e)} -->"]