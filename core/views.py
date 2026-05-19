import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Academia, Acesso
from .utils import identificar_aluno


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

    resultado = identificar_aluno(imagem_base64, academia)

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
