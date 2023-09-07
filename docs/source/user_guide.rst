User Guide
***************

After installation and configuration of the grader labextension and service you should
be able to access the frontend interface of the extension.
The labextension consists of two launchers.
The assignment launcher opens a window where students can pull and submit their
given assignments.
The course management launcher opens a dashboard
for instructors where you can add, edit and delete assignments.
The course management launcher is only visible if the current user is at least
a tutor in one lecture.

.. image:: _static/assets/images/launcher.png
    :alt: launcher window

.. note::
    If you do not see the launcher items, it may be the case that extensions might be disabled in JupyterLab.
    You can find how to enable extensions `here <https://jupyterlab.readthedocs.io/en/stable/user/extensions.html#managing-extensions-using-the-extension-manager>`_.
    Another reason might be that the grader service is not running. However, there will be a warning if this is the case.

One Instance Hub vs. Multiple Instances Hub
============================================
In winter semester 2023 we are introducing One Instance Hub, which allows you to have all of your lectures in one place and easily manage them. 
If you are using Jupyter as a Service for multiple lectures, they are now shown in one list. In each lecture 
you can manage as many assignments as needed and this process and navigation between assignments has been made
easier. You can also switch between completed and current lectures and review assignments that were monitored in completed lectures. 
Students who are enrolled in multiple lectures using Jupyter as a Service will see all of their lecturers and assignments in one place, 
eliminating the need to follow a link provided in each TUWEL course that uses Jupyter as a Service. Once they are logged into JupyterHub,
they can access all of their lectures and assignments released in those lectures.

Create Your First Assignment
=============================
Before students can access the notebooks, an assignment must be created.
To access this feature, open the course management dashboard and navigate to desired lecture:

.. image:: _static/assets/images/courses.png
    :alt: course management list

| The course management table lists all assignments in the chosen lecture and lets you easily manage them:

.. image:: _static/assets/images/assignments.png
    :alt: assignment list

| By pressing on the "+ NEW" button on top of the assignment list, instructors can add new assignments to the lecture:

.. image:: _static/assets/images/add_assignment.png
    :alt: add assignment dialog

Working With Assignments
========================
Once an assignment has been created it can be opened, which will display the overview window.
In the overview window of the assignment, you will find many ways to monitor, grade and extend the current assignment.

.. image:: _static/assets/images/overview_user_guide.png
    :alt: overview window

Files
--------------------

Every assignment includes two crucial directories.
The **source directory** contains the source notebooks which instructors create for their assignment.
The **release directory** contains the release versions of the notebooks, which are the converted source notebooks and is used as a preview of what the student version of the notebook looks.
To view these directories, use the files card in the overview window of the assignment.
By switching between source and release file viewer, the extension will convert the source notebooks to their release versions.

.. image:: _static/assets/images/file_view.png
    :alt: file view

.. note::
    Just the source notebooks and files should be edited! Changes to files in the release directory will be lost when generating the files again.

The grader service and labextension use git to support the collaborative creation of assignments. Also, it provides a simple way to distribute the files to the students.
Notebooks can be added by either using the "Create a new notebook" button or by copying files directly into the correct source directory via the file browser on left-hand side.

The source directory can also be revealed in the JupyterLab file browser or be opened in a terminal window.

Creating a Notebook for an Assignment
=====================================

Up until now, no files have been added to the assignment. To have tasks for students to work on, notebooks have to be added to the assignment.
As mentioned previously, we can either add a notebook from the file view or create it using the JupyterLab launcher.

.. image:: _static/assets/images/creation_mode.png
    :width: 500
    :alt: creation mode
    :align: center

| For notebooks which are in the source directory, a creation mode can be enabled in the notebook toolbar. It adds widgets around notebook cells that can be used to control the function of the code cell.

Grader Cell Types:

- Readonly
    This cell is locked and editing is disabled.
- Autograded answer
    This cell contains the code for the solution of a task.
    It has to be surrounded by  ``BEGIN SOLUTION`` and ``END SOLUTION`` directives as comments around the actual solution code.
    Due to the directives, the code will be replaced by placeholder code such as ``raise NotImplementedError()``.
    Also, a hint can be given to students and solutions can be commented while grading.

    .. image:: _static/assets/images/autograded_answer.png
        :width: 500
        :alt: autograded answer
        :align: center

    .. warning::
        If the ``BEGIN SOLUTION`` and ``END SOLUTION`` directives are omitted, the solution code will end up in the released files!

- Autograded tests
    This cell contains the test cases to test the auto-graded answer given by students.
    These may be ``assert`` statements that check the implemented code.
    Invalid solutions have to lead to an exception.

    .. note::
        Part or all of the tests can be hidden with ``BEGIN HIDDEN TESTS`` and ``END HIDDEN TESTS`` directives.

    .. image:: _static/assets/images/autograded_test.png
        :width: 500
        :alt: autograded test
        :align: center

