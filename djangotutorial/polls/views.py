from django.shortcuts import get_object_or_404, redirect, render

# Create your views here.
from django.db.models import F, Sum, Max
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.views import generic
from .forms import OfferSkillsForm, QuestionAddForm
from .models import Choice, HelpSlot, Question, Skill
from .utils import minimax


def public_index(request):
    return render(request, "polls/public_index.html", {
        "skills": Skill.objects.all(),
        "upcoming_help_slots": HelpSlot.objects.filter(
            starts_at__gte=timezone.now()
        ).values("starts_at", "skill__name", "activity"),
    })


@login_required
def offer_skills(request):
    if request.method == "POST":
        form = OfferSkillsForm(request.POST)
        if form.is_valid():
            request.user.offered_skills.set(form.cleaned_data["skills"])
            return redirect("polls:offer_skills")
    else:
        form = OfferSkillsForm(
            initial={"skills": request.user.offered_skills.all()}
        )

    return render(request, "polls/offer_skills.html", {"form": form})


class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        """Return the last five published questions."""
        return Question.objects.order_by("-pub_date")[:5]


class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"


class ResultsView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"


def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "You didn't select a choice.",
            },
        )
    else:
        selected_choice.votes = F("votes") + 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))


class AllView(generic.ListView):
    model = Question
    template_name = 'polls/all.html'


def frequency(request, question_id):
    question = Question.objects.get(id=question_id)
    choices = question.get_choices()

    return render(request, 'polls/frequency.html', {
        'question': question,
        'choices': choices,
    })

def statistics(request):
    nbr_sondages = Question.objects.count()
    nbr_choix = Choice.objects.count()
    nbr_votes = \
        Choice.objects.aggregate(somme=Sum('votes'))['somme']
    moyenne_par_sondage = nbr_votes / nbr_sondages
    (question_la_moins_populaire, question_la_plus_populaire) = \
        minimax()
    id_derniere_question = \
        Question.objects.aggregate(max=Max('id'))['max']
    derniere_question = \
        Question.objects.get(pk=id_derniere_question)

    return render(request, 'polls/statistics.html', {
        'nbr_sondages': nbr_sondages,
        'nbr_choix': nbr_choix,
        'nbr_votes': nbr_votes,
        'moyenne_par_sondage': moyenne_par_sondage,
        'question_la_plus_populaire': question_la_plus_populaire,
        'question_la_moins_populaire': question_la_moins_populaire,
        'derniere_question': derniere_question, })


def add(request):
     if request.method == 'POST':
        form = QuestionAddForm(request.POST)
        if form.is_valid():
            question = \
                Question(question_text=\
                    form.cleaned_data['question_text'],
                    pub_date=timezone.now())
            question.save()
            # on traite à présent les champs de choix remplis
            # (on s'arrête au premier vide)
            for no_choix in range(NB_MAX_CHOIX):
                nom_champ = 'choice_{}'.format(no_choix)
                choice_text = form.cleaned_data[nom_champ].strip()
                if choice_text:
                    choice = Choice(question=question,choice_text=choice_text)
                    choice.save()
                else:
                    break
                return render(request, 'polls/confirm_add.html')
        else:
            form: QuestionAddForm = QuestionAddForm()
     return render(request, 'polls/add.html', {'form': form})




