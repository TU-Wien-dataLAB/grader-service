# First Time in Grader Service

The labextension consists of two launchers:

- **Assignment Launcher**:  Opens a window where students can pull and work on assignments you have published for them. You as instructor can also access this launcher and see how the assignment looks like for students.

- **Course Management launcher** : Opens a dashboard  for instructors where you can add, edit and delete assignments. The course management launcher is only visible if the current user is at least a tutor in one lecture.


![Launcher Window](../_static/assets/images/instructor_guide/launcher.png)

:::{note}
If you do not see the launcher items, it may be the case that extensions might be disabled in JupyterLab. You can find how to enable extensions [here](https://jupyterlab.readthedocs.io/en/stable/user/extensions.html#managing-extensions-using-the-extension-manager). Another reason might be that the grader service is not running. However, there will be a warning if this is the case.
:::

# Rename Lecture

When JupyterHub is set up for your lecture for the first time, it is named after the lecture code followed by the semester for which it was created. To make it clearer for students (and for yourself), you may want to rename the lecture to its actual title. The system will prompt you to do this if the lecture name displayed in JupyterHub matches the lecture code.

![Rename Lecture](../_static/assets/gifs/instructor_guide/rename_lecture.gif)

