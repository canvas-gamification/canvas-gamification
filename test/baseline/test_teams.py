"""Baseline tests for the canvas team lifecycle.

Covers ``canvas/services/team.py`` (create-and-join, join failures with our own
``PermissionDenied`` messages, ``get_my_team`` auto-creation and
delete-on-last-member) plus the ``/api/team/`` endpoints that wrap them.

The ``PermissionDenied`` strings asserted here come from
``api/error_messages/team.py`` — they are *our* messages, not framework
internals, so pinning them is intentional.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APITestCase

import api.error_messages as ERROR_MESSAGES
from canvas.models.models import CanvasCourseRegistration
from canvas.models.team import Team
from canvas.services.team import create_and_join_team, get_my_team, join_team, leave_team
from test.baseline import fixtures_canvas as fx


class TeamServiceTests(TestCase):
    """canvas/services/team.py:12-65"""

    def setUp(self):
        super().setUp()
        self.category = fx.make_category()
        self.course = fx.make_course()
        self.event = fx.make_event(self.course, name="event", max_team_size=2)
        self.alice = fx.make_user("alice", nickname="Alice")
        self.bob = fx.make_user("bob", nickname="Bob")
        self.alice_reg = fx.make_registration(self.alice, self.course)
        self.bob_reg = fx.make_registration(self.bob, self.course)

    # ------------------------------------------------------------------
    # create_and_join_team
    # ------------------------------------------------------------------
    def test_create_and_join_team_with_an_explicit_name(self):
        team = create_and_join_team(self.event, self.alice, "Rockets")

        self.assertEqual(team.name, "Rockets")
        self.assertEqual(team.event, self.event)
        self.assertFalse(team.is_private)
        self.assertEqual(list(team.course_registrations.all()), [self.alice_reg])
        self.assertEqual(Team.objects.count(), 1)

    def test_create_and_join_team_defaults_the_name_to_the_nickname(self):
        team = create_and_join_team(self.event, self.alice, None)
        self.assertEqual(team.name, "Alice's Team")

    def test_create_and_join_team_accepts_is_private_and_who_can_join(self):
        team = create_and_join_team(self.event, self.alice, "Private", is_private=True, who_can_join=[self.bob_reg.id])

        self.assertTrue(team.is_private)
        self.assertEqual(list(team.who_can_join.all()), [self.bob_reg])

    def test_create_and_join_team_leaves_and_deletes_the_previous_solo_team(self):
        first = create_and_join_team(self.event, self.alice, "First")
        second = create_and_join_team(self.event, self.alice, "Second")

        self.assertFalse(Team.objects.filter(pk=first.pk).exists())
        self.assertEqual(list(Team.objects.values_list("name", flat=True)), ["Second"])
        self.assertEqual(list(second.course_registrations.all()), [self.alice_reg])

    def test_create_and_join_team_keeps_a_shared_previous_team_alive(self):
        shared = create_and_join_team(self.event, self.alice, "Shared")
        join_team(shared, self.bob)

        create_and_join_team(self.event, self.bob, "Bobs own")

        shared.refresh_from_db()
        self.assertEqual(list(shared.course_registrations.all()), [self.alice_reg])
        self.assertEqual(Team.objects.count(), 2)

    def test_create_and_join_team_does_not_require_a_verified_registration(self):
        # KNOWN-BUG: unlike join_team, create_and_join_team performs no
        # registration check at all — an unregistered user can create a team
        # (and get an UNREGISTERED registration row created as a side effect).
        stranger = fx.make_user("stranger", nickname="Stranger")
        self.assertFalse(CanvasCourseRegistration.objects.filter(user=stranger).exists())

        team = create_and_join_team(self.event, stranger, None)

        self.assertEqual(team.name, "Stranger's Team")
        reg = CanvasCourseRegistration.objects.get(user=stranger, course=self.course)
        self.assertEqual(reg.status, "UNREGISTERED")

    def test_teams_are_scoped_to_their_event(self):
        other_event = fx.make_event(self.course, name="other")
        team_a = create_and_join_team(self.event, self.alice, "A")
        team_b = create_and_join_team(other_event, self.alice, "B")

        # joining a team in another event does not disband the first
        self.assertTrue(Team.objects.filter(pk=team_a.pk).exists())
        self.assertTrue(Team.objects.filter(pk=team_b.pk).exists())

    # ------------------------------------------------------------------
    # join_team
    # ------------------------------------------------------------------
    def test_join_team_success(self):
        team = create_and_join_team(self.event, self.alice, "Rockets")
        join_team(team, self.bob)

        self.assertEqual(
            set(team.course_registrations.values_list("id", flat=True)),
            {self.alice_reg.id, self.bob_reg.id},
        )

    def test_join_team_requires_a_verified_registration(self):
        team = create_and_join_team(self.event, self.alice, "Rockets")
        stranger = fx.make_user("stranger")

        with self.assertRaises(PermissionDenied) as ctx:
            join_team(team, stranger)

        self.assertEqual(str(ctx.exception.detail), ERROR_MESSAGES.TEAM.NOT_REGISTERED)
        self.assertEqual(str(ctx.exception.detail), "Cannot join a team without registering in the course.")
        self.assertEqual(team.course_registrations.count(), 1)

    def test_join_team_rejects_a_private_team(self):
        team = create_and_join_team(self.event, self.alice, "Rockets", is_private=True)

        with self.assertRaises(PermissionDenied) as ctx:
            join_team(team, self.bob)

        self.assertEqual(str(ctx.exception.detail), ERROR_MESSAGES.TEAM.PRIVATE)
        self.assertEqual(str(ctx.exception.detail), "Cannot join this team.")

    def test_join_team_allows_a_whitelisted_member_of_a_private_team(self):
        team = create_and_join_team(self.event, self.alice, "Rockets", is_private=True, who_can_join=[self.bob_reg.id])
        join_team(team, self.bob)

        self.assertEqual(team.course_registrations.count(), 2)

    def test_join_team_rejects_a_full_team(self):
        small_event = fx.make_event(self.course, name="small", max_team_size=1)
        team = create_and_join_team(small_event, self.alice, "Solo")

        with self.assertRaises(PermissionDenied) as ctx:
            join_team(team, self.bob)

        self.assertEqual(str(ctx.exception.detail), ERROR_MESSAGES.TEAM.FULL)
        self.assertEqual(str(ctx.exception.detail), "This team is full.")
        self.assertEqual(team.course_registrations.count(), 1)

    def test_join_team_leaves_the_previous_team_first(self):
        old = create_and_join_team(self.event, self.bob, "Bobs")
        target = create_and_join_team(self.event, self.alice, "Rockets")

        join_team(target, self.bob)

        self.assertFalse(Team.objects.filter(pk=old.pk).exists())
        self.assertEqual(target.course_registrations.count(), 2)

    # ------------------------------------------------------------------
    # get_my_team / leave_team
    # ------------------------------------------------------------------
    def test_get_my_team_creates_a_team_when_none_exists(self):
        self.assertEqual(Team.objects.count(), 0)

        team = get_my_team(self.event, self.alice)

        self.assertEqual(Team.objects.count(), 1)
        self.assertEqual(team.name, "Alice's Team")

    def test_get_my_team_is_idempotent(self):
        first = get_my_team(self.event, self.alice)
        second = get_my_team(self.event, self.alice)

        self.assertEqual(first.pk, second.pk)
        self.assertEqual(Team.objects.count(), 1)

    def test_leave_team_of_a_user_without_a_team_is_a_noop(self):
        leave_team(self.event, self.alice)
        self.assertEqual(Team.objects.count(), 0)

    def test_leave_team_removes_only_the_member_when_others_remain(self):
        team = create_and_join_team(self.event, self.alice, "Rockets")
        join_team(team, self.bob)

        leave_team(self.event, self.bob)

        self.assertTrue(Team.objects.filter(pk=team.pk).exists())
        self.assertEqual(list(team.course_registrations.all()), [self.alice_reg])


class TeamTokenCascadeTests(TestCase):
    """Deleting the last-member team removes its token contribution."""

    def setUp(self):
        super().setUp()
        self.category = fx.make_category()
        self.course = fx.make_course()
        # an ended, token-counting event so total_tokens_received sees it
        self.event = fx.make_event(
            self.course,
            name="ended-challenge",
            type="CHALLENGE",
            count_for_tokens=True,
            start_offset=-10,
            end_offset=-1,
            max_team_size=2,
        )
        self.question = fx.make_question(self.category, title="q1", event=self.event)
        self.alice = fx.make_user("alice", nickname="Alice")
        self.bob = fx.make_user("bob", nickname="Bob")
        self.alice_reg = fx.make_registration(self.alice, self.course)
        self.bob_reg = fx.make_registration(self.bob, self.course)
        fx.set_uqj(self.alice, self.question, tokens_received=5.0)
        fx.set_uqj(self.bob, self.question, tokens_received=3.0)

    def test_team_tokens_received_property_delegates_to_the_event(self):
        team = create_and_join_team(self.event, self.alice, "Rockets")
        self.assertEqual(team.tokens_received, 5.0)
        self.assertEqual(team.tokens_received, self.event.tokens_received(team))

    def test_deleting_the_team_on_last_leave_removes_the_token_contribution(self):
        team = create_and_join_team(self.event, self.alice, "Rockets")
        self.assertEqual(self.alice_reg.total_tokens_received, 5.0)

        leave_team(self.event, self.alice)

        self.assertFalse(Team.objects.filter(pk=team.pk).exists())
        self.assertEqual(self.alice_reg.total_tokens_received, 0)

    def test_remaining_member_keeps_the_best_of_team_score(self):
        team = create_and_join_team(self.event, self.alice, "Rockets")
        join_team(team, self.bob)

        # best of the team is Alice's 5.0 for both members
        self.assertEqual(self.alice_reg.total_tokens_received, 5.0)
        self.assertEqual(self.bob_reg.total_tokens_received, 5.0)

        leave_team(self.event, self.alice)

        self.assertTrue(Team.objects.filter(pk=team.pk).exists())
        self.assertEqual(self.bob_reg.total_tokens_received, 3.0)
        self.assertEqual(self.alice_reg.total_tokens_received, 0)

    def test_member_names_uses_nicknames_only_for_complete_profiles(self):
        named = fx.make_user("named", nickname="Named", first_name="Real")
        named_reg = fx.make_registration(named, self.course)
        team = fx.make_team(self.event, "Mixed", [self.alice_reg, named_reg])

        # Alice has no first_name -> has_complete_profile is False
        self.assertEqual(sorted(team.member_names), sorted(["Anonymous User", "Named"]))


class TeamEndpointTests(APITestCase):
    """TeamViewSet (api/views/team.py:16-55)"""

    TEAM_FIELDS = {
        "id",
        "time_created",
        "time_modified",
        "name",
        "is_private",
        "who_can_join",
        "event",
        "course_registrations",
        "tokens_received",
        "member_names",
    }

    def setUp(self):
        super().setUp()
        self.category = fx.make_category()
        self.course = fx.make_course()
        self.event = fx.make_event(self.course, name="event", max_team_size=2)
        self.alice = fx.make_user("alice", nickname="Alice")
        self.bob = fx.make_user("bob", nickname="Bob")
        self.alice_reg = fx.make_registration(self.alice, self.course)
        self.bob_reg = fx.make_registration(self.bob, self.course)

    def test_create_and_join_endpoint(self):
        self.client.force_authenticate(user=self.alice)

        response = self.client.post(
            reverse("api:team-create-and-join"),
            {"event_id": self.event.pk, "name": "Rockets", "is_private": False},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data.keys()), self.TEAM_FIELDS)
        self.assertEqual(response.data["name"], "Rockets")
        self.assertEqual(response.data["member_names"], ["Anonymous User"])
        self.assertEqual(Team.objects.count(), 1)

    def test_create_and_join_endpoint_with_unknown_event_is_404(self):
        self.client.force_authenticate(user=self.alice)
        response = self.client.post(
            reverse("api:team-create-and-join"), {"event_id": 999999, "name": "x"}, format="json"
        )
        self.assertEqual(response.status_code, 404)

    def test_join_endpoint_returns_status_success(self):
        team = create_and_join_team(self.event, self.alice, "Rockets")
        self.client.force_authenticate(user=self.bob)

        response = self.client.post(reverse("api:team-join"), {"team_id": team.pk}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"status": "success"})
        self.assertEqual(team.course_registrations.count(), 2)

    def test_join_endpoint_surfaces_our_permission_messages(self):
        team = create_and_join_team(self.event, self.alice, "Rockets", is_private=True)
        self.client.force_authenticate(user=self.bob)

        response = self.client.post(reverse("api:team-join"), {"team_id": team.pk}, format="json")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(str(response.data["detail"]), ERROR_MESSAGES.TEAM.PRIVATE)
        self.assertEqual(team.course_registrations.count(), 1)

    def test_join_endpoint_for_an_unregistered_user(self):
        team = create_and_join_team(self.event, self.alice, "Rockets")
        stranger = fx.make_user("stranger")
        self.client.force_authenticate(user=stranger)

        response = self.client.post(reverse("api:team-join"), {"team_id": team.pk}, format="json")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(str(response.data["detail"]), ERROR_MESSAGES.TEAM.NOT_REGISTERED)

    def test_my_team_endpoint_creates_a_team(self):
        self.client.force_authenticate(user=self.alice)
        self.assertEqual(Team.objects.count(), 0)

        response = self.client.get(reverse("api:team-my-team"), {"event_id": self.event.pk})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Team.objects.count(), 1)
        self.assertEqual(response.data["name"], "Alice's Team")
        self.assertEqual(set(response.data.keys()), self.TEAM_FIELDS)

        # a second call reuses the same team
        again = self.client.get(reverse("api:team-my-team"), {"event_id": self.event.pk})
        self.assertEqual(again.data["id"], response.data["id"])
        self.assertEqual(Team.objects.count(), 1)

    def test_team_list_is_filterable_by_event(self):
        create_and_join_team(self.event, self.alice, "Rockets")
        other_event = fx.make_event(self.course, name="other")
        create_and_join_team(other_event, self.bob, "Others")
        self.client.force_authenticate(user=self.alice)

        response = self.client.get(reverse("api:team-list"), {"event": self.event.pk})

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["name"] for item in response.data], ["Rockets"])

    def test_team_detail_requires_membership(self):
        # TeamPermission.has_object_permission requires the requesting user to
        # be a member (has_permission is hardcoded True — see api/permissions.py:365).
        team = create_and_join_team(self.event, self.alice, "Rockets")
        url = reverse("api:team-detail", kwargs={"pk": team.pk})

        self.client.force_authenticate(user=self.bob)
        self.assertEqual(self.client.get(url).status_code, 403)

        self.client.force_authenticate(user=self.alice)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_team_list_is_readable_by_anonymous_users(self):
        # KNOWN-BUG: TeamPermission.has_permission is hardcoded to True, so the
        # unauthenticated list endpoint is public.
        create_and_join_team(self.event, self.alice, "Rockets")

        response = self.client.get(reverse("api:team-list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["name"] for item in response.data], ["Rockets"])
