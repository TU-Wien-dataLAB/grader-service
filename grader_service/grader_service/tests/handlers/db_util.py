# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import secrets
from datetime import datetime


def insert_users(session):
    session.execute('INSERT INTO "user" ("name") VALUES ("user1")')
    session.execute('INSERT INTO "user" ("name") VALUES ("user2")')
    session.execute('INSERT INTO "user" ("name") VALUES ("user3")')
    session.execute('INSERT INTO "user" ("name") VALUES ("user4")')


def insert_lectures(session):
    session.execute('INSERT INTO "lecture" ("name","code", "state", "deleted") VALUES ("lecture1","21wle1","active","active")')
    session.execute('INSERT INTO "lecture" ("name","code", "state", "deleted") VALUES ("lecture1","21sle1","active","active")')
    session.execute('INSERT INTO "lecture" ("name","code", "state", "deleted") VALUES ("lecture2","20wle2","active","active")')
    session.execute('INSERT INTO "lecture" ("name","code", "state", "deleted") VALUES ("lecture3","22sle3","active","active")')
    session.execute('INSERT INTO "lecture" ("name","code", "state", "deleted") VALUES ("lecture4","21sle4","active","active")')


def insert_assignments(ex, lecture_id=1):
    ex.execute(
        f'INSERT INTO "assignment" ("name","lectid","duedate","points","status","automatic_grading", "allow_files") VALUES ("assignment_1",{lecture_id},"2055-06-06 23:59:00.000",20,"released","unassisted", 0)')
    ex.execute(
        f'INSERT INTO "assignment" ("name","lectid","duedate","points","status","automatic_grading", "allow_files") VALUES ("assignment_2",{lecture_id},"2055-07-07 23:59:00.000",10,"created","unassisted", 0)')
    num_inserts = 2
    return num_inserts


def insert_submission(ex, assignment_id=1, username="ubuntu"):
    ex.execute(
        f'INSERT INTO "submission" ("date","auto_status","manual_status","assignid","username","commit_hash","feedback_available") VALUES ("{datetime.now().isoformat(" ", "milliseconds")}","not_graded","not_graded",{assignment_id},"{username}", "{secrets.token_hex(20)}",0)')


def insert_take_part(ex, lecture_id, username="ubuntu", role="student"):
    ex.execute(f'INSERT INTO "takepart" ("username","lectid","role") VALUES ("{username}",{lecture_id},"{role}")')


def insert_grading(session):
    pass

