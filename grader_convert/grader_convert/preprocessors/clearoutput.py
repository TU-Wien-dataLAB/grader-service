

from nbconvert.preprocessors import ClearOutputPreprocessor

from grader_convert.preprocessors.base import NbGraderPreprocessor


class ClearOutput(NbGraderPreprocessor, ClearOutputPreprocessor):
    pass
