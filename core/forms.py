from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Profile, Project, Task
from .validators import (
    validate_no_html_tags,
    validate_phone_peru,
    validate_strong_password_extra,
    validate_no_sql_injection,
)
from .utils import sanitize_input, sanitize_email


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ejemplo@dominio.com'})
    )
    first_name = forms.CharField(
        max_length=30,
        label='Nombre',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30,
        label='Apellido',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if len(username) < 4:
            raise ValidationError('El usuario debe tener al menos 4 caracteres.')
        if not username.isalnum():
            raise ValidationError('Solo se permiten caracteres alfanuméricos.')
        validate_no_html_tags(username)
        validate_no_sql_injection(username)
        return username

    def clean_email(self):
        email = sanitize_email(self.cleaned_data.get('email', ''))
        if User.objects.filter(email=email).exists():
            raise ValidationError('Este correo ya está registrado.')
        return email

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if password:
            validate_strong_password_extra(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        first_name = cleaned_data.get('first_name', '')
        last_name = cleaned_data.get('last_name', '')

        if first_name.lower() == last_name.lower():
            self.add_error('last_name', 'El apellido no puede ser igual al nombre.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = sanitize_email(self.cleaned_data['email'])
        user.first_name = sanitize_input(self.cleaned_data['first_name'])
        user.last_name = sanitize_input(self.cleaned_data['last_name'])
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['role', 'bio', 'phone']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '9XXXXXXXX'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if phone:
            validate_phone_peru(phone)
        return phone

    def clean_bio(self):
        bio = self.cleaned_data.get('bio', '')
        validate_no_html_tags(bio)
        return sanitize_input(bio)


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del proyecto'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción del proyecto'}),
        }

    def clean_name(self):
        name = sanitize_input(self.cleaned_data.get('name', ''))
        validate_no_html_tags(name)
        validate_no_sql_injection(name)
        return name


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'project', 'assigned_to', 'priority', 'status', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Implementar login de usuarios'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe la tarea...'}),
            'project': forms.Select(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Hacer que project sea obligatorio (elimina "---------")
        self.fields['project'].empty_label = None
        self.fields['project'].required = True
        
        # Hacer que assigned_to sea opcional pero con label claro
        self.fields['assigned_to'].empty_label = 'Asignar a mí mismo (opcional)'
        self.fields['assigned_to'].required = False
        
        # Filtrar proyectos por usuario (si no es staff)
        if user and not user.is_staff:
            self.fields['project'].queryset = Project.objects.filter(owner=user, is_active=True)
            self.fields['assigned_to'].queryset = User.objects.filter(id=user.id)
        
        # Labels más amigables
        self.fields['project'].label = 'Proyecto'
        self.fields['assigned_to'].label = 'Asignado a'
        self.fields['priority'].label = 'Prioridad'
        self.fields['status'].label = 'Estado'
        self.fields['due_date'].label = 'Fecha límite'

    def clean_title(self):
        title = sanitize_input(self.cleaned_data.get('title', ''))
        if len(title) < 3:
            raise ValidationError('El título debe tener al menos 3 caracteres.')
        validate_no_html_tags(title)
        validate_no_sql_injection(title)
        return title

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        due_date = cleaned_data.get('due_date')

        if status == 'pending' and due_date:
            if due_date < timezone.now().date():
                self.add_error('due_date', 'No puedes asignar una fecha pasada a una tarea pendiente.')

        return cleaned_data