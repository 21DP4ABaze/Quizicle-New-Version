from django.shortcuts import redirect
from django.urls import reverse

class BanMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if hasattr(request.user, 'profile') and request.user.profile.banned:
                
                # List of paths to block
                blocked_paths = [
                    reverse('create_quiz'),    # Creating a quiz
                    reverse('quiz_details', args=[1]),   # Quiz details (we will use startswith to match IDs)
                    reverse('take_quiz', args=[1]),      # Taking a quiz
                    reverse('report_quiz', args=[1]),    # Reporting a quiz
                ]

                # Check if the current path starts with any of the blocked paths
                for path in blocked_paths:
                    if request.path.startswith(path[:-2]):  # Removes the '1' and trailing slash to match any ID
                        return redirect('banned_page')
                        
        return self.get_response(request)