from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from student.models import Student
from student.serializers import (
    StudentSerializer,
    StudentCreateSerializer,
    StudentUpdateSerializer
)
from student.services import StudentService


@extend_schema_view(
    list=extend_schema(
        summary='Listar estudantes',
        description='Lista todos os estudantes com paginação, busca e filtros.',
        parameters=[
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Busca por email, username ou nome'
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Ordenação: id, email, name, date_joined (use - para decrescente)'
            ),
        ],
        tags=['Estudantes'],
        examples=[
            OpenApiExample(
                'Resposta de Listagem',
                value={
                    "count": 2,
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            "id": 1,
                            "email": "joao.silva@email.com",
                            "username": "joao.silva",
                            "name": "João Silva",
                            "is_active": True,
                            "is_staff": False,
                            "is_superuser": False,
                            "date_joined": "2024-01-15T10:30:00Z",
                            "last_login": "2024-01-20T14:20:00Z"
                        },
                        {
                            "id": 2,
                            "email": "maria.santos@email.com",
                            "username": "maria.santos",
                            "name": "Maria Santos",
                            "is_active": True,
                            "is_staff": False,
                            "is_superuser": False,
                            "date_joined": "2024-01-16T09:15:00Z",
                            "last_login": None
                        }
                    ]
                },
                response_only=True,
            ),
        ]
    ),
    retrieve=extend_schema(
        summary='Detalhes do estudante',
        description='Retorna os detalhes completos de um estudante específico.',
        tags=['Estudantes'],
        examples=[
            OpenApiExample(
                'Estudante Detalhado',
                value={
                    "id": 1,
                    "email": "joao.silva@email.com",
                    "username": "joao.silva",
                    "name": "João Silva",
                    "is_active": True,
                    "is_staff": False,
                    "is_superuser": False,
                    "date_joined": "2024-01-15T10:30:00Z",
                    "last_login": "2024-01-20T14:20:00Z"
                },
                response_only=True,
            ),
        ]
    ),
    create=extend_schema(
        summary='Criar estudante',
        description='Cria um novo estudante no sistema.',
        tags=['Estudantes'],
        examples=[
            OpenApiExample(
                'Criar Estudante Completo',
                value={
                    "email": "joao.silva@email.com",
                    "username": "joao.silva",
                    "name": "João Silva",
                    "password": "senhaSegura123",
                    "password_confirmation": "senhaSegura123",
                    "is_active": True
                },
                request_only=True,
            ),
            OpenApiExample(
                'Criar Estudante Mínimo',
                value={
                    "email": "maria.santos@email.com",
                    "name": "Maria Santos",
                    "password": "senhaSegura456",
                    "password_confirmation": "senhaSegura456"
                },
                request_only=True,
            ),
            OpenApiExample(
                'Estudante Criado',
                value={
                    "id": 1,
                    "email": "joao.silva@email.com",
                    "username": "joao.silva",
                    "name": "João Silva",
                    "is_active": True,
                    "is_staff": False,
                    "is_superuser": False,
                    "date_joined": "2024-01-15T10:30:00Z",
                    "last_login": None
                },
                response_only=True,
            ),
        ]
    ),
    update=extend_schema(
        summary='Atualizar estudante',
        description='Atualiza completamente um estudante existente.',
        tags=['Estudantes'],
        examples=[
            OpenApiExample(
                'Atualização Completa',
                value={
                    "email": "joao.silva.novo@email.com",
                    "username": "joao.silva.updated",
                    "name": "João Silva Atualizado",
                    "password": "novaSenha789",
                    "password_confirmation": "novaSenha789",
                    "is_active": True
                },
                request_only=True,
            ),
            OpenApiExample(
                'Estudante Atualizado',
                value={
                    "id": 1,
                    "email": "joao.silva.novo@email.com",
                    "username": "joao.silva.updated",
                    "name": "João Silva Atualizado",
                    "is_active": True,
                    "is_staff": False,
                    "is_superuser": False,
                    "date_joined": "2024-01-15T10:30:00Z",
                    "last_login": "2024-01-20T14:20:00Z"
                },
                response_only=True,
            ),
        ]
    ),
    partial_update=extend_schema(
        summary='Atualizar parcialmente estudante',
        description='Atualiza parcialmente um estudante existente (apenas campos enviados).',
        tags=['Estudantes'],
        examples=[
            OpenApiExample(
                'Atualizar Apenas Nome',
                value={
                    "name": "João Silva Modificado"
                },
                request_only=True,
            ),
            OpenApiExample(
                'Atualizar Senha',
                value={
                    "password": "novaSenhaMaisSegura321",
                    "password_confirmation": "novaSenhaMaisSegura321"
                },
                request_only=True,
            ),
            OpenApiExample(
                'Estudante Atualizado',
                value={
                    "id": 1,
                    "email": "joao.silva@email.com",
                    "username": "joao.silva",
                    "name": "João Silva Modificado",
                    "is_active": True,
                    "is_staff": False,
                    "is_superuser": False,
                    "date_joined": "2024-01-15T10:30:00Z",
                    "last_login": "2024-01-20T14:20:00Z"
                },
                response_only=True,
            ),
        ]
    ),
    destroy=extend_schema(
        summary='Deletar estudante',
        description='Remove um estudante do sistema.',
        tags=['Estudantes'],
    ),
)
class StudentViewSet(viewsets.ModelViewSet):
    lookup_value_regex = r"\d+"
    queryset = Student.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['email', 'username', 'name']
    ordering_fields = ['id', 'email', 'name', 'date_joined']
    ordering = ['-date_joined']

    def get_serializer_class(self):
        if self.action == 'create':
            return StudentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return StudentUpdateSerializer
        return StudentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            validated_data = serializer.validated_data.copy()
            validated_data.pop('password_confirmation', None)
            password = validated_data.pop('password')
            
            student = StudentService.create_student(
                email=validated_data.get('email'),
                username=validated_data.get('username'),
                name=validated_data.get('name'),
                password=password,
                is_active=validated_data.get('is_active', True)
            )
            
            response_serializer = StudentSerializer(student)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            raise ValidationError({'detail': str(e)})

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        
        try:
            validated_data = serializer.validated_data.copy()
            validated_data.pop('password_confirmation', None)
            
            password = validated_data.pop('password', None)
            
            update_data = {k: v for k, v in validated_data.items() if v is not None}
            student = StudentService.update_student(instance, password=password, **update_data)
            
            response_serializer = StudentSerializer(student)
            return Response(response_serializer.data)
        except Exception as e:
            raise ValidationError({'detail': str(e)})

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        try:
            validated_data = serializer.validated_data.copy()
            validated_data.pop('password_confirmation', None)
            
            password = validated_data.pop('password', None)
            
            update_data = {k: v for k, v in validated_data.items() if v is not None}
            student = StudentService.update_student(instance, password=password, **update_data)
            
            response_serializer = StudentSerializer(student)
            return Response(response_serializer.data)
        except Exception as e:
            raise ValidationError({'detail': str(e)})
