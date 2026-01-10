from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from exam.views import ExamViewSet
from exam_answers.views import ExamAnswerViewSet
from question.views import QuestionViewSet
from student.views import StudentViewSet

# Configuração do router do DRF
router = DefaultRouter()
router.register(r'students', StudentViewSet, basename='student')
router.register(r'questions', QuestionViewSet, basename='question')
router.register(r'exams', ExamViewSet, basename='exam')
router.register(r'exam-answers', ExamAnswerViewSet, basename='exam-answer')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(router.urls)),
]
