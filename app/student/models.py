from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class StudentManager(BaseUserManager):

    def create_user(self, email, username=None, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        
        email = self.normalize_email(email)
        if isinstance(email, str):
            email = email.encode('utf-8', errors='ignore').decode('utf-8')
        
        if username is None:
            username = email.split('@')[0] if '@' in email else email
        
        if isinstance(username, str):
            username = username.encode('utf-8', errors='ignore').decode('utf-8')
        
        if 'name' not in extra_fields:
            extra_fields['name'] = username
        
        user = self.model(email=email, username=username, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, username, password, **extra_fields)


class Student(AbstractUser):
    name = models.CharField(max_length=255)
    email = models.EmailField('email address', unique=True, blank=False, null=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = StudentManager()

    def __str__(self):
        return self.email or self.username
