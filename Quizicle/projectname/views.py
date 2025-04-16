from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView, FormView
from django.utils.decorators import method_decorator
from django.db.models import Max
from .models import Quiz, Question, Answer, Results
from .forms import QuizForm
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.db import models
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import DeleteView


# Registration view
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

# Well done page (protected)
@login_required
def well_done(request):
    return render(request, 'well_done.html')

# Home page
def home(request):
    return render(request, 'home.html')

# Create a Quiz and allow adding questions/answers on the same page
@method_decorator(login_required, name='dispatch')
class QuizCreateView(CreateView):
    model = Quiz
    form_class = QuizForm
    template_name = 'create_quiz.html'
    success_url = reverse_lazy('quiz_list')

    def form_valid(self, form):
        quiz = form.save(commit=False)
        quiz.creator = self.request.user
        quiz.save()

        self._save_questions_and_answers(quiz)

        # Update metadata
        quiz.QuestionCount = quiz.questions.count()
        quiz.QuizMaximumPoints = quiz.questions.aggregate(total=models.Sum('points_for_question'))['total'] or 0
        quiz.save()

        return redirect(self.success_url)

    def _save_questions_and_answers(self, quiz):
        request = self.request
        questions = request.POST.getlist('questions[]')
        points = request.POST.getlist('points[]')
        question_images = request.FILES.getlist('question_images[]')

        correct_answers = {
            key.split("_")[2]: value
            for key, value in request.POST.items() if key.startswith("correct_answer_")
        }

        for index, question_text in enumerate(questions):
            if not question_text.strip():
                continue

            question = Question.objects.create(
                quiz=quiz,
                description=question_text.strip(),
                points_for_question=int(points[index]),
                image=question_images[index] if index < len(question_images) else None
            )

            answers = request.POST.getlist(f'all_answers[{index}][]')
            correct_index = int(correct_answers.get(str(index), -1))

            self._create_answers(question, answers, correct_index)

    def _create_answers(self, question, answers, correct_index):
        for i, answer in enumerate(answers):
            if answer.strip():
                Answer.objects.create(
                    question=question,
                    answer=answer.strip(),
                    correct=(i == correct_index)
                )
# View to add questions and answers dynamically inside the Quiz creation page


# List of quizzes
class QuizListView(LoginRequiredMixin, ListView):
    model = Quiz
    template_name = 'quiz_list.html'
    context_object_name = 'quizzes'

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        base_queryset = Quiz.objects.filter(creator=self.request.user)
        return base_queryset.filter(quiz_name__icontains=query) if query else base_queryset

# Take a quiz and submit answers
@method_decorator(login_required, name='dispatch')
class TakeQuizView(DetailView):
    model = Quiz
    template_name = 'take_quiz.html'
    context_object_name = 'quiz'

    def get_object(self):
        return get_object_or_404(Quiz, id=self.kwargs['quiz_id'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['questions'] = self.object.questions.all()  # Use the correct related name
        return context


    def post(self, request, *args, **kwargs):
        quiz = self.get_object()
        questions = quiz.questions.all()  
        score = 0

        for question in questions:
            selected_answer_id = request.POST.get(f'question_{question.id}')
            if selected_answer_id:
                selected_answer = Answer.objects.get(id=selected_answer_id)
                if selected_answer.correct:
                    score += question.points_for_question

        return redirect('quiz_result', quiz_id=quiz.id, score=score)



# View to show quiz results
@method_decorator(login_required, name='dispatch')
class QuizResultView(DetailView):
    model = Quiz
    template_name = 'quiz_result.html'
    context_object_name = 'quiz'

    def get_object(self):
        """ Fetch the quiz using quiz_id instead of pk """
        return get_object_or_404(Quiz, id=self.kwargs['quiz_id'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quiz = self.get_object()
        score = self.kwargs['score']

        # Fetch the previous best result for the user
        previous_result = Results.objects.filter(quiz=quiz, user=self.request.user.username).aggregate(Max('result'))['result__max']

        if previous_result is None or score > previous_result:
            Results.objects.create(quiz=quiz, user=self.request.user.username, result=score)
            message = f"🎉 New High Score! You scored {score}."
        elif score == previous_result:
            message = f"🏆 You matched your previous best score: {score}."
        else:
            message = f"📉 Your best score was {previous_result}. This time you scored {score}."

        context['score'] = score
        context['message'] = message
        return context
    
def search_quizzes(request):
    query = request.GET.get('q', '')
    quizzes = Quiz.objects.filter(QuizName__icontains=query) if query else Quiz.objects.all()
    
    data = {
        "quizzes": list(quizzes.values("id", "QuizName"))
    }
    return JsonResponse(data)


class QuizDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Quiz
    template_name = 'quiz_confirm_delete.html'
    success_url = reverse_lazy('quiz_list')

    def test_func(self):
        quiz = self.get_object()
        return quiz.creator == self.request.user  # Only allow quiz owner to delete
