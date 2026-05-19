# GymAccess — Sistema de Gerenciamento de Rede de Academias

Projeto desenvolvido para a disciplina **GAC116 - Programação Web (2026/1)** utilizando o framework Django.

## Descrição

O GymAccess é um sistema web para gerenciamento de uma rede de academias. O sistema permite o cadastro de alunos via reconhecimento facial, vinculando-os a uma ou mais academias. O acesso (check-in) é liberado automaticamente por meio de reconhecimento facial em uma tela pública dedicada a cada academia.

Cada academia possui um gestor responsável, que gerencia os alunos, planos e matrículas de sua unidade. O controle administrativo é realizado via painel Django Admin.

## Funcionalidades

- Cadastro de alunos com captura facial via câmera
- Check-in por reconhecimento facial (tela pública por academia)
- Área do aluno com login/senha (visualização de plano ativo e histórico de check-ins)
- Painel administrativo para gestores (Django Admin)
- Controle de planos com limite de check-ins diários por academia
- Suporte a múltiplas academias com gestores independentes

## Modelagem de Dados

### Entidades e Relacionamentos

```
SuperAdmin
    └── gerencia Academias e Gestores via Django Admin

Gestor (User — grupo: Gestores)
    └── acesso ao Django Admin restrito à sua Academia
    └── CRUD: Aluno, Plano, Matricula

Aluno (User + AlunoPerfil)
    └── login email/senha → área /aluno/
    └── check-in via reconhecimento facial (tela pública)

Academia ──(1:1)──── Gestor
Academia ──(1:N)──── Plano
Academia ──(N:N)──── Aluno  [via Matricula]
Matricula ──(N:1)─── Plano
Acesso ──(N:1)────── Aluno
Acesso ──(N:1)────── Academia
```

### Tabelas

| Tabela | Campos principais |
|--------|-------------------|
| `User` | id, email, password, first_name, last_name *(Django built-in)* |
| `AlunoPerfil` | id, user (FK), cpf, telefone, data_nascimento, foto, face_encoding |
| `Academia` | id, nome, cnpj, endereco, gestor (FK User), ativa |
| `Plano` | id, academia (FK), nome, max_checkins_dia, valor |
| `Matricula` | id, aluno (FK User), academia (FK), plano (FK), data_inicio, data_fim, ativa |
| `Acesso` | id, aluno (FK), academia (FK), timestamp, status, confianca |

### Regras de Negócio

- Um aluno pode estar matriculado em mais de uma academia, com planos distintos por academia
- O plano define o número máximo de check-ins permitidos por dia naquela academia
- Cada academia possui exatamente um gestor
- O check-in é realizado via reconhecimento facial em tela pública, sem necessidade de login
- A área do aluno (login/senha) é separada da tela de check-in
- O status do acesso pode ser: `LIBERADO`, `NEGADO` ou `DESCONHECIDO`

## Painel Administrativo (Django Admin)

O sistema possui dois níveis de acesso ao painel `/admin`:

### Superadmin
Acesso total ao sistema. Responsável por:
- Cadastrar academias e atribuir gestores
- Gerenciar todos os usuários, planos, matrículas e acessos
- Criar o grupo `Gestores` (criado automaticamente via migration)

### Gestor
Acesso restrito à sua academia. Criado pelo superadmin com `Staff status` ativo e adicionado ao grupo `Gestores`.

| Recurso | Pode ver | Pode adicionar | Pode editar | Pode excluir |
|---------|----------|----------------|-------------|--------------|
| Academias | Somente a sua | Não | Não | Não |
| Planos | Somente da sua academia | Sim | Sim | Sim |
| Matrículas | Somente da sua academia | Sim | Sim | Sim |
| Acessos | Somente da sua academia | Não | Não | Não |
| Usuários (alunos) | Somente matriculados na sua academia | Sim | Sim | Não |

> O grupo `Gestores` é criado automaticamente ao rodar `python manage.py migrate`. Para tornar um usuário gestor: marcar `Staff status` e adicionar ao grupo `Gestores` no painel admin.

## Tecnologias

| Tecnologia | Versão | Uso |
|------------|--------|-----|
| Python | 3.12 | Linguagem principal |
| Django | 6.x | Framework web |
| face_recognition | 1.x | Reconhecimento facial (dlib) |
| OpenCV | 4.x | Captura e processamento de imagens |
| Pillow | 11.x | Manipulação de imagens (ImageField) |
| NumPy | 2.x | Serialização dos encodings faciais |
| Bootstrap | 5.x | Interface responsiva |
| PostgreSQL | 16 | Banco de dados (via Docker) |
| Docker | 28+ | Containerização do banco de dados |
| psycopg2-binary | 2.x | Driver Python para PostgreSQL |

## Pré-requisitos

```bash
# Dependências de sistema (Ubuntu/Debian)
sudo apt update
sudo apt install python3.12 python3.12-venv python3-dev cmake build-essential

# Docker (necessário para o banco de dados)
# Instalar Docker Desktop ou Docker Engine
docker --version
docker compose version
```

## Como Executar

```bash
# Clonar repositório
git clone <url-do-repositorio>
cd projeto-django-GAC116

# Criar e ativar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências Python
pip install -r requirements.txt

# Subir banco de dados PostgreSQL
cd docker
docker compose up -d
cd ..

# Aplicar migrações (cria tabelas e grupo Gestores automaticamente)
python manage.py migrate

# Criar superusuário (acesso ao Django Admin)
python manage.py createsuperuser

# Iniciar servidor
python manage.py runserver
```

Acesse em `http://127.0.0.1:8000` e o painel admin em `http://127.0.0.1:8000/admin`.

## Banco de Dados

O projeto utiliza **PostgreSQL 16** via Docker. O arquivo `docker/docker-compose.yml` sobe o container automaticamente.

```bash
# Subir banco
cd docker && docker compose up -d

# Parar banco
cd docker && docker compose down

# Ver logs do banco
cd docker && docker compose logs db
```

Configuração de conexão (definida em `config/settings.py`):

| Parâmetro | Valor |
|-----------|-------|
| Host | localhost |
| Porta | 5432 |
| Banco | gymaccess |
| Usuário | gymaccess |
| Senha | gymaccess |

## Estrutura do Projeto

```
projeto-django-GAC116/
├── config/             # Configurações do projeto Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/               # App principal
│   ├── models.py       # Modelos de dados
│   ├── admin.py        # Configuração do Django Admin
│   ├── views.py        # Views
│   └── migrations/     # Migrações do banco de dados
├── manage.py
└── requirements.txt
```

## Equipe

| Nome | GitHub |
|------|--------|
|      |        |
|      |        |
|      |        |
