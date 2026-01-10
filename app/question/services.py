from django.core.exceptions import ValidationError

from question.models import Alternative, Question


class QuestionService:

    @staticmethod
    def create_question(content: str) -> Question:
        question = Question(content=content)
        question.save()
        return question


class AlternativeService:

    @staticmethod
    def validate_single_correct_alternative(alternative: Alternative) -> None:
        if not alternative.is_correct:
            return

        other_correct = Alternative.objects.filter(
            question=alternative.question,
            is_correct=True
        ).exclude(pk=alternative.pk if alternative.pk else None)

        if other_correct.exists():
            raise ValidationError({
                'is_correct': 'Já existe uma alternativa correta para esta questão. '
                             'Apenas uma alternativa pode ser marcada como correta.'
            })

    @staticmethod
    def create_alternative(question: Question, content: str, option: int, is_correct: bool = False) -> Alternative:
        alternative = Alternative(
            question=question,
            content=content,
            option=option,
            is_correct=is_correct
        )

        AlternativeService.validate_single_correct_alternative(alternative)

        alternative.save()
        return alternative

    @staticmethod
    def update_alternative(alternative: Alternative, **kwargs) -> Alternative:
        for field, value in kwargs.items():
            if hasattr(alternative, field):
                setattr(alternative, field, value)

        AlternativeService.validate_single_correct_alternative(alternative)

        alternative.save()
        return alternative

    @staticmethod
    def mark_as_correct(alternative: Alternative) -> Alternative:
        Alternative.objects.filter(
            question=alternative.question
        ).exclude(pk=alternative.pk if alternative.pk else None).update(is_correct=False)

        alternative.is_correct = True
        alternative.save()

        return alternative

    
