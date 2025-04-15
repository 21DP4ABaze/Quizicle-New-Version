from django import forms
from .models import Quiz, Question, Answer, Results

# Form for creating a Quiz
class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['quiz_name']
        labels = {'quiz_name': 'Quiz Name'}
        widgets = {'quiz_name': forms.TextInput(attrs={'class': 'form-control'})}

    def save(self, commit=True):
        """Overrides save to update max points & question count after quiz creation"""
        quiz = super().save(commit=False)
        if commit:
            quiz.save()
            quiz.calculate_max_values()  # Auto-update fields
        return quiz

# Form for adding a Question to a Quiz
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
            question.quiz.calculate_max_values()  # Auto-update quiz stats
        return question

# Form for adding Answers to a Question
class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['Answer', 'Correct']
        labels = {
            'Answer': 'Answer Text',
            'Correct': 'Is this answer correct?'
        }
        widgets = {
            'Answer': forms.TextInput(attrs={'class': 'form-control'}),
            'Correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

# Form for storing Results
class ResultsForm(forms.ModelForm):
    class Meta:
        model = Results
        fields = ['Quiz', 'User', 'Result']
        labels = {
            'Quiz': 'Quiz Name',
            'User': 'User Name',
            'Result': 'Score',
        }
        widgets = {
            'Quiz': forms.Select(attrs={'class': 'form-control'}),
            'User': forms.TextInput(attrs={'class': 'form-control'}),
            'Result': forms.NumberInput(attrs={'class': 'form-control'}),
        }
