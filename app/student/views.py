from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from student.models import Student
from student.serializers import (
    StudentSerializer,
    StudentCreateSerializer,
    StudentUpdateSerializer
)
from student.services import StudentService


class StudentViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar estudantes.

    list: Lista todos os estudantes
    retrieve: Retorna um estudante completo
    create: Cria um novo estudante (usa StudentCreateSerializer)
    update: Atualiza um estudante completamente (usa StudentUpdateSerializer)
    partial_update: Atualiza parcialmente um estudante (usa StudentUpdateSerializer)
    destroy: Remove um estudante
    """
    queryset = Student.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['email', 'username', 'name']
    ordering_fields = ['id', 'email', 'name', 'date_joined']
    ordering = ['-date_joined']

    def get_serializer_class(self):
        """Retorna o serializer apropriado para cada ação."""
        if self.action == 'create':
            return StudentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return StudentUpdateSerializer
        return StudentSerializer

    def create(self, request, *args, **kwargs):
        """Cria um novo estudante usando o service."""
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
        """Atualiza um estudante usando o service."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        
        try:
            validated_data = serializer.validated_data.copy()
            validated_data.pop('password_confirmation', None)
            
            # Extrai password separadamente se fornecido
            password = validated_data.pop('password', None)
            
            # Atualiza usando o service
            update_data = {k: v for k, v in validated_data.items() if v is not None}
            student = StudentService.update_student(instance, password=password, **update_data)
            
            response_serializer = StudentSerializer(student)
            return Response(response_serializer.data)
        except Exception as e:
            raise ValidationError({'detail': str(e)})

    def partial_update(self, request, *args, **kwargs):
        """Atualiza parcialmente um estudante usando o service."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        try:
            validated_data = serializer.validated_data.copy()
            validated_data.pop('password_confirmation', None)
            
            # Extrai password separadamente se fornecido
            password = validated_data.pop('password', None)
            
            # Atualiza apenas os campos fornecidos
            update_data = {k: v for k, v in validated_data.items() if v is not None}
            student = StudentService.update_student(instance, password=password, **update_data)
            
            response_serializer = StudentSerializer(student)
            return Response(response_serializer.data)
        except Exception as e:
            raise ValidationError({'detail': str(e)})
