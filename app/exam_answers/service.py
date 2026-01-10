from django.core.exceptions import ValidationError
from django.db import transaction

from exam.models import ExamQuestion
from exam_answers.models import ExamAnswer
from question.models import Alternative
from student.models import Student
from exam.models import Exam


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

    @staticmethod
    def has_student_completed_exam(student: Student, exam: Exam) -> bool:
        total_questions = ExamQuestion.objects.filter(exam=exam).count()
        answered_questions = ExamAnswer.objects.filter(student=student, exam_question__exam=exam).count()
        return answered_questions == total_questions and total_questions > 0
    
    @staticmethod
    @transaction.atomic
    def submit_exam_answers(
        student: Student,
        exam: Exam,
        answers: list[dict]
    ) -> list[ExamAnswer]:
        
        if ExamAnswerService.has_student_completed_exam(student, exam):
            raise ValidationError({
                'student': 'Este estudante já completou o exame.'
            })
        
        exam_question_ids = [item['exam_question_id'] for item in answers]
        alternative_ids = [item['selected_alternative_id'] for item in answers]

        exam_questions = {
            eq.id: eq for eq in ExamQuestion.objects.filter(exam=exam, id__in=exam_question_ids)
        }

        alternatives = {
            alt.id: alt for alt in Alternative.objects.filter(id__in=alternative_ids).select_related('question')
        }

        created_answers = []
        for answer_data in answers:
            exam_question_id = answer_data['exam_question_id']
            alternative_id = answer_data['selected_alternative_id']

            exam_question = exam_questions.get(exam_question_id)
            alternative = alternatives.get(alternative_id)

            if not exam_question:
                raise ValidationError({
                    'answers': f'A questão {exam_question_id} não existe no exame.'
                })
            if not alternative:
                raise ValidationError({
                    'answers': f'A alternativa {alternative_id} não existe.'
                })
            if alternative.question != exam_question.question:
                raise ValidationError({
                    'answers': 'A alternativa selecionada não pertence à questão deste exame.'
                })
            if ExamAnswer.objects.filter(student=student, exam_question=exam_question).exists():
                raise ValidationError({
                    'answers': 'Este estudante já respondeu esta questão do exame.'
                })
            
            is_correct = alternative.is_correct

            exam_answer = ExamAnswer(
                student=student,
                exam_question=exam_question,
                selected_alternative=alternative,
                is_correct=is_correct
            )
            exam_answer.save()
            created_answers.append(exam_answer)
        
        return created_answers