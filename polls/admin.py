# coding=gbk
from django.contrib import admin

# Register your models here.

from guardian.admin import GuardedModelAdmin

from .models import Question, Choice


class ChoiceInline(admin.TabularInline):
#class ChoiceInline(GuardedModelAdmin):
    model = Choice
    extra = 3


class QuestionAdmin(admin.ModelAdmin):
#class QuestionAdmin(GuardedModelAdmin):
    fieldsets = [
        ('基本信息',               {'fields': ['question_text']}),
        ('日期信息', {'fields': ['pub_date'], 'classes': ['collapse']}),
    ]
    inlines = [ChoiceInline]

    list_display = ('question_text', 'pub_date', 'was_published_recently')
    list_filter = ['pub_date']
    search_fields = ['question_text']

admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice)


#admin.site.register(QuestionAdmin)
