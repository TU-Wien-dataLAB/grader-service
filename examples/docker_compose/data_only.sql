INSERT INTO "user" ("name", "encrypted_auth_state", "cookie_id", "display_name")
VALUES
    ('admin', NULL, 'b3c349f83ef94143b644221523e04ca2', 'admin'),
    ('instructor', NULL, '3b80476d54ef49848f1dd00b436e9380', 'instructor'),
    ('student', NULL, '935f9b72143f40459ad7f5e32a94a4c1', 'student'),
    ('tutor', NULL, '77f888fee7f84bfbba6b226fce292115', 'tutor'),
    ('user1', NULL, '393ced73010a47a198edc44609c0d1b6', 'user1');
INSERT INTO lecture ("name", "code", "state", "deleted", "created_at", "updated_at")
VALUES
    ('lect1', 'lect1', 'active', 'active', '2025-04-15 11:58:36.963401', '2025-04-15 11:58:36.963405'),
    ('lect2', 'lect2', 'complete', 'active', '2024-10-02 09:13:53.829556', '2025-03-01 11:58:36.963405');
INSERT INTO "assignment" ("name", "lectid", "points", "status", "deleted", "properties", "created_at", "updated_at", "settings")
VALUES ('Currency Conversion', 1, 5, 'released', 'active',
        '{"notebooks": {"convert_dollar": {"id": "convert_dollar", "name": "convert_dollar", "flagged": false, "kernelspec": "{\"display_name\": \"Python 3 (ipykernel)\", \"language\": \"python\", \"name\": \"python3\"}", "grade_cells_dict": {"cell-6b8b46445e701ed6": {"max_score": 1.0, "cell_type": "code", "notebook_id": null, "name": "cell-6b8b46445e701ed6", "id": null, "grade_id": null, "comment_id": null, "_type": "GradeCell"}, "cell-cc740884dba75f9d": {"max_score": 4.0, "cell_type": "code", "notebook_id": null, "name": "cell-cc740884dba75f9d", "id": null, "grade_id": null, "comment_id": null, "_type": "GradeCell"}}, "solution_cells_dict": {"cell-b830f4cea076409b": {"notebook_id": null, "name": "cell-b830f4cea076409b", "id": null, "grade_id": null, "comment_id": null, "_type": "SolutionCell"}}, "task_cells_dict": {}, "source_cells_dict": {"cell-0a18dfa4b887faf3": {"notebook_id": null, "name": "cell-0a18dfa4b887faf3", "id": null, "cell_type": "markdown", "locked": true, "source": "# Currency Conversion Assignment", "checksum": "44ff1a9784ca989b71235092c135c1d8", "_type": "SourceCell"}, "cell-b830f4cea076409b": {"notebook_id": null, "name": "cell-b830f4cea076409b", "id": null, "cell_type": "code", "locked": false, "source": "# YOUR CODE HERE\nraise NotImplementedError()", "checksum": "5c575adfbb0bd8c9f2ca4391076a32bb", "_type": "SourceCell"}, "cell-6b8b46445e701ed6": {"notebook_id": null, "name": "cell-6b8b46445e701ed6", "id": null, "cell_type": "code", "locked": true, "source": "eur, gbp = convert_dollar(5)\nassert eur == 4.6548194\nassert gbp == 4.0059821499999995", "checksum": "50f93537e80cd52a8e32c3fb884e2887", "_type": "SourceCell"}, "cell-cc740884dba75f9d": {"notebook_id": null, "name": "cell-cc740884dba75f9d", "id": null, "cell_type": "code", "locked": true, "source": "assert convert_dollar(20) == (18.6192776, 16.023928599999998)\n### BEGIN HIDDEN TESTS\nassert convert_dollar(1923810) == (1790997.6219827998, 1541349.7039983)\nassert convert_dollar(0) == (0.0, 0.0)\nassert convert_dollar(999) == (930.03291612, 800.39523357)\n### END HIDDEN TESTS", "checksum": "a3bd87367c79c1a0b2015260b7b59357", "_type": "SourceCell"}}, "grades_dict": {}, "comments_dict": {}, "_type": "Notebook"}}, "extra_files": ["CurrencyConversion.md"], "_type": "GradeBookModel", "schema_version": "1"}',
        '2025-10-30 17:20:35.317757', '2025-10-30 17:30:46.101408',
        '{"deadline": "2059-06-03T23:00:00+00:00", "max_submissions": null, "allowed_files": [], "late_submission": null, "autograde_type": "auto"}');
INSERT INTO takepart ("lectid", "role", "user_id") VALUES(1,'instructor',1);
INSERT INTO takepart ("lectid", "role", "user_id") VALUES(1,'instructor',2);
INSERT INTO takepart ("lectid", "role", "user_id") VALUES(1,'student',3);
INSERT INTO takepart ("lectid", "role", "user_id") VALUES(1,'tutor',4);
INSERT INTO takepart ("lectid", "role", "user_id") VALUES(2,'student',1);
