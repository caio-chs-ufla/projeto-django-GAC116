from datetime import date, timedelta
from decimal import Decimal

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .admin import AcademiaAdmin, AcessoAdmin, MatriculaAdmin, PlanoAdmin
from .models import Academia, Acesso, AlunoPerfil, Matricula, Plano


class CheckpointModelValidationTests(TestCase):
    def setUp(self):
        self.gestor = User.objects.create_user(username='gestor')
        self.aluno = User.objects.create_user(username='aluno')
        self.academia = Academia.objects.create(
            nome='Gym Centro',
            cnpj='00.000.000/0001-00',
            endereco='Rua A',
            gestor=self.gestor,
        )
        self.outra_academia = Academia.objects.create(
            nome='Gym Norte',
            cnpj='00.000.000/0002-00',
            endereco='Rua B',
        )
        self.plano = Plano.objects.create(
            academia=self.academia,
            nome='Mensal',
            max_checkins_dia=1,
            valor=Decimal('99.90'),
        )
        self.plano_outra_academia = Plano.objects.create(
            academia=self.outra_academia,
            nome='Anual',
            max_checkins_dia=2,
            valor=Decimal('899.90'),
        )

    def test_plano_exige_checkins_e_valor_positivos(self):
        plano = Plano(
            academia=self.academia,
            nome='Invalido',
            max_checkins_dia=0,
            valor=Decimal('0.00'),
        )

        with self.assertRaises(ValidationError) as context:
            plano.full_clean()

        self.assertIn('max_checkins_dia', context.exception.message_dict)
        self.assertIn('valor', context.exception.message_dict)

    def test_matricula_exige_periodo_valido(self):
        hoje = date.today()
        matricula = Matricula(
            aluno=self.aluno,
            academia=self.academia,
            plano=self.plano,
            data_inicio=hoje,
            data_fim=hoje - timedelta(days=1),
        )

        with self.assertRaises(ValidationError) as context:
            matricula.full_clean()

        self.assertIn('data_fim', context.exception.message_dict)

    def test_matricula_exige_plano_da_mesma_academia(self):
        hoje = date.today()
        matricula = Matricula(
            aluno=self.aluno,
            academia=self.academia,
            plano=self.plano_outra_academia,
            data_inicio=hoje,
            data_fim=hoje + timedelta(days=30),
        )

        with self.assertRaises(ValidationError) as context:
            matricula.full_clean()

        self.assertIn('plano', context.exception.message_dict)

    def test_grupo_gestores_e_criado_pela_migration(self):
        self.assertTrue(Group.objects.filter(name='Gestores').exists())


