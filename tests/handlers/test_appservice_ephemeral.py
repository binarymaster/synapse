# Copyright 2019 The Matrix.org Foundation C.I.C.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Dict, Iterable, Optional, Tuple, Union
from unittest.mock import Mock

import synapse.rest.admin
import synapse.storage
from synapse.appservice import ApplicationService
from synapse.rest.client import login, receipts, room
from synapse.util.stringutils import random_string

from tests import unittest


class ApplicationServiceEphemeralEventsTestCase(unittest.HomeserverTestCase):
    servlets = [
        synapse.rest.admin.register_servlets_for_client_rest_resource,
        login.register_servlets,
        room.register_servlets,
        receipts.register_servlets,
    ]

    def prepare(self, reactor, clock, hs):
        # Mock the application service scheduler so that we can track any outgoing transactions
        self.mock_scheduler = Mock()

        hs.get_application_service_handler().scheduler = self.mock_scheduler

        self.user1 = self.register_user("user1", "password")
        self.token1 = self.login("user1", "password")

        self.user2 = self.register_user("user2", "password")
        self.token2 = self.login("user2", "password")

    def test_application_services_receive_read_receipts(self):
        """
        Test that when an application service sends a read receipt in a room with
        another user, and that is in an application service's user namespace, that
        application service will receive that read receipt.
        """
        (
            interested_service,
            _,
        ) = self._register_interested_and_uninterested_application_services()

        # Create a room with both user1 and user2
        room_id = self.helper.create_room_as(
            self.user1, tok=self.token1, is_public=True
        )
        self.helper.join(room_id, self.user2, tok=self.token2)

        # Have user2 send a message into the room
        response_dict = self.helper.send(room_id, body="read me", tok=self.token2)

        # Have user1 send a read receipt for the message with an empty body
        channel = self.make_request(
            "POST",
            "/rooms/%s/receipt/m.read/%s" % (room_id, response_dict["event_id"]),
            access_token=self.token1,
        )
        self.assertEqual(channel.code, 200)

        # user2 should have been the recipient of that read receipt.
        # Check if our application service - that is interested in user2 - received
        # the read receipt as part of an AS transaction.
        #
        # The uninterested application service should not have been notified.
        service, events = self.mock_scheduler.submit_ephemeral_events_for_as.call_args[
            0
        ]
        self.assertEqual(service, interested_service)
        self.assertEqual(events[0]["type"], "m.receipt")
        self.assertEqual(events[0]["room_id"], room_id)

        # Assert that this was a read receipt from user1
        read_receipts = list(events[0]["content"].values())
        self.assertIn(self.user1, read_receipts[0]["m.read"])

    def _register_interested_and_uninterested_application_services(
        self,
    ) -> Tuple[ApplicationService, ApplicationService]:
        # Create an application service with exclusive interest in user2
        interested_service = self._make_application_service(
            namespaces={
                ApplicationService.NS_USERS: [
                    {
                        "regex": "@user2:.+",
                        "exclusive": True,
                    }
                ],
            },
        )
        uninterested_service = self._make_application_service()

        # Register this application service, along with another, uninterested one
        services = [
            uninterested_service,
            interested_service,
        ]
        self.hs.get_datastore().get_app_services = Mock(return_value=services)

        return interested_service, uninterested_service

    def _make_application_service(
        self,
        namespaces: Optional[
            Dict[
                Union[
                    ApplicationService.NS_USERS,
                    ApplicationService.NS_ALIASES,
                    ApplicationService.NS_ROOMS,
                ],
                Iterable[Dict],
            ]
        ] = None,
        supports_ephemeral: Optional[bool] = True,
    ) -> ApplicationService:
        return ApplicationService(
            token=None,
            hostname="example.com",
            id=random_string(10),
            sender="@as:example.com",
            rate_limited=False,
            namespaces=namespaces,
            supports_ephemeral=supports_ephemeral,
        )

    # TODO: Test that ephemeral messages aren't sent to application services that have
    #  ephemeral: false
