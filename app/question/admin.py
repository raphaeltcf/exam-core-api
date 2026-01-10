from django.contrib import admin
from django.core.exceptions import ValidationError

from question.models import Question, Alternative
from question.services import AlternativeService


class AlternativeInline(admin.TabularInline):
    model = Alternative
    min_num = 1
    max_num = 5
    ordering = ('option',)

    def clean(self):
        super().clean()

        for form in self.forms:
            if not form.is_valid() or form in self.deleted_forms:
                continue

            if form.cleaned_data:
                instance = form.instance
                for field, value in form.cleaned_data.items():
                    setattr(instance, field, value)

                try:
                    AlternativeService.validate_single_correct_alternative(instance)
                except ValidationError as e:
                    if hasattr(e, 'message_dict'):
                        for field, messages in e.message_dict.items():
                            form.add_error(field, messages[0] if messages else '')
                    else:
                        form.add_error(None, str(e))


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    inlines = [AlternativeInline]
