from django.db import models

class Quiz(models.Model):
    QuizName = models.CharField(max_length=150)
    QuizMaximumPoints = models.IntegerField(default=0, editable=False)  # Auto-calculated
    QuestionCount = models.IntegerField(default=0, editable=False)  # Auto-calculated

    class Meta:
        app_label = 'projectname'

    def __str__(self):
        return self.QuizName

    def calculate_max_values(self):
        """Auto-updates max points & question count"""
        self.QuestionCount = self.questions.count()
        self.QuizMaximumPoints = sum(q.PointsForQuestion for q in self.questions.all())
        self.save()

class Question(models.Model):
    Description = models.TextField()
    Quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    PointsForQuestion = models.IntegerField()
    AdditionalImage = models.ImageField(upload_to='question_images/', blank=True, null=True)

    class Meta:
        app_label = 'projectname'

    def __str__(self):
        return self.Description

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
        return f"{self.User} - {self.Quiz.QuizName} - {self.Result}"
