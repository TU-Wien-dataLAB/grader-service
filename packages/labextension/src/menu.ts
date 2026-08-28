import {
  AssignmentsCommandIDs,
  CourseManageCommandIDs,
  GlobalObjects
} from './index';
import { Lecture } from './model/lecture';
import { AssignmentDetail } from './model/assignmentDetail';
import { Menu } from '@lumino/widgets';
import {
  activeInstructorLecturesQuery,
  activeLecturesQuery
} from './services/queries/lectures.queries';
import { queryClient } from './widget';

export const getLabel = (assignment: AssignmentDetail | null) => {
  return assignment === null ? 'Overview' : assignment.name;
};

const getPath = (lecture: Lecture, assignment: AssignmentDetail | null) => {
  return `/lecture/${lecture.id}`;
};

export const updateMenus = async (reload: boolean = false) => {
  const aMenu = GlobalObjects.assignmentMenu;
  const cmMenu = GlobalObjects.courseManageMenu;
  const [lectures, instructorLectures] = await Promise.all([
    queryClient.ensureQueryData(activeLecturesQuery()),
    queryClient.ensureQueryData(activeInstructorLecturesQuery())
  ]);

  aMenu.clearItems();
  lectures.forEach(v => {
    const subMenu = new Menu({ commands: GlobalObjects.commands });
    subMenu.title.label = v.name;

    const path = getPath(v, null);
    const label = getLabel(null);
    subMenu.addItem({
      type: 'command',
      command: AssignmentsCommandIDs.open,
      args: { path, label }
    });

    aMenu.addItem({
      type: 'submenu',
      submenu: subMenu
    });
  });
  aMenu.update();

  if (cmMenu) {
    cmMenu.clearItems();
    instructorLectures.forEach(v => {
      const subMenu = new Menu({ commands: GlobalObjects.commands });
      subMenu.title.label = v.name;

      const path = getPath(v, null);
      const label = getLabel(null);
      subMenu.addItem({
        type: 'command',
        command: CourseManageCommandIDs.open,
        args: { path, label }
      });

      cmMenu.addItem({
        type: 'submenu',
        submenu: subMenu
      });
    });
    cmMenu.update();
  }
};
