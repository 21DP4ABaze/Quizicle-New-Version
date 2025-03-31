from django.contrib import admin
from .models import Quiz, Question, Answer, Results

admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Results)

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('description', 'quiz', 'creator')  # Shows creator in the list