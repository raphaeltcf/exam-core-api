from django.db import models

from question.models import Question


class Exam(models.Model):
    name = models.CharField(max_length=100)
    questions = models.ManyToManyField(Question, through='ExamQuestion', related_name='exams')

    def __str__(self):
        return self.name


class ExamQuestion(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    number = models.PositiveIntegerField()

    class Meta:
        unique_together = ('exam', 'number')
        ordering = ['number']

    def __str__(self):
        return f'{self.question} - {self.exam}'
