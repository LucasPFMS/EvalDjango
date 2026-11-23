from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import HelpRequest, Skill


class QuestionAddForm(forms.Form):
    question_text = forms.CharField(label='Question text')
    choice_0 = forms.CharField(label='choice #1')
    choice_1 = forms.CharField(label='choice #2', required=False)
    choice_2 = forms.CharField(label='choice #3', required=False)
    choice_3 = forms.CharField(label='choice #4', required=False)
    choice_4 = forms.CharField(label='choice #5', required=False)


class OfferSkillsForm(forms.Form):
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Compétences que je possède et souhaite proposer",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["skills"].queryset = Skill.objects.all()


class HelpRequestForm(forms.ModelForm):
    class Meta:
        model = HelpRequest
        fields = ["activity", "skill", "starts_at"]
        labels = {
            "activity": "Activité pour laquelle vous cherchez de l'aide",
            "skill": "Compétence recherchée",
            "starts_at": "Date et heure du créneau",
        }
        widgets = {
            "activity": forms.Textarea(attrs={"rows": 4}),
            "starts_at": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M",
                attrs={"type": "datetime-local"},
            ),
        }

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["skill"].queryset = Skill.objects.exclude(offered_by=user)
        self.fields["starts_at"].input_formats = ["%Y-%m-%dT%H:%M"]

    def clean_starts_at(self):
        starts_at = self.cleaned_data["starts_at"]
        if starts_at <= timezone.now():
            raise ValidationError("Le créneau doit être situé dans le futur.")
        return starts_at

    def save(self, commit=True):
        help_request = super().save(commit=False)
        help_request.requester = self.user
        if commit:
            help_request.save()
        return help_request