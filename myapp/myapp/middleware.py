from django.urls import reverse, reverse_lazy
from django.shortcuts import redirect

class RedirectAuthenticatedMiddleWare:
    def __init__(self, get_response):
        self.get_response = get_response
        self.login_url = reverse_lazy('blog:login')
        self.register_url = reverse_lazy('blog:register')
        self.index_url = reverse_lazy('blog:index')

    def __call__(self, request):
        if request.user.is_authenticated:
            paths_to_redirect = [self.login_url, self.register_url]

            if request.path in paths_to_redirect:
                return redirect(self.index_url)

        response = self.get_response(request)
        return response

class RestrictUnauthenticatedUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        restricted_paths = [reverse('blog:dashboard')]

        if not request.user.is_authenticated and request.path in restricted_paths:
            return redirect(reverse('blog:login'))

        response = self.get_response(request)
        return response
