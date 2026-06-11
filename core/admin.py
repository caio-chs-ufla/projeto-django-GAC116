from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html

from .models import Acesso, Academia, AlunoPerfil, Matricula, Plano


class AlunoPerfilInline(admin.StackedInline):
    model = AlunoPerfil
    can_delete = False
    fields = ('cpf', 'telefone', 'data_nascimento', 'foto', 'status_encoding')
    readonly_fields = ('status_encoding',)

    def status_encoding(self, obj):
        if not obj or not obj.pk:
            return '-'
        if not obj.foto:
            return format_html(
                '<span style="color:{}">{}</span>',
                '#999',
                'Pendente - sem foto',
            )
        if obj.face_encoding:
            return format_html(
                '<span style="color:{}">{}</span>',
                'green',
                'Encoding gerado',
            )
        return format_html(
            '<span style="color:{}">{}</span>',
            'red',
            'Falhou - reenvie a foto',
        )

    status_encoding.short_description = 'Reconhecimento facial'


class TipoUsuarioFilter(admin.SimpleListFilter):
    title = 'Tipo de usuario'
    parameter_name = 'tipo_usuario'

    def lookups(self, request, model_admin):
        return (
            ('aluno', 'Alunos'),
            ('gestor', 'Gestores'),
            ('admin', 'Administradores'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'aluno':
            return queryset.filter(is_staff=False, is_superuser=False)
        if self.value() == 'gestor':
            return queryset.filter(is_staff=True, is_superuser=False)
        if self.value() == 'admin':
            return queryset.filter(is_superuser=True)
        return queryset


class StatusUsuarioFilter(admin.SimpleListFilter):
    title = 'Status'
    parameter_name = 'status_usuario'

    def lookups(self, request, model_admin):
        return (
            ('ativo', 'Usuarios ativos'),
            ('inativo', 'Usuarios inativos'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'ativo':
            return queryset.filter(is_active=True)
        if self.value() == 'inativo':
            return queryset.filter(is_active=False)
        return queryset


class UserAdmin(BaseUserAdmin):
    inlines = (AlunoPerfilInline,)
    list_filter = (TipoUsuarioFilter, StatusUsuarioFilter)
    search_fields = BaseUserAdmin.search_fields + ('email', 'first_name', 'last_name')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(matriculas__academia__gestor=request.user).distinct()


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Academia)
class AcademiaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cnpj', 'gestor', 'ativa')
    list_filter = ('ativa',)
    search_fields = ('nome', 'cnpj')
    list_select_related = ('gestor',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(gestor=request.user)

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return ('gestor', 'cnpj')
        return ()


@admin.register(Plano)
class PlanoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'academia', 'max_checkins_dia', 'valor')
    list_filter = ('academia',)
    search_fields = ('nome', 'academia__nome')
    list_select_related = ('academia',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(academia__gestor=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'academia' and not request.user.is_superuser:
            kwargs['queryset'] = Academia.objects.filter(gestor=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = ('aluno', 'academia', 'plano', 'data_inicio', 'data_fim', 'ativa')
    list_filter = ('academia', 'ativa')
    search_fields = (
        'aluno__username',
        'aluno__first_name',
        'aluno__last_name',
        'aluno__email',
        'academia__nome',
        'plano__nome',
    )
    list_select_related = ('aluno', 'academia', 'plano')
    date_hierarchy = 'data_inicio'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(academia__gestor=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == 'academia':
                kwargs['queryset'] = Academia.objects.filter(gestor=request.user)
            if db_field.name == 'plano':
                kwargs['queryset'] = Plano.objects.filter(academia__gestor=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Acesso)
class AcessoAdmin(admin.ModelAdmin):
    list_display = ('aluno', 'academia', 'status', 'confianca', 'timestamp')
    list_filter = ('status', 'academia')
    search_fields = ('aluno__username', 'aluno__first_name', 'aluno__last_name', 'academia__nome')
    readonly_fields = ('aluno', 'academia', 'status', 'confianca', 'timestamp')
    list_select_related = ('aluno', 'academia')
    date_hierarchy = 'timestamp'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(academia__gestor=request.user)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
