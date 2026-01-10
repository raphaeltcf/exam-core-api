from rest_framework import serializers

from exam.models import Exam, ExamQuestion
from question.models import Question
from question.serializers import QuestionSerializer, QuestionListSerializer


class ExamQuestionSerializer(serializers.ModelSerializer):
    """Serializer para o relacionamento ExamQuestion."""
    question = QuestionSerializer(read_only=True)
    question_id = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.all(),
        source='question',
        write_only=True
    )

    class Meta:
        model = ExamQuestion
        fields = ['id', 'exam', 'question', 'question_id', 'number']
        read_only_fields = ['exam']


class ExamQuestionNestedSerializer(serializers.ModelSerializer):
    """Serializer aninhado para ExamQuestion (usado dentro de Exam)."""
    question = QuestionListSerializer(read_only=True)

    class Meta:
        model = ExamQuestion
        fields = ['id', 'question', 'number']
        read_only_fields = ['exam']


class ExamListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de exames."""
    questions_count = serializers.IntegerField(source='examquestion_set.count', read_only=True)

    class Meta:
        model = Exam
        fields = ['id', 'name', 'questions_count']


class ExamSerializer(serializers.ModelSerializer):
    """Serializer completo para Exam com questions aninhadas."""
    questions = ExamQuestionNestedSerializer(many=True, read_only=True, source='examquestion_set')
    questions_count = serializers.IntegerField(source='examquestion_set.count', read_only=True)

    class Meta:
        model = Exam
        fields = ['id', 'name', 'questions', 'questions_count']


class ExamCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para criar e atualizar exames."""
    question_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="Lista de IDs das questões a serem adicionadas ao exame."
    )

    class Meta:
        model = Exam
        fields = ['id', 'name', 'question_ids']

    def create(self, validated_data):
        """Cria um exame."""
        question_ids = validated_data.pop('question_ids', [])
        exam = Exam.objects.create(**validated_data)
        
        # Adiciona questões se fornecidas
        if question_ids:
            for index, question_id in enumerate(question_ids, start=1):
                question = Question.objects.get(id=question_id)
                ExamQuestion.objects.create(exam=exam, question=question, number=index)
        
        return exam

    def update(self, instance, validated_data):
        """Atualiza um exame."""
        question_ids = validated_data.pop('question_ids', None)
        
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        
        # Se question_ids for fornecido, reordena as questões
        if question_ids is not None:
            # Remove todas as questões existentes
            ExamQuestion.objects.filter(exam=instance).delete()
            # Adiciona questões na nova ordem
            for index, question_id in enumerate(question_ids, start=1):
                question = Question.objects.get(id=question_id)
                ExamQuestion.objects.create(exam=instance, question=question, number=index)
        
        return instance


class AddQuestionToExamSerializer(serializers.Serializer):
    """Serializer para adicionar uma questão a um exame."""
    question_id = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.all(),
        required=True
    )
    number = serializers.IntegerField(required=True, min_value=1)

    def validate_number(self, value):
        """Valida que o número não está em uso."""
        exam = self.context['exam']
        if ExamQuestion.objects.filter(exam=exam, number=value).exists():
            raise serializers.ValidationError(
                f'Já existe uma questão na posição {value} deste exame.'
            )
        return value


class ReorderQuestionsSerializer(serializers.Serializer):
    """Serializer para reordenar questões de um exame."""
    exam_question_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        help_text="Lista de IDs de ExamQuestion na nova ordem desejada."
    )

    def validate_exam_question_ids(self, value):
        """Valida que todos os IDs pertencem ao exame e não há duplicatas."""
        exam = self.context['exam']
        exam_questions = ExamQuestion.objects.filter(exam=exam)
        exam_question_ids = set(exam_questions.values_list('id', flat=True))
        provided_ids = set(value)

        if provided_ids != exam_question_ids:
            raise serializers.ValidationError(
                'A ordem fornecida não corresponde às questões do exame.'
            )

        if len(value) != len(set(value)):
            raise serializers.ValidationError('Não pode haver IDs duplicados.')

        return value
