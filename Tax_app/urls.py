from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('login',views.user_login,name='login'),
    path('logout',views.logout_user, name='logout'),
    path('',views.ai_agent,name='ai_agent'),
    path('fetch_agents_data/',views.fetch_agents_data,name="fetch_agents_data"),
    path('add_agent/',views.add_agent_data,name="add_agent"),
    path('update-agent/', views.update_agent, name='update_agent'),
    path('delete-agent/<str:agent_id>/', views.delete_agent, name='delete_agent'),
    path('phone-lists/',views.phone_lists, name='phone_lists'),
    path('fetch_phone_data/',views.fetch_phone_data,name="fetch_phone_data"),
    path('update-phone-data/', views.update_phone_data, name='update_phone_data'),
    path('make_call/',views.make_call,name='make_call'),
    path('history-logs/', views.history_logs, name='history_logs'),
    path('fetch_call_history/', views.fetch_call_history, name='fetch_call_history'),
    path('get-call-history-data/<int:page>/<int:limit>/', views.get_call_history_data, name='get_call_history_data'),
    path('history-log-detail/<int:log_id>/', views.history_log_detail, name='history_log_detail'),

]