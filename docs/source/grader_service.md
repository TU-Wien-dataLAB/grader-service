# What is Grader Service?

Grader Service is the backend of the Grader platform. It exposes the REST endpoints used to create, read, update, delete and grade assignments, and it integrates a Git service from which lecturers can pull and push to collaborate on assignment creation and where student submissions are stored.

Grader Service is built for data science, machine learning and programming courses at schools and universities. Instructors and tutors use it to manage and grade assignments, while students use it to work on and submit them. Users normally do not talk to Grader Service directly; they access it through the Grader Labextension running inside JupyterLab on a JupyterHub server.


## As instructor
Grader Service allows you to choose different grading modes: whether you just want an environment that lets you collect student submissions and manually grade them, or fully automate the grading process and let Grader Service handle it for you. You can also combine both options, with some automated tests and tasks within assignments that you prefer to grade manually.

Explore the full guide on using Grader Service as a lecture instructor: [get started as an instructor](instructor_guide/get_started_instructor.md).

---

## As student
Our Grader Service is integrated with JupyterLab, providing an environment where you’re ready to start working on your assignment notebooks immediately. The Grader Labextension allows you to submit assignments and view your results once your instructor generates feedback.

Dive into the Grader Service guide to get the most out of your lecture experience! Check it out here: [Student Guide](student_guide.md).

---

## Grader Service at TU Wien

The Grader Service is an important component of the 🔎 [TU Wien dataLAB](https://colab.tuwien.ac.at/display/DLJAAS/dataLAB+Jupyter+as+a+Service) project. The dataLAB team offers lecturers at TU Wien the opportunity to seamlessly integrate a JupyterHub instance into their TUWEL spaces.

This service simplifies the process for instructors, eliminating the need for complex TUWEL configurations. Students can access their assignments directly through a link provided in TUWEL, allowing them to start working immediately-completely online and without the need to install resource-intensive software. dataLAB ensures that students have access to the necessary computational resources to complete their tasks effectively.

If you are a lecturer at TU Wien and would like to request a JupyterHub instance, please do so 📌 [here](https://colab.tuwien.ac.at/display/DLJAAS/Request+a+JupyterHub).
