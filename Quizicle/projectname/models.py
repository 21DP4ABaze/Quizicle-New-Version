from django.db import models

class Quiz(models.Model):
    quiz_name = models.CharField(max_length=150)
    quiz_maximum_points = models.IntegerField(default=0, editable=False)  # Auto-calculated
    question_count = models.IntegerField(default=0, editable=False)  # Auto-calculated

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
    Question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    Answer = models.CharField(max_length=255)
    Correct = models.BooleanField(default=False)

    class Meta:
        app_label = 'projectname'

    def __str__(self):
        return self.Answer

class Results(models.Model):
    Quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="results")
    User = models.CharField(max_length=150)
    Result = models.IntegerField()

    class Meta:
        app_label = 'projectname'

    def __str__(self):
        return f"{self.User} - {self.Quiz.quiz_name} - {self.Result}"
