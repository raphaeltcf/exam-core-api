import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-x95(-4u6g#ewh23@v7%wvz_(=ml^w64-iu&k#6*aw4-8%c=9z^"
)

DEBUG = os.environ.get("DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = [host.strip() for host in os.environ.get(
    "ALLOWED_HOSTS",
    "localhost,127.0.0.1,0.0.0.0"
).split(",")]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "drf_spectacular",
    "student",
    "question",
    "exam",
    "utils",
    "exam_answers",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "exam_api.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "exam_api.wsgi.application"


USE_POSTGRES = os.environ.get("USE_POSTGRES", "False").lower() == "true"

if USE_POSTGRES:
    DATABASES = {
        "default": {
            'ENGINE': "django.db.backends.postgresql",
            'NAME': os.environ.get("POSTGRES_DB", "teste"),
            'USER': os.environ.get("POSTGRES_USER", "teste"),
            'PASSWORD': os.environ.get("POSTGRES_PASSWORD", "teste"),
            'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
            'PORT': os.environ.get("POSTGRES_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 30,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_VERSION': 'v1',
    'EXCEPTION_HANDLER': 'exam_api.exception_handler.custom_exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Exam Core API',
    'DESCRIPTION': """
    API completa para gerenciamento de provas online com questões de múltipla escolha.
    
    ## Funcionalidades
    
    - **Estudantes**: Gerenciamento de estudantes com autenticação
    - **Questões**: CRUD completo de questões e alternativas
    - **Provas**: Criação e gerenciamento de provas com questões
    - **Respostas**: Submissão de provas e consulta de resultados
    
    ## Fluxo de Uso
    
    1. Criar questões com alternativas (POST /api/v1/questions/)
    2. Criar uma prova adicionando questões (POST /api/v1/exams/)
    3. Buscar prova para realizar (GET /api/v1/exams/{id}/)
    4. Submeter respostas completas (POST /api/v1/exam-answers/submit/)
    5. Consultar resultado (GET /api/v1/exam-answers/result/)
    """,
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
        'filter': True,
        'tryItOutEnabled': True,
        'syntaxHighlight.theme': 'monokai',
    },
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': r'/api/v[0-9]',
    'SERVERS': [
        {'url': 'http://localhost:8000', 'description': 'Servidor de Desenvolvimento'},
        {'url': 'http://0.0.0.0:8000', 'description': 'Servidor Docker'},
    ],
}

AUTH_USER_MODEL = 'student.Student'
