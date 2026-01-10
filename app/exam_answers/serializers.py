from rest_framework import serializers
from rest_framework.exceptions import NotFound

from exam.models import ExamQuestion
from exam.models import Exam
from exam_answers.models import ExamAnswer
from question.models import Alternative
from student.models import Student
from student.serializers import StudentSerializer
from question.utils import AlternativesChoices


class ExamAnswerListSerializer(serializers.ModelSerializer):
    student_email = serializers.EmailField(source='student.email', read_only=True)
    student_name = serializers.CharField(source='student.name', read_only=True)
    exam_name = serializers.CharField(source='exam_question.exam.name', read_only=True)
    question_number = serializers.IntegerField(source='exam_question.number', read_only=True)
    question_content = serializers.CharField(source='exam_question.question.content', read_only=True)

    class Meta:
        model = ExamAnswer
        fields = [
            'id', 'student_email', 'student_name', 'exam_name',
            'question_number', 'question_content', 'is_correct',
            'created_at', 'updated_at'
        ]


class ExamAnswerSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)
    exam_question = serializers.SerializerMethodField()
    selected_alternative = serializers.SerializerMethodField()
    selected_alternative_id = serializers.PrimaryKeyRelatedField(
        queryset=Alternative.objects.all(),
        source='selected_alternative',
        write_only=True,
        required=False
    )
    exam_name = serializers.CharField(source='exam_question.exam.name', read_only=True)
    question_number = serializers.IntegerField(source='exam_question.number', read_only=True)

    class Meta:
        model = ExamAnswer
        fields = [
            'id', 'student', 'exam_question',
            'selected_alternative', 'selected_alternative_id',
            'is_correct', 'exam_name', 'question_number',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'student', 'exam_question', 'is_correct', 'created_at', 'updated_at']

    def get_exam_question(self, obj):
        return {
            'id': obj.exam_question.id,
            'exam_id': obj.exam_question.exam.id,
            'exam_name': obj.exam_question.exam.name,
            'question_id': obj.exam_question.question.id,
            'question_content': obj.exam_question.question.content[:100],
            'number': obj.exam_question.number
        }

    def get_selected_alternative(self, obj):
        return {
            'id': obj.selected_alternative.id,
            'content': obj.selected_alternative.content,
            'option': obj.selected_alternative.option,
            'option_display': obj.selected_alternative.get_option_display(),
            'is_correct': obj.selected_alternative.is_correct
        }

    def validate_selected_alternative_id(self, value):
        if self.instance and value:
            exam_question = self.instance.exam_question
            if value.question != exam_question.question:
                raise serializers.ValidationError(
                    'A alternativa selecionada não pertence à questão deste exame.'
                )
        return value


class ExamAnswerResultSerializer(serializers.ModelSerializer):
    question_number = serializers.IntegerField(source='exam_question.number', read_only=True)
    question_content = serializers.CharField(source='exam_question.question.content', read_only=True)
    selected_alternative = serializers.SerializerMethodField()
    correct_alternative = serializers.SerializerMethodField()

    class Meta:
        model = ExamAnswer
        fields = [
            'id',
            'question_number',
            'question_content',
            'selected_alternative',
            'correct_alternative',
            'is_correct',
            'created_at',
        ]
        read_only_fields = fields

    def get_selected_alternative(self, obj):
        return {
            'id': obj.selected_alternative.id,
            'content': obj.selected_alternative.content,
            'option': obj.selected_alternative.option,
            'option_display': obj.selected_alternative.get_option_display(),
        }

    def get_correct_alternative(self, obj):
        correct_map = self.context.get('correct_alternatives_by_question_id', {})
        alt = correct_map.get(obj.exam_question.question_id)
        if not alt:
            return None
        return {
            'id': alt.id,
            'content': alt.content,
            'option': alt.option,
            'option_display': alt.get_option_display(),
        }


