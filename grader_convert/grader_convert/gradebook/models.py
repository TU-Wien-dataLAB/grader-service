

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Dict, List, Optional, Set, Type, Union


@dataclass
class BaseModel:
    def __post_init__(self):
        self._type = self.__class__.__name__

    @classmethod
    def empty_dict(cls: Type["BaseModel"]) -> dict:
        fields = cls.__dataclass_fields__.keys()
        return {f: None for f in fields}

    def to_dict(self) -> dict:
        d = asdict(self)
        d["_type"] = self.__class__.__name__
        return d

    @classmethod
    def from_dict(cls: Type["BaseModel"], d: dict) -> Type["BaseModel"]:
        if d is None or len(d) == 0:
            return None
        d_no_type = {k: v for k, v in d.items() if k != "_type"}
        return cls(**d_no_type)


@dataclass
class IDMixin:
    id: str


@dataclass
class NameMixin:
    name: str


@dataclass
class NotebookRelashionship:
    notebook_id: str


@dataclass
class CellRelashionship:
    cell_id: str


@dataclass
class Grade(BaseModel, IDMixin, NotebookRelashionship, CellRelashionship):
    """Representation of a grade assigned to the submitted version of a grade cell."""

    auto_score: float
    manual_score: float
    extra_credit: float
    needs_manual_grade: bool
    #: The maximum possible score that can be assigned, inherited from :class:`~GradeCell`
    max_score_gradecell: float
    max_score_taskcell: float

    #: Whether the autograded score is a result of failed autograder tests. This
    #: is True if the autograder score is zero and the cell type is "code", and
    #: otherwise False.
    failed_tests: bool

    @property
    def score(self) -> float:
        """
        The overall score, computed automatically from the
        :attr:`~models.Grade.auto_score` and :attr:`~models.Grade.manual_score`
        values. If neither are set, the score is zero. If both are set, then the
        manual score takes precedence. If only one is set, then that value is used
        for the score
        """
        if self.manual_score is None and self.auto_score is None:
            return 0.0
        elif self.manual_score is None:
            return self.auto_score
        elif self.auto_score is None:
            return self.manual_score
        else:
            return self.manual_score

    @property
    def max_score(self):
        if self.max_score_taskcell:
            return self.max_score_taskcell
        else:
            return self.max_score_gradecell

    @classmethod
    def from_dict(cls: Type["Grade"], d: dict) -> Type["Grade"]:
        if d is None or len(d) == 0:
            return None
        d = {k: v for k, v in d.items() if k not in ["_type", "max_score"]}
        return cls(**d)

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["max_score"] = self.max_score
        return d


@dataclass
class Comment(BaseModel, IDMixin, NotebookRelashionship, CellRelashionship):
    auto_comment: str
    manual_comment: str

    @property
    def comment(self) -> Optional[str]:
        if self.manual_comment is None:
            return self.auto_comment
        else:
            return self.manual_comment


class CellType(Enum):
    "code"
    "markdown"


@dataclass
class BaseCell(BaseModel, IDMixin, NameMixin, NotebookRelashionship):
    grade_id: str  # we can have only one grade
    comment_id: str  # we can have only one comment since we only process a single notebook

    @classmethod
    def from_dict(cls: Type["BaseCell"], d: dict) -> Type["BaseCell"]:
        if d["_type"] == "GradeCell":
            return GradeCell.from_dict(d)
        elif d["_type"] == "SolutionCell":
            return SolutionCell.from_dict(d)
        elif d["_type"] == "TaskCell":
            return TaskCell.from_dict(d)
        elif d["_type"] == "SourceCell":
            return SourceCell.from_dict(d)


@dataclass
class GradedMixin:
    max_score: float
    cell_type: CellType


@dataclass
class GradeCell(BaseCell, GradedMixin):
    @classmethod
    def from_dict(cls: Type["BaseCell"], d: dict) -> "GradeCell":
        return GradeCell(
            max_score=d["max_score"],
            cell_type=d["cell_type"],
            id=d["id"],
            notebook_id=d["notebook_id"],
            name=d["name"],
            grade_id=d["grade_id"],
            comment_id=d["comment_id"],
        )


@dataclass
class SolutionCell(BaseCell):
    @classmethod
    def from_dict(cls: Type["BaseCell"], d: dict) -> "SolutionCell":
        return SolutionCell(
            id=d["id"],
            notebook_id=d["notebook_id"],
            name=d["name"],
            grade_id=d["grade_id"],
            comment_id=d["comment_id"],
        )


@dataclass
class TaskCell(BaseCell, GradedMixin):
    @classmethod
    def from_dict(cls: Type["BaseCell"], d: dict) -> "TaskCell":
        return TaskCell(
            max_score=d["max_score"],
            cell_type="code",  # cell_type from GradedMixin should always be 'code'
            id=d["id"],
            notebook_id=d["notebook_id"],
            name=d["name"],
            grade_id=d["grade_id"],
            comment_id=d["comment_id"],
        )


@dataclass
class SourceCell(BaseModel, IDMixin, NameMixin, NotebookRelashionship):
    cell_type: CellType

    #: Whether the cell is locked (e.g. the source saved in the database should
    #: be used to overwrite the source of students' cells)
    locked: bool

    #: The source code or text of the cell
    source: str

    #: A checksum of the cell contents. This should usually be computed
    #: using :func:`utils.compute_checksum`
    checksum: str

    @classmethod
    def from_dict(cls: Type["BaseModel"], d: dict) -> Type["BaseModel"]:
        return super().from_dict(d)


