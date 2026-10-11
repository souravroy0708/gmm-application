from django.shortcuts import render

MAX_THOUGHT_CHARS = 160


def create(request):
    """Public thought-card maker (no login needed).

    The card is drawn in the visitor's browser (HTML canvas), so nothing is stored on the server:
    the visitor types or pastes a short thought, picks a template and downloads / shares the image.
    """
    user = request.user
    return render(request, "thoughts/create.html", {
        "max_chars": MAX_THOUGHT_CHARS,
        "default_name": user.name if user.is_authenticated else "",
        "site_host": request.get_host(),
    })
