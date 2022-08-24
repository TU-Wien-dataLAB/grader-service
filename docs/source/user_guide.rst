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
tutor in one lecture.

.. image:: _static/assets/images/launcher.png
    :alt: launcher window

Create Your First Assignment
=============================
Before students can access the notebooks an assignment must be created.
To access this feature open the course management dashboard:

.. image:: _static/assets/images/course_management.png
    :alt: course management dashboard

The course management dashboard lists all lectures and their assignments the current user is assigned to
as instructor. By pressing on the plus field below the lecture name instructors can
add new assignments to the lecture:

.. image:: _static/assets/images/add_assignment.png
    :alt: add assignment dialog

Working With Assignments
========================
In the overview window of the assignment you will find many ways to monitor, grade and extend the current assignment.

Files
--------------------
Every assignment has two important directories.
The source directory contains the source notebooks which instructors create for their assignment.
The release directory contains the release notebooks which are the converted source notebooks and is used as a local preview of their assignment notebooks.
To view these directories use the files card in the overview window of the assignment.
By switching between source and release file viewer the extension will convert the source notebooks to release notebooks.

The grader service and labextension use git to support collaborative creation of assignments. Also it provides a simple way to distribute the files to the students.
Notebooks can be added by either using the "Create a new notebook" button or by copying files directly in the correct source directory via the filebrowser.





