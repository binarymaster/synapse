# Copyright 2021 The Matrix.org Foundation C.I.C.
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

SCHEMA_VERSION = 65  # remember to update the list below when updating
"""Represents the expectations made by the codebase about the database schema

This should be incremented whenever the codebase changes its requirements on the
shape of the database schema (even if those requirements are backwards-compatible with
older versions of Synapse).

See https://matrix-org.github.io/synapse/develop/development/database_schema.html
for more information on how this works.

Changes in SCHEMA_VERSION = 61:
    - The `user_stats_historical` and `room_stats_historical` tables are not written and
      are not read (previously, they were written but not read).
    - MSC2716: Add `insertion_events` and `insertion_event_edges` tables to keep track
      of insertion events in order to navigate historical chunks of messages.
    - MSC2716: Add `chunk_events` table to track how the chunk is labeled and
      determines which insertion event it points to.

Changes in SCHEMA_VERSION = 62:
    - MSC2716: Add `insertion_event_extremities` table that keeps track of which
      insertion events need to be backfilled.

Changes in SCHEMA_VERSION = 63:
    - The `public_room_list_stream` table is not written nor read to
      (previously, it was written and read to, but not for any significant purpose).
      https://github.com/matrix-org/synapse/pull/10565

Changes in SCHEMA_VERSION = 64:
    - MSC2716: Rename related tables and columns from "chunks" to "batches".

Changes in SCHEMA_VERSION = 65:
    - MSC2716: Remove unique event_id constraint from insertion_event_edges
      because an insertion event can have multiple edges.
    - Remove unused tables `user_stats_historical` and `room_stats_historical`.
"""


SCHEMA_COMPAT_VERSION = (
    61  # 61: Remove unused tables `user_stats_historical` and `room_stats_historical`
)
"""Limit on how far the synapse codebase can be rolled back without breaking db compat

This value is stored in the database, and checked on startup. If the value in the
database is greater than SCHEMA_VERSION, then Synapse will refuse to start.
"""
