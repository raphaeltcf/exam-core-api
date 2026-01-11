from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError as DRFValidationError

from django.core.exceptions import ValidationError as DjangoValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from question.models import Question, Alternative
from question.serializers import (
    QuestionSerializer,
    QuestionListSerializer,
    QuestionCreateUpdateSerializer,
    AlternativeSerializer
)
from question.services import QuestionService, AlternativeService
from question.filters import QuestionFilter


@extend_schema_view(
    list=extend_schema(
        summary='Listar questões',
        description='Lista todas as questões com paginação, busca e filtros.',
        parameters=[
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Busca por conteúdo da questão'
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Ordenação: id, content (use - para decrescente)'
            ),
        ],
        tags=['Questões'],
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
                            "content": "Qual é a capital do Brasil?",
                            "alternatives_count": 4,
                            "has_correct_alternative": True
                        },
                        {
                            "id": 2,
                            "content": "Quanto é 2 + 2?",
                            "alternatives_count": 4,
                            "has_correct_alternative": True
                        }
                    ]
                },
                response_only=True,
            ),
        ]
    ),
    retrieve=extend_schema(
        summary='Detalhes da questão',
        description='Retorna os detalhes completos de uma questão com suas alternativas.',
        tags=['Questões'],
        examples=[
            OpenApiExample(
                'Questão Detalhada',
                value={
                    "id": 1,
                    "content": "Qual é a capital do Brasil?",
                    "alternatives": [
                        {
                            "id": 1,
                            "content": "São Paulo",
                            "option": 1,
                            "option_display": "A",
                            "is_correct": False
                        },
                        {
                            "id": 2,
                            "content": "Brasília",
                            "option": 2,
                            "option_display": "B",
                            "is_correct": True
                        },
                        {
                            "id": 3,
                            "content": "Rio de Janeiro",
                            "option": 3,
                            "option_display": "C",
                            "is_correct": False
                        },
                        {
                            "id": 4,
                            "content": "Salvador",
                            "option": 4,
                            "option_display": "D",
                            "is_correct": False
                        }
                    ],
                    "has_correct_alternative": True
                },
                response_only=True,
            ),
        ]
    ),
    create=extend_schema(
        summary='Criar questão',
        description='Cria uma nova questão com alternativas. A questão deve ter entre 1 e 5 alternativas, e exatamente uma alternativa correta.',
        tags=['Questões'],
        examples=[
            OpenApiExample(
                'Questão de Múltipla Escolha',
                value={
                    "content": "Qual é a capital do Brasil?",
                    "alternatives": [
                        {
                            "content": "São Paulo",
                            "option": 1,
                            "is_correct": False
                        },
                        {
                            "content": "Brasília",
                            "option": 2,
                            "is_correct": True
                        },
                        {
                            "content": "Rio de Janeiro",
                            "option": 3,
                            "is_correct": False
                        },
                        {
                            "content": "Salvador",
                            "option": 4,
                            "is_correct": False
                        }
                    ]
                },
                request_only=True,
            ),
            OpenApiExample(
                'Questão de Matemática',
                value={
                    "content": "Quanto é 2 + 2?",
                    "alternatives": [
                        {
                            "content": "3",
                            "option": 1,
                            "is_correct": False
                        },
                        {
                            "content": "4",
                            "option": 2,
                            "is_correct": True
                        },
                        {
                            "content": "5",
                            "option": 3,
                            "is_correct": False
                        }
                    ]
                },
                request_only=True,
            ),
            OpenApiExample(
                'Questão Criada',
                value={
                    "id": 1,
                    "content": "Qual é a capital do Brasil?",
                    "alternatives": [
                        {
                            "id": 1,
                            "content": "São Paulo",
                            "option": 1,
                            "option_display": "A",
                            "is_correct": False
                        },
                        {
                            "id": 2,
                            "content": "Brasília",
                            "option": 2,
                            "option_display": "B",
                            "is_correct": True
                        },
                        {
                            "id": 3,
                            "content": "Rio de Janeiro",
                            "option": 3,
                            "option_display": "C",
                            "is_correct": False
                        },
                        {
                            "id": 4,
                            "content": "Salvador",
                            "option": 4,
                            "option_display": "D",
                            "is_correct": False
                        }
                    ],
                    "has_correct_alternative": True
                },
                response_only=True,
            ),
        ]
    ),
    update=extend_schema(
        summary='Atualizar questão',
        description='Atualiza completamente uma questão existente.',
        tags=['Questões'],
        examples=[
            OpenApiExample(
                'Atualização Completa',
                value={
                    "content": "Qual é a capital do Brasil? (Atualizada)",
                    "alternatives": [
                        {
                            "content": "São Paulo",
                            "option": 1,
                            "is_correct": False
                        },
                        {
                            "content": "Brasília",
                            "option": 2,
                            "is_correct": True
                        }
                    ]
                },
                request_only=True,
            ),
        ]
    ),
    partial_update=extend_schema(
        summary='Atualizar parcialmente questão',
        description='Atualiza parcialmente uma questão existente.',
        tags=['Questões'],
        examples=[
            OpenApiExample(
                'Atualizar Apenas Conteúdo',
                value={
                    "content": "Nova pergunta atualizada"
                },
                request_only=True,
            ),
        ]
    ),
    destroy=extend_schema(
        summary='Deletar questão',
        description='Remove uma questão do sistema.',
        tags=['Questões'],
    ),
)
class QuestionViewSet(viewsets.ModelViewSet):
    lookup_value_regex = r"\d+"
    queryset = Question.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = QuestionFilter
    search_fields = ['content']
    ordering_fields = ['id', 'content']
    ordering = ['-id']

    def get_serializer_class(self):
        if self.action == 'list':
            return QuestionListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return QuestionCreateUpdateSerializer
        return QuestionSerializer

    def get_queryset(self):
        queryset = Question.objects.prefetch_related('alternatives').all()
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            alternatives_data = serializer.validated_data.pop('alternatives', [])
            question = QuestionService.create_question(
                content=serializer.validated_data['content']
            )
            
            for alt_data in alternatives_data:
                AlternativeService.create_alternative(
                    question=question,
                    content=alt_data['content'],
                    option=alt_data['option'],
                    is_correct=alt_data.get('is_correct', False)
                )
            
            response_serializer = QuestionSerializer(question)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, 'message_dict') else {'detail': str(e)})
        except DRFValidationError:
            raise
        except Exception as e:
            raise DRFValidationError({'detail': str(e)})

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        
        try:
            alternatives_data = serializer.validated_data.pop('alternatives', None)
            
            instance.content = serializer.validated_data.get('content', instance.content)
            instance.save()
            
            if alternatives_data is not None:
                instance.alternatives.all().delete()
                
                for alt_data in alternatives_data:
                    AlternativeService.create_alternative(
                        question=instance,
                        content=alt_data['content'],
                        option=alt_data['option'],
                        is_correct=alt_data.get('is_correct', False)
                    )
            
            response_serializer = QuestionSerializer(instance)
            return Response(response_serializer.data)
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, 'message_dict') else {'detail': str(e)})
        except DRFValidationError:
            raise
        except Exception as e:
            raise DRFValidationError({'detail': str(e)})

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        try:
            alternatives_data = serializer.validated_data.pop('alternatives', None)
            
            if 'content' in serializer.validated_data:
                instance.content = serializer.validated_data['content']
                instance.save()
            
            if alternatives_data is not None:
                instance.alternatives.all().delete()
                
                for alt_data in alternatives_data:
                    AlternativeService.create_alternative(
                        question=instance,
                        content=alt_data['content'],
                        option=alt_data['option'],
                        is_correct=alt_data.get('is_correct', False)
                    )
            
            response_serializer = QuestionSerializer(instance)
            return Response(response_serializer.data)
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, 'message_dict') else {'detail': str(e)})
        except DRFValidationError:
            raise
        except Exception as e:
            raise DRFValidationError({'detail': str(e)})

    @extend_schema(
        summary='Listar alternativas da questão',
        description='Retorna todas as alternativas de uma questão específica.',
        tags=['Questões'],
        examples=[
            OpenApiExample(
                'Lista de Alternativas',
                value=[
                    {
                        "id": 1,
                        "content": "São Paulo",
                        "option": 1,
                        "option_display": "A",
                        "is_correct": False
                    },
                    {
                        "id": 2,
                        "content": "Brasília",
                        "option": 2,
                        "option_display": "B",
                        "is_correct": True
                    },
                    {
                        "id": 3,
                        "content": "Rio de Janeiro",
                        "option": 3,
                        "option_display": "C",
                        "is_correct": False
                    }
                ],
                response_only=True,
            ),
        ]
    )
    @action(detail=True, methods=['get'], url_path='alternatives')
    def alternatives(self, request, pk=None):
        question = self.get_object()
        alternatives = question.alternatives.all()
        serializer = AlternativeSerializer(alternatives, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary='Marcar alternativa como correta',
        description='Marca uma alternativa específica como correta. Automaticamente desmarca as outras alternativas da mesma questão.',
        tags=['Questões'],
        parameters=[
            OpenApiParameter(
                name='alternative_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='ID da alternativa a ser marcada como correta'
            ),
        ],
        examples=[
            OpenApiExample(
                'Alternativa Marcada',
                value={
                    "id": 2,
                    "content": "Brasília",
                    "option": 2,
                    "option_display": "B",
                    "is_correct": True
                },
                response_only=True,
            ),
        ]
    )
    @action(detail=True, methods=['post'], url_path='alternatives/(?P<alternative_id>[^/.]+)/mark-correct')
    def mark_alternative_correct(self, request, pk=None, alternative_id=None):
        question = self.get_object()
        try:
            alternative_id = int(alternative_id)
        except (TypeError, ValueError):
            raise DRFValidationError({'detail': 'alternative_id inválido.'})
        try:
            alternative = question.alternatives.get(id=alternative_id)
            AlternativeService.mark_as_correct(alternative)
            serializer = AlternativeSerializer(alternative)
            return Response(serializer.data)
        except Alternative.DoesNotExist:
            raise DRFValidationError({'detail': 'Alternativa não encontrada.'})
