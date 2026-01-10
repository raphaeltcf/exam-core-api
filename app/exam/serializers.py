from rest_framework import serializers

from exam.models import Exam, ExamQuestion
from question.models import Question, Alternative
from question.serializers import QuestionSerializer, QuestionListSerializer


class ExamQuestionSerializer(serializers.ModelSerializer):
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
    question = QuestionListSerializer(read_only=True)

    class Meta:
        model = ExamQuestion
        fields = ['id', 'question', 'number']
        read_only_fields = ['exam']


class ExamListSerializer(serializers.ModelSerializer):
    questions_count = serializers.IntegerField(source='examquestion_set.count', read_only=True)

    class Meta:
        model = Exam
        fields = ['id', 'name', 'questions_count']


class ExamSerializer(serializers.ModelSerializer):
    questions = ExamQuestionNestedSerializer(many=True, read_only=True, source='examquestion_set')
    questions_count = serializers.IntegerField(source='examquestion_set.count', read_only=True)

    class Meta:
        model = Exam
        fields = ['id', 'name', 'questions', 'questions_count']


class ExamCreateUpdateSerializer(serializers.ModelSerializer):
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
        question_ids = validated_data.pop('question_ids', [])
        exam = Exam.objects.create(**validated_data)
        
        if question_ids:
            for index, question_id in enumerate(question_ids, start=1):
                question = Question.objects.get(id=question_id)
                ExamQuestion.objects.create(exam=exam, question=question, number=index)
        
        return exam

    def update(self, instance, validated_data):
        question_ids = validated_data.pop('question_ids', None)
        
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        
        if question_ids is not None:
            ExamQuestion.objects.filter(exam=instance).delete()
            for index, question_id in enumerate(question_ids, start=1):
                question = Question.objects.get(id=question_id)
                ExamQuestion.objects.create(exam=instance, question=question, number=index)
        
        return instance


class AddQuestionToExamSerializer(serializers.Serializer):
    question_id = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.all(),
        required=True
    )
    number = serializers.IntegerField(required=True, min_value=1)

    def validate_number(self, value):
        exam = self.context['exam']
        if ExamQuestion.objects.filter(exam=exam, number=value).exists():
            raise serializers.ValidationError(
                f'Já existe uma questão na posição {value} deste exame.'
            )
        return value


class ReorderQuestionsSerializer(serializers.Serializer):
    exam_question_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        help_text="Lista de IDs de ExamQuestion na nova ordem desejada."
    )

    def validate_exam_question_ids(self, value):
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


class AlternativeTakeSerializer(serializers.ModelSerializer):
    option_display = serializers.CharField(source='get_option_display', read_only=True)

    class Meta:
        model = Alternative
        fields = ['id', 'content', 'option', 'option_display']


class QuestionTakeSerializer(serializers.ModelSerializer):
    alternatives = AlternativeTakeSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'content', 'alternatives']


class ExamQuestionTakeSerializer(serializers.ModelSerializer):
    question = QuestionTakeSerializer(read_only=True)
    number = serializers.IntegerField()

    class Meta:
        model = ExamQuestion
        fields = ['id', 'question', 'number']


class ExamTakeSerializer(serializers.ModelSerializer):
    questions = ExamQuestionTakeSerializer(
        many=True, 
        read_only=True, 
        source='examquestion_set',
        help_text="Lista de questões do exame sem mostrar as respostas corretas"
    )

    class Meta:
        model = Exam
        fields = ['id', 'name', 'questions']
