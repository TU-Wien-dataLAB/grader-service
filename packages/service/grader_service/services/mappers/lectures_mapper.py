from grader_service.api.models import LectureListItemDto, LectureDetailDto
from grader_service.orm import Lecture


def to_lecture_list_item_dto(lecture: Lecture, assignment_count, student_count=None):
    return LectureListItemDto(
        lecture.id, lecture.name, lecture.code, lecture.state, assignment_count, student_count
    )


def to_lecture_detail_dto(lecture: Lecture):
    return LectureDetailDto(lecture.id, lecture.name, lecture.code, lecture.state)
