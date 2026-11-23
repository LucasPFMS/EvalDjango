from django import forms
from .models import Skill


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