class CheckpointAdminScopingTests(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.factory = RequestFactory()
        hoje = date.today()

        self.gestor_a = User.objects.create_user(username='gestor-a')
        self.gestor_b = User.objects.create_user(username='gestor-b')
        self.aluno_a = User.objects.create_user(username='aluno-a')
        self.aluno_b = User.objects.create_user(username='aluno-b')

        self.academia_a = Academia.objects.create(
            nome='Gym A',
            cnpj='11.111.111/0001-11',
            endereco='Rua A',
            gestor=self.gestor_a,
        )
        self.academia_b = Academia.objects.create(
            nome='Gym B',
            cnpj='22.222.222/0001-22',
            endereco='Rua B',
            gestor=self.gestor_b,
        )
        self.plano_a = Plano.objects.create(
            academia=self.academia_a,
            nome='Mensal A',
            max_checkins_dia=1,
            valor=Decimal('99.90'),
        )
        self.plano_b = Plano.objects.create(
            academia=self.academia_b,
            nome='Mensal B',
            max_checkins_dia=1,
            valor=Decimal('109.90'),
        )
        self.matricula_a = Matricula.objects.create(
            aluno=self.aluno_a,
            academia=self.academia_a,
            plano=self.plano_a,
            data_inicio=hoje,
            data_fim=hoje + timedelta(days=30),
        )
        self.matricula_b = Matricula.objects.create(
            aluno=self.aluno_b,
            academia=self.academia_b,
            plano=self.plano_b,
            data_inicio=hoje,
            data_fim=hoje + timedelta(days=30),
        )
        self.acesso_a = Acesso.objects.create(
            aluno=self.aluno_a,
            academia=self.academia_a,
            status=Acesso.Status.LIBERADO,
            confianca=92.0,
        )
        self.acesso_b = Acesso.objects.create(
            aluno=self.aluno_b,
            academia=self.academia_b,
            status=Acesso.Status.LIBERADO,
            confianca=91.0,
        )

    def request_for(self, user):
        request = self.factory.get('/admin/')
        request.user = user
        return request

    def test_admin_filtra_academias_do_gestor(self):
        model_admin = AcademiaAdmin(Academia, self.site)
        qs = model_admin.get_queryset(self.request_for(self.gestor_a))

        self.assertEqual(list(qs), [self.academia_a])

    def test_admin_filtra_planos_do_gestor(self):
        model_admin = PlanoAdmin(Plano, self.site)
        qs = model_admin.get_queryset(self.request_for(self.gestor_a))

        self.assertEqual(list(qs), [self.plano_a])

    def test_admin_filtra_matriculas_do_gestor(self):
        model_admin = MatriculaAdmin(Matricula, self.site)
        qs = model_admin.get_queryset(self.request_for(self.gestor_a))

        self.assertEqual(list(qs), [self.matricula_a])

    def test_admin_filtra_acessos_do_gestor(self):
        model_admin = AcessoAdmin(Acesso, self.site)
        qs = model_admin.get_queryset(self.request_for(self.gestor_a))

        self.assertEqual(list(qs), [self.acesso_a])


class CheckpointAdminRenderingTests(TestCase):
    def test_admin_renderiza_edicao_de_usuario_com_perfil_sem_foto(self):
        admin_user = User.objects.create_superuser(
            username='admin-render',
            password='senha12345',
        )
        aluno = User.objects.create_user(
            username='aluno-render',
            password='senha12345',
        )
        AlunoPerfil.objects.create(
            user=aluno,
            cpf='444.555.666-77',
            telefone='(35) 95555-4444',
        )

        self.client.force_login(admin_user)
        response = self.client.get(reverse('admin:auth_user_change', args=[aluno.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pendente - sem foto')

    def test_admin_user_filter_tipo_usuario_lista_apenas_alunos(self):
        admin_user = User.objects.create_superuser(
            username='admin-filter',
            password='senha12345',
        )
        User.objects.create_user(
            username='aluno-filter',
            password='senha12345',
        )
        User.objects.create_user(
            username='gestor-filter',
            password='senha12345',
            is_staff=True,
        )

        self.client.force_login(admin_user)
        response = self.client.get(
            reverse('admin:auth_user_changelist'),
            {'tipo_usuario': 'aluno'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'aluno-filter')
        self.assertNotContains(response, 'gestor-filter')


class CheckpointUserInterfaceTests(TestCase):
    def setUp(self):
        hoje = date.today()
        self.gestor = User.objects.create_user(
            username='gestor-ui',
            password='senha12345',
            first_name='Gestor',
        )
        self.aluno = User.objects.create_user(
            username='aluno-ui',
            password='senha12345',
            first_name='Aluno',
        )
        self.academia = Academia.objects.create(
            nome='Gym UI',
            cnpj='33.333.333/0001-33',
            endereco='Rua UI',
            gestor=self.gestor,
        )
        self.plano = Plano.objects.create(
            academia=self.academia,
            nome='Mensal UI',
            max_checkins_dia=1,
            valor=Decimal('89.90'),
        )
        self.matricula = Matricula.objects.create(
            aluno=self.aluno,
            academia=self.academia,
            plano=self.plano,
            data_inicio=hoje,
            data_fim=hoje + timedelta(days=30),
        )

    def test_home_redireciona_para_login_quando_anonimo(self):
        response = self.client.get(reverse('home'))

        self.assertRedirects(response, reverse('login'), fetch_redirect_response=False)

    def test_dashboard_exige_login(self):
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response['Location'])

    def test_dashboard_renderiza_para_gestor(self):
        self.client.login(username='gestor-ui', password='senha12345')

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gestor')
        self.assertContains(response, 'Gym UI')

    def test_dashboard_renderiza_para_aluno(self):
        self.client.login(username='aluno-ui', password='senha12345')

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Aluno')
        self.assertContains(response, 'Gym UI')

    def test_checkin_page_exige_login(self):
        response = self.client.get(reverse('checkin_page'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response['Location'])

    def test_checkin_retorna_erro_para_imagem_invalida(self):
        response = self.client.post(
            reverse('checkin_verificar', args=[self.academia.pk]),
            data='{"imagem": "nao-e-base64"}',
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('erro', response.json())
