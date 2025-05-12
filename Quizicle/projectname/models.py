from django.db import models
from django.contrib.auth.models import User

class Quiz(models.Model):
    quiz_name = models.CharField(max_length=150)
    quiz_maximum_points = models.IntegerField(default=0, editable=False)  # Auto-calculated
    question_count = models.IntegerField(default=0, editable=False)  # Auto-calculated
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions_created')
    class Meta:
        app_label = 'projectname'

    def __str__(self):
        return self.quiz_name

    def calculate_max_values(self):
        """Auto-updates max points & question count"""
        self.QuestionCount = self.questions.count()
        self.QuizMaximumPoints = sum(q.points_for_question for q in self.questions.all())
        self.save()

class Question(models.Model):
    description = models.TextField()
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    points_for_question = models.IntegerField()
    image = models.ImageField(upload_to='question_images/', blank=True, null=True)

    class Meta:
        app_label = 'projectname'

    def __str__(self):
        return self.description

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    answer = models.CharField(max_length=255)
    correct = models.BooleanField(default=False)

    class Meta:
        app_label = 'projectname'

    def __str__(self):
        return self.answer

class Results(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="results")
    user = models.CharField(max_length=150)
    result = models.IntegerField()

    class Meta:
        app_label = 'projectname'

    def __str__(self):
        return f"{self.user} - {self.quiz.quiz_name} - {self.result}"
