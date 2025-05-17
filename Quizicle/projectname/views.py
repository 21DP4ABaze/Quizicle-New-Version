from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView, DeleteView, TemplateView,View
from django.utils.decorators import method_decorator
from django.db.models import Max
from .models import Quiz, Question, Answer, Results, Report,Description
from .forms import QuizForm, ReportForm
from django.http import JsonResponse
from django.db import models
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import user_passes_test


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
        quiz.question_count = quiz.questions.count()
        quiz.quiz_maximum_points = quiz.questions.aggregate(total=models.Sum('points_for_question'))['total'] or 0
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

        description_texts = request.POST.getlist('descriptions[]')
        description_images = request.FILES.getlist('description_images[]')

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

            # Save the description with optional image
            Description.objects.create(
                question=question,
                text=description_texts[index] if index < len(description_texts) else '',
                image=description_images[index] if index < len(description_images) else None
            )

    def _create_answers(self, question, answers, correct_index):
        for i, answer in enumerate(answers):
            if answer.strip():
                Answer.objects.create(
                    question=question,
                    answer=answer.strip(),
                    correct=(i == correct_index)
                )



# List of quizzes
class QuizListView(LoginRequiredMixin, ListView):
    model = Quiz
    template_name = 'quiz_list.html'
    context_object_name = 'quizzes'

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        base_queryset = Quiz.objects.filter(creator=self.request.user)
        return base_queryset.filter(quiz_name__icontains=query) if query else base_queryset
    
class PopularQuizView(ListView):
    model = Quiz
    template_name='popular_quizes.html'
    context_object_name='popular_quizes'

    def get_queryset(self):
        return super().get_queryset()

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
            message = f"New High Score! You scored {score}."
        elif score == previous_result:
            message = f"You matched your previous best score: {score}."
        else:
            message = f"Your best score was {previous_result}. This time you scored {score}."

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


class QuizPublicList(TemplateView):
    template_name = 'quiz_public_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['quizzes'] = Quiz.objects.all()
        return context
    
class UserResultsView(ListView):
    model = Results
    template_name = 'user_results.html'
    context_object_name = 'results'

    def get_queryset(self):
        return Results.objects.filter(user=self.request.user.username).select_related('quiz')
    
@method_decorator(login_required, name='dispatch')

class ModifyQuizView(View):
    template_name = 'modify_quiz.html'

    def get(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id, creator=request.user)
        return render(request, self.template_name, {'quiz': quiz})

    def post(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id, creator=request.user)

        # Update quiz name
        quiz.quiz_name = request.POST.get('quiz_name')
        quiz.save()

        # Delete existing questions and answers
        quiz.questions.all().delete()

        # Re-create the questions and answers
        questions = request.POST.getlist('questions[]')
        points = request.POST.getlist('points[]')
        
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
                points_for_question=int(points[index])
            )

            answers = request.POST.getlist(f'all_answers[{index}][]')
            correct_index = int(correct_answers.get(str(index), -1))

            for i, answer in enumerate(answers):
                Answer.objects.create(
                    question=question,
                    answer=answer.strip(),
                    correct=(i == correct_index)
                )

        # Recalculate the maximum points and question count
        quiz.calculate_max_values()

        return redirect('quiz_list')
    
class QuizDetailView(View):
    template_name = 'quiz_details.html'

    def get(self, request, pk, *args, **kwargs):
        quiz = get_object_or_404(Quiz, id=pk)
        return render(request, self.template_name, {'quiz': quiz})
    
@method_decorator(login_required, name='dispatch')
class ReportCreateView(CreateView):
    model = Report
    form_class = ReportForm
    template_name = 'report_quiz.html'
    success_url = reverse_lazy('quiz_list')

    def form_valid(self, form):
        quiz = get_object_or_404(Quiz, id=self.kwargs['quiz_id'])
        report = form.save(commit=False)
        report.quiz = quiz
        report.user = self.request.user
        report.save()
        return redirect(self.success_url)
@user_passes_test(lambda u: u.is_superuser)
def admin_reports_view(request):
    reports = Report.objects.all()
    context = {
        'reports': reports
    }
    return render(request, 'admin_reports.html', context)

@user_passes_test(lambda u: u.is_superuser)
def admin_quiz_delete_view(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    
    if request.method == 'POST':
        quiz.delete()
        return redirect('quiz_list')

    return render(request, 'quiz_confirm_delete.html', {'object': quiz})

class ReportDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Report
    template_name = 'report_confirm_delete.html'
    success_url = reverse_lazy('admin_reports')  # or wherever you want to redirect after deletion

    def test_func(self):
        # Only superusers or the report's user can delete
        report = self.get_object()
        return self.request.user.is_superuser or report.user == self.request.user

