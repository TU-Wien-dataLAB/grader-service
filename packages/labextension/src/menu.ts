import {
  AssignmentsCommandIDs,
  CourseManageCommandIDs,
  GlobalObjects
} from './index';
import { getAllLectures } from './services/lectures.service';
import { Lecture } from './model/lecture';
import { AssignmentDetail } from './model/assignmentDetail';
import { Menu } from '@lumino/widgets';

export const getLabel = (assignment: AssignmentDetail | null) => {
  return assignment === null ? 'Overview' : assignment.name;
};

const getPath = (lecture: Lecture, assignment: AssignmentDetail | null) => {
  return `/lecture/${lecture.id}`;
};

export const updateMenus = async (reload: boolean = false) => {
  const aMenu = GlobalObjects.assignmentMenu;
  const cmMenu = GlobalObjects.courseManageMenu;
  const instructorLectures = await getAllLectures(
    { complete: false, instructor: true },
    reload
  );
  const lectures = await getAllLectures(
    { complete: false, instructor: false },
    reload
  );

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
