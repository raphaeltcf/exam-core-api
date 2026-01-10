import django_filters

from question.models import Question


class QuestionFilter(django_filters.FilterSet):
    """Filtros para Question."""
    content = django_filters.CharFilter(lookup_expr='icontains', help_text="Filtrar por conteúdo (busca parcial)")
    has_correct_alternative = django_filters.BooleanFilter(
        method='filter_has_correct_alternative',
        help_text="Filtrar por questões que têm alternativa correta (true/false)"
    )
    alternatives_count_min = django_filters.NumberFilter(
        field_name='alternatives__count',
        lookup_expr='gte',
        help_text="Número mínimo de alternativas"
    )
    alternatives_count_max = django_filters.NumberFilter(
        field_name='alternatives__count',
        lookup_expr='lte',
        help_text="Número máximo de alternativas"
    )

    class Meta:
        model = Question
        fields = ['content', 'has_correct_alternative']

    def filter_has_correct_alternative(self, queryset, name, value):
        """Filtra questões que têm ou não alternativa correta."""
        if value is True:
            return queryset.filter(alternatives__is_correct=True).distinct()
        elif value is False:
            # Questões que não têm alternativa correta
            questions_with_correct = queryset.filter(alternatives__is_correct=True).values_list('id', flat=True)
            return queryset.exclude(id__in=questions_with_correct)
        return queryset
