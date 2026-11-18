import logging
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.views import View
from django.db.models import Q

from .forms import RegistrationForm, ProfileForm, TaskForm, ProjectForm
from .models import Task, Project, Profile

logger = logging.getLogger('core')


class RegisterView(View):
    template_name = 'core/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('core:dashboard')
        form = RegistrationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'¡Bienvenido {user.username}! Tu cuenta ha sido creada.')
            logger.info(f"[AUTH] Nuevo usuario registrado: {user.username}")
            return redirect('core:dashboard')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
        return render(request, self.template_name, {'form': form})


class LoginView(View):
    template_name = 'core/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('core:dashboard')
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            request.session['last_login_ip'] = request.META.get('REMOTE_ADDR', '')
            request.session.modified = True
            messages.success(request, f'¡Hola de nuevo, {user.username}!')
            logger.info(f"[AUTH] Login exitoso: {user.username}")
            next_url = request.GET.get('next', 'core:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Credenciales inválidas.')
            logger.warning(f"[AUTH] Login fallido para: {username}")
        return render(request, self.template_name)


class LogoutView(View):
    def post(self, request):
        username = request.user.username if request.user.is_authenticated else 'Anonymous'
        logout(request)
        request.session.flush()
        messages.info(request, 'Sesión cerrada correctamente.')
        logger.info(f"[AUTH] Logout: {username}")
        return redirect('core:login')


@login_required
def dashboard(request):
    user = request.user
    tasks = Task.objects.filter(
        Q(assigned_to=user) | Q(project__owner=user)
    ).select_related('project', 'assigned_to')

    stats = {
        'total': tasks.count(),
        'pending': tasks.filter(status='pending').count(),
        'in_progress': tasks.filter(status='in_progress').count(),
        'done': tasks.filter(status='done').count(),
        'overdue': sum(1 for t in tasks if t.is_overdue),
    }
    recent_tasks = tasks[:5]

    return render(request, 'core/dashboard.html', {
        'stats': stats,
        'recent_tasks': recent_tasks,
    })


class TaskCreateView(LoginRequiredMixin, View):
    template_name = 'core/task_form.html'

    def get(self, request):
        form = TaskForm(user=request.user)
        return render(request, self.template_name, {'form': form, 'mode': 'Crear'})

    def post(self, request):
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            if not task.assigned_to:
                task.assigned_to = request.user
            task.save()
            messages.success(request, f'Tarea "{task.title}" creada exitosamente.')
            logger.info(f"[TASK] Creada: {task.title} por {request.user.username}")
            return redirect('core:dashboard')
        return render(request, self.template_name, {'form': form, 'mode': 'Crear'})


class ProjectCreateView(LoginRequiredMixin, View):
    template_name = 'core/project_form.html'

    def get(self, request):
        form = ProjectForm()
        return render(request, self.template_name, {'form': form, 'mode': 'Crear'})

    def post(self, request):
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            messages.success(request, f'Proyecto "{project.name}" creado exitosamente.')
            logger.info(f"[PROJECT] Creado: {project.name} por {request.user.username}")
            return redirect('core:task_create')
        return render(request, self.template_name, {'form': form, 'mode': 'Crear'})


class ProfileView(LoginRequiredMixin, View):
    template_name = 'core/profile.html'

    def get(self, request):
        profile_form = ProfileForm(instance=request.user.profile)
        return render(request, self.template_name, {'profile_form': profile_form})

    def post(self, request):
        profile_form = ProfileForm(request.POST, instance=request.user.profile)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Perfil actualizado.')
            return redirect('core:profile')
        return render(request, self.template_name, {'profile_form': profile_form})