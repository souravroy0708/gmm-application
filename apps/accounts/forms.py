from unfold.forms import UserChangeForm as UnfoldUserChangeForm
from unfold.forms import UserCreationForm as UnfoldUserCreationForm

from .models import User


class UserCreationForm(UnfoldUserCreationForm):
    class Meta:
        model = User
        fields = ("phone", "name")


class UserChangeForm(UnfoldUserChangeForm):
    class Meta:
        model = User
        fields = "__all__"
