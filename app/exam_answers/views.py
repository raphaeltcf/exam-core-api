from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from exam.models import Exam, ExamQuestion
from exam_answers.models import ExamAnswer
from exam_answers.serializers import (
    ExamAnswerSerializer,
    ExamAnswerCreateSerializer,
    ExamAnswerListSerializer
)
from exam_answers.service import ExamAnswerService
from exam_answers.filters import ExamAnswerFilter
from question.models import Alternative
from student.models import Student


class ExamAnswerViewSet(viewsets.ModelViewSet):
    queryset = ExamAnswer.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ExamAnswerFilter
    ordering_fields = ['id', 'created_at', 'updated_at', 'is_correct']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ExamAnswerListSerializer
        elif self.action == 'create':
            return ExamAnswerCreateSerializer
        return ExamAnswerSerializer

    def get_queryset(self):
        queryset = ExamAnswer.objects.select_related(
            'student',
            'exam_question__exam',
            'exam_question__question',
            'selected_alternative'
        ).prefetch_related(
            'exam_question__question__alternatives'
        ).all()
        
        exam_id = self.request.query_params.get('exam_id', None)
        student_id = self.request.query_params.get('student_id', None)
        exam_question_id = self.request.query_params.get('exam_question_id', None)
        
        if exam_id:
            queryset = queryset.filter(exam_question__exam_id=exam_id)
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if exam_question_id:
            queryset = queryset.filter(exam_question_id=exam_question_id)
        
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            exam_answer = serializer.save()
            response_serializer = ExamAnswerSerializer(exam_answer)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            raise ValidationError(e)
        except Exception as e:
            raise ValidationError({'detail': str(e)})

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        
        try:
            selected_alternative = serializer.validated_data.get('selected_alternative')
            
            if selected_alternative:
                ExamAnswerService.validate_answer(instance.exam_question, selected_alternative)
                exam_answer = ExamAnswerService.update_answer(
                    instance,
                    selected_alternative=selected_alternative
                )
            else:
                exam_answer = ExamAnswerService.update_answer(instance)
            
            response_serializer = ExamAnswerSerializer(exam_answer)
            return Response(response_serializer.data)
        except ValidationError as e:
            raise ValidationError(e)
        except Exception as e:
            raise ValidationError({'detail': str(e)})

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        try:
            selected_alternative = serializer.validated_data.get('selected_alternative')
            
            if selected_alternative:
                ExamAnswerService.validate_answer(instance.exam_question, selected_alternative)
                
                exam_answer = ExamAnswerService.update_answer(
                    instance,
                    selected_alternative=selected_alternative
                )
            else:
                exam_answer = ExamAnswerService.update_answer(instance)
            
            response_serializer = ExamAnswerSerializer(exam_answer)
            return Response(response_serializer.data)
        except ValidationError as e:
            raise ValidationError(e)
        except Exception as e:
            raise ValidationError({'detail': str(e)})

    @action(detail=False, methods=['get'], url_path='by-exam')
    def by_exam(self, request):
        exam_id = request.query_params.get('exam_id', None)
        
        if not exam_id:
            raise ValidationError({'detail': 'Parâmetro exam_id é obrigatório.'})
        
        try:
            exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            raise NotFound({'detail': 'Exame não encontrado.'})
        
        queryset = self.get_queryset().filter(exam_question__exam=exam)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ExamAnswerListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ExamAnswerListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='by-student')
    def by_student(self, request):
        student_id = request.query_params.get('student_id', None)
        
        if not student_id:
            raise ValidationError({'detail': 'Parâmetro student_id é obrigatório.'})
        
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            raise NotFound({'detail': 'Estudante não encontrado.'})
        
        queryset = self.get_queryset().filter(student=student)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ExamAnswerListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ExamAnswerListSerializer(queryset, many=True)
        return Response(serializer.data)
