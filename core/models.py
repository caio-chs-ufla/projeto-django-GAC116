from django.db import models
from django.contrib.auth.models import User


class Academia(models.Model):
    gestor = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='academia_gerenciada',
    )
    nome = models.CharField(max_length=100)
    cnpj = models.CharField(max_length=18, unique=True)
    endereco = models.CharField(max_length=200)
    ativa = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Academia'
        verbose_name_plural = 'Academias'

    def __str__(self):
        return self.nome


class Plano(models.Model):
    academia = models.ForeignKey(Academia, on_delete=models.CASCADE, related_name='planos')
    nome = models.CharField(max_length=50)
    max_checkins_dia = models.PositiveIntegerField(default=1)
    valor = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        verbose_name = 'Plano'
        verbose_name_plural = 'Planos'

    def __str__(self):
        return f'{self.nome} — {self.academia.nome}'


class AlunoPerfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    cpf = models.CharField(max_length=14, unique=True)
    telefone = models.CharField(max_length=15, blank=True)
    data_nascimento = models.DateField(null=True, blank=True)
    foto = models.ImageField(upload_to='alunos/', null=True, blank=True)
    face_encoding = models.BinaryField(null=True, blank=True)

    class Meta:
        verbose_name = 'Perfil do Aluno'
        verbose_name_plural = 'Perfis dos Alunos'

    def __str__(self):
        return self.user.get_full_name()


class Matricula(models.Model):
    aluno = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matriculas')
    academia = models.ForeignKey(Academia, on_delete=models.CASCADE, related_name='matriculas')
    plano = models.ForeignKey(Plano, on_delete=models.SET_NULL, null=True, related_name='matriculas')
    data_inicio = models.DateField()
    data_fim = models.DateField()
    ativa = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Matrícula'
        verbose_name_plural = 'Matrículas'
        unique_together = ('aluno', 'academia')

    def __str__(self):
        return f'{self.aluno.get_full_name()} — {self.academia.nome}'


class Acesso(models.Model):
    class Status(models.TextChoices):
        LIBERADO = 'LIBERADO', 'Liberado'
        NEGADO = 'NEGADO', 'Negado'
        DESCONHECIDO = 'DESCONHECIDO', 'Desconhecido'

    aluno = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acessos',
    )
    academia = models.ForeignKey(Academia, on_delete=models.CASCADE, related_name='acessos')
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DESCONHECIDO)
    confianca = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = 'Acesso'
        verbose_name_plural = 'Acessos'
        ordering = ['-timestamp']

    def __str__(self):
        nome = self.aluno.get_full_name() if self.aluno else 'Desconhecido'
        return f'{self.get_status_display()} — {nome} — {self.academia.nome}'
