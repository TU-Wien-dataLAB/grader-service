import traceback

from nbformat.notebooknode import NotebookNode

from grader_service.convert.nbgraderformat import MetadataValidator, ValidationError
from grader_service.convert.preprocessors.base import NbGraderPreprocessor


class CheckCellMetadata(NbGraderPreprocessor):
    """A preprocessor for checking that grade ids are unique."""

    def preprocess(self, nb: NotebookNode, resources: dict) -> tuple[NotebookNode, dict]:
        try:
            MetadataValidator().validate_nb(nb)
        except ValidationError as e:
            self.log.error(traceback.format_exc())
            msg = "Notebook failed to validate: " + e.message
            self.log.error(msg)
            raise ValidationError(msg)

        return nb, resources
