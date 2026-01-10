from exam.models import Exam, ExamQuestion
from question.models import Question


class ExamService:

    @staticmethod
    def create_exam(name: str) -> Exam:
        exam = Exam(name=name)
        exam.save()
        return exam

    @staticmethod
    def add_question_to_exam(exam: Exam, question: Question, number: int) -> ExamQuestion:
        if ExamQuestion.objects.filter(exam=exam, number=number).exists():
            raise ValueError(f'Já existe uma questão na posição {number} deste exame.')

        exam_question = ExamQuestion(exam=exam, question=question, number=number)
        exam_question.save()
        return exam_question

    @staticmethod
    def remove_question_from_exam(exam: Exam, question: Question) -> None:
        ExamQuestion.objects.filter(exam=exam, question=question).delete()

    @staticmethod
    def reorder_questions(exam: Exam, question_order: list[int]) -> None:
        exam_questions = ExamQuestion.objects.filter(exam=exam)
        exam_question_ids = set(exam_questions.values_list('id', flat=True))

        if set(question_order) != exam_question_ids:
            raise ValueError('A ordem fornecida não corresponde às questões do exame.')

        for new_number, question_id in enumerate(question_order, start=1):
            ExamQuestion.objects.filter(id=question_id).update(number=new_number)
