from retell import Retell
from dotenv import load_dotenv
import os
from .models import *
import re
from django.db import transaction
from django.shortcuts import get_object_or_404
from .utils import *

load_dotenv()

client =  Retell(api_key=os.environ.get('RETELL_API_KEY'))

def save_voices_from_retell():
    try:
        voice_responses = client.voice.list()
        voice_list = filter_voices(voice_responses)
        if voice_list:
            for voice_data in voice_list:
                voice, created = Voice.objects.get_or_create(
                    voice_id=voice_data.voice_id, 
                    defaults={
                        'voice_type': voice_data.voice_type,
                        'voice_name': voice_data.voice_name,
                        'provider': voice_data.provider,
                        'accent': voice_data.accent,
                        'gender': voice_data.gender,
                        'age': voice_data.age,
                        'avatar_url': voice_data.avatar_url,
                        'preview_audio_url': voice_data.preview_audio_url,
                    }
                )

                if created:
                    print(f"Voice {voice.voice_name} created successfully.")
                else:
                    print(f"Voice {voice.voice_name} updated successfully.")

    except Exception as e:
        print(f"Error fetching voices: {e}")


def fetch_and_save_all_agents(request):
    try:
        save_voices_from_retell()
        agent_responses = client.agent.list()
        user = request.user

        # Loop through each agent in the list and save/update in the database
        for agent_response in agent_responses:
            llm_websocket_url = agent_response.llm_websocket_url
            llm_id_match = re.search(r"llm_(\w+)", llm_websocket_url)
            llm_id = llm_id_match.group(0) if llm_id_match else None

            if llm_id:
                llm_response = client.llm.retrieve(llm_id)
                llm_id = llm_response.llm_id
                prompt = llm_response.general_prompt
                model_type = llm_response.model
                begin_message = llm_response.begin_message

            voice = get_object_or_404(Voice, voice_id=agent_response.voice_id)

            agent_obj, created = Agent.objects.update_or_create(
                agent_id=agent_response.agent_id, 
                defaults={
                    'user': user,
                    'agent_name': agent_response.agent_name,
                    'model_type': model_type,
                    'voice': voice,
                    'llm_websocket_url': agent_response.llm_websocket_url,
                    'llm_id': llm_id,
                    'prompt': prompt,
                    'language': agent_response.language,
                    'beginMessage':begin_message
                }
            )

            if created:
                print(f"Agent {agent_obj.agent_name} created successfully.")
            else:
                print(f"Agent {agent_obj.agent_name} updated successfully.")

    except Exception as e:
        print(f"Error fetching agents: {e}")


def create_and_save_agent(request):
    try:
        llm_response = client.llm.create(
            model='gpt-4o-mini',
            general_tools=[
            {
                "type":"end_call",
                "name":"end_call",
                "description":"cut the call"
            }
        ]
        )
        llm_websocket_url = llm_response.llm_websocket_url
        llm_id = llm_response.llm_id
        model_type = llm_response.model

        agent_response = client.agent.create(
            llm_websocket_url=llm_websocket_url,
            voice_id="11labs-Billy",
            agent_name="Single-Prompt Agent"
        )
        voice = get_object_or_404(Voice, voice_id=agent_response.voice_id)
        agent = Agent.objects.create(
            user=request.user,
            agent_id=agent_response.agent_id,
            agent_name=agent_response.agent_name,
            model_type=model_type,
            voice=voice,
            llm_websocket_url=agent_response.llm_websocket_url,
            llm_id=llm_id,
            language=agent_response.language
        )
        return agent

    except Exception as e:
        raise Exception(f"Error creating and saving agent: {str(e)}")


def delete_agent_retell(agent_id):
    try:
        client.agent.delete(agent_id)
    except Exception as e:
        raise Exception(f"Error in deleting agent: {str(e)}")  

