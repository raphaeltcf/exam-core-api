from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from exam.models import Exam, ExamQuestion
from exam.serializers import (
    ExamSerializer,
    ExamListSerializer,
    ExamCreateUpdateSerializer,
    ExamQuestionSerializer,
    AddQuestionToExamSerializer,
    ReorderQuestionsSerializer,
    ExamTakeSerializer
)
from exam_answers.serializers import ExamAnswerSerializer
from exam.services import ExamService
from exam_answers.service import ExamAnswerService
from exam.filters import ExamFilter
from student.services import StudentService
from question.models import Question


@extend_schema_view(
    list=extend_schema(
        summary='Listar provas',
        description='Lista todas as provas com paginação, busca e filtros.',
        parameters=[
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Busca por nome da prova'
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Ordenação: id, name (use - para decrescente)'
            ),
        ],
        tags=['Provas'],
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
                            "name": "Prova de Geografia",
                            "questions_count": 10
                        },
                        {
                            "id": 2,
                            "name": "Prova de Matemática",
                            "questions_count": 15
                        }
                    ]
                },
                response_only=True,
            ),
        ]
    ),
    retrieve=extend_schema(
        summary='Detalhes da prova',
        description='Retorna os detalhes completos de uma prova com todas as questões (sem mostrar as respostas corretas). Use este endpoint para obter a prova que o estudante deve responder.',
        tags=['Provas'],
        examples=[
            OpenApiExample(
                'Prova para Realizar',
                value={
                    "id": 1,
                    "name": "Prova de Geografia",
                    "questions": [
                        {
                            "id": 1,
                            "number": 1,
                            "question": {
                                "id": 1,
                                "content": "Qual é a capital do Brasil?",
                                "alternatives": [
                                    {
                                        "id": 1,
                                        "content": "São Paulo",
                                        "option": 1,
                                        "option_display": "A"
                                    },
                                    {
                                        "id": 2,
                                        "content": "Brasília",
                                        "option": 2,
                                        "option_display": "B"
                                    },
                                    {
                                        "id": 3,
                                        "content": "Rio de Janeiro",
                                        "option": 3,
                                        "option_display": "C"
                                    },
                                    {
                                        "id": 4,
                                        "content": "Salvador",
                                        "option": 4,
                                        "option_display": "D"
                                    }
                                ]
                            }
                        },
                        {
                            "id": 2,
                            "number": 2,
                            "question": {
                                "id": 5,
                                "content": "Qual é o maior oceano do mundo?",
                                "alternatives": [
                                    {
                                        "id": 20,
                                        "content": "Atlântico",
                                        "option": 1,
                                        "option_display": "A"
                                    },
                                    {
                                        "id": 21,
                                        "content": "Pacífico",
                                        "option": 2,
                                        "option_display": "B"
                                    },
                                    {
                                        "id": 22,
                                        "content": "Índico",
                                        "option": 3,
                                        "option_display": "C"
                                    }
                                ]
                            }
                        }
                    ]
                },
                response_only=True,
            ),
        ]
    ),
    create=extend_schema(
        summary='Criar prova',
        description='Cria uma nova prova. Opcionalmente pode incluir questões na criação.',
        tags=['Provas'],
        examples=[
            OpenApiExample(
                'Prova Simples',
                value={
                    "name": "Prova de Geografia"
                },
                request_only=True,
            ),
            OpenApiExample(
                'Prova com Questões',
                value={
                    "name": "Prova de Matemática",
                    "question_ids": [1, 5, 8, 12, 15]
                },
                request_only=True,
            ),
            OpenApiExample(
                'Prova Criada',
                value={
                    "id": 1,
                    "name": "Prova de Geografia",
                    "questions": [],
                    "questions_count": 0
                },
                response_only=True,
            ),
        ]
    ),
    update=extend_schema(
        summary='Atualizar prova',
        description='Atualiza completamente uma prova existente. Se question_ids for fornecido, substitui todas as questões da prova.',
        tags=['Provas'],
        examples=[
            OpenApiExample(
                'Atualizar Nome e Questões',
                value={
                    "name": "Prova de Geografia Avançada",
                    "question_ids": [1, 2, 3, 4, 5]
                },
                request_only=True,
            ),
        ]
    ),
    partial_update=extend_schema(
        summary='Atualizar parcialmente prova',
        description='Atualiza parcialmente uma prova existente.',
        tags=['Provas'],
        examples=[
            OpenApiExample(
                'Atualizar Apenas Nome',
                value={
                    "name": "Nova Prova de Geografia"
                },
                request_only=True,
            ),
        ]
    ),
    destroy=extend_schema(
        summary='Deletar prova',
        description='Remove uma prova do sistema.',
        tags=['Provas'],
    ),
)
class ExamViewSet(viewsets.ModelViewSet):
    lookup_value_regex = r"\d+"
    queryset = Exam.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ExamFilter
    search_fields = ['name']
    ordering_fields = ['id', 'name']
    ordering = ['-id']

    def get_serializer_class(self):
        if self.action == 'list':
            return ExamListSerializer
        elif self.action == 'retrieve':
                                                                  
                                                                   
            return ExamTakeSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ExamCreateUpdateSerializer
        return ExamSerializer

    def get_queryset(self):
        queryset = Exam.objects.prefetch_related(
            'examquestion_set__question__alternatives'
        ).all()
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        question_ids = serializer.validated_data.pop('question_ids', [])
        exam = ExamService.create_exam(name=serializer.validated_data['name'])
        
        try:
            for index, question_id in enumerate(question_ids, start=1):
                question = Question.objects.get(id=question_id)
                ExamService.add_question_to_exam(exam, question, index)
            
            response_serializer = ExamSerializer(exam)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            raise ValidationError({'detail': str(e)})
        except Question.DoesNotExist:
            raise ValidationError({'detail': 'Questão não encontrada.'})
        except Exception as e:
            raise ValidationError({'detail': str(e)})

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)

        try:
            updated = serializer.save()
            response_serializer = ExamSerializer(updated)
            return Response(response_serializer.data)
        except Question.DoesNotExist:
            raise ValidationError({'detail': 'Questão não encontrada.'})
        except ValueError as e:
            raise ValidationError({'detail': str(e)})
        except Exception as e:
            raise ValidationError({'detail': str(e)})

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            updated = serializer.save()
            response_serializer = ExamSerializer(updated)
            return Response(response_serializer.data)
        except Question.DoesNotExist:
            raise ValidationError({'detail': 'Questão não encontrada.'})
        except ValueError as e:
            raise ValidationError({'detail': str(e)})
        except Exception as e:
            raise ValidationError({'detail': str(e)})

    @extend_schema(
        summary='Adicionar questão à prova',
        description='Adiciona uma questão específica à prova em uma posição determinada.',
        tags=['Provas'],
        request=AddQuestionToExamSerializer,
        examples=[
            OpenApiExample(
                'Adicionar Questão',
                value={
                    "question_id": 5,
                    "number": 3
                },
                request_only=True,
            ),
            OpenApiExample(
                'Questão Adicionada',
                value={
                    "id": 10,
                    "exam": 1,
                    "question": {
                        "id": 5,
                        "content": "Qual é o maior oceano do mundo?",
                        "alternatives": [
                            {
                                "id": 20,
                                "content": "Atlântico",
                                "option": 1,
                                "option_display": "A",
                                "is_correct": False
                            },
                            {
                                "id": 21,
                                "content": "Pacífico",
                                "option": 2,
                                "option_display": "B",
                                "is_correct": True
                            }
                        ],
                        "has_correct_alternative": True
                    },
                    "number": 3
                },
                response_only=True,
            ),
        ]
    )
    @action(detail=True, methods=['post'], url_path='add-question')
    def add_question(self, request, pk=None):
        exam = self.get_object()
        serializer = AddQuestionToExamSerializer(
            data=request.data,
            context={'exam': exam}
        )
        serializer.is_valid(raise_exception=True)
        
        question = serializer.validated_data['question_id']
        number = serializer.validated_data['number']
        
        try:
            exam_question = ExamService.add_question_to_exam(exam, question, number)
            response_serializer = ExamQuestionSerializer(exam_question)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            raise ValidationError({'detail': str(e)})
        except Exception as e:
            raise ValidationError({'detail': str(e)})

    @extend_schema(
        summary='Remover questão da prova',
        description='Remove uma questão específica da prova.',
        tags=['Provas'],
        parameters=[
            OpenApiParameter(
                name='question_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='ID da questão a ser removida'
            ),
        ],
        examples=[
            OpenApiExample(
                'Questão Removida',
                value={
                    "detail": "Questão removida do exame com sucesso."
                },
                response_only=True,
            ),
        ]
    )
    @action(detail=True, methods=['delete'], url_path='remove-question/(?P<question_id>[^/.]+)')
    def remove_question(self, request, pk=None, question_id=None):
        exam = self.get_object()
        try:
            question_id = int(question_id)
        except (TypeError, ValueError):
            raise ValidationError({'detail': 'question_id inválido.'})
        
        try:
            question = Question.objects.get(id=question_id)
            ExamService.remove_question_from_exam(exam, question)
            return Response(
                {'detail': 'Questão removida do exame com sucesso.'},
                status=status.HTTP_204_NO_CONTENT
            )
        except Question.DoesNotExist:
            raise NotFound({'detail': 'Questão não encontrada.'})
        except Exception as e:
            raise ValidationError({'detail': str(e)})

    @extend_schema(
        summary='Reordenar questões da prova',
        description='Reordena as questões de uma prova. Envie a lista de IDs de ExamQuestion na ordem desejada.',
        tags=['Provas'],
        request=ReorderQuestionsSerializer,
        examples=[
            OpenApiExample(
                'Reordenar Questões',
                value={
                    "exam_question_ids": [5, 3, 1, 4, 2]
                },
                request_only=True,
            ),
            OpenApiExample(
                'Prova Reordenada',
                value={
                    "id": 1,
                    "name": "Prova de Geografia",
                    "questions": [
                        {
                            "id": 5,
                            "number": 1,
                            "question": {
                                "id": 10,
                                "content": "Questão 5",
                                "alternatives_count": 4,
                                "has_correct_alternative": True
                            }
                        },
                        {
                            "id": 3,
                            "number": 2,
                            "question": {
                                "id": 8,
                                "content": "Questão 3",
                                "alternatives_count": 3,
                                "has_correct_alternative": True
                            }
                        }
                    ],
                    "questions_count": 5
                },
                response_only=True,
            ),
        ]
    )
    @action(detail=True, methods=['post'], url_path='reorder-questions')
    def reorder_questions(self, request, pk=None):
        exam = self.get_object()
        serializer = ReorderQuestionsSerializer(
            data=request.data,
            context={'exam': exam}
        )
        serializer.is_valid(raise_exception=True)
        
        try:
            exam_question_ids = serializer.validated_data['exam_question_ids']
            
            ExamService.reorder_questions(exam, exam_question_ids)
            
            exam.refresh_from_db()
            response_serializer = ExamSerializer(exam)
            return Response(response_serializer.data)
        except ValueError as e:
            raise ValidationError({'detail': str(e)})
        except Exception as e:
            raise ValidationError({'detail': str(e)})

                                                                                 
                                                                                  
                                     