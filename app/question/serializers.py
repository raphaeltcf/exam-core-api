from rest_framework import serializers

from question.models import Alternative, Question


class AlternativeSerializer(serializers.ModelSerializer):
    """Serializer para Alternative."""
    option_display = serializers.CharField(source='get_option_display', read_only=True)

    class Meta:
        model = Alternative
        fields = ['id', 'content', 'option', 'option_display', 'is_correct']


class AlternativeNestedSerializer(serializers.ModelSerializer):
    """Serializer aninhado para Alternative (usado dentro de Question)."""
    option_display = serializers.CharField(source='get_option_display', read_only=True)

    class Meta:
        model = Alternative
        fields = ['id', 'content', 'option', 'option_display', 'is_correct']


class QuestionListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de questões."""
    alternatives_count = serializers.IntegerField(source='alternatives.count', read_only=True)
    has_correct_alternative = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ['id', 'content', 'alternatives_count', 'has_correct_alternative']

    def get_has_correct_alternative(self, obj):
        """Verifica se a questão tem pelo menos uma alternativa correta."""
        return obj.alternatives.filter(is_correct=True).exists()


class QuestionSerializer(serializers.ModelSerializer):
    """Serializer completo para Question com alternatives aninhadas."""
    alternatives = AlternativeNestedSerializer(many=True, read_only=True)
    has_correct_alternative = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ['id', 'content', 'alternatives', 'has_correct_alternative']

    def get_has_correct_alternative(self, obj):
        """Verifica se a questão tem pelo menos uma alternativa correta."""
        return obj.alternatives.filter(is_correct=True).exists()


class QuestionCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para criar e atualizar questões."""
    alternatives = AlternativeNestedSerializer(many=True, required=False)

    class Meta:
        model = Question
        fields = ['id', 'content', 'alternatives']

    def create(self, validated_data):
        """Cria uma questão com suas alternativas."""
        alternatives_data = validated_data.pop('alternatives', [])
        question = Question.objects.create(**validated_data)
        
        for alt_data in alternatives_data:
            Alternative.objects.create(question=question, **alt_data)
        
        return question

    def update(self, instance, validated_data):
        """Atualiza uma questão e suas alternativas."""
        alternatives_data = validated_data.pop('alternatives', None)
        
        instance.content = validated_data.get('content', instance.content)
        instance.save()
        
        if alternatives_data is not None:
            # Remove alternativas existentes
            instance.alternatives.all().delete()
            # Cria novas alternativas
            for alt_data in alternatives_data:
                Alternative.objects.create(question=instance, **alt_data)
        
        return instance

    def validate_alternatives(self, value):
        """Valida que há pelo menos uma alternativa e no máximo 5."""
        if len(value) < 1:
            raise serializers.ValidationError("A questão deve ter pelo menos uma alternativa.")
        if len(value) > 5:
            raise serializers.ValidationError("A questão não pode ter mais de 5 alternativas.")
        
        # Valida que há apenas uma alternativa correta
        correct_count = sum(1 for alt in value if alt.get('is_correct', False))
        if correct_count == 0:
            raise serializers.ValidationError("A questão deve ter pelo menos uma alternativa correta.")
        if correct_count > 1:
            raise serializers.ValidationError("A questão deve ter apenas uma alternativa correta.")
        
        # Valida que não há opções duplicadas
        options = [alt.get('option') for alt in value]
        if len(options) != len(set(options)):
            raise serializers.ValidationError("Não pode haver opções duplicadas.")
        
        return value
