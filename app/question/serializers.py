from rest_framework import serializers

from question.models import Alternative, Question


class AlternativeSerializer(serializers.ModelSerializer):
    option_display = serializers.CharField(source='get_option_display', read_only=True)

    class Meta:
        model = Alternative
        fields = ['id', 'content', 'option', 'option_display', 'is_correct']


class AlternativeNestedSerializer(serializers.ModelSerializer):
    option_display = serializers.CharField(source='get_option_display', read_only=True)

    class Meta:
        model = Alternative
        fields = ['id', 'content', 'option', 'option_display', 'is_correct']


class QuestionListSerializer(serializers.ModelSerializer):
    alternatives_count = serializers.IntegerField(source='alternatives.count', read_only=True)
    has_correct_alternative = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ['id', 'content', 'alternatives_count', 'has_correct_alternative']

    def get_has_correct_alternative(self, obj):
        return obj.alternatives.filter(is_correct=True).exists()


class QuestionSerializer(serializers.ModelSerializer):
    alternatives = AlternativeNestedSerializer(many=True, read_only=True)
    has_correct_alternative = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ['id', 'content', 'alternatives', 'has_correct_alternative']

    def get_has_correct_alternative(self, obj):
        return obj.alternatives.filter(is_correct=True).exists()


class QuestionCreateUpdateSerializer(serializers.ModelSerializer):
    alternatives = AlternativeNestedSerializer(many=True, required=False)

    class Meta:
        model = Question
        fields = ['id', 'content', 'alternatives']

    def create(self, validated_data):
        alternatives_data = validated_data.pop('alternatives', [])
        question = Question.objects.create(**validated_data)
        
        for alt_data in alternatives_data:
            Alternative.objects.create(question=question, **alt_data)
        
        return question

    def update(self, instance, validated_data):
        alternatives_data = validated_data.pop('alternatives', None)
        
        instance.content = validated_data.get('content', instance.content)
        instance.save()
        
        if alternatives_data is not None:
            instance.alternatives.all().delete()
            for alt_data in alternatives_data:
                Alternative.objects.create(question=instance, **alt_data)
        
        return instance

    def validate_alternatives(self, value):
        if len(value) < 1:
            raise serializers.ValidationError("A questão deve ter pelo menos uma alternativa.")
        if len(value) > 5:
            raise serializers.ValidationError("A questão não pode ter mais de 5 alternativas.")
        
        correct_count = sum(1 for alt in value if alt.get('is_correct', False))
        if correct_count == 0:
            raise serializers.ValidationError("A questão deve ter pelo menos uma alternativa correta.")
        if correct_count > 1:
            raise serializers.ValidationError("A questão deve ter apenas uma alternativa correta.")
        
        options = [alt.get('option') for alt in value]
        if len(options) != len(set(options)):
            raise serializers.ValidationError("Não pode haver opções duplicadas.")
        
        return value
