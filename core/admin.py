from django.contrib import admin
from django.utils.html import format_html
from .models import Profile, Project, Task


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone', 'created_at', 'updated_at')
    list_filter = ('role', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'tasks_count_display', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'owner')
    search_fields = ('name', 'description', 'owner__username')
    readonly_fields = ('created_at', 'tasks_count_display')
    list_select_related = ('owner',)

    @admin.display(description='N° Tareas', ordering='tasks')
    def tasks_count_display(self, obj):
        count = obj.tasks_count
        color = 'green' if count > 5 else 'orange' if count > 0 else 'gray'
        return format_html('<span style="color:{}; font-weight:bold;">{}</span>', color, count)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'assigned_to', 'priority_badge', 'status_badge',
                    'due_date', 'overdue_display', 'created_at')
    list_filter = ('status', 'priority', 'project', 'due_date')
    search_fields = ('title', 'description', 'project__name', 'assigned_to__username')
    readonly_fields = ('created_at', 'updated_at', 'overdue_display')
    date_hierarchy = 'created_at'
    list_select_related = ('project', 'assigned_to')
    list_per_page = 25

    @admin.display(description='Prioridad', ordering='priority')
    def priority_badge(self, obj):
        colors = {
            'low': '#6c757d', 'medium': '#0d6efd',
            'high': '#fd7e14', 'critical': '#dc3545'
        }
        color = colors.get(obj.priority, '#000')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; border-radius:4px;">{}</span>',
            color, obj.get_priority_display()
        )

    @admin.display(description='Estado', ordering='status')
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107', 'in_progress': '#0dcaf0',
            'done': '#198754', 'cancelled': '#6c757d'
        }
        color = colors.get(obj.status, '#000')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; border-radius:4px;">{}</span>',
            color, obj.get_status_display()
        )

    @admin.display(description='¿Vencida?', boolean=True)
    def overdue_display(self, obj):
        return obj.is_overdue

    actions = ['mark_as_done', 'mark_as_cancelled']

    @admin.action(description='Marcar seleccionadas como completadas')
    def mark_as_done(self, request, queryset):
        updated = queryset.update(status='done')
        self.message_user(request, f'{updated} tarea(s) marcadas como completadas.')

    @admin.action(description='Cancelar tareas seleccionadas')
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} tarea(s) canceladas.')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('project', 'assigned_to')


admin.site.site_header = 'TaskManager Admin'
admin.site.site_title = 'TaskManager'
admin.site.index_title = 'Panel de Administración'