from django.db import models
from django.db.models import UniqueConstraint


class ExamAnswer(models.Model):
    student = models.ForeignKey(
        'student.Student',
        on_delete=models.CASCADE,
        related_name='exam_answers'
    )
    exam_question = models.ForeignKey(
        'exam.ExamQuestion',
        on_delete=models.CASCADE,
        related_name='answers'
    )
    selected_alternative = models.ForeignKey(
        'question.Alternative',
        on_delete=models.CASCADE
    )
    is_correct = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['student', 'exam_question'],
                name='unique_student_exam_question'
            )
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.student.email} - {self.exam_question.exam.name} - Q{self.exam_question.number}'