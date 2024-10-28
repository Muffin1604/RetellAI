from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError("Users must have an email address")
        if not username:
            raise ValueError("Users must have a username")

        user = self.model(
            email=self.normalize_email(email),
            username=username,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None):
        user = self.create_user(
            email=email,
            username=username,
            password=password,
        )
        user.is_admin = True
        user.is_staff = True
        user.save(using=self._db)
        return user

class CustomUser(AbstractBaseUser):
    email = models.EmailField(verbose_name="email", max_length=60, unique=True)
    username = models.CharField(max_length=30, unique=True)
    date_joined = models.DateTimeField(verbose_name="date joined", auto_now_add=True)
    last_login = models.DateTimeField(verbose_name="last login", auto_now=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True

class Voice(models.Model):
    voice_id = models.CharField(max_length=255, unique=True)
    voice_type = models.CharField(max_length=255)  
    voice_name = models.CharField(max_length=255)
    provider = models.CharField(max_length=255)  
    accent = models.CharField(max_length=255,null=True, blank=True)
    gender = models.CharField(max_length=50)  
    age = models.CharField(max_length=50,null=True, blank=True) 
    avatar_url = models.URLField()  
    preview_audio_url = models.URLField()

    def __str__(self):
        return self.voice_name
    
class Agent(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    agent_id = models.CharField(max_length=255, unique=True)
    agent_name = models.CharField(max_length=255)
    model_type = models.CharField(max_length=255)
    voice = models.ForeignKey(Voice, on_delete=models.CASCADE) 
    llm_websocket_url = models.CharField(max_length=255)
    llm_id = models.CharField(max_length=255)
    prompt = models.TextField(null=True, blank=True)
    beginMessage = models.TextField(null=True,blank=True)
    language = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True) 
    modified_at = models.DateTimeField(auto_now=True)     

    def __str__(self):
        return self.agent_name
# Create your models here.
class Phone_Number(models.Model):
    phone_num = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    inbound_agent = models.ForeignKey(Agent, null=True,blank=True,related_name='inbound_calls', on_delete=models.SET_NULL)
    outbound_agent = models.ForeignKey(Agent,null=True,blank=True, related_name='outbound_calls', on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.phone_num

class CallHistory(models.Model):
    call_id = models.CharField(max_length=50, unique=True)
    agent_id = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=50)
    call_type = models.CharField(max_length=50)
    call_summary = models.TextField(null=True, blank=True)
    call_recording_url = models.URLField(null=True, blank=True)
    start_timestamp = models.BigIntegerField()
    end_timestamp = models.BigIntegerField()
    duration_ms = models.IntegerField()
    transcript = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.call_id} - Agent {self.agent_id}"