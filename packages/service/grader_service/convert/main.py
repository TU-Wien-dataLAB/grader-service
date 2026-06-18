from textwrap import dedent

from grader_service.convert.converters.autograde import AutogradeApp
from grader_service.convert.converters.baseapp import (
    ConverterApp,
    base_converter_aliases,
    base_converter_flags,
)
from grader_service.convert.converters.generate_assignment import GenerateAssignmentApp
from grader_service.convert.converters.generate_feedback import GenerateFeedbackApp

aliases = {}
aliases.update(base_converter_aliases)
aliases.update({})

flags = {}
flags.update(base_converter_flags)
flags.update({})


class GraderConverter(ConverterApp):
    name = "grader-converter"
    description = "Convert notebooks to different formats"
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
    )


def main():
    GraderConverter.launch_instance()


if __name__ == "__main__":
    main()
