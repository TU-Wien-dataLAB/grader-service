INSERT INTO "user" VALUES('admin',NULL,'b3c349f83ef94143b644221523e04ca2','admin',1);
INSERT INTO "user" VALUES('instructor',NULL,'3b80476d54ef49848f1dd00b436e9380','instructor',2);
INSERT INTO "user" VALUES('student',NULL,'935f9b72143f40459ad7f5e32a94a4c1','student',3);
INSERT INTO "user" VALUES('tutor',NULL,'77f888fee7f84bfbba6b226fce292115','tutor',4);
INSERT INTO "user" VALUES('user1',NULL,'393ced73010a47a198edc44609c0d1b6','user1',5);
INSERT INTO lecture VALUES(1,'lect1','lect1','active','active','2025-04-15 11:58:36.963401','2025-04-15 11:58:36.963405');
INSERT INTO lecture VALUES(2,'lecture1','lecture1','active','active','2025-05-08 13:15:46.405114','2025-05-08 13:15:46.405118');
INSERT INTO assignment VALUES(1,'Assignment',1,1,'pushed','deleted','{"notebooks": {"sum_numbers": {"id": "sum_numbers", "name": "sum_numbers", "flagged": false, "kernelspec": "{\"display_name\": \"Python 3 (ipykernel)\", \"language\": \"python\", \"name\": \"python3\"}", "grade_cells_dict": {"cell-1e1d884e2e83e97f": {"max_score": 1.0, "cell_type": "code", "notebook_id": null, "name": "cell-1e1d884e2e83e97f", "id": null, "grade_id": null, "comment_id": null, "_type": "GradeCell"}}, "solution_cells_dict": {"cell-ec1c0a6598d73f81": {"notebook_id": null, "name": "cell-ec1c0a6598d73f81", "id": null, "grade_id": null, "comment_id": null, "_type": "SolutionCell"}}, "task_cells_dict": {}, "source_cells_dict": {"cell-ec1c0a6598d73f81": {"notebook_id": null, "name": "cell-ec1c0a6598d73f81", "id": null, "cell_type": "code", "locked": false, "source": "\ndef sum_numbers(num):\n    # YOUR CODE HERE\n    raise NotImplementedError()\n", "checksum": "3abfdaf7b8b9569fc58d25d6471d4cbd", "_type": "SourceCell"}, "cell-1e1d884e2e83e97f": {"notebook_id": null, "name": "cell-1e1d884e2e83e97f", "id": null, "cell_type": "code", "locked": true, "source": "assert sum_numbers(1) == 1\nassert sum_numbers(2) == 3\nassert sum_numbers(5) == 15", "checksum": "6453ffdd62ea1a1eabcf95616174dd88", "_type": "SourceCell"}}, "grades_dict": {}, "comments_dict": {}, "_type": "Notebook"}}, "extra_files": ["title.md"], "_type": "GradeBookModel", "schema_version": "1"}','2025-04-15 13:09:04.651575','2025-06-03 12:20:17.821961','{"deadline": "2025-04-17T12:10:18.317000+00:00", "max_submissions": null, "allowed_files": [], "late_submission": null, "autograde_type": "auto"}');
INSERT INTO assignment VALUES(2,'Assignment 2',1,2,'pushed','deleted','{"notebooks": {"add_numbers": {"id": "add_numbers", "name": "add_numbers", "flagged": false, "kernelspec": "{\"display_name\": \"Python 3 (ipykernel)\", \"language\": \"python\", \"name\": \"python3\"}", "grade_cells_dict": {"cell-3df764e6d829e6ef": {"max_score": 2.0, "cell_type": "code", "notebook_id": null, "name": "cell-3df764e6d829e6ef", "id": null, "grade_id": null, "comment_id": null, "_type": "GradeCell"}}, "solution_cells_dict": {"cell-7d6a4f3241ca6383": {"notebook_id": null, "name": "cell-7d6a4f3241ca6383", "id": null, "grade_id": null, "comment_id": null, "_type": "SolutionCell"}}, "task_cells_dict": {}, "source_cells_dict": {"cell-7d6a4f3241ca6383": {"notebook_id": null, "name": "cell-7d6a4f3241ca6383", "id": null, "cell_type": "code", "locked": false, "source": "# YOUR CODE HERE\nraise NotImplementedError()", "checksum": "bb2a9f9fb0716b1f5a0ca91a1720f598", "_type": "SourceCell"}, "cell-3df764e6d829e6ef": {"notebook_id": null, "name": "cell-3df764e6d829e6ef", "id": null, "cell_type": "code", "locked": true, "source": "assert add_numbers(1,2) == 3\nassert add_numbers(1,6) == 7\nassert add_numbers(111,2) == 113\nassert add_numbers(5,2) == 7\nassert add_numbers(3,2) == 5", "checksum": "b9d6c3f56495b529e96ab79696dbe8a8", "_type": "SourceCell"}}, "grades_dict": {}, "comments_dict": {}, "_type": "Notebook"}}, "extra_files": [], "_type": "GradeBookModel", "schema_version": "1"}','2025-04-16 09:20:50.853495','2025-06-03 12:21:08.093437','{"deadline": "2025-04-23T09:20:26.339000+00:00", "max_submissions": null, "allowed_files": [], "late_submission": null, "autograde_type": "auto"}');
INSERT INTO assignment VALUES(3,'Assignment 3',1,0,'pushed','deleted','{"notebooks": {"sub_numbers": {"id": "sub_numbers", "name": "sub_numbers", "flagged": false, "kernelspec": "{\"display_name\": \"Python 3 (ipykernel)\", \"language\": \"python\", \"name\": \"python3\"}", "grade_cells_dict": {}, "solution_cells_dict": {}, "task_cells_dict": {}, "source_cells_dict": {}, "grades_dict": {}, "comments_dict": {}, "_type": "Notebook"}}, "extra_files": [], "_type": "GradeBookModel", "schema_version": "1"}','2025-04-16 09:41:14.941462','2025-06-03 12:21:20.765016','{"deadline": "2025-04-24T09:41:25.309000+00:00", "max_submissions": null, "allowed_files": [], "late_submission": [], "autograde_type": "auto"}');
INSERT INTO assignment VALUES(4,'Assignment 4',1,0,'created','deleted',NULL,'2025-05-06 11:28:40.331742','2025-06-03 12:20:37.613322','{"deadline": "2025-05-10T11:28:22.412000+00:00", "max_submissions": null, "allowed_files": [], "late_submission": null, "autograde_type": "auto"}');
INSERT INTO assignment VALUES(5,'Currency Conversion',1,5,'released','active','{"notebooks": {"convert_dollar": {"id": "convert_dollar", "name": "convert_dollar", "flagged": false, "kernelspec": "{\"display_name\": \"Python 3 (ipykernel)\", \"language\": \"python\", \"name\": \"python3\"}", "grade_cells_dict": {"cell-ac6f865522fb45c0": {"max_score": 1.0, "cell_type": "code", "notebook_id": null, "name": "cell-ac6f865522fb45c0", "id": null, "grade_id": null, "comment_id": null, "_type": "GradeCell"}, "cell-97b08476829c31b2": {"max_score": 4.0, "cell_type": "code", "notebook_id": null, "name": "cell-97b08476829c31b2", "id": null, "grade_id": null, "comment_id": null, "_type": "GradeCell"}}, "solution_cells_dict": {"cell-87e7eb777dedef14": {"notebook_id": null, "name": "cell-87e7eb777dedef14", "id": null, "grade_id": null, "comment_id": null, "_type": "SolutionCell"}}, "task_cells_dict": {}, "source_cells_dict": {"cell-87e7eb777dedef14": {"notebook_id": null, "name": "cell-87e7eb777dedef14", "id": null, "cell_type": "code", "locked": false, "source": "def convert_dollar(dollar):\n    # YOUR CODE HERE\n    raise NotImplementedError()", "checksum": "5ed5fb06cd04ff189fa63b6345d4f246", "_type": "SourceCell"}, "cell-ac6f865522fb45c0": {"notebook_id": null, "name": "cell-ac6f865522fb45c0", "id": null, "cell_type": "code", "locked": true, "source": "eur, gbp = convert_dollar(5)\nassert eur == 4.6548194\nassert gbp == 4.0059821499999995", "checksum": "721905ff987abff4d78f1fa62f764059", "_type": "SourceCell"}, "cell-97b08476829c31b2": {"notebook_id": null, "name": "cell-97b08476829c31b2", "id": null, "cell_type": "code", "locked": true, "source": "assert convert_dollar(20) == (18.6192776, 16.023928599999998)\n### BEGIN HIDDEN TESTS\nassert convert_dollar(1923810) == (1790997.6219827998, 1541349.7039983)\nassert convert_dollar(0) == (0.0, 0.0)\nassert convert_dollar(999) == (930.03291612, 800.39523357)\n### END HIDDEN TESTS", "checksum": "a10b1b507cc9ecafa74b3cbfdf59bd3a", "_type": "SourceCell"}}, "grades_dict": {}, "comments_dict": {}, "_type": "Notebook"}}, "extra_files": ["Currency Conversion.md"], "_type": "GradeBookModel", "schema_version": "1"}','2025-06-03 12:23:27.310610','2025-06-04 10:12:32.878997','{"deadline": "2025-06-03T12:23:04+00:00", "max_submissions": null, "allowed_files": [], "late_submission": [], "autograde_type": "auto"}');
INSERT INTO assignment VALUES(6,'Introduction to numpy',1,2,'released','active','{"notebooks": {"introduction_to_numpy": {"id": "introduction_to_numpy", "name": "introduction_to_numpy", "flagged": false, "kernelspec": "{\"display_name\": \"Python 3 (ipykernel)\", \"language\": \"python\", \"name\": \"python3\"}", "grade_cells_dict": {"cell-35637aad1a42d8a0": {"max_score": 2.0, "cell_type": "code", "notebook_id": null, "name": "cell-35637aad1a42d8a0", "id": null, "grade_id": null, "comment_id": null, "_type": "GradeCell"}}, "solution_cells_dict": {"cell-25eebd639059cd56": {"notebook_id": null, "name": "cell-25eebd639059cd56", "id": null, "grade_id": null, "comment_id": null, "_type": "SolutionCell"}, "cell-180fb26ddc489bfc": {"notebook_id": null, "name": "cell-180fb26ddc489bfc", "id": null, "grade_id": null, "comment_id": null, "_type": "SolutionCell"}}, "task_cells_dict": {}, "source_cells_dict": {"cell-25eebd639059cd56": {"notebook_id": null, "name": "cell-25eebd639059cd56", "id": null, "cell_type": "code", "locked": false, "source": "import numpy as np\n\ndef create_array_with_zeros(length):\n    # YOUR CODE HERE\n    raise NotImplementedError()", "checksum": "d324a6aeb5afd8f8f93166e12701880f", "_type": "SourceCell"}, "cell-180fb26ddc489bfc": {"notebook_id": null, "name": "cell-180fb26ddc489bfc", "id": null, "cell_type": "code", "locked": false, "source": "import numpy as np\n\ndef create_array_with_value(length, value):\n    # YOUR CODE HERE\n    raise NotImplementedError()\n    ", "checksum": "d93f5938b7a2cd8dd16f41cd81170f0f", "_type": "SourceCell"}, "cell-35637aad1a42d8a0": {"notebook_id": null, "name": "cell-35637aad1a42d8a0", "id": null, "cell_type": "code", "locked": true, "source": "import numpy as np\n\nassert np.array_equal(create_array_with_zeros(5), np.array([0, 0, 0, 0, 0]))\nassert np.array_equal(create_array_with_value(5, 2), np.array([2, 2, 2, 2, 2]))\n\n### BEGIN HIDDEN TESTS\nassert np.array_equal(create_array_with_zeros(10), np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))\nassert np.array_equal(create_array_with_value(7, 3), np.array([3, 3, 3, 3, 3, 3, 3]))\n### END HIDDEN TESTS", "checksum": "d29660fbfeb3ef146b119b849cd90791", "_type": "SourceCell"}}, "grades_dict": {}, "comments_dict": {}, "_type": "Notebook"}}, "extra_files": ["Introduction to numpy.md"], "_type": "GradeBookModel", "schema_version": "1"}','2025-06-04 09:13:01.470737','2025-06-04 09:42:48.682905','{"deadline": null, "max_submissions": null, "allowed_files": [], "late_submission": [], "autograde_type": "auto"}');
INSERT INTO assignment VALUES(7,'Repeated List',1,4,'pushed','active','{"notebooks": {"repeat_list": {"id": "repeat_list", "name": "repeat_list", "flagged": false, "kernelspec": "{\"display_name\": \"Python 3 (ipykernel)\", \"language\": \"python\", \"name\": \"python3\"}", "grade_cells_dict": {"cell-c163851be78a4581": {"max_score": 4.0, "cell_type": "code", "notebook_id": null, "name": "cell-c163851be78a4581", "id": null, "grade_id": null, "comment_id": null, "_type": "GradeCell"}}, "solution_cells_dict": {"cell-4706c7c4d2dc5c83": {"notebook_id": null, "name": "cell-4706c7c4d2dc5c83", "id": null, "grade_id": null, "comment_id": null, "_type": "SolutionCell"}}, "task_cells_dict": {}, "source_cells_dict": {"cell-4706c7c4d2dc5c83": {"notebook_id": null, "name": "cell-4706c7c4d2dc5c83", "id": null, "cell_type": "code", "locked": false, "source": "def repeat_list(item, times):\n    # YOUR CODE HERE\n    raise NotImplementedError()\n", "checksum": "c86c729bb6799cf30e47aaeb05f3a19d", "_type": "SourceCell"}, "cell-c163851be78a4581": {"notebook_id": null, "name": "cell-c163851be78a4581", "id": null, "cell_type": "code", "locked": true, "source": "assert repeat_list(''x'', 5) == [''x'', ''x'', ''x'', ''x'', ''x'']\nassert repeat_list(0, 3) == [0, 0, 0]\n### BEGIN HIDDEN TESTS\nassert repeat_list(True, 2) == [True, True]\nassert repeat_list(''hi'', 0) == []\n### END HIDDEN TESTS", "checksum": "de72b3aa803cdc9c9e7b2cf5dc425176", "_type": "SourceCell"}}, "grades_dict": {}, "comments_dict": {}, "_type": "Notebook"}}, "extra_files": [], "_type": "GradeBookModel", "schema_version": "1"}','2025-06-04 09:45:14.998759','2025-06-04 09:54:32.374718','{"deadline": null, "max_submissions": null, "allowed_files": [], "late_submission": null, "autograde_type": "auto"}');
INSERT INTO takepart VALUES(1,'instructor',1);
INSERT INTO takepart VALUES(1,'instructor',2);
INSERT INTO takepart VALUES(1,'student',3);
INSERT INTO takepart VALUES(1,'tutor',4);
--                           id |     date                 | auto_status | manual_status            |edited|score|assignid |     commit_hash                |          updated_at    |grading_score| score_scaling | feedback_status | deleted | user_id
INSERT INTO submission VALUES(1,'2025-04-16 08:32:44.856742','GRADING_FAILED','NOT_GRADED',           NULL,NULL, 1,'287b17b30bb46764eb106b2194e0fae8fc72bb17','2025-04-16 08:32:44.926463', NULL,   1,                 'NOT_GENERATED','active',1);
INSERT INTO submission VALUES(2,'2025-04-16 08:46:07.458149','GRADING_FAILED','NOT_GRADED',           NULL,NULL, 1,'9e519305e1f009ad31c3ccd46fe326b3c7993b40','2025-04-16 08:46:07.530051', NULL,   1,                 'NOT_GENERATED','active',1);
INSERT INTO submission VALUES(3,'2025-04-16 09:16:43.602760','AUTOMATICALLY_GRADED','NOT_GRADED',     NULL,0,    1,'c5d9c676595ac13ad2abc8ea93ac4ecfec72b47c','2025-04-16 09:16:45.704466', 0,      1,                 'NOT_GENERATED','active',1);
INSERT INTO submission VALUES(4,'2025-04-16 09:30:40.750970','AUTOMATICALLY_GRADED','MANUALLY_GRADED',true,1.125,2,'7412d697155511de7c88d7990ad3616cc3437f79','2025-04-16 10:16:11.630340', 1.25,   0.900000000000000022,'GENERATED','active',1);
INSERT INTO submission VALUES(5,'2025-04-16 09:47:23.946933','AUTOMATICALLY_GRADED','NOT_GRADED',     NULL,0,    3,'79ca26a5f2b560432454c05a0c7c2fb7846fdb91','2025-04-16 09:47:25.484453', 0,      1,                 'NOT_GENERATED','active',1);
INSERT INTO submission VALUES(6,'2025-04-16 09:48:33.323631','AUTOMATICALLY_GRADED','MANUALLY_GRADED',true,0,    3,'6611b94515027e5e3a3818ff1a18a1e43b9e724b','2025-04-16 09:53:18.163605', 0,      1,                 'NOT_GENERATED','active',1);
INSERT INTO submission VALUES(7,'2025-05-22 09:49:01.106028','NOT_GRADED','NOT_GRADED',               true,NULL, 3,'0000000000000000000000000000000000000000','2025-05-22 09:49:01.244816', NULL,   0,                 'NOT_GENERATED','active',3);
INSERT INTO submission VALUES(8,'2025-06-04 10:01:20.607586','AUTOMATICALLY_GRADED','NOT_GRADED',     NULL,0,    5,'b03cd5004521bdbaf362267a5f9acd12ff699cb2','2025-06-04 10:09:11.726552', 5,      0,                 'NOT_GENERATED','active',1);
INSERT INTO submission VALUES(9,'2025-06-04 10:11:30.572845','AUTOMATICALLY_GRADED','NOT_GRADED',     NULL,5,    5,'97ca42691d63d727826d966a7a8d574e25abab0b','2025-06-04 10:11:31.784424', 5,      1,                 'NOT_GENERATED','active',3);
INSERT INTO submission_logs VALUES(1,'[2025-04-16 10:32:44] [WARNING] No notebooks were matched by ''/home/nadja/work/service/service_dir/convert_in/submission_1/*.ipynb''
[2025-04-16 10:32:44] [INFO] Reading 1335 bytes from /home/nadja/work/service/service_dir/convert_out/submission_1/gradebook.json
[2025-04-16 10:32:44] [INFO] Found additional file patterns: []
[2025-04-16 10:32:44] [INFO] Copying files from /home/nadja/work/service/service_dir/convert_in/submission_1 to /home/nadja/work/service/service_dir/convert_out/submission_1 that match allowed patterns and don''t match ignored patterns.
[2025-04-16 10:32:44] [INFO] Copied the following files: []
');
INSERT INTO submission_logs VALUES(2,'[2025-04-16 10:46:07] [INFO] Reading 1345 bytes from /home/nadja/work/service/service_dir/convert_out/submission_2/gradebook.json
[2025-04-16 10:46:07] [INFO] Found additional file patterns: []
[2025-04-16 10:46:07] [INFO] Copying files from /home/nadja/work/service/service_dir/convert_in/submission_2 to /home/nadja/work/service/service_dir/convert_out/submission_2 that match allowed patterns and don''t match ignored patterns.
[2025-04-16 10:46:07] [INFO] Copied the following files: []
');
INSERT INTO submission_logs VALUES(3,'[2025-04-16 11:16:43] [INFO] Reading 1345 bytes from /home/nadja/work/service/service_dir/convert_out/submission_3/gradebook.json
[2025-04-16 11:16:43] [INFO] Found additional file patterns: []
[2025-04-16 11:16:43] [INFO] Copying files from /home/nadja/work/service/service_dir/convert_in/submission_3 to /home/nadja/work/service/service_dir/convert_out/submission_3 that match allowed patterns and don''t match ignored patterns.
[2025-04-16 11:16:43] [INFO] Copied the following files: [''title.md'']
[2025-04-16 11:16:43] [INFO] Writing 1345 bytes to /home/nadja/work/service/service_dir/convert_out/submission_3/gradebook.json
[2025-04-16 11:16:43] [INFO] Reading 1345 bytes from /home/nadja/work/service/service_dir/convert_out/submission_3/gradebook.json
[2025-04-16 11:16:43] [INFO] Sanitizing /home/nadja/work/service/service_dir/convert_in/submission_3/sum_numbers.ipynb
[2025-04-16 11:16:43] [INFO] Converting notebook /home/nadja/work/service/service_dir/convert_in/submission_3/sum_numbers.ipynb
[2025-04-16 11:16:43] [INFO] Reading 1345 bytes from /home/nadja/work/service/service_dir/convert_out/submission_3/gradebook.json
[2025-04-16 11:16:43] [INFO] Overwriting submitted notebook kernelspec: {''display_name'': ''Python 3 (ipykernel)'', ''language'': ''python'', ''name'': ''python3''}
[2025-04-16 11:16:43] [INFO] Reading 1345 bytes from /home/nadja/work/service/service_dir/convert_out/submission_3/gradebook.json
[2025-04-16 11:16:43] [INFO] Writing 1625 bytes to /home/nadja/work/service/service_dir/convert_out/submission_3/sum_numbers.ipynb
[2025-04-16 11:16:43] [INFO] Autograding /home/nadja/work/service/service_dir/convert_out/submission_3/sum_numbers.ipynb
[2025-04-16 11:16:43] [INFO] Converting notebook /home/nadja/work/service/service_dir/convert_out/submission_3/sum_numbers.ipynb
[2025-04-16 11:16:45] [INFO] Reading 1345 bytes from /home/nadja/work/service/service_dir/convert_out/submission_3/gradebook.json
[2025-04-16 11:16:45] [INFO] Writing 1907 bytes to /home/nadja/work/service/service_dir/convert_out/submission_3/gradebook.json
[2025-04-16 11:16:45] [INFO] Writing 3814 bytes to /home/nadja/work/service/service_dir/convert_out/submission_3/sum_numbers.ipynb
[2025-04-16 11:16:45] [INFO] Setting destination file permissions to 664
[2025-04-16 11:16:45] [INFO] Reading 1907 bytes from /home/nadja/work/service/service_dir/convert_out/submission_3/gradebook.json
[2025-04-16 11:16:45] [INFO] Found additional file patterns: []
[2025-04-16 11:16:45] [INFO] Copying files from /home/nadja/work/service/service_dir/convert_in/submission_3 to /home/nadja/work/service/service_dir/convert_out/submission_3 that match allowed patterns and don''t match ignored patterns.
[2025-04-16 11:16:45] [INFO] Copied the following files: [''title.md'']
[2025-04-16 11:16:45] [INFO] Writing 1907 bytes to /home/nadja/work/service/service_dir/convert_out/submission_3/gradebook.json
');
INSERT INTO submission_logs VALUES(4,'[2025-04-16 11:30:40] [INFO] Reading 1404 bytes from /home/nadja/work/service/service_dir/convert_out/submission_4/gradebook.json
[2025-04-16 11:30:40] [INFO] Found additional file patterns: []
[2025-04-16 11:30:40] [INFO] Copying files from /home/nadja/work/service/service_dir/convert_in/submission_4 to /home/nadja/work/service/service_dir/convert_out/submission_4 that match allowed patterns and don''t match ignored patterns.
[2025-04-16 11:30:40] [INFO] Copied the following files: []
[2025-04-16 11:30:40] [INFO] Writing 1404 bytes to /home/nadja/work/service/service_dir/convert_out/submission_4/gradebook.json
[2025-04-16 11:30:40] [INFO] Reading 1404 bytes from /home/nadja/work/service/service_dir/convert_out/submission_4/gradebook.json
[2025-04-16 11:30:40] [INFO] Sanitizing /home/nadja/work/service/service_dir/convert_in/submission_4/add_numbers.ipynb
[2025-04-16 11:30:40] [INFO] Converting notebook /home/nadja/work/service/service_dir/convert_in/submission_4/add_numbers.ipynb
[2025-04-16 11:30:40] [INFO] Reading 1404 bytes from /home/nadja/work/service/service_dir/convert_out/submission_4/gradebook.json
[2025-04-16 11:30:40] [INFO] Overwriting submitted notebook kernelspec: {''display_name'': ''Python 3 (ipykernel)'', ''language'': ''python'', ''name'': ''python3''}
[2025-04-16 11:30:40] [INFO] Reading 1404 bytes from /home/nadja/work/service/service_dir/convert_out/submission_4/gradebook.json
[2025-04-16 11:30:40] [INFO] Writing 1731 bytes to /home/nadja/work/service/service_dir/convert_out/submission_4/add_numbers.ipynb
[2025-04-16 11:30:40] [INFO] Autograding /home/nadja/work/service/service_dir/convert_out/submission_4/add_numbers.ipynb
[2025-04-16 11:30:40] [INFO] Converting notebook /home/nadja/work/service/service_dir/convert_out/submission_4/add_numbers.ipynb
[2025-04-16 11:30:42] [INFO] Reading 1404 bytes from /home/nadja/work/service/service_dir/convert_out/submission_4/gradebook.json
[2025-04-16 11:30:42] [INFO] Writing 1958 bytes to /home/nadja/work/service/service_dir/convert_out/submission_4/gradebook.json
[2025-04-16 11:30:42] [INFO] Writing 2239 bytes to /home/nadja/work/service/service_dir/convert_out/submission_4/add_numbers.ipynb
[2025-04-16 11:30:42] [INFO] Setting destination file permissions to 664
[2025-04-16 11:30:42] [INFO] Reading 1958 bytes from /home/nadja/work/service/service_dir/convert_out/submission_4/gradebook.json
[2025-04-16 11:30:42] [INFO] Found additional file patterns: []
[2025-04-16 11:30:42] [INFO] Copying files from /home/nadja/work/service/service_dir/convert_in/submission_4 to /home/nadja/work/service/service_dir/convert_out/submission_4 that match allowed patterns and don''t match ignored patterns.
[2025-04-16 11:30:42] [INFO] Copied the following files: []
[2025-04-16 11:30:42] [INFO] Writing 1958 bytes to /home/nadja/work/service/service_dir/convert_out/submission_4/gradebook.json
');
INSERT INTO submission_logs VALUES(5,'[2025-04-16 11:47:23] [INFO] Reading 434 bytes from /home/nadja/work/service/service_dir/convert_out/submission_5/gradebook.json
[2025-04-16 11:47:23] [INFO] Found additional file patterns: []
[2025-04-16 11:47:23] [INFO] Copying files from /home/nadja/work/service/service_dir/convert_in/submission_5 to /home/nadja/work/service/service_dir/convert_out/submission_5 that match allowed patterns and don''t match ignored patterns.
[2025-04-16 11:47:23] [INFO] Copied the following files: []
[2025-04-16 11:47:23] [INFO] Writing 434 bytes to /home/nadja/work/service/service_dir/convert_out/submission_5/gradebook.json
[2025-04-16 11:47:23] [INFO] Reading 434 bytes from /home/nadja/work/service/service_dir/convert_out/submission_5/gradebook.json
[2025-04-16 11:47:23] [INFO] Sanitizing /home/nadja/work/service/service_dir/convert_in/submission_5/sub_numbers.ipynb
[2025-04-16 11:47:23] [INFO] Converting notebook /home/nadja/work/service/service_dir/convert_in/submission_5/sub_numbers.ipynb
[2025-04-16 11:47:23] [DEBUG] Applying preprocessor: ClearOutput
[2025-04-16 11:47:24] [DEBUG] Applying preprocessor: DeduplicateIds
[2025-04-16 11:47:24] [WARNING] cell above
[2025-04-16 11:47:24] [WARNING] cell above
[2025-04-16 11:47:24] [DEBUG] Applying preprocessor: OverwriteKernelspec
[2025-04-16 11:47:24] [INFO] Reading 434 bytes from /home/nadja/work/service/service_dir/convert_out/submission_5/gradebook.json
[2025-04-16 11:47:24] [DEBUG] Source notebook kernelspec: {''display_name'': ''Python 3 (ipykernel)'', ''language'': ''python'', ''name'': ''python3''}
[2025-04-16 11:47:24] [DEBUG] Submitted notebook kernelspec: {''display_name'': ''Python 3 (ipykernel)'', ''language'': ''python'', ''name'': ''python3''}
[2025-04-16 11:47:24] [INFO] Overwriting submitted notebook kernelspec: {''display_name'': ''Python 3 (ipykernel)'', ''language'': ''python'', ''name'': ''python3''}
[2025-04-16 11:47:24] [DEBUG] Applying preprocessor: OverwriteCells
[2025-04-16 11:47:24] [INFO] Reading 434 bytes from /home/nadja/work/service/service_dir/convert_out/submission_5/gradebook.json
[2025-04-16 11:47:24] [DEBUG] Applying preprocessor: CheckCellMetadata
[2025-04-16 11:47:24] [INFO] Writing 1146 bytes to /home/nadja/work/service/service_dir/convert_out/submission_5/sub_numbers.ipynb
[2025-04-16 11:47:24] [INFO] Autograding /home/nadja/work/service/service_dir/convert_out/submission_5/sub_numbers.ipynb
[2025-04-16 11:47:24] [INFO] Converting notebook /home/nadja/work/service/service_dir/convert_out/submission_5/sub_numbers.ipynb
[2025-04-16 11:47:24] [DEBUG] Applying preprocessor: Execute
[2025-04-16 11:47:24] [DEBUG] Instantiating kernel ''Python 3 (ipykernel)'' with kernel provisioner: local-provisioner
[2025-04-16 11:47:24] [DEBUG] Starting kernel: [''/home/nadja/micromamba/envs/grader/bin/python'', ''-m'', ''ipykernel_launcher'', ''-f'', ''/tmp/tmpq7hkzjyb.json'', ''--HistoryManager.hist_file=:memory:'']
[2025-04-16 11:47:24] [DEBUG] Connecting to: tcp://127.0.0.1:37235
[2025-04-16 11:47:24] [DEBUG] connecting iopub channel to tcp://127.0.0.1:41609
[2025-04-16 11:47:24] [DEBUG] Connecting to: tcp://127.0.0.1:41609
[2025-04-16 11:47:24] [DEBUG] connecting shell channel to tcp://127.0.0.1:56029
[2025-04-16 11:47:24] [DEBUG] Connecting to: tcp://127.0.0.1:56029
[2025-04-16 11:47:24] [DEBUG] connecting stdin channel to tcp://127.0.0.1:48669
[2025-04-16 11:47:24] [DEBUG] Connecting to: tcp://127.0.0.1:48669
[2025-04-16 11:47:24] [DEBUG] connecting heartbeat channel to tcp://127.0.0.1:56613
[2025-04-16 11:47:24] [DEBUG] connecting control channel to tcp://127.0.0.1:37235
[2025-04-16 11:47:24] [DEBUG] Connecting to: tcp://127.0.0.1:37235
[2025-04-16 11:47:24] [DEBUG] Executing cell:
# YOUR CODE HERE
[2025-04-16 11:47:24] [DEBUG] msg_type: status
[2025-04-16 11:47:24] [DEBUG] content: {''execution_state'': ''busy''}
[2025-04-16 11:47:24] [DEBUG] msg_type: execute_input
[2025-04-16 11:47:24] [DEBUG] content: {''code'': ''# YOUR CODE HERE'', ''execution_count'': 1}
[2025-04-16 11:47:24] [DEBUG] msg_type: status
[2025-04-16 11:47:24] [DEBUG] content: {''execution_state'': ''idle''}
[2025-04-16 11:47:24] [DEBUG] Executing cell:
assert sub_numbers(3,1) == 2
assert sub_numbers(6,21) == -15
assert sub_numbers(7,1) == 6
assert sub_numbers(94,5) == 89
[2025-04-16 11:47:24] [DEBUG] msg_type: status
[2025-04-16 11:47:24] [DEBUG] content: {''execution_state'': ''busy''}
[2025-04-16 11:47:24] [DEBUG] msg_type: execute_input
[2025-04-16 11:47:24] [DEBUG] content: {''code'': ''assert sub_numbers(3,1) == 2\nassert sub_numbers(6,21) == -15\nassert sub_numbers(7,1) == 6\nassert sub_numbers(94,5) == 89'', ''execution_count'': 2}
[2025-04-16 11:47:24] [DEBUG] msg_type: error
[2025-04-16 11:47:24] [DEBUG] content: {''traceback'': [''\x1b[31m---------------------------------------------------------------------------\x1b[39m'', ''\x1b[31mNameError\x1b[39m                                 Traceback (most recent call last)'', ''\x1b[36mCell\x1b[39m\x1b[36m \x1b[39m\x1b[32mIn[2]\x1b[39m\x1b[32m, line 1\x1b[39m\n\x1b[32m----> \x1b[39m\x1b[32m1\x1b[39m \x1b[38;5;28;01massert\x1b[39;00m \x1b[43msub_numbers\x1b[49m(\x1b[32m3\x1b[39m,\x1b[32m1\x1b[39m) == \x1b[32m2\x1b[39m\n\x1b[32m      2\x1b[39m \x1b[38;5;28;01massert\x1b[39;00m sub_numbers(\x1b[32m6\x1b[39m,\x1b[32m21\x1b[39m) == -\x1b[32m15\x1b[39m\n\x1b[32m      3\x1b[39m \x1b[38;5;28;01massert\x1b[39;00m sub_numbers(\x1b[32m7\x1b[39m,\x1b[32m1\x1b[39m) == \x1b[32m6\x1b[39m\n'', "\x1b[31mNameError\x1b[39m: name ''sub_numbers'' is not defined"], ''ename'': ''NameError'', ''evalue'': "name ''sub_numbers'' is not defined"}
[2025-04-16 11:47:24] [DEBUG] msg_type: status
[2025-04-16 11:47:24] [DEBUG] content: {''execution_state'': ''idle''}
[2025-04-16 11:47:25] [DEBUG] Destroying zmq context for <jupyter_client.asynchronous.client.AsyncKernelClient object at 0x7937dcfcc410>
[2025-04-16 11:47:25] [DEBUG] Applying preprocessor: LimitOutput
[2025-04-16 11:47:25] [DEBUG] Applying preprocessor: SaveAutoGrades
[2025-04-16 11:47:25] [INFO] Reading 434 bytes from /home/nadja/work/service/service_dir/convert_out/submission_5/gradebook.json
[2025-04-16 11:47:25] [DEBUG] Applying preprocessor: CheckCellMetadata
[2025-04-16 11:47:25] [DEBUG] Applying preprocessor: ClearAlwaysHiddenTests
[2025-04-16 11:47:25] [INFO] Writing 2688 bytes to /home/nadja/work/service/service_dir/convert_out/submission_5/sub_numbers.ipynb
[2025-04-16 11:47:25] [INFO] Setting destination file permissions to 664
[2025-04-16 11:47:25] [INFO] Reading 434 bytes from /home/nadja/work/service/service_dir/convert_out/submission_5/gradebook.json
[2025-04-16 11:47:25] [INFO] Found additional file patterns: []
[2025-04-16 11:47:25] [INFO] Copying files from /home/nadja/work/service/service_dir/convert_in/submission_5 to /home/nadja/work/service/service_dir/convert_out/submission_5 that match allowed patterns and don''t match ignored patterns.
[2025-04-16 11:47:25] [INFO] Copied the following files: []
[2025-04-16 11:47:25] [INFO] Writing 434 bytes to /home/nadja/work/service/service_dir/convert_out/submission_5/gradebook.json');
INSERT INTO submission_logs VALUES(6,'[2025-04-16 11:53:16] [INFO] Reading 434 bytes from /home/nadja/work/service/service_dir/convert_out/submission_6/gradebook.json
[2025-04-16 11:53:16] [INFO] Found additional file patterns: []
[2025-04-16 11:53:16] [INFO] Copying files from /home/nadja/work/service/service_dir/convert_in/submission_6 to /home/nadja/work/service/service_dir/convert_out/submission_6 that match allowed patterns and don''t match ignored patterns.
[2025-04-16 11:53:16] [INFO] Copied the following files: []
[2025-04-16 11:53:16] [INFO] Writing 434 bytes to /home/nadja/work/service/service_dir/convert_out/submission_6/gradebook.json
[2025-04-16 11:53:16] [INFO] Reading 434 bytes from /home/nadja/work/service/service_dir/convert_out/submission_6/gradebook.json
[2025-04-16 11:53:16] [INFO] Sanitizing /home/nadja/work/service/service_dir/convert_in/submission_6/sub_numbers.ipynb
[2025-04-16 11:53:16] [INFO] Converting notebook /home/nadja/work/service/service_dir/convert_in/submission_6/sub_numbers.ipynb
[2025-04-16 11:53:16] [DEBUG] Applying preprocessor: ClearOutput
[2025-04-16 11:53:16] [DEBUG] Applying preprocessor: DeduplicateIds
[2025-04-16 11:53:16] [WARNING] cell above
[2025-04-16 11:53:16] [WARNING] cell above
[2025-04-16 11:53:16] [DEBUG] Applying preprocessor: OverwriteKernelspec
[2025-04-16 11:53:16] [INFO] Reading 434 bytes from /home/nadja/work/service/service_dir/convert_out/submission_6/gradebook.json
[2025-04-16 11:53:16] [DEBUG] Source notebook kernelspec: {''display_name'': ''Python 3 (ipykernel)'', ''language'': ''python'', ''name'': ''python3''}
[2025-04-16 11:53:16] [DEBUG] Submitted notebook kernelspec: {''display_name'': ''Python 3 (ipykernel)'', ''language'': ''python'', ''name'': ''python3''}
[2025-04-16 11:53:16] [INFO] Overwriting submitted notebook kernelspec: {''display_name'': ''Python 3 (ipykernel)'', ''language'': ''python'', ''name'': ''python3''}
[2025-04-16 11:53:16] [DEBUG] Applying preprocessor: OverwriteCells
[2025-04-16 11:53:16] [INFO] Reading 434 bytes from /home/nadja/work/service/service_dir/convert_out/submission_6/gradebook.json
[2025-04-16 11:53:16] [DEBUG] Applying preprocessor: CheckCellMetadata
[2025-04-16 11:53:16] [INFO] Writing 1228 bytes to /home/nadja/work/service/service_dir/convert_out/submission_6/sub_numbers.ipynb
[2025-04-16 11:53:16] [INFO] Autograding /home/nadja/work/service/service_dir/convert_out/submission_6/sub_numbers.ipynb
[2025-04-16 11:53:16] [INFO] Converting notebook /home/nadja/work/service/service_dir/convert_out/submission_6/sub_numbers.ipynb
[2025-04-16 11:53:16] [DEBUG] Applying preprocessor: Execute
[2025-04-16 11:53:16] [DEBUG] Instantiating kernel ''Python 3 (ipykernel)'' with kernel provisioner: local-provisioner
[2025-04-16 11:53:16] [DEBUG] Starting kernel: [''/home/nadja/micromamba/envs/grader/bin/python'', ''-m'', ''ipykernel_launcher'', ''-f'', ''/tmp/tmpfku4x2w6.json'', ''--HistoryManager.hist_file=:memory:'']
[2025-04-16 11:53:16] [DEBUG] Connecting to: tcp://127.0.0.1:45351
[2025-04-16 11:53:16] [DEBUG] connecting iopub channel to tcp://127.0.0.1:41693
[2025-04-16 11:53:16] [DEBUG] Connecting to: tcp://127.0.0.1:41693
[2025-04-16 11:53:16] [DEBUG] connecting shell channel to tcp://127.0.0.1:47441
[2025-04-16 11:53:16] [DEBUG] Connecting to: tcp://127.0.0.1:47441
[2025-04-16 11:53:16] [DEBUG] connecting stdin channel to tcp://127.0.0.1:34463
[2025-04-16 11:53:16] [DEBUG] Connecting to: tcp://127.0.0.1:34463
[2025-04-16 11:53:16] [DEBUG] connecting heartbeat channel to tcp://127.0.0.1:47001
[2025-04-16 11:53:16] [DEBUG] connecting control channel to tcp://127.0.0.1:45351
[2025-04-16 11:53:16] [DEBUG] Connecting to: tcp://127.0.0.1:45351
[2025-04-16 11:53:17] [DEBUG] Executing cell:
# YOUR CODE HERE
def sub_numbers(a, b):
    return a - b
    # good job
[2025-04-16 11:53:17] [DEBUG] msg_type: status
[2025-04-16 11:53:17] [DEBUG] content: {''execution_state'': ''busy''}
[2025-04-16 11:53:17] [DEBUG] msg_type: execute_input
[2025-04-16 11:53:17] [DEBUG] content: {''code'': ''# YOUR CODE HERE\ndef sub_numbers(a, b):\n    return a - b\n    # good job'', ''execution_count'': 1}
[2025-04-16 11:53:17] [DEBUG] msg_type: status
[2025-04-16 11:53:17] [DEBUG] content: {''execution_state'': ''idle''}
[2025-04-16 11:53:17] [DEBUG] Executing cell:
assert sub_numbers(3,1) == 2
assert sub_numbers(6,21) == -15
assert sub_numbers(7,1) == 6
assert sub_numbers(94,5) == 89
[2025-04-16 11:53:17] [DEBUG] msg_type: status
[2025-04-16 11:53:17] [DEBUG] content: {''execution_state'': ''busy''}
[2025-04-16 11:53:17] [DEBUG] msg_type: execute_input
[2025-04-16 11:53:17] [DEBUG] content: {''code'': ''assert sub_numbers(3,1) == 2\nassert sub_numbers(6,21) == -15\nassert sub_numbers(7,1) == 6\nassert sub_numbers(94,5) == 89'', ''execution_count'': 2}
[2025-04-16 11:53:17] [DEBUG] msg_type: status
[2025-04-16 11:53:17] [DEBUG] content: {''execution_state'': ''idle''}
[2025-04-16 11:53:17] [DEBUG] Destroying zmq context for <jupyter_client.asynchronous.client.AsyncKernelClient object at 0x7937ddcbb5c0>
[2025-04-16 11:53:17] [DEBUG] Applying preprocessor: LimitOutput
[2025-04-16 11:53:18] [DEBUG] Applying preprocessor: SaveAutoGrades
[2025-04-16 11:53:18] [INFO] Reading 434 bytes from /home/nadja/work/service/service_dir/convert_out/submission_6/gradebook.json
[2025-04-16 11:53:18] [DEBUG] Applying preprocessor: CheckCellMetadata
[2025-04-16 11:53:18] [DEBUG] Applying preprocessor: ClearAlwaysHiddenTests
[2025-04-16 11:53:18] [INFO] Writing 1736 bytes to /home/nadja/work/service/service_dir/convert_out/submission_6/sub_numbers.ipynb
[2025-04-16 11:53:18] [INFO] Setting destination file permissions to 664
[2025-04-16 11:53:18] [INFO] Reading 434 bytes from /home/nadja/work/service/service_dir/convert_out/submission_6/gradebook.json
[2025-04-16 11:53:18] [INFO] Found additional file patterns: []
[2025-04-16 11:53:18] [INFO] Copying files from /home/nadja/work/service/service_dir/convert_in/submission_6 to /home/nadja/work/service/service_dir/convert_out/submission_6 that match allowed patterns and don''t match ignored patterns.
[2025-04-16 11:53:18] [INFO] Copied the following files: []
[2025-04-16 11:53:18] [INFO] Writing 434 bytes to /home/nadja/work/service/service_dir/convert_out/submission_6/gradebook.json
');
INSERT INTO submission_logs VALUES(7,'fatal: reference is not a tree: 0000000000000000000000000000000000000000');
INSERT INTO submission_logs VALUES(8,'[2025-06-04 10:09:10] [INFO] Reading 2096 bytes from /app/service_dir/convert_out/submission_8/gradebook.json
[2025-06-04 10:09:10] [INFO] Found additional file patterns: []
[2025-06-04 10:09:10] [INFO] Copying files from /app/service_dir/convert_in/submission_8 to /app/service_dir/convert_out/submission_8 that match allowed patterns and don''t match ignored patterns.
[2025-06-04 10:09:10] [INFO] Copied the following files: [''Currency Conversion.md'']
[2025-06-04 10:09:10] [INFO] Writing 2096 bytes to /app/service_dir/convert_out/submission_8/gradebook.json
[2025-06-04 10:09:10] [INFO] Reading 2096 bytes from /app/service_dir/convert_out/submission_8/gradebook.json
[2025-06-04 10:09:10] [INFO] Sanitizing /app/service_dir/convert_in/submission_8/convert_dollar.ipynb
[2025-06-04 10:09:10] [INFO] Converting notebook /app/service_dir/convert_in/submission_8/convert_dollar.ipynb
[2025-06-04 10:09:10] [INFO] Reading 2096 bytes from /app/service_dir/convert_out/submission_8/gradebook.json
[2025-06-04 10:09:10] [INFO] Overwriting submitted notebook kernelspec: {''display_name'': ''Python 3 (ipykernel)'', ''language'': ''python'', ''name'': ''python3''}
[2025-06-04 10:09:10] [INFO] Reading 2096 bytes from /app/service_dir/convert_out/submission_8/gradebook.json
[2025-06-04 10:09:10] [INFO] Source of cell cell-97b08476829c31b2 in overwritten order to prove checksum.
[2025-06-04 10:09:10] [INFO] Writing 2549 bytes to /app/service_dir/convert_out/submission_8/convert_dollar.ipynb
[2025-06-04 10:09:10] [INFO] Autograding /app/service_dir/convert_out/submission_8/convert_dollar.ipynb
[2025-06-04 10:09:10] [INFO] Converting notebook /app/service_dir/convert_out/submission_8/convert_dollar.ipynb
[2025-06-04 10:09:11] [INFO] Reading 2096 bytes from /app/service_dir/convert_out/submission_8/gradebook.json
[2025-06-04 10:09:11] [INFO] Writing 3008 bytes to /app/service_dir/convert_out/submission_8/gradebook.json
[2025-06-04 10:09:11] [INFO] Writing 3311 bytes to /app/service_dir/convert_out/submission_8/convert_dollar.ipynb
[2025-06-04 10:09:11] [INFO] Setting destination file permissions to 664
[2025-06-04 10:09:11] [INFO] Reading 3008 bytes from /app/service_dir/convert_out/submission_8/gradebook.json
[2025-06-04 10:09:11] [INFO] Found additional file patterns: []
[2025-06-04 10:09:11] [INFO] Copying files from /app/service_dir/convert_in/submission_8 to /app/service_dir/convert_out/submission_8 that match allowed patterns and don''t match ignored patterns.
[2025-06-04 10:09:11] [INFO] Copied the following files: [''Currency Conversion.md'']
[2025-06-04 10:09:11] [INFO] Writing 3008 bytes to /app/service_dir/convert_out/submission_8/gradebook.json
');
INSERT INTO submission_logs VALUES(9,'[2025-06-04 10:11:30] [INFO] Reading 2096 bytes from /app/service_dir/convert_out/submission_9/gradebook.json
[2025-06-04 10:11:30] [INFO] Found additional file patterns: []
[2025-06-04 10:11:30] [INFO] Copying files from /app/service_dir/convert_in/submission_9 to /app/service_dir/convert_out/submission_9 that match allowed patterns and don''t match ignored patterns.
[2025-06-04 10:11:30] [INFO] Copied the following files: [''Currency Conversion.md'']
[2025-06-04 10:11:30] [INFO] Writing 2096 bytes to /app/service_dir/convert_out/submission_9/gradebook.json
[2025-06-04 10:11:30] [INFO] Reading 2096 bytes from /app/service_dir/convert_out/submission_9/gradebook.json
[2025-06-04 10:11:30] [INFO] Sanitizing /app/service_dir/convert_in/submission_9/convert_dollar.ipynb
[2025-06-04 10:11:30] [INFO] Converting notebook /app/service_dir/convert_in/submission_9/convert_dollar.ipynb
[2025-06-04 10:11:30] [INFO] Reading 2096 bytes from /app/service_dir/convert_out/submission_9/gradebook.json
[2025-06-04 10:11:30] [INFO] Overwriting submitted notebook kernelspec: {''display_name'': ''Python 3 (ipykernel)'', ''language'': ''python'', ''name'': ''python3''}
[2025-06-04 10:11:30] [INFO] Reading 2096 bytes from /app/service_dir/convert_out/submission_9/gradebook.json
[2025-06-04 10:11:30] [INFO] Source of cell cell-97b08476829c31b2 in overwritten order to prove checksum.
[2025-06-04 10:11:30] [INFO] Writing 2549 bytes to /app/service_dir/convert_out/submission_9/convert_dollar.ipynb
[2025-06-04 10:11:30] [INFO] Autograding /app/service_dir/convert_out/submission_9/convert_dollar.ipynb
[2025-06-04 10:11:30] [INFO] Converting notebook /app/service_dir/convert_out/submission_9/convert_dollar.ipynb
[2025-06-04 10:11:31] [INFO] Reading 2096 bytes from /app/service_dir/convert_out/submission_9/gradebook.json
[2025-06-04 10:11:31] [INFO] Writing 3008 bytes to /app/service_dir/convert_out/submission_9/gradebook.json
[2025-06-04 10:11:31] [INFO] Writing 3311 bytes to /app/service_dir/convert_out/submission_9/convert_dollar.ipynb
[2025-06-04 10:11:31] [INFO] Setting destination file permissions to 664
[2025-06-04 10:11:31] [INFO] Reading 3008 bytes from /app/service_dir/convert_out/submission_9/gradebook.json
[2025-06-04 10:11:31] [INFO] Found additional file patterns: []
[2025-06-04 10:11:31] [INFO] Copying files from /app/service_dir/convert_in/submission_9 to /app/service_dir/convert_out/submission_9 that match allowed patterns and don''t match ignored patterns.
[2025-06-04 10:11:31] [INFO] Copied the following files: [''Currency Conversion.md'']
[2025-06-04 10:11:31] [INFO] Writing 3008 bytes to /app/service_dir/convert_out/submission_9/gradebook.json
');
INSERT INTO submission_properties VALUES(3,'{"notebooks": {"sum_numbers": {"id": "sum_numbers", "name": "sum_numbers", "flagged": false, "kernelspec": "{\"display_name\": \"Python 3 (ipykernel)\", \"language\": \"python\", \"name\": \"python3\"}", "grade_cells_dict": {"cell-1e1d884e2e83e97f": {"max_score": 1.0, "cell_type": "code", "notebook_id": null, "name": "cell-1e1d884e2e83e97f", "id": null, "grade_id": "cell-1e1d884e2e83e97f", "comment_id": null, "_type": "GradeCell"}}, "solution_cells_dict": {"cell-ec1c0a6598d73f81": {"notebook_id": null, "name": "cell-ec1c0a6598d73f81", "id": null, "grade_id": null, "comment_id": "cell-ec1c0a6598d73f81", "_type": "SolutionCell"}}, "task_cells_dict": {}, "source_cells_dict": {"cell-ec1c0a6598d73f81": {"notebook_id": null, "name": "cell-ec1c0a6598d73f81", "id": null, "cell_type": "code", "locked": false, "source": "# YOUR CODE HERE\nraise NotImplementedError()", "checksum": "4249b24f09b6278a68bae93a067d84e7", "_type": "SourceCell"}, "cell-1e1d884e2e83e97f": {"notebook_id": null, "name": "cell-1e1d884e2e83e97f", "id": null, "cell_type": "code", "locked": true, "source": "assert sum_numbers(1) == 1\nassert sum_numbers(2) == 3\nassert sum_numbers(5) == 15", "checksum": "6453ffdd62ea1a1eabcf95616174dd88", "_type": "SourceCell"}}, "grades_dict": {"cell-1e1d884e2e83e97f": {"cell_id": "cell-1e1d884e2e83e97f", "notebook_id": "sum_numbers", "id": "cell-1e1d884e2e83e97f", "auto_score": 0, "manual_score": null, "extra_credit": null, "needs_manual_grade": false, "max_score_gradecell": 1.0, "max_score_taskcell": null, "failed_tests": null, "_type": "Grade", "max_score": 1.0}}, "comments_dict": {"cell-ec1c0a6598d73f81": {"cell_id": "cell-ec1c0a6598d73f81", "notebook_id": "sum_numbers", "id": "cell-ec1c0a6598d73f81", "auto_comment": "No response.", "manual_comment": null, "_type": "Comment"}}, "_type": "Notebook"}}, "extra_files": ["title.md"], "_type": "GradeBookModel", "schema_version": "1"}');
INSERT INTO submission_properties VALUES(4,'{"notebooks":{"add_numbers":{"id":"add_numbers","name":"add_numbers","flagged":false,"kernelspec":"{\"display_name\": \"Python 3 (ipykernel)\", \"language\": \"python\", \"name\": \"python3\"}","grade_cells_dict":{"cell-3df764e6d829e6ef":{"max_score":2,"cell_type":"code","notebook_id":null,"name":"cell-3df764e6d829e6ef","id":null,"grade_id":"cell-3df764e6d829e6ef","comment_id":null,"_type":"GradeCell"}},"solution_cells_dict":{"cell-7d6a4f3241ca6383":{"notebook_id":null,"name":"cell-7d6a4f3241ca6383","id":null,"grade_id":null,"comment_id":"cell-7d6a4f3241ca6383","_type":"SolutionCell"}},"task_cells_dict":{},"source_cells_dict":{"cell-7d6a4f3241ca6383":{"notebook_id":null,"name":"cell-7d6a4f3241ca6383","id":null,"cell_type":"code","locked":false,"source":"# YOUR CODE HERE\nraise NotImplementedError()","checksum":"bb2a9f9fb0716b1f5a0ca91a1720f598","_type":"SourceCell"},"cell-3df764e6d829e6ef":{"notebook_id":null,"name":"cell-3df764e6d829e6ef","id":null,"cell_type":"code","locked":true,"source":"assert add_numbers(1,2) == 3\nassert add_numbers(1,6) == 7\nassert add_numbers(111,2) == 113\nassert add_numbers(5,2) == 7\nassert add_numbers(3,2) == 5","checksum":"b9d6c3f56495b529e96ab79696dbe8a8","_type":"SourceCell"}},"grades_dict":{"cell-3df764e6d829e6ef":{"cell_id":"cell-3df764e6d829e6ef","notebook_id":"add_numbers","id":"cell-3df764e6d829e6ef","auto_score":2,"manual_score":1.25,"extra_credit":null,"needs_manual_grade":false,"max_score_gradecell":2,"max_score_taskcell":null,"failed_tests":null,"_type":"Grade","max_score":2}},"comments_dict":{"cell-7d6a4f3241ca6383":{"cell_id":"cell-7d6a4f3241ca6383","notebook_id":"add_numbers","id":"cell-7d6a4f3241ca6383","auto_comment":null,"manual_comment":null,"_type":"Comment"}},"_type":"Notebook"}},"extra_files":[],"_type":"GradeBookModel","schema_version":"1"}');
INSERT INTO submission_properties VALUES(5,'{"notebooks": {"sub_numbers": {"id": "sub_numbers", "name": "sub_numbers", "flagged": false, "kernelspec": "{\"display_name\": \"Python 3 (ipykernel)\", \"language\": \"python\", \"name\": \"python3\"}", "grade_cells_dict": {}, "solution_cells_dict": {}, "task_cells_dict": {}, "source_cells_dict": {}, "grades_dict": {}, "comments_dict": {}, "_type": "Notebook"}}, "extra_files": [], "_type": "GradeBookModel", "schema_version": "1"}');
INSERT INTO submission_properties VALUES(6,'{"notebooks": {"sub_numbers": {"id": "sub_numbers", "name": "sub_numbers", "flagged": false, "kernelspec": "{\"display_name\": \"Python 3 (ipykernel)\", \"language\": \"python\", \"name\": \"python3\"}", "grade_cells_dict": {}, "solution_cells_dict": {}, "task_cells_dict": {}, "source_cells_dict": {}, "grades_dict": {}, "comments_dict": {}, "_type": "Notebook"}}, "extra_files": [], "_type": "GradeBookModel", "schema_version": "1"}');
INSERT INTO submission_properties VALUES(8,'{"notebooks": {"convert_dollar": {"id": "convert_dollar", "name": "convert_dollar", "flagged": false, "kernelspec": "{\"display_name\": \"Python 3 (ipykernel)\", \"language\": \"python\", \"name\": \"python3\"}", "grade_cells_dict": {"cell-ac6f865522fb45c0": {"max_score": 1.0, "cell_type": "code", "notebook_id": null, "name": "cell-ac6f865522fb45c0", "id": null, "grade_id": "cell-ac6f865522fb45c0", "comment_id": null, "_type": "GradeCell"}, "cell-97b08476829c31b2": {"max_score": 4.0, "cell_type": "code", "notebook_id": null, "name": "cell-97b08476829c31b2", "id": null, "grade_id": "cell-97b08476829c31b2", "comment_id": null, "_type": "GradeCell"}}, "solution_cells_dict": {"cell-87e7eb777dedef14": {"notebook_id": null, "name": "cell-87e7eb777dedef14", "id": null, "grade_id": null, "comment_id": "cell-87e7eb777dedef14", "_type": "SolutionCell"}}, "task_cells_dict": {}, "source_cells_dict": {"cell-87e7eb777dedef14": {"notebook_id": null, "name": "cell-87e7eb777dedef14", "id": null, "cell_type": "code", "locked": false, "source": "def convert_dollar(dollar):\n    # YOUR CODE HERE\n    raise NotImplementedError()", "checksum": "5ed5fb06cd04ff189fa63b6345d4f246", "_type": "SourceCell"}, "cell-ac6f865522fb45c0": {"notebook_id": null, "name": "cell-ac6f865522fb45c0", "id": null, "cell_type": "code", "locked": true, "source": "eur, gbp = convert_dollar(5)\nassert eur == 4.6548194\nassert gbp == 4.0059821499999995", "checksum": "721905ff987abff4d78f1fa62f764059", "_type": "SourceCell"}, "cell-97b08476829c31b2": {"notebook_id": null, "name": "cell-97b08476829c31b2", "id": null, "cell_type": "code", "locked": true, "source": "assert convert_dollar(20) == (18.6192776, 16.023928599999998)\n### BEGIN HIDDEN TESTS\nassert convert_dollar(1923810) == (1790997.6219827998, 1541349.7039983)\nassert convert_dollar(0) == (0.0, 0.0)\nassert convert_dollar(999) == (930.03291612, 800.39523357)\n### END HIDDEN TESTS", "checksum": "a10b1b507cc9ecafa74b3cbfdf59bd3a", "_type": "SourceCell"}}, "grades_dict": {"cell-ac6f865522fb45c0": {"cell_id": "cell-ac6f865522fb45c0", "notebook_id": "convert_dollar", "id": "cell-ac6f865522fb45c0", "auto_score": 1.0, "manual_score": null, "extra_credit": null, "needs_manual_grade": false, "max_score_gradecell": 1.0, "max_score_taskcell": null, "failed_tests": null, "_type": "Grade", "max_score": 1.0}, "cell-97b08476829c31b2": {"cell_id": "cell-97b08476829c31b2", "notebook_id": "convert_dollar", "id": "cell-97b08476829c31b2", "auto_score": 4.0, "manual_score": null, "extra_credit": null, "needs_manual_grade": false, "max_score_gradecell": 4.0, "max_score_taskcell": null, "failed_tests": null, "_type": "Grade", "max_score": 4.0}}, "comments_dict": {"cell-87e7eb777dedef14": {"cell_id": "cell-87e7eb777dedef14", "notebook_id": "convert_dollar", "id": "cell-87e7eb777dedef14", "auto_comment": null, "manual_comment": null, "_type": "Comment"}}, "_type": "Notebook"}}, "extra_files": ["Currency Conversion.md"], "_type": "GradeBookModel", "schema_version": "1"}');
INSERT INTO submission_properties VALUES(9,'{"notebooks": {"convert_dollar": {"id": "convert_dollar", "name": "convert_dollar", "flagged": false, "kernelspec": "{\"display_name\": \"Python 3 (ipykernel)\", \"language\": \"python\", \"name\": \"python3\"}", "grade_cells_dict": {"cell-ac6f865522fb45c0": {"max_score": 1.0, "cell_type": "code", "notebook_id": null, "name": "cell-ac6f865522fb45c0", "id": null, "grade_id": "cell-ac6f865522fb45c0", "comment_id": null, "_type": "GradeCell"}, "cell-97b08476829c31b2": {"max_score": 4.0, "cell_type": "code", "notebook_id": null, "name": "cell-97b08476829c31b2", "id": null, "grade_id": "cell-97b08476829c31b2", "comment_id": null, "_type": "GradeCell"}}, "solution_cells_dict": {"cell-87e7eb777dedef14": {"notebook_id": null, "name": "cell-87e7eb777dedef14", "id": null, "grade_id": null, "comment_id": "cell-87e7eb777dedef14", "_type": "SolutionCell"}}, "task_cells_dict": {}, "source_cells_dict": {"cell-87e7eb777dedef14": {"notebook_id": null, "name": "cell-87e7eb777dedef14", "id": null, "cell_type": "code", "locked": false, "source": "def convert_dollar(dollar):\n    # YOUR CODE HERE\n    raise NotImplementedError()", "checksum": "5ed5fb06cd04ff189fa63b6345d4f246", "_type": "SourceCell"}, "cell-ac6f865522fb45c0": {"notebook_id": null, "name": "cell-ac6f865522fb45c0", "id": null, "cell_type": "code", "locked": true, "source": "eur, gbp = convert_dollar(5)\nassert eur == 4.6548194\nassert gbp == 4.0059821499999995", "checksum": "721905ff987abff4d78f1fa62f764059", "_type": "SourceCell"}, "cell-97b08476829c31b2": {"notebook_id": null, "name": "cell-97b08476829c31b2", "id": null, "cell_type": "code", "locked": true, "source": "assert convert_dollar(20) == (18.6192776, 16.023928599999998)\n### BEGIN HIDDEN TESTS\nassert convert_dollar(1923810) == (1790997.6219827998, 1541349.7039983)\nassert convert_dollar(0) == (0.0, 0.0)\nassert convert_dollar(999) == (930.03291612, 800.39523357)\n### END HIDDEN TESTS", "checksum": "a10b1b507cc9ecafa74b3cbfdf59bd3a", "_type": "SourceCell"}}, "grades_dict": {"cell-ac6f865522fb45c0": {"cell_id": "cell-ac6f865522fb45c0", "notebook_id": "convert_dollar", "id": "cell-ac6f865522fb45c0", "auto_score": 1.0, "manual_score": null, "extra_credit": null, "needs_manual_grade": false, "max_score_gradecell": 1.0, "max_score_taskcell": null, "failed_tests": null, "_type": "Grade", "max_score": 1.0}, "cell-97b08476829c31b2": {"cell_id": "cell-97b08476829c31b2", "notebook_id": "convert_dollar", "id": "cell-97b08476829c31b2", "auto_score": 4.0, "manual_score": null, "extra_credit": null, "needs_manual_grade": false, "max_score_gradecell": 4.0, "max_score_taskcell": null, "failed_tests": null, "_type": "Grade", "max_score": 4.0}}, "comments_dict": {"cell-87e7eb777dedef14": {"cell_id": "cell-87e7eb777dedef14", "notebook_id": "convert_dollar", "id": "cell-87e7eb777dedef14", "auto_comment": null, "manual_comment": null, "_type": "Comment"}}, "_type": "Notebook"}}, "extra_files": ["Currency Conversion.md"], "_type": "GradeBookModel", "schema_version": "1"}');
