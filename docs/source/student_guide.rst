Student Guide
=============

Lectures and Assignments
------------------------

When Juypterhub is launched students see only the Assignments card:

.. image:: _static/assets/images/student_launcher.png
    :alt: student launcher


| Studnets are presented with a list of courses they are enrolled in. They can also see completed lectures from previous semesters as well and take a look at their old assignments:

.. image:: _static/assets/images/student_lecture_list.png
    :alt: student lecture list 

| Each lecture has its dedicated assignment table, with each table cell representing an assignment along with a brief overview.

.. image:: _static/assets/gifs/student_assignment_table.gif
    :alt: assignment overview for studnets

Working on Assignments
----------------------

| If a new assignment is released for students, students must first pull it from the remote repository in order to obtain assignment files they can work on. Afterwards, an "Edit" icon will be shown in the table cell.

| Each table cell displays the name of the assignment, indicates whether feedback for submission is available, and shows the maximum points reached in the submission. Each table cell also features a countdown of the deadline. Once the deadline has been reached, students can no longer submit the assignment files.

When clicking on an assignment table cell or the 'Detail View' button, students are presented with a detailed view of the assignment, allowing them to work on the assignment and make submissions.


.. image:: _static/assets/images/student_detail_view.png
    :alt: student view

| The status bar is supposed to guide the students through the stages, from working on the assignment to viewing the feedback they received.

The files in the assignment are displayed in a list and can be opened from there. The submit button submits the current state of the assignment.
To reset the assignment to its original state, students can use the reset button.
No progress is lost when resetting the assignment, the release state is just a new commit in the underlying git repository.

Submissions and Feedback
------------------------

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




