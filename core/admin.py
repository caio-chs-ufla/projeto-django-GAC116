from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import Academia, AlunoPerfil, Plano, Matricula, Acesso


class AlunoPerfilInline(admin.StackedInline):
    model = AlunoPerfil
    can_delete = False
    fields = ('cpf', 'telefone', 'data_nascimento', 'foto', 'status_encoding')
    readonly_fields = ('status_encoding',)

    def status_encoding(self, obj):
        if not obj or not obj.pk:
            return '—'
        if not obj.foto:
            return format_html('<span style="color:#999">Pendente — sem foto</span>')
        if obj.face_encoding:
            return format_html('<span style="color:green">✓ Encoding gerado</span>')
        return format_html('<span style="color:red">✗ Falhou — reenvie a foto</span>')

    status_encoding.short_description = 'Reconhecimento facial'


class UserAdmin(BaseUserAdmin):
    inlines = (AlunoPerfilInline,)

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
    search_fields = ('nome',)

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
    search_fields = ('aluno__first_name', 'aluno__last_name', 'aluno__email')

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
    search_fields = ('aluno__first_name', 'aluno__last_name')
    readonly_fields = ('aluno', 'academia', 'status', 'confianca', 'timestamp')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(academia__gestor=request.user)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
