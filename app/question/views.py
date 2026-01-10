from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from question.models import Question, Alternative
from question.serializers import (
    QuestionSerializer,
    QuestionListSerializer,
    QuestionCreateUpdateSerializer,
    AlternativeSerializer
)
from question.services import QuestionService, AlternativeService
from question.filters import QuestionFilter


class QuestionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar questões.

    list: Lista todas as questões (versão simplificada)
    retrieve: Retorna uma questão completa com alternatives
    create: Cria uma nova questão com alternatives
    update: Atualiza uma questão e suas alternatives
    partial_update: Atualiza parcialmente uma questão
    destroy: Remove uma questão
    """
    queryset = Question.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = QuestionFilter
    search_fields = ['content']
    ordering_fields = ['id', 'content']
    ordering = ['-id']

    def get_serializer_class(self):
        """Retorna o serializer apropriado para cada ação."""
        if self.action == 'list':
            return QuestionListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return QuestionCreateUpdateSerializer
        return QuestionSerializer

    def get_queryset(self):
        """Retorna o queryset otimizado com prefetch_related."""
        queryset = Question.objects.prefetch_related('alternatives').all()
        return queryset

    def create(self, request, *args, **kwargs):
        """Cria uma nova questão usando o service."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            alternatives_data = serializer.validated_data.pop('alternatives', [])
            question = QuestionService.create_question(
                content=serializer.validated_data['content']
            )
            
            # Cria as alternativas usando o service
            for alt_data in alternatives_data:
                AlternativeService.create_alternative(
                    question=question,
                    content=alt_data['content'],
                    option=alt_data['option'],
                    is_correct=alt_data.get('is_correct', False)
                )
            
            response_serializer = QuestionSerializer(question)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            raise ValidationError(e)
        except Exception as e:
            raise ValidationError({'detail': str(e)})

    def update(self, request, *args, **kwargs):
        """Atualiza uma questão e suas alternatives."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        
        try:
            alternatives_data = serializer.validated_data.pop('alternatives', None)
            
            instance.content = serializer.validated_data.get('content', instance.content)
            instance.save()
            
            # Atualiza alternativas se fornecidas
            if alternatives_data is not None:
                # Remove alternativas existentes
                instance.alternatives.all().delete()
                
                # Cria novas alternativas usando o service
                for alt_data in alternatives_data:
                    AlternativeService.create_alternative(
                        question=instance,
                        content=alt_data['content'],
                        option=alt_data['option'],
                        is_correct=alt_data.get('is_correct', False)
                    )
            
            response_serializer = QuestionSerializer(instance)
            return Response(response_serializer.data)
        except ValidationError as e:
            raise ValidationError(e)
        except Exception as e:
            raise ValidationError({'detail': str(e)})

    def partial_update(self, request, *args, **kwargs):
        """Atualiza parcialmente uma questão."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        try:
            alternatives_data = serializer.validated_data.pop('alternatives', None)
            
            if 'content' in serializer.validated_data:
                instance.content = serializer.validated_data['content']
                instance.save()
            
            # Atualiza alternativas se fornecidas
            if alternatives_data is not None:
                # Remove alternativas existentes
                instance.alternatives.all().delete()
                
                # Cria novas alternativas usando o service
                for alt_data in alternatives_data:
                    AlternativeService.create_alternative(
                        question=instance,
                        content=alt_data['content'],
                        option=alt_data['option'],
                        is_correct=alt_data.get('is_correct', False)
                    )
            
            response_serializer = QuestionSerializer(instance)
            return Response(response_serializer.data)
        except ValidationError as e:
            raise ValidationError(e)
        except Exception as e:
            raise ValidationError({'detail': str(e)})

    @action(detail=True, methods=['get'], url_path='alternatives')
    def alternatives(self, request, pk=None):
        """Lista todas as alternativas de uma questão."""
        question = self.get_object()
        alternatives = question.alternatives.all()
        serializer = AlternativeSerializer(alternatives, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='alternatives/(?P<alternative_id>[^/.]+)/mark-correct')
    def mark_alternative_correct(self, request, pk=None, alternative_id=None):
        """Marca uma alternativa como correta."""
        question = self.get_object()
        try:
            alternative = question.alternatives.get(id=alternative_id)
            AlternativeService.mark_as_correct(alternative)
            serializer = AlternativeSerializer(alternative)
            return Response(serializer.data)
        except Alternative.DoesNotExist:
            raise ValidationError({'detail': 'Alternativa não encontrada.'})
