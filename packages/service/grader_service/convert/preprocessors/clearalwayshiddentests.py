import warnings
from textwrap import dedent
from typing import Tuple

from nbconvert.exporters.exporter import ResourcesDict
from nbformat.notebooknode import NotebookNode
from traitlets import Bool, Unicode, observe

from grader_service.convert import utils
from grader_service.convert.preprocessors.base import NbGraderPreprocessor


class ClearAlwaysHiddenTests(NbGraderPreprocessor):
    begin_util_delimiter = Unicode(
        "BEGIN ALWAYS HIDDEN TESTS", help="The delimiter marking the beginning of hidden util code"
    ).tag(config=True)

    end_util_delimiter = Unicode(
        "END ALWAYS HIDDEN TESTS", help="The delimiter marking the end of hidden tests cases"
    ).tag(config=True)

    # Deprecated aliases (removed in a future release)
    begin_util_delimeter = Unicode(help="Deprecated alias for begin_util_delimiter.").tag(
        config=True
    )
    end_util_delimeter = Unicode(help="Deprecated alias for end_util_delimiter.").tag(config=True)

    @observe("begin_util_delimeter")
    def _begin_util_delimeter_changed(self, change):
        warnings.warn(
            "begin_util_delimeter is deprecated; use begin_util_delimiter",
            DeprecationWarning,
            stacklevel=2,
        )
        self.begin_util_delimiter = change.new

    @observe("end_util_delimeter")
    def _end_util_delimeter_changed(self, change):
        warnings.warn(
            "end_util_delimeter is deprecated; use end_util_delimiter",
            DeprecationWarning,
            stacklevel=2,
        )
        self.end_util_delimiter = change.new

    enforce_metadata = Bool(
        True,
        help=dedent(
            """
            Whether or not to complain if cells containing hidden util regions
            are not marked as grade cells.
            """
        ),
    ).tag(config=True)

    def _remove_hidden_util_region(self, cell: NotebookNode) -> bool:
        """Find a region in the cell that is delimeted by
        `self.begin_util_delimiter` and `self.end_util_delimiter` (e.g.  ###
        BEGIN HIDDEN UTILS and ### END HIDDEN UTILS). Remove that region
        depending on the cell type.

        This modifies the cell in place, and then returns True if a
        hidden test region was removed, and False otherwise.
        """
        # pull out the cell input/source
        lines = cell.source.split("\n")

        new_lines = []
        in_util = False
        removed_util = False

        for line in lines:
            # begin the test area
            if self.begin_util_delimiter in line:
                # check to make sure this isn't a nested BEGIN ALWAYS HIDDEN UTILS
                # region
                if in_util:
                    raise RuntimeError("Encountered nested begin always hidden statements")
                in_util = True
                removed_util = True

            # end the utils area
            elif self.end_util_delimiter in line:
                in_util = False

            # add lines as long as it's not in the hidden util region
            elif not in_util:
                new_lines.append(line)

        # we finished going through all the lines, but didn't find a
        # matching END HIDDEN UTILS statment
        if in_util:
            raise RuntimeError("No end always hidden utils statement found")

        # replace the cell source
        cell.source = "\n".join(new_lines)

        return removed_util

    def preprocess(
        self, nb: NotebookNode, resources: ResourcesDict
    ) -> Tuple[NotebookNode, ResourcesDict]:
        nb, resources = super(ClearAlwaysHiddenTests, self).preprocess(nb, resources)
        if "celltoolbar" in nb.metadata:
            del nb.metadata["celltoolbar"]
        return nb, resources

    def preprocess_cell(
        self, cell: NotebookNode, resources: ResourcesDict, cell_index: int
    ) -> Tuple[NotebookNode, ResourcesDict]:
        # remove hidden test regions
        removed_util = self._remove_hidden_util_region(cell)

        # determine whether the cell is a grade cell
        is_grade = utils.is_grade(cell)

        # check that it is marked as a grade cell if we remove a test
        # region -- if it's not, then this is a problem, because the cell needs
        # to be given an id
        if not is_grade and removed_util:
            if self.enforce_metadata:
                raise RuntimeError(
                    "Hidden util region detected in a non-grade cell; "
                    "please make sure all solution regions are within "
                    "'Autograded test cells' cells."
                )

        return cell, resources
