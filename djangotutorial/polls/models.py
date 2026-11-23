import datetime
from django.contrib import admin
from django.conf import settings
from django.db import models
from django.utils import timezone


class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published")

    def __repr__(self):
        return "<Question: {}>".format(self.question_text)

    def __str__(self):
        return self.question_text

    @admin.display(
        boolean=True,
        ordering="pub_date",
        description="Published recently?",)

    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.choice_text


def get_choices(self):
    total = 0
    choices = self.choice_set.all()
    for c in choices:
        total += c.votes
    return [(c.choice_text, c.votes, c.votes / total) for c in choices]


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    offered_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="offered_skills",
        blank=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class HelpSlot(models.Model):
    helper = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="help_slots_given",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="help_slots_received",
    )
    skill = models.ForeignKey(Skill, on_delete=models.PROTECT)
    activity = models.CharField(max_length=255)
    starts_at = models.DateTimeField()

    class Meta:
        ordering = ["starts_at"]

    def __str__(self):
        return f"{self.skill} - {self.starts_at:%d/%m/%Y %H:%M}"