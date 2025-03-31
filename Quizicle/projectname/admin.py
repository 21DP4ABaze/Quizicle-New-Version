<<<<<<< HEAD
from django.contrib import admin
from .models import Quiz, Question, Answer, Results

admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Results)

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('description', 'quiz', 'creator')  # Shows creator in the list
=======
from django.contrib import admin
from .models import Quiz, Question, Answer, Results

admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Results)
>>>>>>> 1aa76192b204e63c9c4fe886ce418540db6ba48e
