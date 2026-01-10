import django_filters
from django.db import models

from exam.models import Exam


class ExamFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains', help_text="Filtrar por nome (busca parcial)")
    questions_count_min = django_filters.NumberFilter(
        method='filter_questions_count_min',
        help_text="Número mínimo de questões no exame"
    )
    questions_count_max = django_filters.NumberFilter(
        method='filter_questions_count_max',
        help_text="Número máximo de questões no exame"
    )
    has_question = django_filters.NumberFilter(
        field_name='examquestion__question',
        lookup_expr='exact',
        help_text="Filtrar por exames que contêm uma questão específica (ID da questão)"
    )

    class Meta:
        model = Exam
        fields = ['name', 'has_question']

    def filter_questions_count_min(self, queryset, name, value):
        return queryset.annotate(
            questions_count=models.Count('examquestion')
        ).filter(questions_count__gte=value)

    def filter_questions_count_max(self, queryset, name, value):
        return queryset.annotate(
            questions_count=models.Count('examquestion')
        ).filter(questions_count__lte=value)
