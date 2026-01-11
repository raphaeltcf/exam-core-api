from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from exam.views import ExamViewSet
from exam_answers.views import ExamAnswerViewSet
from question.views import QuestionViewSet
from student.views import StudentViewSet

router = DefaultRouter()
router.register(r'students', StudentViewSet, basename='student')
router.register(r'questions', QuestionViewSet, basename='question')
router.register(r'exams', ExamViewSet, basename='exam')
router.register(r'exam-answers', ExamAnswerViewSet, basename='exam-answer')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(router.urls)),
    # Swagger/OpenAPI endpoints
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
