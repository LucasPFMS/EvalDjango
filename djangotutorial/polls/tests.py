from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
import datetime

from .models import HelpSlot, Skill


class PublicIndexTests(TestCase):
    def test_lists_skills_and_future_slots_without_user_names(self):
        skill = Skill.objects.create(name="Jardinage")
        helper = get_user_model().objects.create_user(username="helper-private")
        recipient = get_user_model().objects.create_user(
            username="recipient-private"
        )
        HelpSlot.objects.create(
            helper=helper,
            recipient=recipient,
            skill=skill,
            activity="Tailler une haie",
            starts_at=timezone.now() + datetime.timedelta(days=1),
        )
        HelpSlot.objects.create(
            helper=helper,
            recipient=recipient,
            skill=skill,
            activity="Ancien créneau",
            starts_at=timezone.now() - datetime.timedelta(days=1),
        )

        response = self.client.get(reverse("home"))

        self.assertContains(response, "Jardinage")
        self.assertContains(response, "Tailler une haie")
        self.assertNotContains(response, "Ancien créneau")
        self.assertNotContains(response, "helper-private")
        self.assertNotContains(response, "recipient-private")


class OfferedSkillsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="member")
        self.skill = Skill.objects.create(name="Cuisine")

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse("polls:offer_skills"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('polls:offer_skills')}",
        )

    def test_logged_in_user_can_select_offered_skills(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("polls:offer_skills"),
            {"skills": [self.skill.pk]},
        )

        self.assertRedirects(response, reverse("polls:offer_skills"))
        self.assertQuerySetEqual(
            self.user.offered_skills.all(),
            [self.skill],
        )
