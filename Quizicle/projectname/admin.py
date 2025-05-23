from django.contrib import admin
from .models import *


class QuizAdmin(admin.ModelAdmin):
    list_display = ('quizName', 'creator', 'question_count', 'QuizMaximumPoints', 'created_at')
    list_filter = ('creator',)
    search_fields = ('quizName', 'creator__username')
    readonly_fields = ('created_at', 'updated_at')


class DescriptionInline(admin.StackedInline):
    model = Description
    extra = 0
    max_num = 1
    fields = ('description', 'image')
    readonly_fields = ()


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('description', 'quiz', 'points_for_question', 'image')
    list_filter = ('quiz', 'points_for_question')
    search_fields = ('description', 'quiz__quizName')
    ordering = ('quiz', 'points_for_question')
    inlines = [DescriptionInline]

### ANSWER ADMIN ###
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('answer', 'question', 'correct')
    list_filter = ('correct',)
    search_fields = ('answer',)

### RESULT ADMIN ###
class ResultsAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'result')
    list_filter = ('quiz', 'user')
    search_fields = ('user__username', 'quiz__quizName')
    ordering = ('result', 'user')

### REPORT ADMIN ###
class ReportAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'user', 'description', 'timestamp')
    list_filter = ('quiz', 'user', 'timestamp')
    search_fields = ('quiz__quiz_name', 'user__username', 'description')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)

### INLINE QUESTIONS INSIDE QUIZ ###
class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1

class QuizAdminWithQuestions(admin.ModelAdmin):
    inlines = [QuestionInline]


class QuizResultAnswerAdmin(admin.ModelAdmin):
    list_display = ('quiz_result', 'question', 'answer')

### REGISTER MODELS ###
admin.site.register(Quiz, QuizAdminWithQuestions)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer, AnswerAdmin)
admin.site.register(Results, ResultsAdmin)
admin.site.register(Report, ReportAdmin)
admin.site.register(QuizResultAnswer, QuizResultAnswerAdmin)
# admin.site.register(Description, DescriptionAdmin)