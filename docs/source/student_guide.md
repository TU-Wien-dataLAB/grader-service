# Student Guide

<!-- TODO: should not mention students in 3rd person -->

## Lectures and Assignments

When JuypterHub is launched you see the Assignments card in the launcher:

```{image} _static/assets/images/student_launcher.png
:alt: student launcher
```

You can also access the assignments through the 'Assignments' menu bar item.

<!-- TODO: Add image of menu bar item. -->

```{image} _static/assets/images/assignments_menu_item.png
:alt: menu bar items
```

When clicking on the assignment panel, you are presented with a list of courses you are enrolled in. They can also see completed lectures from previous semesters as well and take a look at your old assignments.

```{image} _static/assets/images/student_lecture_list.png
:alt: student lecture list
```

Each lecture has its dedicated assignment table, with each table cell representing an assignment along with a brief overview.

```{image} _static/assets/gifs/student_assignment_table.gif
:alt: assignment overview for students
```

## Working on Assignments

If a new assignment is released for students, students must first pull it from the remote repository in order to obtain assignment files they can work on. Afterwards, an "Edit" icon will be shown in the table cell.

Each table cell displays the name of the assignment, indicates whether feedback for submission is available, and shows the maximum points reached in the submission. Each table cell also features a countdown of the deadline. Once the deadline has been reached, students can no longer submit the assignment files.

When clicking on an assignment table cell or the 'Detail View' button, students are presented with a detailed view of the assignment, allowing them to work on the assignment and make submissions.

```{image} _static/assets/images/student_detail_view.png
:alt: student view
```

The status bar is supposed to guide the students through the stages, from working on the assignment to viewing the feedback they received.

The files in the assignment are displayed in a list and can be opened from there. The submit button submits the current state of the assignment.
To reset the assignment to its original state, students can use the reset button.
No progress is lost when resetting the assignment, the release state is just a new commit in the underlying git repository.

## Submissions and Feedback

Submissions are shown in the submission list. On top of the submission list is a chip that tells the students whether there is a limited number of submissions they are allowed to make until the deadline has been reached.

```{image} _static/assets/images/student_view_feedback.png
:alt: student view feedback
```

## Late Submissions

The system allows for late submissions, but with penalties applied based on the amount of delay after the deadline, if configured by the instructor.

**Penalty Multiplier**:  
When an assignment allows for late submission and a submission is made after the initial deadline, a penalty multiplier will be applied to the score. The later the submission, the higher the penalty. The exact penalty schedule and multipliers are determined by the course settings (e.g., 10% deduction per day late).

**Late Submission Period**:  
After the late submission period(s), no further submissions are allowed. This means once this period has passed, submitting assignments will no longer be possible, and it will be treated as if the regular deadline has expired. The specific duration of the late submission period (e.g., 2 days, 1 week) depends on the course setup.

<!-- TODO: image -->

## Deleting Submissions

You have the option to delete your submissions, but this action has certain limitations. When you delete a submission, it will no longer appear in the instructor's grading view. This prevents the deleted submission from being reviewed or graded. However, the deletion only affects the grading process and not the underlying submission record.

**Impact on Submission Limit**:  
If there is a submission limit set for the assignment (e.g., students can only submit up to 3 times), deleting a submission does not restore a submission opportunity. Each deleted submission will still count toward the total submission limit. For example, if you submit twice and delete both submissions, you will still only have one remaining submission attempt.

## Restoring Submissions

You have the ability to restore a previous submission, which reverts the assignment files to the state they were in during that submission.

**Restore Submission Functionality**:  
At any point, you can choose to restore the files associated with any of your previous submissions. When you select this option, the system will reset the current state of your assignment to match the files and conditions of the selected submission. This can be useful if you want to revert changes you’ve made since the last submission or review and edit based on a prior version.

**Current State Is Not Saved**:  
Restoring a submission will overwrite the current state of your assignment. The files in your workspace will be replaced with those from the restored submission, and any unsaved progress will be lost. You can restore any of your previous submissions, whether it’s the most recent one or an earlier version. There’s no limit to how many times you can restore a submission.


Once the student submissions have been graded and feedback is available we can see it in the submission list and can open the feedback view. It will present an overview of the score reached and a list of detailed feedback for each graded notebook.

```{image} _static/assets/images/student_feedback_window.png
:alt: feedback view
```

The detailed feedback is a HTML file and shows the student answers along with the score and comments from instructors.

```{image} _static/assets/images/feedback_html.png
:alt: feedback html
```
