import django_filters

from exam_answers.models import ExamAnswer


class ExamAnswerFilter(django_filters.FilterSet):
    """Filtros para ExamAnswer."""
    student = django_filters.NumberFilter(
        field_name='student',
        lookup_expr='exact',
        help_text="Filtrar por estudante (ID do estudante)"
    )
    student_email = django_filters.CharFilter(
        field_name='student__email',
        lookup_expr='icontains',
        help_text="Filtrar por email do estudante (busca parcial)"
    )
    exam = django_filters.NumberFilter(
        field_name='exam_question__exam',
        lookup_expr='exact',
        help_text="Filtrar por exame (ID do exame)"
    )
    exam_name = django_filters.CharFilter(
        field_name='exam_question__exam__name',
        lookup_expr='icontains',
        help_text="Filtrar por nome do exame (busca parcial)"
    )
    exam_question = django_filters.NumberFilter(
        field_name='exam_question',
        lookup_expr='exact',
        help_text="Filtrar por questão do exame (ID do ExamQuestion)"
    )
    is_correct = django_filters.BooleanFilter(
        field_name='is_correct',
        help_text="Filtrar por respostas corretas/incorretas (true/false)"
    )
    created_at = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        help_text="Filtrar por data de criação (maior ou igual)"
    )
    created_at_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        help_text="Filtrar por data de criação (menor ou igual)"
    )
    created_at_range = django_filters.DateTimeFromToRangeFilter(
        field_name='created_at',
        help_text="Filtrar por intervalo de data de criação (created_at_range_after e created_at_range_before)"
    )

    class Meta:
        model = ExamAnswer
        fields = [
            'student', 'student_email',
            'exam', 'exam_name',
            'exam_question',
            'is_correct',
            'created_at'
        ]