- Manual graded answer
    This cell type supports free-form answers from students.
    They should not be tested with automatic tests but are intended to be manually graded.
    The cells can be configured to either be code or markdown cells, so students can either implement code or answer in text.

    .. image:: _static/assets/images/manual_answer.png
        :width: 500
        :alt: manual answer
        :align: center


Assignment Lifecycle
=====================================

.. image:: _static/assets/images/assignment_status.png
    :width: 400
    :alt: assignment status
    :align: center

| An assignment can have 3 states that can be switched between and represent the lifecycle of the assignment.

- Edit
    When first created, the assignment is in "Edit mode", where the assignment files can be added and edited.
    In this stage, the assignment is not visible to students. However, when an instructor opens the student view ("Assignments" card in launcher), it will be displayed to them.
- Released
    The assignment is released to students and the students can work on it.
    The released files are identical to the files in the release directory at the time of the release.
    It is possible to undo the release and publish a new release. However, some students may have already pulled the old release.
    In this case the students might have to reset their files and might loose progress, which has to be communicated.
    In general, a re-release should be avoided.

    .. warning::
        Revoking a released assignment may lead to diverging states of student files and submissions that fail auto-grading.

- Completed
    The assignment is over and cannot be worked on anymore and new submissions will be rejected, but it is still visible.
    This state can be revoked without any consideration and will return to a released state.


Grading Assignments
=====================================

To grade student submissions navigate to submissions tab:

.. image:: _static/assets/images/submission_grading.png
    :alt: submission grading


| Submissions can be selected from the list and actions can be performed on the submissions.

Grader Service supports batch auto-grading and batch feedback generation of several submissions.
Naturally, submissions have to be manually graded individually.

Generally, submissions have to be auto-graded first before anything else can be done.
If manual grading is not needed or not wanted, it can be skipped.
The last step is feedback generation, at which point students will see their results.


Auto-Grading Behavior
-----------------------

In the edit and creation menu for an assignment, it is possible to select the auto-grading behavior for the assignment.
It specifies the action taken when a user submits an assignment.

- No Automatic Grading
    No action is taken when users submit the assignment.
- Automatic Grading (Recommended)
    The assignment is being auto-graded as soon as the user submits the assignment.
    This means that submissions in the grading view are always auto-graded.
- Fully Automatic Grading
    The assignment is auto-graded and feedback is generated as soon as the student submits their assignment.
    This requires that no manually graded cells are part of the assignment.

.. image:: _static/assets/images/autograding_behavior.png
    :width: 350
    :alt: autograding behavior
    :align: center


Student Guide
===============

When Juypterhub is launched students see only the Assignments card:

.. image:: _static/assets/images/student_launcher.png
    :alt: student launcher


| Studnets are presented with a list of courses they are enrolled in. They can also see completed lectures from previous semesters as well and take a look at their old assignments:

.. image:: _static/assets/images/student_lecture_list.png
    :alt: student lecture list 

| Each lecture has its dedicated assignment table, with each table cell representing an assignment along with a brief overview.

.. image:: _static/assets/gifs/student_assignment_table.gif
    :alt: assignment overview for studnets

| If a new assignment is released for students, students must first pull it from the remote repository in order to obtain assignment files they can work on. Afterwards, an "Edit" icon will be shown in the table cell.

| Each table cell displays the name of the assignment, indicates whether feedback for submission is available, and shows the maximum points reached in the submission. Each table cell also features a countdown of the deadline. Once the deadline has been reached, students can no longer submit the assignment files.

When clicking on an assignment table cell or the 'Detail View' button, students are presented with a detailed view of the assignment, allowing them to work on the assignment and make submissions.


.. image:: _static/assets/images/student_detail_view.png
    :alt: student view

| The status bar is supposed to guide the students through the stages, from working on the assignment to viewing the feedback they received.

The files in the assignment are displayed in a list and can be opened from there. The submit button submits the current state of the assignment.
To reset the assignment to its original state, students can use the reset button.
No progress is lost when resetting the assignment, the release state is just a new commit in the underlying git repository.

Submissions are shown in the submission list. On top of the submission list is a chip that tells the students wheter there is a limited number of submissions they are allowed to make until the deadline has been reached.
If a submission has feedback available, it will be displayed in this submission list and can be viewed from there.

.. image:: _static/assets/images/student_view_feedback.png
    :alt: student view feedback

| Once the student submissions have been graded and feedback is available we can see it in the submission list and can open the feedback view. It will present an overview of the score reached and a list of detailed feedback for each graded notebook.

.. image:: _static/assets/images/student_feedback_window.png
    :alt: feedback view

| The detailed feedback is a HTML file and shows the student answers along with the score and comments from instructors.

.. image:: _static/assets/images/feedback_html.png
    :alt: feedback html




