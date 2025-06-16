from django import forms
from .models import *
from .models import Report  


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['quiz_name','description']
        labels = {'quiz_name': 'Quiz Name',
                  'description': 'Description'
                  }
        widgets = {
            'quiz_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'})
        }

    def save(self, commit=True):
        """Overrides save to update max points & question count after quiz creation"""
        quiz = super().save(commit=False)
        if commit:
            quiz.save()
            quiz.calculate_max_values()  
        return quiz


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['description', 'points_for_question', 'image']
        labels = {
            'description': 'Question Text',
            'points_for_question': 'Points for Question',
            'image': 'Optional Image'
        }
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'points_for_question': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'})
        }

    def save(self, commit=True):
        """Updates quiz statistics after saving a question"""
        question = super().save(commit=False)
        if commit:
            question.save()
            question.quiz.calculate_max_values()  
        return question

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['answer', 'correct']
        labels = {
            'answer': 'Answer Text',
            'correct': 'Is this answer correct?'
        }
        widgets = {
            'answer': forms.TextInput(attrs={'class': 'form-control'}),
            'correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ResultsForm(forms.ModelForm):
    class Meta:
        model = Results
        fields = ['quiz', 'user', 'result']
        labels = {
            'quiz': 'Quiz Name',
            'user': 'User Name',
            'result': 'Score',
        }
        widgets = {
            'quiz': forms.Select(attrs={'class': 'form-control'}),
            'user': forms.TextInput(attrs={'class': 'form-control'}),
            'result': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe why you are reporting this quiz...'}),
        }
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Write your comment...'})
        }