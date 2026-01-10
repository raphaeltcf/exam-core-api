from django.contrib import admin

from exam.models import Exam, ExamQuestion


class ExamQuestionInline(admin.TabularInline):
    model = ExamQuestion


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    inlines = [ExamQuestionInline]
