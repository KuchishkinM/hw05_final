from django.shortcuts import render
from django.http import HttpResponseServerError


def page_not_found(request, exception):
    return render(request, 'core/404.html', {'path': request.path}, status=404)


def csrf_failure(request, reason=''):
    return render(request, 'core/403csrf.html')


def permission_denied(request, exception):
    return render(request, 'core/403.html', {'path': request.path}, status=403)


def server_error(request):
    return render(HttpResponseServerError, 'core/500.html',
                  {'path': request.path}, status=500)
