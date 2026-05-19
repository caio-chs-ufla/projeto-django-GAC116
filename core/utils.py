import base64
import io
from datetime import date

import face_recognition
import numpy as np
from PIL import Image

THRESHOLD = 0.5


def extrair_encoding(foto_path: str) -> bytes:
    """
    Extrai encoding facial de uma imagem em disco.
    Raises ValueError se nenhum ou mais de um rosto for detectado.
    """
    image = face_recognition.load_image_file(foto_path)
    encodings = face_recognition.face_encodings(image)

    if len(encodings) == 0:
        raise ValueError("Nenhum rosto detectado na foto.")
    if len(encodings) > 1:
        raise ValueError("Mais de um rosto detectado. Envie uma foto individual.")

    return encodings[0].tobytes()


def _decodificar_base64(imagem_base64: str) -> np.ndarray:
    if "," in imagem_base64:
        imagem_base64 = imagem_base64.split(",", 1)[1]

    image_bytes = base64.b64decode(imagem_base64)
    pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return np.array(pil_image)


def identificar_aluno(imagem_base64: str, academia) -> dict:
    """
    Compara rosto capturado contra todos os alunos matriculados na academia.

    Retorna dict com:
        status: 'LIBERADO' | 'NEGADO' | 'DESCONHECIDO'
        aluno:  instância User ou None
        confianca: float (0-100) ou None
    """
    frame = _decodificar_base64(imagem_base64)
    encodings_frame = face_recognition.face_encodings(frame)

    if not encodings_frame:
        return {"status": "DESCONHECIDO", "aluno": None, "confianca": None}

    encoding_visitante = encodings_frame[0]

    hoje = date.today()
    matriculas_ativas = academia.matriculas.filter(
        ativa=True,
        data_inicio__lte=hoje,
        data_fim__gte=hoje,
        aluno__perfil__face_encoding__isnull=False,
    ).select_related("aluno__perfil")

    if not matriculas_ativas.exists():
        return {"status": "DESCONHECIDO", "aluno": None, "confianca": None}

    encodings_conhecidos = []
    alunos = []

    for matricula in matriculas_ativas:
        enc_bytes = matricula.aluno.perfil.face_encoding
        enc_array = np.frombuffer(bytes(enc_bytes), dtype=np.float64)
        encodings_conhecidos.append(enc_array)
        alunos.append(matricula.aluno)

    distancias = face_recognition.face_distance(encodings_conhecidos, encoding_visitante)
    idx_melhor = int(np.argmin(distancias))
    melhor_distancia = distancias[idx_melhor]

    if melhor_distancia >= THRESHOLD:
        return {"status": "DESCONHECIDO", "aluno": None, "confianca": None}

    aluno_identificado = alunos[idx_melhor]
    confianca = round((1 - melhor_distancia) * 100, 1)

    matricula_valida = academia.matriculas.filter(
        aluno=aluno_identificado,
        ativa=True,
        data_inicio__lte=hoje,
        data_fim__gte=hoje,
    ).exists()

    status = "LIBERADO" if matricula_valida else "NEGADO"
    return {"status": status, "aluno": aluno_identificado, "confianca": confianca}