class ExamAnswerCreateSerializer(serializers.ModelSerializer):
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(),
        source='student',
        write_only=True,
        required=False,
        help_text="ID do estudante."
    )
    email = serializers.EmailField(
        write_only=True,
        required=False,
        help_text="Email do estudante (alternativa ao student_id). Se não existir, será criado automaticamente."
    )
    exam_question_id = serializers.PrimaryKeyRelatedField(
        queryset=ExamQuestion.objects.all(),
        source='exam_question',
        write_only=True
    )
    selected_alternative_id = serializers.PrimaryKeyRelatedField(
        queryset=Alternative.objects.all(),
        source='selected_alternative',
        write_only=True
    )

    class Meta:
        model = ExamAnswer
        fields = [
            'student_id', 'email', 'exam_question_id', 'selected_alternative_id'
        ]

    def validate(self, attrs):
        student = attrs.get('student')
        email = attrs.get('email')

        if not student and not email:
            raise serializers.ValidationError({
                'student': 'Informe student_id ou email.'
            })
        if student and email:
            raise serializers.ValidationError({
                'student': 'Informe apenas um: student_id OU email.'
            })

        exam_question = attrs.get('exam_question')
        selected_alternative = attrs.get('selected_alternative')

        if selected_alternative.question != exam_question.question:
            raise serializers.ValidationError({
                'selected_alternative_id': 'A alternativa selecionada não pertence à questão deste exame.'
            })

        return attrs

    def create(self, validated_data):
        from exam_answers.service import ExamAnswerService
        from django.core.exceptions import ValidationError as DjangoValidationError
        from student.services import StudentService
        
        student = validated_data.get('student')
        email = validated_data.get('email')
        exam_question = validated_data.get('exam_question')
        selected_alternative = validated_data.get('selected_alternative')

        if not student:
            student, _created = StudentService.get_or_create_student_by_email(email)

        try:
            exam_answer = ExamAnswerService.create_answer(
                student=student,
                exam_question=exam_question,
                selected_alternative=selected_alternative
            )
            return exam_answer
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict if hasattr(e, 'message_dict') else {'detail': str(e)})
        except Exception as e:
            raise serializers.ValidationError({'detail': str(e)})


class ExamAnswerSubmitSerializer(serializers.Serializer):

    email = serializers.EmailField(required=True)
    exam_id = serializers.IntegerField(required=True)
    answers = serializers.DictField(
        child=serializers.JSONField(),
        required=True
    )

    def validate_exam_id(self, value):
        if value is None or int(value) < 1:
            raise serializers.ValidationError('exam_id inválido.')
        if not Exam.objects.filter(id=value).exists():
            raise NotFound('Exame não encontrado.')
        return value

    @staticmethod
    def _parse_number_key(key) -> int:
        try:
            n = int(key)
        except (TypeError, ValueError):
            raise serializers.ValidationError('Chaves de answers devem ser números (ex.: "1", "2", ...).')
        if n < 1:
            raise serializers.ValidationError('Número de questão inválido (deve ser >= 1).')
        return n

    @staticmethod
    def _parse_option_value(value) -> int:
                                                    
        if isinstance(value, str):
            v = value.strip().upper()
            letter_to_int = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5}
            if v in letter_to_int:
                return letter_to_int[v]
                                                    
            try:
                value = int(v)
            except (TypeError, ValueError):
                raise serializers.ValidationError('Opção inválida. Use "A".."E" ou 1..5.')

        try:
            opt = int(value)
        except (TypeError, ValueError):
            raise serializers.ValidationError('Opção inválida. Use "A".."E" ou 1..5.')

        valid_options = {choice.value for choice in AlternativesChoices}
        if opt not in valid_options:
            raise serializers.ValidationError('Opção inválida. Use "A".."E" ou 1..5.')
        return opt

    def validate_answers(self, value):
        if not isinstance(value, dict) or not value:
            raise serializers.ValidationError('answers deve ser um objeto não-vazio.')

        normalized = {}
        for raw_key, raw_value in value.items():
            number = self._parse_number_key(raw_key)
            if number in normalized:
                raise serializers.ValidationError('Não é permitido repetir o número da questão.')
            normalized[number] = self._parse_option_value(raw_value)

        return normalized

    def validate(self, attrs):
        exam_id = attrs['exam_id']
        answers = attrs['answers']                                                  

        exam_questions = list(
            ExamQuestion.objects.filter(exam_id=exam_id).select_related('question')
        )
        if not exam_questions:
            raise serializers.ValidationError({'exam_id': 'Este exame não possui questões.'})

        valid_numbers = {eq.number for eq in exam_questions}
        provided_numbers = set(answers.keys())

        if provided_numbers != valid_numbers:
            missing = sorted(valid_numbers - provided_numbers)
            extra = sorted(provided_numbers - valid_numbers)
            errors = {}
            if missing:
                errors['missing_numbers'] = missing
            if extra:
                errors['extra_numbers'] = extra
            errors['detail'] = 'É necessário responder todas as questões do exame, exatamente uma vez.'
            raise serializers.ValidationError(errors)

                                                         
        question_ids = [eq.question_id for eq in exam_questions]
        option_set = set(answers.values())
        alternatives = Alternative.objects.filter(
            question_id__in=question_ids,
            option__in=option_set
        ).select_related('question')
        alt_map = {(alt.question_id, alt.option): alt for alt in alternatives}

                                                                                        
        exam_question_by_number = {eq.number: eq for eq in exam_questions}
        mapped_answers = []
        for number, option in sorted(answers.items()):
            eq = exam_question_by_number[number]
            alt = alt_map.get((eq.question_id, option))
            if not alt:
                raise serializers.ValidationError({
                    'answers': f'Não existe alternativa "{AlternativesChoices(option).label}" para a questão {number}.'
                })
            mapped_answers.append({
                'exam_question_id': eq.id,
                'selected_alternative_id': alt.id,
            })

        attrs['mapped_answers'] = mapped_answers
        return attrs
