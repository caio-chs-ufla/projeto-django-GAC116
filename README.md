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

Aluno (User)
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
| `Academia` | id, nome, cnpj, endereco, gestor (FK User), ativa |
| `Plano` | id, academia (FK), nome, max_checkins_dia, valor |
| `Matricula` | id, aluno (FK User), academia (FK), plano (FK), data_inicio, data_fim, ativa |
| `Acesso` | id, aluno (FK), academia (FK), timestamp, liberado, confianca |

### Regras de Negócio

- Um aluno pode estar matriculado em mais de uma academia, com planos distintos por academia
- O plano define o número máximo de check-ins permitidos por dia naquela academia
- Cada academia possui exatamente um gestor
- O check-in é realizado via reconhecimento facial em tela pública, sem necessidade de login
- A área do aluno (login/senha) é separada da tela de check-in

## Tecnologias

- Python 3.12
- Django 5.x
- face_recognition (reconhecimento facial)
- Bootstrap 5 (interface responsiva)
- SQLite (desenvolvimento)
- Django Admin (painel administrativo)

## Como Executar

```bash
# Clonar repositório
git clone <url-do-repositorio>
cd projeto-django-GAC116

# Criar e ativar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Aplicar migrações
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Iniciar servidor
python manage.py runserver
```

Acesse em `http://127.0.0.1:8000` e o painel admin em `http://127.0.0.1:8000/admin`.

## Equipe

| Nome | GitHub |
|------|--------|
|      |        |
|      |        |
|      |        |
