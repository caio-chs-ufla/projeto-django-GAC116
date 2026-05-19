# Reconhecimento Facial — GymAccess

Este documento explica como funciona o reconhecimento facial no sistema GymAccess: desde o cadastro do aluno até a validação de acesso na catraca.

---

## Visão Geral

O sistema usa reconhecimento facial em dois momentos:

1. **Cadastro** — gestor faz upload da foto do aluno via Django Admin
2. **Check-in** — aluno se posiciona na câmera da academia, sistema identifica e libera/nega acesso

A comparação **não é entre imagens**. É entre vetores matemáticos chamados **encodings**.

---

## A Biblioteca: `face_recognition`

Usamos a biblioteca Python [`face_recognition`](https://github.com/ageitgey/face_recognition), que é um wrapper de alto nível sobre a biblioteca **dlib**.

Por baixo, ela usa uma **rede neural ResNet** treinada em mais de 3 milhões de rostos. Essa rede aprendeu a extrair características geométricas invariantes do rosto humano:

- Distância entre os olhos
- Proporção e formato do nariz
- Linha do maxilar
- Posição das maçãs do rosto
- Formato da boca

Essas características **não mudam** quando a pessoa corta o cabelo, usa óculos, ou está sob iluminação diferente.

---

## O Encoding: 128 Floats

A principal saída da biblioteca é o **encoding facial** — um vetor de **128 números decimais (floats)** que representa unicamente o rosto de uma pessoa.

```python
import face_recognition

image = face_recognition.load_image_file("foto_joao.jpg")
encodings = face_recognition.face_encodings(image)

print(encodings[0])
# array([ 0.12, -0.43,  0.87,  0.03, -0.21, ... ])  ← 128 valores
```

**Analogia:** pense no encoding como uma "impressão digital matemática" do rosto. Duas fotos da mesma pessoa geram vetores muito parecidos. Fotos de pessoas diferentes geram vetores muito distintos.

### Tamanho no banco

- 128 floats × 8 bytes cada = **1024 bytes por aluno**
- Armazenado como `BinaryField` no PostgreSQL

---

## Armazenamento no Banco de Dados

O model `AlunoPerfil` possui dois campos relacionados ao reconhecimento facial:

```python
# core/models.py
class AlunoPerfil(models.Model):
    foto = models.ImageField(upload_to='alunos/', null=True, blank=True)
    face_encoding = models.BinaryField(null=True, blank=True)
```

| Campo | O que guarda | Por quê |
|---|---|---|
| `foto` | Imagem original (JPG/PNG) | Exibição no Admin, referência visual |
| `face_encoding` | 1024 bytes (128 floats serializados) | Comparação no check-in |

### Serialização (encoding → banco)

```python
import numpy as np

# Salvar
encoding_numpy = face_recognition.face_encodings(image)[0]  # numpy array
aluno_perfil.face_encoding = encoding_numpy.tobytes()        # bytes → BinaryField

# Ler
bytes_do_banco = aluno_perfil.face_encoding
encoding_numpy = np.frombuffer(bytes_do_banco, dtype=np.float64)  # de volta ao array
```

**Por que BinaryField e não JSON?**

- JSON de 128 floats = ~1.5KB + overhead de parsing a cada comparação
- BinaryField = 1024 bytes exatos, leitura direta para NumPy sem parsing
- Performance importa: no check-in comparamos contra todos os alunos da academia

---

## Fluxo 1: Cadastro do Aluno (Django Admin)

```
Gestor acessa Django Admin
         │
         ▼
Preenche dados do aluno + faz upload da foto
         │
         ▼
AlunoPerfil.save() é chamado
         │
         ▼
face_recognition.load_image_file(foto)
→ converte imagem para array NumPy RGB
         │
         ▼
face_recognition.face_encodings(image)
→ retorna lista de encodings detectados na foto
         │
         ├── len == 0 → erro: "Nenhum rosto detectado na foto"
         ├── len > 1  → erro: "Mais de um rosto na foto. Envie foto individual"
         └── len == 1 → prossegue
         │
         ▼
encoding[0].tobytes() → salva em face_encoding (BinaryField)
         │
         ▼
AlunoPerfil salvo com sucesso ✓
```

---

## Fluxo 2: Check-in (Tela Pública da Academia)

A tela de check-in fica em `/academia/<id>/checkin/` — pública, sem login.

### Etapa 1 — Captura via Webcam (Frontend)

```
Navegador abre página de check-in
         │
         ▼
JavaScript solicita acesso à câmera
navigator.mediaDevices.getUserMedia({ video: true })
         │
         ▼
<video> exibe feed da câmera em tempo real
         │
         ▼
Aluno clica em "Verificar Acesso"
         │
         ▼
JS captura frame atual do <video> em um <canvas>
canvas.drawImage(video, 0, 0)
         │
         ▼
Converte para base64 JPEG
canvas.toDataURL("image/jpeg", 0.8)
→ "data:image/jpeg;base64,/9j/4AAQSkZJRgAB..."
         │
         ▼
POST /academia/<id>/checkin/verificar/
{ "imagem": "<base64 string>" }
```

> **Por que base64?** JavaScript não consegue enviar binário de imagem diretamente num POST JSON. Base64 é só a "embalagem" para trafegar a imagem via HTTP. O backend decodifica imediatamente e nunca usa base64 novamente.

### Etapa 2 — Processamento no Backend (Django)

```
View recebe POST com imagem base64
         │
         ▼
Decodifica base64 → bytes → Pillow Image → array NumPy RGB
         │
         ▼
face_recognition.face_encodings(frame)
→ extrai encoding do rosto capturado pela webcam
         │
         ├── Nenhum rosto detectado → retorna status DESCONHECIDO
         └── Rosto detectado → prossegue
         │
         ▼
Busca todos AlunoPerfil onde:
  - face_encoding IS NOT NULL
  - possui Matricula ativa nessa academia
         │
         ▼
Para cada aluno: np.frombuffer(face_encoding) → array NumPy
→ monta lista [enc_aluno1, enc_aluno2, enc_aluno3, ...]
         │
         ▼
face_recognition.face_distance(encodings_conhecidos, enc_visitante)
→ retorna array de distâncias: [0.31, 0.72, 0.48, ...]
         │
         ▼
melhor_match = índice da menor distância
distancia_min = min(distâncias)
         │
         ├── distancia_min >= 0.5 → status = DESCONHECIDO
         │                          confianca = None
         │
         └── distancia_min < 0.5  → aluno identificado
                    │
                    ├── Matrícula ativa + dentro da validade → status = LIBERADO
                    └── Matrícula vencida ou inativa         → status = NEGADO
         │
         ▼
Cria registro Acesso(aluno, academia, status, confianca)
         │
         ▼
Retorna JSON → JS exibe resultado na tela
```

---

## A Comparação: Distância Euclidiana

A comparação entre dois encodings usa **distância euclidiana** — a distância geométrica entre dois pontos em espaço de 128 dimensões.

```
distância = √( (a₁-b₁)² + (a₂-b₂)² + ... + (a₁₂₈-b₁₂₈)² )
```

**Mesma pessoa** → pontos próximos no espaço → distância pequena  
**Pessoas diferentes** → pontos distantes → distância grande

### Exemplos

```
João (cadastro) → [0.12, -0.43, 0.87, ...]
João (check-in, óculos) → [0.14, -0.41, 0.89, ...]
distância = 0.28  ✓ MESMO ROSTO

João (cadastro) → [0.12, -0.43, 0.87, ...]
Maria (check-in) → [0.67,  0.21, -0.34, ...]
distância = 0.81  ✗ ROSTO DIFERENTE
```

### Por que a rede é robusta a variações?

A rede foi treinada com a mesma pessoa fotografada em centenas de condições diferentes (luz, ângulo, acessórios, envelhecimento). Aprendeu a extrair somente características estruturais do rosto — que não mudam. Variações superficiais como cabelo, barba ou óculos causam diferenças mínimas no vetor final.

---

## O Threshold: 0.5

O threshold é o limite que define "mesma pessoa" vs "pessoas diferentes".

| Distância | Interpretação |
|---|---|
| 0.0 | Foto idêntica (mesmo arquivo) |
| 0.0 – 0.4 | Mesma pessoa, condições diferentes |
| 0.4 – 0.5 | Provável mesma pessoa |
| 0.5 – 0.6 | Zona de incerteza |
| > 0.6 | Pessoas diferentes |

Usamos **0.5** (mais rígido que o padrão 0.6 da biblioteca). Num sistema de controle de acesso, é melhor negar um acesso legítimo do que liberar um acesso indevido.

### Cálculo da Confiança

```python
confianca = (1 - distancia) * 100

# Exemplos:
# distância 0.2 → confiança 80%
# distância 0.4 → confiança 60%
# distância 0.5 → confiança 50%  (limite)
```

O campo `confianca` no model `Acesso` guarda esse valor para auditoria pelo gestor.

---

## Diagrama Resumido

```
CADASTRO
────────
foto.jpg → [face_recognition] → [0.12, -0.43, 0.87, ...128 floats...]
                                              │
                                     .tobytes() (1024 bytes)
                                              │
                                       BinaryField no banco


CHECK-IN
────────
webcam → base64 → [Django] → numpy array
                                  │
                        [face_recognition]
                                  │
                         [0.14, -0.41, 0.89, ...128 floats...]
                                  │
                    face_distance() contra todos alunos da academia
                                  │
                    distância < 0.5?
                         ├── Não → DESCONHECIDO
                         └── Sim → aluno identificado
                                        │
                              matrícula ativa?
                                   ├── Sim → LIBERADO
                                   └── Não → NEGADO
                                        │
                              salva Acesso no banco
```

---

## Requisitos e Dependências

```
face_recognition==1.3.0
numpy>=1.24
Pillow>=10.0
opencv-python>=4.8   # opcional, usado no servidor para decodificar imagem
```

> **Atenção:** `face_recognition` depende de `dlib`, que precisa ser compilado. A instalação pode ser lenta em alguns ambientes. No Docker, garanta que `cmake` e `build-essential` estejam instalados antes.
