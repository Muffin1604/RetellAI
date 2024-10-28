from django.shortcuts import render,redirect
from .models import *
from .retell_api import *
from django.views.decorators.csrf import csrf_exempt 
from django.http import JsonResponse
from django.contrib import messages
from django.http import HttpResponse
import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .serializers import *
from .utils import *
from django.views.decorators.http import require_POST
import pandas as pd

# Create your views here.
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('ai_agent')
        else:
            return render(request, "login.html", {'error_message': 'Invalid login credentials'})

    return render(request, "login.html")

def logout_user(request):
    logout(request)
    return redirect('login')

@login_required(login_url='/login')
def ai_agent(request):
    ai_agents = Agent.objects.all().order_by('-created_at')
    voice_list = Voice.objects.all()
    return render(request, 'ai-agent.html',{"ai_agents":ai_agents,"voice_list":voice_list})

@login_required(login_url='/login')
def phone_lists(request):
    phone_data = Phone_Number.objects.all()
    ai_agents_count = Agent.objects.count()  
    phone_num_count = Phone_Number.objects.count() 
    ai_agents = Agent.objects.all()  
    return render(request, 'phone-list.html',{"phone_data":phone_data,"ai_agents_count":ai_agents_count,"phone_num_count":phone_num_count,"ai_agents":ai_agents})
    
@login_required(login_url='/login')
def history_logs(request):
    return render(request, 'history-logs.html')

@csrf_exempt
def fetch_agents_data(request):
    if request.method == 'POST':
        try:
            fetch_and_save_all_agents(request)
            return JsonResponse({'status': 'success', 'message': 'Agents fetched successfully!'}, status=200)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@csrf_exempt
def fetch_phone_data(request):
    if request.method == 'POST':
        try:
            fetch_and_save_phone_numbers()
            return JsonResponse({'status': 'success', 'message': 'Phone data fetched successfully!'}, status=200)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

def update_phone_data(request):
    if request.method == "POST":
        phone_id = request.POST.get('phone_id')
        description = request.POST.get('description')
        inbound_agent_id = request.POST.get('inbound_agent')
        outbound_agent_id = request.POST.get('outbound_agent')

        try:
            phone_num = Phone_Number.objects.get(id=phone_id)

            inbound_agent = Agent.objects.get(id=inbound_agent_id)
            outbound_agent = Agent.objects.get(id=outbound_agent_id)

            phone_num.description = description
            phone_num.inbound_agent = inbound_agent
            phone_num.outbound_agent = outbound_agent
            phone_num.save()
            
            retell_response = update_phone_number_in_retell(phone_num.phone_num,inbound_agent.agent_id,outbound_agent.agent_id,description)

            if retell_response['status'] == 'success':
                return JsonResponse({'status': 'success','description': phone_num.description,'inbound_agent': phone_num.inbound_agent.id,'outbound_agent': phone_num.outbound_agent.id}, status=200)
            else:
                return JsonResponse({'status': 'error', 'message': retell_response['message']}, status=500)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@csrf_exempt
def add_agent_data(request):
    if request.method == 'POST':
        try:
            agent = create_and_save_agent(request)
            return JsonResponse({
                'status': 'success',
                'message': 'New Agent added successfully',
                'agent': {
                    'id': agent.id,
                    'agent_id': agent.agent_id,
                    'agent_name': agent.agent_name,
                    'voice_id': agent.voice.id  
                }
            }, status=200)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

def delete_agent(request, agent_id):
    try:
        agent = Agent.objects.get(agent_id=agent_id)
        delete_agent_retell(agent_id)
        agent.delete()
        return JsonResponse({'status': 'success'}, status=200)
    except Agent.DoesNotExist:
        return JsonResponse({'error': 'Agent not found'}, status=404)

