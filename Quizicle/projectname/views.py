from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView, FormView
from django.utils.decorators import method_decorator
from django.db.models import Max
from .models import Quiz, Question, Answer, Results
from .forms import QuizForm, QuestionForm
from django.http import JsonResponse
from django.core.files.storage import default_storage

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
        quiz = form.save()

        # Get question data from POST
        questions = self.request.POST.getlist('questions[]')
        points = self.request.POST.getlist('points[]')
        question_images = self.request.FILES.getlist('question_images[]')  # Get uploaded images

        # Get correct answers dynamically
        correct_answers = {
            key.split("_")[2]: value  # Extracts the question index
            for key, value in self.request.POST.items() if key.startswith("correct_answer_")
        }

        for q_index, question_text in enumerate(questions):
            if question_text.strip():
                # Save the question image if it exists
                additional_image = question_images[q_index] if q_index < len(question_images) else None

                question = Question.objects.create(
                    quiz=quiz,
                    description=question_text.strip(),
                    points_for_question=int(points[q_index]),
                    image=additional_image  # Save the image
                )

                # Get answers for this specific question
                answers_for_question = self.request.POST.getlist(f'all_answers[{q_index}][]')

                # Retrieve correct answer index safely
                correct_answer_index = correct_answers.get(str(q_index))
                correct_answer_index = int(correct_answer_index) if correct_answer_index is not None else None

                for a_index, answer_text in enumerate(answers_for_question):
                    if answer_text.strip():
                        is_correct = (a_index == correct_answer_index)  # Match correct answer index

                        Answer.objects.create(
                            Question=question,
                            Answer=answer_text.strip(),
                            Correct=is_correct
                        )

        # Update quiz metadata
        quiz.QuestionCount = len(questions)
        quiz.QuizMaximumPoints = sum(map(int, points))
        quiz.save()

        return redirect(self.success_url)
# View to add questions and answers dynamically inside the Quiz creation page


# List of quizzes
class QuizListView(ListView):
    model = Quiz
    template_name = 'quiz_list.html'
    context_object_name = 'quizzes'

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        return Quiz.objects.filter(QuizName__icontains=query) if query else Quiz.objects.all()

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
                if selected_answer.Correct:
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
        previous_result = Results.objects.filter(Quiz=quiz, User=self.request.user.username).aggregate(Max('Result'))['Result__max']

        if previous_result is None or score > previous_result:
            Results.objects.create(Quiz=quiz, User=self.request.user.username, Result=score)
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

