from rest_framework import serializers

from exam.models import ExamQuestion
from exam_answers.models import ExamAnswer
from question.models import Alternative
from student.models import Student
from student.serializers import StudentSerializer


class ExamAnswerListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de respostas."""
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
    """Serializer completo para ExamAnswer (usado para retrieve, update, partial_update)."""
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
        """Retorna informações do ExamQuestion."""
        return {
            'id': obj.exam_question.id,
            'exam_id': obj.exam_question.exam.id,
            'exam_name': obj.exam_question.exam.name,
            'question_id': obj.exam_question.question.id,
            'question_content': obj.exam_question.question.content[:100],
            'number': obj.exam_question.number
        }

    def get_selected_alternative(self, obj):
        """Retorna informações da alternativa selecionada."""
        return {
            'id': obj.selected_alternative.id,
            'content': obj.selected_alternative.content,
            'option': obj.selected_alternative.option,
            'option_display': obj.selected_alternative.get_option_display(),
            'is_correct': obj.selected_alternative.is_correct
        }

    def validate_selected_alternative_id(self, value):
        """Valida que a alternativa pertence à questão do exame."""
        if self.instance and value:
            exam_question = self.instance.exam_question
            if value.question != exam_question.question:
                raise serializers.ValidationError(
                    'A alternativa selecionada não pertence à questão deste exame.'
                )
        return value


class ExamAnswerCreateSerializer(serializers.ModelSerializer):
    """Serializer para criar respostas de exame."""
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(),
        source='student',
        write_only=True,
        required=True,
        help_text="ID do estudante."
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
            'student_id', 'exam_question_id', 'selected_alternative_id'
        ]

    def validate(self, attrs):
        """Valida que a alternativa pertence à questão do exame."""
        exam_question = attrs.get('exam_question')
        selected_alternative = attrs.get('selected_alternative')

        if selected_alternative.question != exam_question.question:
            raise serializers.ValidationError({
                'selected_alternative_id': 'A alternativa selecionada não pertence à questão deste exame.'
            })

        return attrs

    def create(self, validated_data):
        """Cria uma nova resposta usando o service."""
        from exam_answers.service import ExamAnswerService
        from django.core.exceptions import ValidationError as DjangoValidationError
        
        student = validated_data.get('student')
        exam_question = validated_data.get('exam_question')
        selected_alternative = validated_data.get('selected_alternative')

        if not student:
            raise serializers.ValidationError({'student_id': 'ID do estudante é obrigatório.'})

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
