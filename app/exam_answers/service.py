from django.core.exceptions import ValidationError

from exam.models import ExamQuestion
from exam_answers.models import ExamAnswer
from question.models import Alternative
from student.models import Student


class ExamAnswerService:

    @staticmethod
    def validate_answer(exam_question: ExamQuestion, selected_alternative: Alternative) -> None:
        """Valida se a alternativa selecionada pertence à questão do exame."""
        if selected_alternative.question != exam_question.question:
            raise ValidationError({
                'selected_alternative': 'A alternativa selecionada não pertence à questão deste exame.'
            })

    @staticmethod
    def calculate_correctness(selected_alternative: Alternative) -> bool:
        """Calcula se a resposta está correta comparando com a alternativa selecionada."""
        return selected_alternative.is_correct

    @staticmethod
    def create_answer(
        student: Student,
        exam_question: ExamQuestion,
        selected_alternative: Alternative
    ) -> ExamAnswer:
        """Cria uma nova resposta de exame e calcula automaticamente se está correta."""
        # Valida se já existe resposta para este estudante e questão
        if ExamAnswer.objects.filter(student=student, exam_question=exam_question).exists():
            raise ValidationError({
                'exam_question': 'Este estudante já respondeu esta questão do exame.'
            })

        # Valida se a alternativa pertence à questão
        ExamAnswerService.validate_answer(exam_question, selected_alternative)

        # Calcula se está correta
        is_correct = ExamAnswerService.calculate_correctness(selected_alternative)

        # Cria a resposta
        exam_answer = ExamAnswer(
            student=student,
            exam_question=exam_question,
            selected_alternative=selected_alternative,
            is_correct=is_correct
        )
        exam_answer.save()
        return exam_answer

    @staticmethod
    def update_answer(
        exam_answer: ExamAnswer,
        selected_alternative: Alternative = None
    ) -> ExamAnswer:
        """Atualiza uma resposta existente."""
        if selected_alternative is not None:
            # Valida se a nova alternativa pertence à questão
            ExamAnswerService.validate_answer(exam_answer.exam_question, selected_alternative)
            exam_answer.selected_alternative = selected_alternative
            # Recalcula se está correta
            exam_answer.is_correct = ExamAnswerService.calculate_correctness(selected_alternative)

        exam_answer.save()
        return exam_answer
