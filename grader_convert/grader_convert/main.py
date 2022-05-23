

from textwrap import dedent

from grader_convert.converters.autograde import AutogradeApp
from grader_convert.converters.baseapp import (
    ConverterApp,
    base_converter_aliases,
    base_converter_flags,
)
from grader_convert.converters.generate_assignment import GenerateAssignmentApp
from grader_convert.converters.generate_feedback import GenerateFeedbackApp
from grader_convert.converters.generate_solution import GenerateSolutionApp
from grader_convert.converters.updateapp import UpdateApp
from grader_convert.converters.validateapp import ValidateApp

aliases = {}
aliases.update(base_converter_aliases)
aliases.update({})

flags = {}
flags.update(base_converter_flags)
flags.update({})


class GraderConverter(ConverterApp):

    name = u"grader-converter"
    description = u"Convert notebooks to different formats"
    version = ConverterApp.__version__

    aliases = aliases
    flags = flags

    subcommands = dict(
        generate_assignment=(
            GenerateAssignmentApp,
            dedent(
                """
                Create the student version of an assignment. Intended for use by
                instructors only.
                """
            ).strip(),
        ),
        generate_solution=(
            GenerateSolutionApp,
            dedent(
                """
                Generates the solution for the given assignment.
                """
            ).strip(),
        ),
        autograde=(
            AutogradeApp,
            dedent(
                """
                Autograde submitted assignments. Intended for use by instructors
                only.
                """
            ).strip(),
        ),
        generate_feedback=(
            GenerateFeedbackApp,
            dedent(
                """
                Generate feedback (after autograding and manual grading).
                Intended for use by instructors only.
                """
            ).strip(),
        ),
        validate=(
            ValidateApp,
            dedent(
                """
                Validate a notebook. Intended for use by instructors and students.
                """
            ).strip(),
        ),
        update=(
            UpdateApp,
            dedent(
                """
                Update nbgrader cell metadata to the most recent version.
                """
            ).strip(),
        ),
    )


def main():
    GraderConverter.launch_instance()


if __name__ == "__main__":
    main()
