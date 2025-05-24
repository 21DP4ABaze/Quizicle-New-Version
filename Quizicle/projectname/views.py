from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import View, ListView, DetailView, CreateView, DeleteView, TemplateView
from django.utils.decorators import method_decorator
from django.db.models import Max
from django.db import models
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.db.models import Count

from .models import Quiz, Question, Answer, Results, Report, Comment, Description, QuizResultAnswer
from .forms import QuizForm, CommentForm, ReportForm


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


@login_required
def well_done(request):
    return render(request, 'well_done.html')


def home(request):
    return render(request, 'home.html')


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
    template_name = 'popular_quizes.html'
    context_object_name = 'popular_quizes'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.annotate(result_count=Count('results')).order_by('-result_count')[:10]


@method_decorator(login_required, name='dispatch')
class TakeQuizView(DetailView):
    model = Quiz
    template_name = 'take_quiz.html'
    context_object_name = 'quiz'

    def get_object(self):
        return get_object_or_404(Quiz, id=self.kwargs['quiz_id'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['questions'] = self.object.questions.all()
        return context

    def post(self, request, *args, **kwargs):
        quiz = self.get_object()
        questions = quiz.questions.all()
        score = 0

        result = Results.objects.create(quiz=quiz, user=self.request.user.username, result=score)

        for question in questions:
            selected_answer_id = request.POST.get(f'question_{question.id}')
            if selected_answer_id:
                selected_answer = Answer.objects.get(id=selected_answer_id)
                if selected_answer.correct:
                    score += question.points_for_question

            QuizResultAnswer.objects.create(
                quiz_result=result,
                question=question,
                answer=selected_answer,
            )

        result.result = score
        result.save()

        return redirect('quiz_result', quiz_id=quiz.id, score=score)



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

        latest_result = Results.objects.filter(
            quiz=quiz,
            user=self.request.user.username
        ).order_by('-id').first()
        answers = QuizResultAnswer.objects.filter(quiz_result=latest_result)

        for answer in answers:
            answer.correct_answer = answer.question.answers.filter(correct=True).first()

        previous_result = Results.objects.filter(
            quiz=quiz,
            user=self.request.user.username
        ).exclude(id=latest_result.id).aggregate(Max('result'))['result__max']

        if previous_result is None or score > previous_result:
            message = f"New High Score! You scored {score}."
        elif score == previous_result:
            message = f"You matched your previous best score: {score}."
        else:
            message = f"Your best score was {previous_result}. This time you scored {score}."

        context['score'] = score
        context['message'] = message
        context['answers'] = answers
        return context


class QuizDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Quiz
    template_name = 'quiz_confirm_delete.html'
    success_url = reverse_lazy('quiz_list')

    def test_func(self):
        quiz = self.get_object()
        return quiz.creator == self.request.user


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

        # Handle questions
        existing_questions = list(quiz.questions.all())
        new_questions = request.POST.getlist('questions[]')
        points = request.POST.getlist('points[]')

        correct_answers = {
            key.split("_")[2]: value
            for key, value in request.POST.items() if key.startswith("correct_answer_")
        }

        for index, question_text in enumerate(new_questions):
            if not question_text.strip():
                continue

            if index < len(existing_questions):
                # Update existing question
                question = existing_questions[index]
                question.description = question_text.strip()
                question.points_for_question = int(points[index])
                question.save()
                question.answers.all().delete() 
            else:
                # Create new question
                question = Question.objects.create(
                    quiz=quiz,
                    description=question_text.strip(),
                    points_for_question=int(points[index])
                )

            # Handle answers
            answers = request.POST.getlist(f'all_answers[{index}][]')
            correct_index = int(correct_answers.get(str(index), -1))

            for i, answer_text in enumerate(answers):
                Answer.objects.create(
                    question=question,
                    answer=answer_text.strip(),
                    correct=(i == correct_index)
                )

            # Handle description
            desc_text = request.POST.get(f'description_text[{index}]', '').strip()
            desc_image = request.FILES.get(f'description_image[{index}]')

            if desc_text or desc_image:
                if hasattr(question, 'answer_description'):
                    description = question.answer_description
                    description.text = desc_text
                    if desc_image:
                        description.image = desc_image
                    description.save()
                else:
                    Description.objects.create(
                        question=question,
                        text=desc_text,
                        image=desc_image
                    )

        # Delete leftover old questions
        if len(existing_questions) > len(new_questions):
            for extra_question in existing_questions[len(new_questions):]:
                extra_question.delete()

        quiz.calculate_max_values()

        return redirect('quiz_list')


class QuizDetailView(View):
    template_name = 'quiz_details.html'

    def get(self, request, pk, *args, **kwargs):
        quiz = get_object_or_404(Quiz, id=pk)
        comments = Comment.objects.filter(quiz=quiz).order_by('-created_at')
        form = CommentForm()
        return render(request, self.template_name, {
            'quiz': quiz,
            'comments': comments,
            'form': form
        })

    @method_decorator(login_required)
    def post(self, request, pk, *args, **kwargs):
        quiz = get_object_or_404(Quiz, id=pk)
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.quiz = quiz
            comment.user = request.user
            comment.save()
        return redirect('quiz_details', pk=pk)


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
    return render(request, 'admin/admin_reports.html', context)


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
    success_url = reverse_lazy('admin_reports')

    def test_func(self):

        report = self.get_object()
        return self.request.user.is_superuser or report.user == self.request.user


@login_required
def user_profile(request):
    user = request.user

    if request.method == 'POST':
        if 'change_username' in request.POST:
            new_username = request.POST.get('new_username')
            if new_username and new_username != user.username:
                user.username = new_username
                user.save()
                messages.success(request, 'Username successfully updated!')

        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Your password was successfully updated!')
            else:
                messages.error(request, 'Please correct the error below.')

        elif 'delete_account' in request.POST:
            password = request.POST.get('password')
            if user.check_password(password):
                user.delete()
                messages.success(request, 'Account deleted successfully.')
                return redirect('home')
            else:
                messages.error(request, 'Incorrect password.')

        elif 'delete_all_data' in request.POST:
            password = request.POST.get('password')
            if user.check_password(password):
                Quiz.objects.filter(creator=user).delete()
                Results.objects.filter(user=user).delete()
                Report.objects.filter(user=user).delete()
                messages.success(request, 'All associated data deleted successfully.')
            else:
                messages.error(request, 'Incorrect password.')

    password_form = PasswordChangeForm(user)
    context = {
        'user': user,
        'password_form': password_form
    }
    return render(request, 'user_profile.html', context)


class DeleteCommentView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        comment = get_object_or_404(Comment, id=pk)
        if comment.user == request.user:
            comment.delete()
        return redirect('quiz_details', pk=comment.quiz.id)


@user_passes_test(lambda u: u.is_superuser)
def user_handler(request):
    users = User.objects.all()

    if request.method == "POST":
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        user = User.objects.get(id=user_id)

        if action == "delete":
            user.delete()
        elif action == "ban":
            user.profile.banned = True
            user.profile.save()
        elif action == "unban":
            user.profile.banned = False
            user.profile.save()

    return render(request, 'admin/user_handler.html', {'users': users})


def banned_page(request):
    return render(request, 'banned_page.html')
