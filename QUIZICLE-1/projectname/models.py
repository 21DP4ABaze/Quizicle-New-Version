import os
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver


class Quiz(models.Model):
    quiz_name = models.CharField(max_length=150)
    description = models.TextField(default="Complete the quiz—get results")
    quiz_maximum_points = models.IntegerField(default=0, editable=False)  # Auto-calculated
    question_count = models.IntegerField(default=0, editable=False)  # Auto-calculated
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions_created')

    class Meta:
        app_label = 'projectname'
        ordering = ['-id']

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


class QuizResultAnswer(models.Model):
    quiz_result = models.ForeignKey('Results', on_delete=models.CASCADE, related_name='quiz_result_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)

    class Meta:
        app_label = 'projectname'

    def __str__(self):
        return f"{self.quiz_result} - {self.question} - {self.answer}"


class Report(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="reports")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_reports")
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'projectname'
        ordering = ['-timestamp']

    def __str__(self):
        return f"Report by {self.user.username} on '{self.quiz.quiz_name}'"

class Description(models.Model):
    question = models.OneToOneField(Question, on_delete=models.CASCADE, related_name='answer_description')
    text = models.TextField()
    image = models.ImageField(upload_to='description_images/', blank=True, null=True)

    def __str__(self):
        return f"Description for Question {self.question.id}"


class Comment(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment by {self.user} on {self.quiz}'


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    banned = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} Profile"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


# Signal handlers
@receiver(post_delete, sender=Question)
def delete_question_image(sender, instance, **kwargs):
    """Delete image file when Question instance is deleted."""
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)


@receiver(pre_save, sender=Question)
def delete_old_image_on_update(sender, instance, **kwargs):
    """Delete old image file when Question image is updated."""
    if not instance.pk:
        return False

    try:
        old_image = Question.objects.get(pk=instance.pk).image
    except Question.DoesNotExist:
        return False

    if old_image and old_image != instance.image:
        if os.path.isfile(old_image.path):
            os.remove(old_image.path)
