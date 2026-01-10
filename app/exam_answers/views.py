from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError as DRFValidationError, NotFound, MethodNotAllowed

from django.core.exceptions import ValidationError as DjangoValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from exam.models import Exam
from exam_answers.models import ExamAnswer
from exam_answers.serializers import (
    ExamAnswerSerializer,
    ExamAnswerCreateSerializer,
    ExamAnswerListSerializer,
    ExamAnswerSubmitSerializer,
    ExamAnswerResultSerializer
)
from exam_answers.service import ExamAnswerService
from exam_answers.filters import ExamAnswerFilter
from question.models import Alternative
from student.models import Student
from student.services import StudentService


class ExamAnswerViewSet(viewsets.ModelViewSet):
    queryset = ExamAnswer.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ExamAnswerFilter
    ordering_fields = ['id', 'created_at', 'updated_at', 'is_correct']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ExamAnswerListSerializer
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
                                                                 
        raise MethodNotAllowed(
            method='POST',
            detail='Não é permitido responder questão por questão. Use POST /api/v1/exam-answers/submit/ e envie o exame completo.'
        )

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed(
            method='PUT',
            detail='Não é permitido editar respostas individualmente. Use o endpoint de resultado para consulta.'
        )

    def partial_update(self, request, *args, **kwargs):
        raise MethodNotAllowed(
            method='PATCH',
            detail='Não é permitido editar respostas individualmente. Use o endpoint de resultado para consulta.'
        )

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed(
            method='DELETE',
            detail='Não é permitido deletar respostas individualmente.'
        )

    @action(detail=False, methods=['get'], url_path='by-exam')
    def by_exam(self, request):
        exam_id = request.query_params.get('exam_id', None)
        
        if not exam_id:
            raise DRFValidationError({'detail': 'Parâmetro exam_id é obrigatório.'})
        
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
            raise DRFValidationError({'detail': 'Parâmetro student_id é obrigatório.'})
        
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

    @action(detail=False, methods=['post'], url_path='submit')
    def submit(self, request):
        serializer = ExamAnswerSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        exam_id = serializer.validated_data['exam_id']
        mapped_answers = serializer.validated_data['mapped_answers']

        exam = Exam.objects.get(id=exam_id)
        student, created = StudentService.get_or_create_student_by_email(email)

                                                                  
        if ExamAnswer.objects.filter(student=student, exam_question__exam=exam).exists():
            raise DRFValidationError({
                'detail': 'Este estudante já possui respostas registradas para este exame. A prova deve ser enviada completa em uma única tentativa.',
                'email': email,
                'exam_id': exam.id,
                'exam_name': exam.name,
            })

        try:
            exam_answers = ExamAnswerService.submit_exam_answers(
                student=student,
                exam=exam,
                answers=mapped_answers
            )

            total_questions = len(exam_answers)
            correct_answers = sum(1 for ans in exam_answers if ans.is_correct)
            incorrect_answers = total_questions - correct_answers
            score_percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0

                                                                                     
            question_ids = [ans.exam_question.question_id for ans in exam_answers]
            correct_alts = Alternative.objects.filter(
                question_id__in=question_ids,
                is_correct=True
            )
            correct_map = {alt.question_id: alt for alt in correct_alts}
            response_serializer = ExamAnswerResultSerializer(
                exam_answers,
                many=True,
                context={'correct_alternatives_by_question_id': correct_map}
            )

            return Response({
                'message': 'Exame submetido com sucesso!',
                'exam_id': exam.id,
                'exam_name': exam.name,
                'student_email': student.email,
                'student_created': created,
                'total_questions': total_questions,
                'correct_answers': correct_answers,
                'incorrect_answers': incorrect_answers,
                'score_percentage': round(score_percentage, 2),
                'answers': response_serializer.data
            }, status=status.HTTP_201_CREATED)

        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, 'message_dict') else {'detail': str(e)})

    @action(detail=False, methods=['get'], url_path='result')
    def result(self, request):
        exam_id = request.query_params.get('exam_id')
        email = request.query_params.get('email')

        if not exam_id:
            raise DRFValidationError({'detail': 'Parâmetro exam_id é obrigatório.'})
        if not email:
            raise DRFValidationError({'detail': 'Parâmetro email é obrigatório.'})

        try:
            exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            raise NotFound({'detail': 'Exame não encontrado.'})

        student, _created = StudentService.get_or_create_student_by_email(email)

        total_questions = exam.examquestion_set.count()
        answers_qs = ExamAnswer.objects.select_related(
            'exam_question__question',
            'selected_alternative'
        ).filter(
            student=student,
            exam_question__exam=exam
        ).order_by('exam_question__number')

        answered_questions = answers_qs.count()
        if answered_questions != total_questions or total_questions == 0:
            raise DRFValidationError({
                'detail': 'Resultado indisponível: a prova só existe quando todas as questões foram respondidas em uma única submissão.',
                'exam_id': exam.id,
                'exam_name': exam.name,
                'student_email': student.email,
                'total_questions': total_questions,
                'answered_questions': answered_questions,
            })

        correct_answers = answers_qs.filter(is_correct=True).count()
        incorrect_answers = total_questions - correct_answers
        score_percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0

                                           
        question_ids = list(exam.examquestion_set.values_list('question_id', flat=True))
        correct_alts = Alternative.objects.filter(question_id__in=question_ids, is_correct=True)
        correct_map = {alt.question_id: alt for alt in correct_alts}

        serializer = ExamAnswerResultSerializer(
            list(answers_qs),
            many=True,
            context={'correct_alternatives_by_question_id': correct_map}
        )

        return Response({
            'exam_id': exam.id,
            'exam_name': exam.name,
            'student_email': student.email,
            'total_questions': total_questions,
            'correct_answers': correct_answers,
            'incorrect_answers': incorrect_answers,
            'score_percentage': round(score_percentage, 2),
            'answers': serializer.data,
        })
