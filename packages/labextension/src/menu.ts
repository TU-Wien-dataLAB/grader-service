import { GlobalObjects, GraderServiceCommandIDs } from './index';
import { Lecture } from './model/lecture';
import { AssignmentDetail } from './model/assignmentDetail';
import { Menu } from '@lumino/widgets';
import { activeLecturesQuery } from './services/queries/lectures.queries';
import { queryClient } from './widget';

export const getLabel = (assignment: AssignmentDetail | null) => {
  return assignment === null ? 'Overview' : assignment.name;
};

const getPath = (lecture: Lecture, assignment: AssignmentDetail | null) => {
  return `lectures/${lecture.id}`;
};

export const updateMenus = async (reload: boolean = false) => {
  const menu = GlobalObjects.graderServiceMenu;
  const [lectures] = await Promise.all([
    queryClient.ensureQueryData(activeLecturesQuery())
  ]);

  menu.clearItems();
  lectures.forEach(v => {
    const subMenu = new Menu({ commands: GlobalObjects.commands });
    subMenu.title.label = v.name;

    const path = getPath(v, null);
    const label = getLabel(null);
    subMenu.addItem({
      type: 'command',
      command: GraderServiceCommandIDs.open,
      args: { path, label }
    });

    menu.addItem({
      type: 'submenu',
      submenu: subMenu
    });
  });
  menu.update();
};
