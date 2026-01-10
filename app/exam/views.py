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
    ReorderQuestionsSerializer,
    ExamTakeSerializer
)
from exam_answers.serializers import ExamAnswerSerializer
from exam.services import ExamService
from exam_answers.service import ExamAnswerService
from exam.filters import ExamFilter
from student.services import StudentService
from question.models import Question


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

                                                                                 
                                                                                  
                                     