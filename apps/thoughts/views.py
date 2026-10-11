from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import render

MAX_THOUGHT_CHARS = 160


def create(request):
    """Thought-card maker for GMM team members.

    The card is drawn in the browser (HTML canvas), so nothing is stored on the server:
    the employee pastes a short thought, picks a template and downloads / shares the image.
    Access: logged-in staff accounts only (User.is_staff).
    """
    user = request.user
    if not user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    if not user.is_staff:
        raise PermissionDenied
    return render(request, "thoughts/create.html", {
        "max_chars": MAX_THOUGHT_CHARS,
        "default_name": user.name,
        "site_host": request.get_host(),
    })
