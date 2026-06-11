from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from core.models import Academia, Acesso, AlunoPerfil, Matricula, Plano


class Command(BaseCommand):
    help = 'Cria dados de demonstracao para apresentar o GymAccess.'

    def handle(self, *args, **options):
        grupo_gestores, _ = Group.objects.get_or_create(name='Gestores')

        admin = self._usuario(
            username='admin',
            password='admin12345',
            first_name='Admin',
            last_name='GymAccess',
            email='admin@gymaccess.local',
            is_staff=True,
            is_superuser=True,
        )
        gestor = self._usuario(
            username='gestor',
            password='gestor12345',
            first_name='Gestor',
            last_name='Centro',
            email='gestor@gymaccess.local',
            is_staff=True,
        )
        gestor.groups.add(grupo_gestores)

        aluno = self._usuario(
            username='aluno',
            password='aluno12345',
            first_name='Aluno',
            last_name='Demo',
            email='aluno@gymaccess.local',
        )
        AlunoPerfil.objects.get_or_create(
            user=aluno,
            defaults={
                'cpf': '123.456.789-00',
                'telefone': '(35) 99999-0000',
                'data_nascimento': date(2000, 1, 1),
            },
        )

        academia, _ = Academia.objects.get_or_create(
            cnpj='12.345.678/0001-00',
            defaults={
                'nome': 'GymAccess Centro',
                'endereco': 'Rua Principal, 100',
                'gestor': gestor,
                'ativa': True,
            },
        )
        if academia.gestor_id != gestor.id:
            academia.gestor = gestor
            academia.save(update_fields=['gestor'])

        plano, _ = Plano.objects.get_or_create(
            academia=academia,
            nome='Plano Mensal',
            defaults={
                'max_checkins_dia': 1,
                'valor': Decimal('99.90'),
            },
        )

        hoje = date.today()
        Matricula.objects.get_or_create(
            aluno=aluno,
            academia=academia,
            defaults={
                'plano': plano,
                'data_inicio': hoje,
                'data_fim': hoje + timedelta(days=30),
                'ativa': True,
            },
        )

        Acesso.objects.get_or_create(
            aluno=aluno,
            academia=academia,
            status=Acesso.Status.LIBERADO,
            confianca=95.0,
        )

        self.stdout.write(self.style.SUCCESS('Dados de demonstracao criados.'))
        self.stdout.write('Admin: admin / admin12345')
        self.stdout.write('Gestor: gestor / gestor12345')
        self.stdout.write('Aluno: aluno / aluno12345')

    def _usuario(self, username, password, **defaults):
        user, created = User.objects.get_or_create(username=username, defaults=defaults)
        for field, value in defaults.items():
            setattr(user, field, value)
        if created or not user.has_usable_password():
            user.set_password(password)
        user.save()
        return user
