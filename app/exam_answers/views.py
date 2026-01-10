from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError as DRFValidationError, NotFound, MethodNotAllowed

from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from exam.models import Exam
from exam_answers.models import ExamAnswer
from exam_answers.serializers import (
    ExamAnswerSerializer,
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
    lookup_value_regex = r"\d+"
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
        
        def parse_int_param(name, value):
            if value is None or value == '':
                return None
            try:
                return int(value)
            except (TypeError, ValueError):
                raise DRFValidationError({'detail': f'Parâmetro {name} inválido.'})

        exam_id = parse_int_param('exam_id', self.request.query_params.get('exam_id', None))
        student_id = parse_int_param('student_id', self.request.query_params.get('student_id', None))
        exam_question_id = parse_int_param('exam_question_id', self.request.query_params.get('exam_question_id', None))
        
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
            exam_id = int(exam_id)
        except (TypeError, ValueError):
            raise DRFValidationError({'detail': 'Parâmetro exam_id inválido.'})
        
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
            student_id = int(student_id)
        except (TypeError, ValueError):
            raise DRFValidationError({'detail': 'Parâmetro student_id inválido.'})
        
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

        try:
            exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            raise NotFound({'detail': 'Exame não encontrado.'})

        total_questions = exam.examquestion_set.count()
        if total_questions == 0:
            return Response(
                {'detail': 'Este exame não possui questões.'},
                status=status.HTTP_409_CONFLICT
            )

        student, created = StudentService.get_or_create_student_by_email(email)

                                                                  
        if ExamAnswer.objects.filter(student=student, exam_question__exam=exam).exists():
            return Response(
                {
                    'detail': 'Este estudante já possui respostas registradas para este exame. A prova deve ser enviada completa em uma única tentativa.',
                    'email': email,
                    'exam_id': exam.id,
                    'exam_name': exam.name,
                },
                status=status.HTTP_409_CONFLICT
            )

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
            counts = Alternative.objects.filter(
                question_id__in=question_ids,
                is_correct=True
            ).values('question_id').annotate(cnt=Count('id'))
            counts_map = {row['question_id']: row['cnt'] for row in counts}
            invalid_list = [
                {'question_id': qid, 'correct_count': counts_map.get(qid, 0)}
                for qid in question_ids
                if counts_map.get(qid, 0) != 1
            ]
            if invalid_list:
                return Response(
                    {
                        'detail': 'Prova inválida: existe questão sem gabarito correto (ou com mais de um).',
                        'invalid_questions': invalid_list,
                    },
                    status=status.HTTP_409_CONFLICT
                )
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
            return Response(
                e.message_dict if hasattr(e, 'message_dict') else {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'], url_path='result')
    def result(self, request):
        exam_id = request.query_params.get('exam_id')
        email = request.query_params.get('email')

        if not exam_id:
            raise DRFValidationError({'detail': 'Parâmetro exam_id é obrigatório.'})
        if not email:
            raise DRFValidationError({'detail': 'Parâmetro email é obrigatório.'})

        try:
            exam_id_int = int(exam_id)
        except (TypeError, ValueError):
            raise DRFValidationError({'detail': 'exam_id inválido.'})

        email_normalized = str(email).strip().lower()
        try:
            EmailValidator()(email_normalized)
        except DjangoValidationError:
            raise DRFValidationError({'detail': 'Email inválido.'})

        try:
            exam = Exam.objects.get(id=exam_id_int)
        except Exam.DoesNotExist:
            raise NotFound({'detail': 'Exame não encontrado.'})

        student = Student.objects.filter(email=email_normalized).first()
        if not student:
            raise NotFound({'detail': 'Nenhum resultado encontrado para este email e exame.'})

        total_questions = exam.examquestion_set.count()
        if total_questions == 0:
            return Response(
                {'detail': 'Este exame não possui questões.'},
                status=status.HTTP_409_CONFLICT
            )
        answers_qs = ExamAnswer.objects.select_related(
            'exam_question__question',
            'selected_alternative'
        ).filter(
            student=student,
            exam_question__exam=exam
        ).order_by('exam_question__number')

        answered_questions = answers_qs.count()
        if answered_questions == 0:
            raise NotFound({'detail': 'Nenhum resultado encontrado para este email e exame.'})
        if answered_questions != total_questions:
            return Response(
                {
                    'detail': 'Resultado indisponível: a prova precisa estar completa.',
                    'exam_id': exam.id,
                    'exam_name': exam.name,
                    'student_email': student.email,
                    'total_questions': total_questions,
                    'answered_questions': answered_questions,
                },
                status=status.HTTP_409_CONFLICT
            )

        correct_answers = answers_qs.filter(is_correct=True).count()
        incorrect_answers = total_questions - correct_answers
        score_percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0

                                           
        question_ids = list(exam.examquestion_set.values_list('question_id', flat=True))
        counts = Alternative.objects.filter(
            question_id__in=question_ids,
            is_correct=True
        ).values('question_id').annotate(cnt=Count('id'))
        counts_map = {row['question_id']: row['cnt'] for row in counts}
        invalid_list = [
            {'question_id': qid, 'correct_count': counts_map.get(qid, 0)}
            for qid in question_ids
            if counts_map.get(qid, 0) != 1
        ]
        if invalid_list:
            return Response(
                {
                    'detail': 'Prova inválida: existe questão sem gabarito correto (ou com mais de um).',
                    'invalid_questions': invalid_list,
                },
                status=status.HTTP_409_CONFLICT
            )
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
