import json

from nbconvert.exporters.exporter import ResourcesDict
from nbformat.notebooknode import NotebookNode

from grader_service.convert.gradebook.gradebook import Gradebook
from grader_service.convert.preprocessors.base import NbGraderPreprocessor


class OverwriteKernelspec(NbGraderPreprocessor):
    """A preprocessor for checking the notebook kernelspec metadata."""

    def preprocess(
        self, nb: NotebookNode, resources: ResourcesDict
    ) -> tuple[NotebookNode, ResourcesDict]:
        # pull information from the resources
        self.notebook_id = resources["unique_key"]
        self.json_path = resources["output_json_path"]

        with Gradebook(self.json_path) as gb:
            kernelspec = json.loads(gb.find_notebook(self.notebook_id).kernelspec)
            self.log.debug(f"Source notebook kernelspec: {kernelspec}")
            self.log.debug(
                "Submitted notebook kernelspec: {}".format(nb.metadata.get("kernelspec", None))
            )
            if kernelspec:
                self.log.info(f"Overwriting submitted notebook kernelspec: {kernelspec}")
                nb.metadata["kernelspec"] = kernelspec
        return nb, resources
