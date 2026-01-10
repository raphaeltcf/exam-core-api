from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from exam.models import Exam, ExamQuestion
from exam.serializers import (
    ExamSerializer,
    ExamListSerializer,
    ExamCreateUpdateSerializer,
    ExamQuestionSerializer,
    AddQuestionToExamSerializer,
    ReorderQuestionsSerializer
)
from exam.services import ExamService
from exam.filters import ExamFilter
from question.models import Question


class ExamViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar exames.

    list: Lista todos os exames (versão simplificada)
    retrieve: Retorna um exame completo com questions
    create: Cria um novo exame
    update: Atualiza um exame
    partial_update: Atualiza parcialmente um exame
    destroy: Remove um exame

    Custom actions:
    - add_question: Adiciona uma questão ao exame
    - remove_question: Remove uma questão do exame
    - reorder_questions: Reordena as questões do exame
    - questions: Lista as questões do exame
    """
    queryset = Exam.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ExamFilter
    search_fields = ['name']
    ordering_fields = ['id', 'name']
    ordering = ['-id']

    def get_serializer_class(self):
        """Retorna o serializer apropriado para cada ação."""
        if self.action == 'list':
            return ExamListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ExamCreateUpdateSerializer
        return ExamSerializer

    def get_queryset(self):
        """Retorna o queryset otimizado com prefetch_related."""
        queryset = Exam.objects.prefetch_related(
            'examquestion_set__question__alternatives'
        ).all()
        return queryset

    def create(self, request, *args, **kwargs):
        """Cria um novo exame usando o service."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            question_ids = serializer.validated_data.pop('question_ids', [])
            exam = ExamService.create_exam(name=serializer.validated_data['name'])
            
            # Adiciona questões se fornecidas
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

    @action(detail=True, methods=['post'], url_path='add-question')
    def add_question(self, request, pk=None):
        """Adiciona uma questão ao exame."""
        exam = self.get_object()
        serializer = AddQuestionToExamSerializer(
            data=request.data,
            context={'exam': exam}
        )
        serializer.is_valid(raise_exception=True)
        
        try:
            question = serializer.validated_data['question_id']
            number = serializer.validated_data['number']
            
            exam_question = ExamService.add_question_to_exam(exam, question, number)
            response_serializer = ExamQuestionSerializer(exam_question)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            raise ValidationError({'detail': str(e)})
        except Exception as e:
            raise ValidationError({'detail': str(e)})

    @action(detail=True, methods=['delete'], url_path='remove-question/(?P<question_id>[^/.]+)')
    def remove_question(self, request, pk=None, question_id=None):
        """Remove uma questão do exame."""
        exam = self.get_object()
        
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

    @action(detail=True, methods=['post'], url_path='reorder-questions')
    def reorder_questions(self, request, pk=None):
        """Reordena as questões do exame."""
        exam = self.get_object()
        serializer = ReorderQuestionsSerializer(
            data=request.data,
            context={'exam': exam}
        )
        serializer.is_valid(raise_exception=True)
        
        try:
            exam_question_ids = serializer.validated_data['exam_question_ids']
            
            # Usa os IDs na ordem fornecida pelo usuário
            ExamService.reorder_questions(exam, exam_question_ids)
            
            # Recarrega o exame para obter as questões reordenadas
            exam.refresh_from_db()
            response_serializer = ExamSerializer(exam)
            return Response(response_serializer.data)
        except ValueError as e:
            raise ValidationError({'detail': str(e)})
        except Exception as e:
            raise ValidationError({'detail': str(e)})

    @action(detail=True, methods=['get'], url_path='questions')
    def questions(self, request, pk=None):
        """Lista todas as questões do exame ordenadas por número."""
        exam = self.get_object()
        exam_questions = ExamQuestion.objects.filter(exam=exam).select_related(
            'question'
        ).prefetch_related('question__alternatives').order_by('number')
        
        serializer = ExamQuestionSerializer(exam_questions, many=True)
        return Response(serializer.data)
