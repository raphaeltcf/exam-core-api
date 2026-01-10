from django.core.exceptions import ValidationError

from exam.models import ExamQuestion
from exam_answers.models import ExamAnswer
from question.models import Alternative
from student.models import Student


class ExamAnswerService:

    @staticmethod
    def validate_answer(exam_question: ExamQuestion, selected_alternative: Alternative) -> None:
        if selected_alternative.question != exam_question.question:
            raise ValidationError({
                'selected_alternative': 'A alternativa selecionada não pertence à questão deste exame.'
            })

    @staticmethod
    def calculate_correctness(selected_alternative: Alternative) -> bool:
        return selected_alternative.is_correct

    @staticmethod
    def create_answer(
        student: Student,
        exam_question: ExamQuestion,
        selected_alternative: Alternative
    ) -> ExamAnswer:
        if ExamAnswer.objects.filter(student=student, exam_question=exam_question).exists():
            raise ValidationError({
                'exam_question': 'Este estudante já respondeu esta questão do exame.'
            })

        ExamAnswerService.validate_answer(exam_question, selected_alternative)

        is_correct = ExamAnswerService.calculate_correctness(selected_alternative)

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
        if selected_alternative is not None:
            ExamAnswerService.validate_answer(exam_answer.exam_question, selected_alternative)
            exam_answer.selected_alternative = selected_alternative
            exam_answer.is_correct = ExamAnswerService.calculate_correctness(selected_alternative)

        exam_answer.save()
        return exam_answer
