from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
import datetime

from .models import HelpRequest, HelpSlot, Skill


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


class HelpRequestTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="requester")
        self.owned_skill = Skill.objects.create(name="Cuisine")
        self.missing_skill = Skill.objects.create(name="Bricolage")
        self.user.offered_skills.add(self.owned_skill)
        self.client.force_login(self.user)

    def test_anonymous_user_is_redirected_to_login(self):
        self.client.logout()

        response = self.client.get(reverse("polls:create_help_request"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('polls:create_help_request')}",
        )

    def test_user_can_request_a_future_slot_for_a_missing_skill(self):
        response = self.client.get(reverse("polls:create_help_request"))

        self.assertContains(response, "Bricolage")
        self.assertNotContains(response, "Cuisine")

        starts_at = (timezone.now() + datetime.timedelta(days=1)).replace(
            second=0,
            microsecond=0,
        )
        response = self.client.post(
            reverse("polls:create_help_request"),
            {
                "activity": "Monter une étagère dans le salon",
                "skill": self.missing_skill.pk,
                "starts_at": starts_at.strftime("%Y-%m-%dT%H:%M"),
            },
        )

        self.assertRedirects(response, reverse("polls:create_help_request"))
        help_request = HelpRequest.objects.get()
        self.assertEqual(help_request.requester, self.user)
        self.assertEqual(help_request.skill, self.missing_skill)
        self.assertEqual(help_request.activity, "Monter une étagère dans le salon")

    def test_user_cannot_request_a_skill_they_offer(self):
        response = self.client.post(
            reverse("polls:create_help_request"),
            {
                "activity": "Préparer un repas",
                "skill": self.owned_skill.pk,
                "starts_at": (
                    timezone.now() + datetime.timedelta(days=1)
                ).strftime("%Y-%m-%dT%H:%M"),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(HelpRequest.objects.count(), 0)

    def test_user_cannot_request_a_past_slot(self):
        response = self.client.post(
            reverse("polls:create_help_request"),
            {
                "activity": "Monter une étagère",
                "skill": self.missing_skill.pk,
                "starts_at": (
                    timezone.now() - datetime.timedelta(days=1)
                ).strftime("%Y-%m-%dT%H:%M"),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(HelpRequest.objects.count(), 0)


class AvailableHelpRequestTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.requester = user_model.objects.create_user(username="requester")
        self.skilled_requester = user_model.objects.create_user(
            username="skilled-requester"
        )
        self.helper = user_model.objects.create_user(username="helper")
        self.other_helper = user_model.objects.create_user(
            username="other-helper"
        )
        self.skill = Skill.objects.create(name="Bricolage")
        self.other_skill = Skill.objects.create(name="Cuisine")
        self.skill.offered_by.add(self.helper, self.other_helper)
        self.client.force_login(self.helper)

    def make_request(
        self,
        requester=None,
        skill=None,
        starts_at=None,
        claimed_by=None,
        activity="Demande compatible",
    ):
        return HelpRequest.objects.create(
            requester=requester or self.requester,
            skill=skill or self.skill,
            starts_at=starts_at or timezone.now() + datetime.timedelta(days=1),
            claimed_by=claimed_by,
            activity=activity,
        )

    def test_only_future_unclaimed_compatible_requests_are_listed(self):
        self.make_request(activity="À afficher")
        self.make_request(
            skill=self.other_skill,
            activity="Mauvaise compétence",
        )
        self.make_request(
            requester=self.helper,
            activity="Ma propre demande",
        )
        self.make_request(
            starts_at=timezone.now() - datetime.timedelta(days=1),
            activity="Demande passée",
        )
        self.make_request(
            claimed_by=self.other_helper,
            activity="Déjà prise",
        )
        self.skilled_requester.offered_skills.add(self.skill)
        self.make_request(
            requester=self.skilled_requester,
            activity="Demandeur possède déjà la compétence",
        )

        response = self.client.get(reverse("polls:available_help_requests"))

        self.assertContains(response, "À afficher")
        self.assertNotContains(response, "Mauvaise compétence")
        self.assertNotContains(response, "Ma propre demande")
        self.assertNotContains(response, "Demande passée")
        self.assertNotContains(response, "Déjà prise")
        self.assertNotContains(response, "Demandeur possède déjà la compétence")
        self.assertNotContains(response, "requester")

    def test_claimed_request_disappears_for_all_other_helpers(self):
        help_request = self.make_request()

        response = self.client.post(
            reverse("polls:offer_help", args=[help_request.pk]),
            follow=True,
        )

        self.assertRedirects(response, reverse("polls:available_help_requests"))
        help_request.refresh_from_db()
        self.assertEqual(help_request.claimed_by, self.helper)
        public_response = self.client.get(reverse("home"))
        self.assertContains(public_response, "Demande compatible")
        self.assertNotContains(public_response, "requester")
        self.assertNotContains(public_response, "helper")
        self.assertContains(
            self.client.get(reverse("polls:available_help_requests")),
            "Aucune demande à venir",
        )

        self.client.force_login(self.other_helper)
        self.assertContains(
            self.client.get(reverse("polls:available_help_requests")),
            "Aucune demande à venir",
        )
        response = self.client.post(
            reverse("polls:offer_help", args=[help_request.pk]),
            follow=True,
        )
        help_request.refresh_from_db()
        self.assertEqual(help_request.claimed_by, self.helper)
        self.assertContains(response, "Ce créneau")

    def test_anonymous_user_cannot_view_compatible_requests(self):
        self.client.logout()

        response = self.client.get(reverse("polls:available_help_requests"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('polls:available_help_requests')}",
        )