def fetch_and_save_phone_numbers():
    try:
        phone_number_responses = client.phone_number.list()  

        for phone_data in phone_number_responses:
            phone_num = phone_data.phone_number

            try:
                inbound_agent = Agent.objects.get(agent_id=phone_data.inbound_agent_id)
            except Agent.DoesNotExist:
                inbound_agent = None 

            try:
                outbound_agent = Agent.objects.get(agent_id=phone_data.outbound_agent_id)
            except Agent.DoesNotExist:
                outbound_agent = None  

            phone_record, created = Phone_Number.objects.update_or_create(
                phone_num=phone_num,
                defaults={
                    'inbound_agent': inbound_agent,
                    'outbound_agent': outbound_agent,
                    'description': phone_data.nickname
                }
            )

            if created:
                print(f"Phone number: {phone_record.phone_num} created successfully.")
            else:
                print(f"Phone number: {phone_record.phone_num} updated successfully.")

    except Exception as e:
        print(f"An error occurred: {str(e)}")


def update_phone_number_in_retell(phone_number,inbound_agent,outbout_agent,description):
    try:
        phone_number_response = client.phone_number.update(
            phone_number=phone_number,
            inbound_agent_id=inbound_agent,
            outbound_agent_id=outbout_agent,
            nickname=description
        )

        if phone_number_response:
            return {'status': 'success'}
        else:
            return {'status': 'error', 'message': 'Failed to update phone number in Retell API'}

    except Exception as e:
        return {'status': 'error', 'message': f'Retell API error: {str(e)}'}
    
def retrieve_call_details(call_id):
    try:
        call_response = client.call.retrieve(call_id)
        return call_response
    except Exception as e:
        return {'status': 'error', 'message': f'Retell API error: {str(e)}'}

def update_agent_llm(agent_id, agent_name, voice_id, llm_id, prompt, begin_message):
    try:
        # Update agent in Retell API
        client.agent.update(
            agent_id=agent_id,
            agent_name=agent_name,
            voice_id=voice_id
        )
        
        # Update LLM in Retell API
        client.llm.update(
            llm_id=llm_id,
            general_prompt=prompt,
            begin_message=begin_message
        )
        return True, None
    except Exception as e:
        return False, str(e)

def initiate_call(from_phone_number, to_phone_number=False, name=False):    
    phone_str = str(to_phone_number)
    if not phone_str.startswith('+'):
        phone_str = '+' + phone_str
    phone_call_response = client.call.create_phone_call(
    from_number = from_phone_number,
    to_number = phone_str,
    )

    return phone_call_response

def fetch_and_save_call_history():
    try:
        call_history_response = client.call.list(
            
        )  # Fetch call history

        with transaction.atomic():  # Ensure all operations are atomic
            for call in call_history_response:
                # Only process phone calls
                if call.call_type != 'phone_call':
                    continue

                # Check if transcript_object exists
                transcript_data = None
                if hasattr(call, 'transcript_object') and call.transcript_object:
                    # Create a list of structured dictionaries for all transcript objects
                    transcript_data = [
                        {
                            'role': transcript_obj.role,
                            'content': transcript_obj.content,
                            'words': [
                                {
                                    'word': word.word,
                                    'start': word.start,
                                    'end': word.end
                                } for word in transcript_obj.words
                            ],
                        } for transcript_obj in call.transcript_object
                    ]

                # Determine the phone number to save based on the call direction
                phone_number = call.from_number if call.direction == 'inbound' else call.to_number
                
                # Update or create the CallHistory entry
                CallHistory.objects.update_or_create(
                    call_id=call.call_id,
                    defaults={
                        'agent_id': call.agent_id,
                        'phone_number': phone_number,
                        'call_type': call.direction,
                        'call_summary': call.call_analysis.call_summary,
                        'call_recording_url': call.recording_url,
                        'start_timestamp': call.start_timestamp,
                        'end_timestamp': call.end_timestamp,
                        'duration_ms': call.duration_ms,
                        'transcript': transcript_data if transcript_data else None,
                    }
                )

        return {'status': 'success', 'message': f'Saved {len(call_history_response)} call records'}
    
    except Exception as e:
        return {'status': 'error', 'message': f'Retell API error: {str(e)}'}