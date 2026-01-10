from django.db import models


class AlternativesChoices(models.IntegerChoices):
    A = 1, 'A'
    B = 2, 'B'
    C = 3, 'C'
    D = 4, 'D'
    E = 5, 'E'