@csrf_exempt
def make_call(request):
    if request.method == 'POST':
        from_number = request.POST.get('fromNumber')
        phone_numbers = []

        if 'excelFile' in request.FILES:
            excel_file = request.FILES['excelFile']
            df = pd.read_excel(excel_file)
            phone_numbers = df['phone_number'].tolist()  # Assuming 'phone_number' is the column name
        else:
            phone_numbers = json.loads(request.POST.get('phoneNumbers', '[]'))

    responses = []
    for phone in phone_numbers:
        try:
            response = initiate_call(from_number, phone)
            responses.append(response)
        except Exception as e:
            responses.append(f"Error calling {phone}: {str(e)}")

    messages.success(request, 'Calls initiated successfully!')
    return HttpResponse('Calls initiated successfully!')


def get_call_history_data(request, page, limit):
    try:
        start = int(page) * limit
        end = start + limit

        data = CallHistory.objects.all().order_by('-created_at')

        if data.exists():
            paginator = Paginator(data, limit) 
            try:
                call_history_data = paginator.page(page)
            except PageNotAnInteger:
                call_history_data = paginator.page(1)
            except EmptyPage:
                call_history_data = paginator.page(paginator.num_pages)

            pagination_data = {
                'page_number': call_history_data.number,
                'total_pages': paginator.num_pages,
                'has_previous': call_history_data.has_previous(),
                'has_next': call_history_data.has_next(),
            }
            serialized_data = CallHistorySerializer(data=call_history_data, many=True, context={'request': request})
            serialized_data.is_valid()
            return JsonResponse({'Error': 'NA', 'Status': serialized_data.data, 'pagination_data': pagination_data})
        return JsonResponse({'Error': 'No Data found', 'Status': 'No data found', 'pagination_data': list()})
    except Exception as ex:
        return JsonResponse({'Error': 'Some Error Occurred', 'Status': str(ex), 'pagination_data': list()})

@csrf_exempt
def fetch_call_history(request):
    if request.method == 'POST':
        try:
            fetch_and_save_call_history()
            return JsonResponse({'status': 'success', 'message': 'Call data fetched successfully!'}, status=200)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

def history_log_detail(request, log_id):
    call_history = get_object_or_404(CallHistory, id=log_id)
    
    # Use get_or_none pattern for agent lookup
    agent = Agent.objects.filter(agent_id=call_history.agent_id).first()
    agent_name = agent.agent_name if agent else "Agent"

    user_name = "User"
    
    context = {
        'call_date': convert_timestamp_to_date(call_history.start_timestamp),
        'call_history': call_history,
        'agent_name': agent_name,
        'user_name': user_name,
        'formatted_start_time': format_timestamp_to_time(call_history.start_timestamp),
        'formatted_end_time': format_timestamp_to_time(call_history.end_timestamp),
        'human_readable_time': convert_duration_to_human_readable(call_history.duration_ms),
        'formatted_transcript': process_transcript(call_history.transcript, agent_name, user_name),
    }
    
    return render(request, 'history-log-detail.html', context)

@csrf_exempt
@require_POST
def update_agent(request):
    try:
        data = json.loads(request.body)
        agent_id = data.get('agent_id')
        agent_name = data.get('agent_name')
        prompt = data.get('prompt')
        begin_message = data.get('begin_message')
        voice_id = data.get('voice_id')

        # Retrieve the selected voice
        voice = Voice.objects.get(id = voice_id)
        # Retrieve the Agent
        agent = Agent.objects.get(id=agent_id)

        # Now use the agent data for the API call
        success, error_message = update_agent_llm(
            agent_id=agent.agent_id,
            agent_name=agent_name,
            voice_id=voice.voice_id,
            llm_id=agent.llm_id,
            prompt=prompt,
            begin_message=begin_message
        )

        if not success:
            return JsonResponse({'status': 'error', 'message': f'Retell API update failed: {error_message}'}, status=500)

        # Update the agent in the database
        agent.agent_name = agent_name
        agent.prompt = prompt
        agent.beginMessage = begin_message
        agent.voice = Voice.objects.get(id=voice_id)
        agent.save()

        return JsonResponse({'status': 'success', 'message': 'Agent updated successfully'})
    except Agent.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Agent not found'}, status=404)
    except Voice.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Voice not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