@dataclass
class Notebook(BaseModel, IDMixin, NameMixin):
    kernelspec: str
    grade_cells_dict: Dict[str, Type[GradeCell]]
    solution_cells_dict: Dict[str, Type[SolutionCell]]
    task_cells_dict: Dict[str, Type[TaskCell]]
    source_cells_dict: Dict[str, Type[SourceCell]]
    grades_dict: Dict[str, Type[Grade]]
    comments_dict: Dict[str, Type[Comment]]
    #: Whether this assignment has been flagged by a human grader
    flagged: bool

    def __post_init__(self):
        super().__post_init__()
        if self.flagged is None:
            self.flagged = False

    @property
    def grade_cells(self) -> List[GradeCell]:
        return [x for x in self.grade_cells_dict.values() if isinstance(x, GradeCell)]

    @property
    def solution_cells(self) -> List[SolutionCell]:
        return [
            x for x in self.solution_cells_dict.values() if isinstance(x, SolutionCell)
        ]

    @property
    def task_cells(self) -> List[TaskCell]:
        return [x for x in self.task_cells_dict.values() if isinstance(x, TaskCell)]

    @property
    def source_cells(self) -> List[SourceCell]:
        return [x for x in self.source_cells_dict.values()]

    @property
    def graded_cells(self) -> List[Union[GradeCell, TaskCell]]:
        return self.grade_cells + self.task_cells

    @property
    def max_score(self) -> float:
        return sum([g.max_score for g in self.graded_cells])

    @property
    def score(self) -> float:
        return sum([gr.score for gr in self.grades_dict.values()])

    @property
    def code_score(self) -> float:
        return sum(
            [
                self.grades_dict[g.grade_id].score
                for g in self.graded_cells
                if g.cell_type == "code" and g is not None and g.grade_id is not None
            ]
        )

    @property
    def max_code_score(self) -> float:
        return sum([g.max_score for g in self.graded_cells if g.cell_type == "code"])

    @property
    def written_score(self) -> float:
        return sum(
            [
                self.grades_dict[g.grade_id].score
                for g in self.graded_cells
                if g.cell_type == "markdown"
            ]
        )

    @property
    def max_written_score(self) -> float:
        return sum(
            [g.max_score for g in self.graded_cells if g.cell_type == "markdown"]
        )

    @property
    def failed_tests(self) -> bool:
        return any([g.failed_tests for g in self.grades])

    @property
    def grades(self) -> List[Type[Grade]]:
        return list(self.grades_dict.values())

    @property
    def comments(self) -> List[Type[Comment]]:
        return list(self.comments_dict.values())

    @classmethod
    def from_dict(cls: Type["Notebook"], d: dict) -> "Notebook":
        gc = {id: GradeCell.from_dict(v) for id, v in d["grade_cells_dict"].items()}
        sc = {i: SolutionCell.from_dict(v) for i, v in d["solution_cells_dict"].items()}
        tc = {id: TaskCell.from_dict(v) for id, v in d["task_cells_dict"].items()}
        sr = {id: SourceCell.from_dict(v) for id, v in d["source_cells_dict"].items()}
        gr = {id: Grade.from_dict(v) for id, v in d["grades_dict"].items()}
        co = {id: Comment.from_dict(v) for id, v in d["comments_dict"].items()}
        return Notebook(
            kernelspec=d["kernelspec"],
            grade_cells_dict=gc,
            solution_cells_dict=sc,
            task_cells_dict=tc,
            id=d["id"],
            name=d["name"],
            flagged=d["flagged"],
            source_cells_dict=sr,
            grades_dict=gr,
            comments_dict=co,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "flagged": self.flagged,
            "kernelspec": self.kernelspec,
            "grade_cells_dict": {
                k: v.to_dict() for k, v in self.grade_cells_dict.items()
            },
            "solution_cells_dict": {
                k: v.to_dict() for k, v in self.solution_cells_dict.items()
            },
            "task_cells_dict": {
                k: v.to_dict() for k, v in self.task_cells_dict.items()
            },
            "source_cells_dict": {
                k: v.to_dict() for k, v in self.source_cells_dict.items()
            },
            "grades_dict": {k: v.to_dict() for k, v in self.grades_dict.items()},
            "comments_dict": {k: v.to_dict() for k, v in self.comments_dict.items()},
            "_type": self._type,
        }


@dataclass
class GradeBookModel(BaseModel):
    notebooks: Dict[str, Notebook]

    @property
    def score(self) -> float:
        score = 0
        for nb in self.notebooks.values():
            score += nb.score
        return score

    @property
    def notebook_id_set(self) -> Set[Notebook]:
        return {x for x in self.notebooks.keys()}

    @classmethod
    def from_dict(cls: Type["GradeBookModel"], d: dict) -> "GradeBookModel":
        ns = {id: Notebook.from_dict(v) for id, v in d["notebooks"].items()}
        return GradeBookModel(notebooks=ns)

    def to_dict(self) -> dict:
        return {
            "notebooks": {k: v.to_dict() for k, v in self.notebooks.items()},
            "_type": self._type,
            "schema_version": "1",
        }
