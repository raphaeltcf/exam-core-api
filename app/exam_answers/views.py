from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError as DRFValidationError, NotFound, MethodNotAllowed

from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiExample,
    OpenApiParameter,
    PolymorphicProxySerializer,
)
from drf_spectacular.types import OpenApiTypes

from exam.models import Exam
from exam_answers.models import ExamAnswer
from exam_answers.serializers import (
    ExamAnswerSerializer,
    ExamAnswerListSerializer,
    ExamAnswerSubmitSerializer,
    ExamAnswerResultSerializer,
    StudentExamSummarySerializer,
)
from exam_answers.service import ExamAnswerService
from exam_answers.filters import ExamAnswerFilter
from question.models import Alternative
from student.models import Student
from student.services import StudentService


@extend_schema_view(
    list=extend_schema(
        summary='Listar respostas',
        description='Lista todas as respostas de provas com paginação e filtros.',
        parameters=[
            OpenApiParameter(
                name='exam_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filtrar por ID da prova'
            ),
            OpenApiParameter(
                name='student_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filtrar por ID do estudante'
            ),
            OpenApiParameter(
                name='exam_question_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filtrar por ID da questão do exame'
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Ordenação: id, created_at, updated_at, is_correct (use - para decrescente)'
            ),
        ],
        tags=['Respostas'],
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
                            "student": {
                                "id": 1,
                                "email": "joao.silva@email.com",
                                "name": "João Silva"
                            },
                            "exam_question": {
                                "id": 1,
                                "exam": {"id": 1, "name": "Prova de Geografia"},
                                "question": {"id": 1, "content": "Qual é a capital do Brasil?"},
                                "number": 1
                            },
                            "selected_alternative": {
                                "id": 2,
                                "content": "Brasília",
                                "option": 2,
                                "option_display": "B"
                            },
                            "is_correct": True,
                            "created_at": "2024-01-20T10:30:00Z",
                            "updated_at": "2024-01-20T10:30:00Z"
                        }
                    ]
                },
                response_only=True,
            ),
        ]
    ),
    retrieve=extend_schema(
        summary='Detalhes da resposta',
        description='Retorna os detalhes completos de uma resposta específica.',
        tags=['Respostas'],
    ),
    create=extend_schema(
        summary='Criar resposta (BLOQUEADO)',
        description='Este endpoint está bloqueado. Use POST /api/v1/exam-answers/submit/ para enviar a prova completa.',
        tags=['Respostas'],
    ),
    update=extend_schema(
        summary='Atualizar resposta (BLOQUEADO)',
        description='Este endpoint está bloqueado. Não é permitido editar respostas após submissão.',
        tags=['Respostas'],
    ),
    partial_update=extend_schema(
        summary='Atualizar parcialmente resposta (BLOQUEADO)',
        description='Este endpoint está bloqueado. Não é permitido editar respostas após submissão.',
        tags=['Respostas'],
    ),
    destroy=extend_schema(
        summary='Deletar resposta (BLOQUEADO)',
        description='Este endpoint está bloqueado. Não é permitido deletar respostas.',
        tags=['Respostas'],
    ),
)
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

    @staticmethod
    def _normalize_email_or_400(email: str) -> str:
        email_normalized = str(email).strip().lower()
        try:
            EmailValidator()(email_normalized)
        except DjangoValidationError:
            raise DRFValidationError({'detail': 'Email inválido.'})
        return email_normalized

    @staticmethod
    def _parse_int_or_400(param_name: str, raw_value):
        try:
            return int(raw_value)
        except (TypeError, ValueError):
            raise DRFValidationError({'detail': f'{param_name} inválido.'})

    def _build_exam_summary(self, student: Student, exam: Exam):
        """
        Constrói o resumo do exame para o estudante, incluindo estatísticas e respostas detalhadas.
        """
        total_questions = exam.examquestion_set.count()
        if total_questions == 0:
            return None

        answers_qs = ExamAnswer.objects.select_related(
            'exam_question__question',
            'selected_alternative'
        ).filter(
            student=student,
            exam_question__exam=exam
        ).order_by('exam_question__number')

        answered_questions = answers_qs.count()
        if answered_questions == 0:
            return None
        if answered_questions != total_questions:
            # Consideramos "fez o exame" apenas quando está completo
            return None

        correct_answers = answers_qs.filter(is_correct=True).count()
        incorrect_answers = total_questions - correct_answers
        score_percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0

        completed_at = answers_qs.order_by('-created_at').first().created_at

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
            # Mantém a mesma regra do /result/: prova inválida
            raise DRFValidationError(
                {
                    'detail': 'Prova inválida: existe questão sem gabarito correto (ou com mais de um).',
                    'invalid_questions': invalid_list,
                }
            )

        correct_alts = Alternative.objects.filter(question_id__in=question_ids, is_correct=True)
        correct_map = {alt.question_id: alt for alt in correct_alts}

        serializer = ExamAnswerResultSerializer(
            list(answers_qs),
            many=True,
            context={'correct_alternatives_by_question_id': correct_map}
        )

        return {
            'exam_id': exam.id,
            'exam_name': exam.name,
            'total_questions': total_questions,
            'correct_answers': correct_answers,
            'incorrect_answers': incorrect_answers,
            'score_percentage': round(score_percentage, 2),
            'completed_at': completed_at,
            'answers': serializer.data,
        }

    def _get_exam_result_response(self, student: Student, exam: Exam):
        """
        Retorna o mesmo formato do endpoint /result/, reaproveitando as regras atuais.
        """
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

    @extend_schema(
        summary='Respostas por prova',
        description='Lista todas as respostas de uma prova específica.',
        tags=['Respostas'],
        parameters=[
            OpenApiParameter(
                name='exam_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID da prova (obrigatório)',
                required=True
            ),
        ],
        examples=[
            OpenApiExample(
                'Respostas da Prova',
                value={
                    "count": 2,
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            "id": 1,
                            "student": {
                                "id": 1,
                                "email": "joao.silva@email.com",
                                "name": "João Silva"
                            },
                            "exam_question": {
                                "id": 1,
                                "exam": {"id": 1, "name": "Prova de Geografia"},
                                "question": {"id": 1, "content": "Qual é a capital do Brasil?"},
                                "number": 1
                            },
                            "selected_alternative": {
                                "id": 2,
                                "content": "Brasília"
                            },
                            "is_correct": True,
                            "created_at": "2024-01-20T10:30:00Z"
                        }
                    ]
                },
                response_only=True,
            ),
        ]
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

    @extend_schema(
        summary='Exames por estudante',
        description="""
        Retorna os exames realizados por um estudante, agrupados por prova, com a porcentagem em cada exame.

        ## Parâmetros:
        - **email**: Email do estudante (obrigatório)
        - **exam_id**: ID do exame (opcional). Quando enviado, retorna o exame específico (formato detalhado).
        """,
        tags=['Respostas'],
        parameters=[
            OpenApiParameter(
                name='email',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Email do estudante (obrigatório)',
                required=True
            ),
            OpenApiParameter(
                name='exam_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID do exame (opcional)',
                required=False
            ),
        ],
        responses={
            200: PolymorphicProxySerializer(
                component_name='ExamAnswersByStudentResponse',
                serializers=[
                    StudentExamSummarySerializer,
                    StudentExamSummarySerializer(many=True),
                ],
                resource_type_field_name=None,
            ),
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
            409: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Lista de Exames do Estudante',
                value=[
                    {
                        "exam_id": 1,
                        "exam_name": "Prova de Geografia",
                        "total_questions": 3,
                        "correct_answers": 2,
                        "incorrect_answers": 1,
                        "score_percentage": 66.67,
                        "completed_at": "2024-01-20T10:30:00Z",
                        "answers": [
                            {
                                "id": 1,
                                "question_number": 1,
                                "question_content": "Qual é a capital do Brasil?",
                                "selected_alternative": {"id": 2, "content": "Brasília", "option": 2, "option_display": "B"},
                                "correct_alternative": {"id": 2, "content": "Brasília", "option": 2, "option_display": "B"},
                                "is_correct": True,
                                "created_at": "2024-01-20T10:30:00Z"
                            }
                        ]
                    }
                ],
                response_only=True,
            ),
            OpenApiExample(
                'Exame Específico do Estudante (com exam_id)',
                value={
                    "exam_id": 1,
                    "exam_name": "Prova de Geografia",
                    "student_email": "joao.silva@email.com",
                    "total_questions": 3,
                    "correct_answers": 2,
                    "incorrect_answers": 1,
                    "score_percentage": 66.67,
                    "answers": []
                },
                response_only=True,
            ),
        ]
    )
    @action(detail=False, methods=['get'], url_path='by-student')
    def by_student(self, request):
        email = request.query_params.get('email', None)
        exam_id = request.query_params.get('exam_id', None)

        if not email:
            raise DRFValidationError({'detail': 'Parâmetro email é obrigatório.'})

        email_normalized = self._normalize_email_or_400(email)

        student = Student.objects.filter(email=email_normalized).first()
        if not student:
            raise NotFound({'detail': 'Estudante não encontrado com este email.'})

        # Se exam_id foi fornecido, retorna apenas aquele exame (formato detalhado igual ao /result/)
        if exam_id is not None and str(exam_id).strip() != '':
            exam_id_int = self._parse_int_or_400('exam_id', exam_id)
            try:
                exam = Exam.objects.get(id=exam_id_int)
            except Exam.DoesNotExist:
                raise NotFound({'detail': 'Exame não encontrado.'})

            # Se não tiver nenhuma resposta, consideramos que não fez esse exame
            has_any = ExamAnswer.objects.filter(student=student, exam_question__exam=exam).exists()
            if not has_any:
                raise NotFound({'detail': 'Exame não encontrado para este estudante.'})

            return self._get_exam_result_response(student, exam)

        # Caso contrário: retorna todos os exames concluídos
        exam_ids = ExamAnswer.objects.filter(
            student=student
        ).values_list('exam_question__exam_id', flat=True).distinct()

        if not exam_ids:
            return Response([])

        exams = Exam.objects.filter(id__in=exam_ids)
        results = []
        for exam in exams:
            summary = self._build_exam_summary(student, exam)
            if summary is not None:
                results.append(summary)

        results.sort(
            key=lambda x: (x.get('completed_at') is not None, x.get('completed_at')),
            reverse=True
        )
        return Response(results)

    @extend_schema(
        summary='Submeter prova completa',
        description="""
        **Endpoint principal para submissão de provas.**
        
        O estudante deve enviar a prova completa em uma única requisição. 
        
        ## Regras:
        - Cada estudante pode enviar a prova apenas uma vez
        - Todas as questões devem ser respondidas
        - O sistema cria automaticamente o estudante se o email não existir
        - Retorna imediatamente o resultado com gabarito
        
        ## Formato das Respostas:
        O campo `answers` deve ser um objeto onde:
        - **Chave**: número da questão (number do ExamQuestion)
        - **Valor**: ID da alternativa selecionada
        
        Exemplo: `{"1": "B", "2": "C", "3": "D", "4": "E", "5": "A"}` significa:
        - Questão 1: alternativa ID 5
        - Questão 2: alternativa ID 8
        - Questão 3: alternativa ID 12
        """,
        tags=['Respostas'],
        request=ExamAnswerSubmitSerializer,
        examples=[
            OpenApiExample(
                'Submissão de Prova',
                value={
                    "email": "joao.silva@email.com",
                    "exam_id": 1,
                    "answers": {
                        "1": "B",
                        "2": "C",
                        "3": "D",
                        "4": "E",
                        "5": "A"
                    }
                },
                request_only=True,
            ),
            OpenApiExample(
                'Submissão com Email Novo',
                value={
                    "email": "maria.nova@email.com",
                    "exam_id": 1,
                    "answers": {
                        "1": "A",
                        "2": "B",
                        "3": "C"
                    }
                },
                request_only=True,
            ),
            OpenApiExample(
                'Resultado da Submissão',
                value={
                    "message": "Exame submetido com sucesso!",
                    "exam_id": 1,
                    "exam_name": "Prova de Geografia",
                    "student_email": "joao.silva@email.com",
                    "student_created": False,
                    "total_questions": 3,
                    "correct_answers": 2,
                    "incorrect_answers": 1,
                    "score_percentage": 66.67,
                    "answers": [
                        {
                            "id": 1,
                            "question_number": 1,
                            "question_content": "Qual é a capital do Brasil?",
                            "selected_alternative": {
                                "id": 2,
                                "content": "Brasília",
                                "option": 2,
                                "option_display": "B"
                            },
                            "correct_alternative": {
                                "id": 2,
                                "content": "Brasília",
                                "option": 2,
                                "option_display": "B"
                            },
                            "is_correct": True
                        },
                        {
                            "id": 2,
                            "question_number": 2,
                            "question_content": "Qual é o maior oceano?",
                            "selected_alternative": {
                                "id": 6,
                                "content": "Atlântico",
                                "option": 1,
                                "option_display": "A"
                            },
                            "correct_alternative": {
                                "id": 7,
                                "content": "Pacífico",
                                "option": 2,
                                "option_display": "B"
                            },
                            "is_correct": False
                        },
                        {
                            "id": 3,
                            "question_number": 3,
                            "question_content": "Quantos continentes existem?",
                            "selected_alternative": {
                                "id": 11,
                                "content": "7",
                                "option": 2,
                                "option_display": "B"
                            },
                            "correct_alternative": {
                                "id": 11,
                                "content": "7",
                                "option": 2,
                                "option_display": "B"
                            },
                            "is_correct": True
                        }
                    ]
                },
                response_only=True,
            ),
            OpenApiExample(
                'Erro: Prova Já Respondida',
                value={
                    "detail": "Este estudante já possui respostas registradas para este exame. A prova deve ser enviada completa em uma única tentativa.",
                    "email": "joao.silva@email.com",
                    "exam_id": 1,
                    "exam_name": "Prova de Geografia"
                },
                status_codes=['409'],
                response_only=True,
            ),
        ]
    )
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

    @extend_schema(
        summary='Consultar resultado da prova',
        description="""
        Consulta o resultado completo de uma prova já submetida.
        
        ## Parâmetros:
        - **exam_id**: ID da prova (obrigatório)
        - **email**: Email do estudante (obrigatório)
        
        Retorna o gabarito completo com todas as respostas, alternativas corretas e estatísticas.
        """,
        tags=['Respostas'],
        parameters=[
            OpenApiParameter(
                name='exam_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID da prova (obrigatório)',
                required=True
            ),
            OpenApiParameter(
                name='email',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Email do estudante (obrigatório)',
                required=True
            ),
        ],
        examples=[
            OpenApiExample(
                'Resultado Completo',
                value={
                    "exam_id": 1,
                    "exam_name": "Prova de Geografia",
                    "student_email": "joao.silva@email.com",
                    "total_questions": 3,
                    "correct_answers": 2,
                    "incorrect_answers": 1,
                    "score_percentage": 66.67,
                    "answers": [
                        {
                            "id": 1,
                            "question_number": 1,
                            "question_content": "Qual é a capital do Brasil?",
                            "selected_alternative": {
                                "id": 2,
                                "content": "Brasília",
                                "option": 2,
                                "option_display": "B"
                            },
                            "correct_alternative": {
                                "id": 2,
                                "content": "Brasília",
                                "option": 2,
                                "option_display": "B"
                            },
                            "is_correct": True
                        },
                        {
                            "id": 2,
                            "question_number": 2,
                            "question_content": "Qual é o maior oceano?",
                            "selected_alternative": {
                                "id": 6,
                                "content": "Atlântico",
                                "option": 1,
                                "option_display": "A"
                            },
                            "correct_alternative": {
                                "id": 7,
                                "content": "Pacífico",
                                "option": 2,
                                "option_display": "B"
                            },
                            "is_correct": False
                        },
                        {
                            "id": 3,
                            "question_number": 3,
                            "question_content": "Quantos continentes existem?",
                            "selected_alternative": {
                                "id": 11,
                                "content": "7",
                                "option": 2,
                                "option_display": "B"
                            },
                            "correct_alternative": {
                                "id": 11,
                                "content": "7",
                                "option": 2,
                                "option_display": "B"
                            },
                            "is_correct": True
                        }
                    ]
                },
                response_only=True,
            ),
            OpenApiExample(
                'Erro: Resultado Não Encontrado',
                value={
                    "detail": "Nenhum resultado encontrado para este email e exame."
                },
                status_codes=['404'],
                response_only=True,
            ),
        ]
    )
    @action(detail=False, methods=['get'], url_path='result')
    def result(self, request):
        exam_id = request.query_params.get('exam_id')
        email = request.query_params.get('email')

        if not exam_id:
            raise DRFValidationError({'detail': 'Parâmetro exam_id é obrigatório.'})
        if not email:
            raise DRFValidationError({'detail': 'Parâmetro email é obrigatório.'})

        exam_id_int = self._parse_int_or_400('exam_id', exam_id)
        email_normalized = self._normalize_email_or_400(email)

        try:
            exam = Exam.objects.get(id=exam_id_int)
        except Exam.DoesNotExist:
            raise NotFound({'detail': 'Exame não encontrado.'})

        student = Student.objects.filter(email=email_normalized).first()
        if not student:
            raise NotFound({'detail': 'Nenhum resultado encontrado para este email e exame.'})

        return self._get_exam_result_response(student, exam)
