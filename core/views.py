import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Academia, Acesso, Matricula, Plano
from .utils import identificar_aluno


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


@login_required
def dashboard(request):
    user = request.user

    if user.is_superuser:
        contexto = {
            'perfil': 'Superadmin',
            'academias': Academia.objects.all().order_by('nome'),
            'planos': Plano.objects.select_related('academia').order_by('academia__nome', 'nome'),
            'matriculas': Matricula.objects.select_related('aluno', 'academia', 'plano').order_by('-data_inicio')[:10],
            'acessos': Acesso.objects.select_related('aluno', 'academia').order_by('-timestamp')[:10],
            'totais': {
                'academias': Academia.objects.count(),
                'planos': Plano.objects.count(),
                'matriculas': Matricula.objects.count(),
                'acessos': Acesso.objects.count(),
            },
        }
    elif hasattr(user, 'academia_gerenciada'):
        academia = user.academia_gerenciada
        contexto = {
            'perfil': 'Gestor',
            'academias': Academia.objects.filter(pk=academia.pk),
            'planos': Plano.objects.filter(academia=academia).order_by('nome'),
            'matriculas': Matricula.objects.filter(academia=academia).select_related('aluno', 'plano').order_by('-data_inicio')[:10],
            'acessos': Acesso.objects.filter(academia=academia).select_related('aluno', 'academia').order_by('-timestamp')[:10],
            'totais': {
                'academias': 1,
                'planos': academia.planos.count(),
                'matriculas': academia.matriculas.count(),
                'acessos': academia.acessos.count(),
            },
        }
    else:
        matriculas = Matricula.objects.filter(aluno=user).select_related('academia', 'plano').order_by('-data_inicio')
        contexto = {
            'perfil': 'Aluno',
            'academias': Academia.objects.filter(matriculas__aluno=user).distinct().order_by('nome'),
            'planos': Plano.objects.none(),
            'matriculas': matriculas,
            'acessos': Acesso.objects.filter(aluno=user).select_related('academia').order_by('-timestamp')[:10],
            'totais': {
                'academias': matriculas.values('academia').distinct().count(),
                'planos': matriculas.values('plano').distinct().count(),
                'matriculas': matriculas.count(),
                'acessos': Acesso.objects.filter(aluno=user).count(),
            },
        }

    return render(request, 'core/dashboard.html', contexto)


@login_required
def checkin_page(request):
    if request.user.is_superuser:
        academias = Academia.objects.filter(ativa=True).order_by('nome')
    elif hasattr(request.user, 'academia_gerenciada'):
        academias = Academia.objects.filter(pk=request.user.academia_gerenciada.pk, ativa=True)
    else:
        academias = Academia.objects.filter(matriculas__aluno=request.user, ativa=True).distinct().order_by('nome')

    return render(request, 'core/checkin.html', {'academias': academias})


@csrf_exempt
@require_POST
def checkin_verificar(request, pk):
    academia = get_object_or_404(Academia, pk=pk, ativa=True)

    try:
        payload = json.loads(request.body)
        imagem_base64 = payload.get("imagem", "")
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({"erro": "Payload inválido. Envie { \"imagem\": \"<base64>\" }."}, status=400)

    if not imagem_base64:
        return JsonResponse({"erro": "Campo 'imagem' obrigatório."}, status=400)

    try:
        resultado = identificar_aluno(imagem_base64, academia)
    except ValueError as exc:
        return JsonResponse({"erro": str(exc)}, status=400)

    Acesso.objects.create(
        aluno=resultado["aluno"],
        academia=academia,
        status=resultado["status"],
        confianca=resultado["confianca"],
    )

    resposta = {
        "status": resultado["status"],
        "confianca": resultado["confianca"],
        "nome": resultado["aluno"].get_full_name() if resultado["aluno"] else None,
    }
    return JsonResponse(resposta)
