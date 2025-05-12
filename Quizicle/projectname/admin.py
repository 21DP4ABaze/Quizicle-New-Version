from django.contrib import admin
from .models import Quiz, Question, Answer, Results

### QUIZ ADMIN ###
class QuizAdmin(admin.ModelAdmin):
    list_display = ('quizName', 'creator', 'question_count', 'QuizMaximumPoints', 'created_at')
    list_filter = ('creator')
    search_fields = ('QuizName', 'creator')
    readonly_fields = ('created_at', 'updated_at')

### QUESTION ADMIN ###
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('description', 'quiz', 'points_for_question','image')  # ✅ Check that `creator` exists in the model
    list_filter = ('quiz','points_for_question')  # ✅ Ensure `creator` is a valid field
    search_fields = ('description', 'quiz__quizName')
    ordering = ('quiz','points_for_question')

### ANSWER ADMIN ###
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('answer', 'question', 'correct')  # ✅ Use correct field names
    list_filter = ('correct',)  # ✅ Ensure the field exists in the `Answer` model
    search_fields = ('answer', 'description')

### RESULT ADMIN ###
class ResultsAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'result')  # ✅ Use correct field name instead of `score`
    list_filter = ('quiz', 'user')
    search_fields = ('user__username', 'quiz__QuizName')
    ordering = ('result','user')  # ✅ Ensure this field exists

### INLINE QUESTIONS INSIDE QUIZ ###
class QuestionInline(admin.TabularInline):  
    model = Question
    extra = 1

class QuizAdminWithQuestions(admin.ModelAdmin):
    inlines = [QuestionInline]

### REGISTER MODELS ###
admin.site.register(Quiz, QuizAdminWithQuestions)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer, AnswerAdmin)
admin.site.register(Results, ResultsAdmin)