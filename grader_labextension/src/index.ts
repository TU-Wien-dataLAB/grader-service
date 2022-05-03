// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

/* eslint-disable no-constant-condition */
/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable no-prototype-builtins */
import {
  ILayoutRestorer,
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import {
  ICommandPalette,
  MainAreaWidget,
  WidgetTracker,
  IWidgetTracker
} from '@jupyterlab/apputils';

import { ILauncher } from '@jupyterlab/launcher';
import { INotebookTools, Notebook, NotebookPanel } from '@jupyterlab/notebook';

import { CourseManageView } from './widgets/coursemanage';

import { Cell } from '@jupyterlab/cells';

import { INotebookTracker } from '@jupyterlab/notebook';

import { CellWidget } from './components/notebook/create-assignment/cellwidget';

import { PanelLayout } from '@lumino/widgets';

import { NotebookModeSwitch } from './components/notebook/slider';

import { checkIcon, editIcon } from '@jupyterlab/ui-components';
import { CommandRegistry } from '@lumino/commands';
import { DocumentRegistry } from '@jupyterlab/docregistry';
import { ServiceManager } from '@jupyterlab/services';
import { IDocumentManager } from '@jupyterlab/docmanager';
import { IFileBrowserFactory } from '@jupyterlab/filebrowser';
import { UserPermissions } from './services/permission.service';
import { CellPlayButton } from './components/notebook/create-assignment/widget';
import { AssignmentList } from './widgets/assignment-list';
import { CreationWidget } from './components/notebook/create-assignment/creation-widget';

namespace AssignmentsCommandIDs {
  export const create = 'assignments:create';

  export const open = 'assignments:open';
}

namespace CourseManageCommandIDs {
  export const create = 'coursemanage:create';

  export const open = 'coursemanage:open';
}

namespace GradingCommandIDs {
  export const create = 'grading:create';

  export const open = 'grading:open';
}

namespace ManualGradeCommandIDs {
  export const create = 'manualgrade:create';

  export const open = 'manualgrade:open';
}

namespace FeedbackCommandIDs {
  export const create = 'feedback:create';

  export const open = 'feedback:open';
}

export class GlobalObjects {
  static commands: CommandRegistry;
  static docRegistry: DocumentRegistry;
  static serviceManager: ServiceManager;
  static docManager: IDocumentManager;
  static browserFactory: IFileBrowserFactory;
  static tracker: INotebookTracker;
}

/**
 * Initialization data for the grading extension.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: 'coursemanage:plugin',
  autoStart: true,
  requires: [
    ICommandPalette,
    ILauncher,
    INotebookTools,
    IDocumentManager,
    IFileBrowserFactory,
    INotebookTracker,
    ILayoutRestorer
  ],
  activate: (
    app: JupyterFrontEnd,
    palette: ICommandPalette,
    launcher: ILauncher,
    nbtools: INotebookTools,
    docManager: IDocumentManager,
    browserFactory: IFileBrowserFactory,
    tracker: INotebookTracker,
    restorer: ILayoutRestorer
  ) => {
    console.log('JupyterLab extension grader_labextension is activated!');
    console.log('JupyterFrontEnd:', app);
    console.log('ICommandPalette:', palette);
    console.log('Tracker', tracker);

    GlobalObjects.commands = app.commands;
    GlobalObjects.docRegistry = app.docRegistry;
    GlobalObjects.serviceManager = app.serviceManager;
    GlobalObjects.docManager = docManager;
    GlobalObjects.browserFactory = browserFactory;
    GlobalObjects.tracker = tracker;

    const assignmentTracker = new WidgetTracker<MainAreaWidget<AssignmentList>>(
      {
        namespace: 'grader-assignments'
      }
    );

    restorer.restore(assignmentTracker, {
      command: AssignmentsCommandIDs.open,
      name: () => 'grader-assignments'
    });

    const courseManageTracker = new WidgetTracker<
      MainAreaWidget<CourseManageView>
    >({
      namespace: 'grader-coursemanage'
    });

    restorer.restore(courseManageTracker, {
      command: CourseManageCommandIDs.open,
      name: () => 'grader-coursemanage'
    });

    //Creation of in-cell widget for create assignment
    const connectTrackerSignals = (tracker: INotebookTracker) => {
      tracker.currentChanged.connect(async () => {
        const notebookPanel = tracker.currentWidget;
        const notebook: Notebook = tracker.currentWidget.content;
        const mode = false;

        notebookPanel.context.ready.then(() => {
          //Creation of widget switch
          const switcher: NotebookModeSwitch = new NotebookModeSwitch(
            mode,
            notebookPanel,
            notebook
          );
          notebookPanel.toolbar.insertItem(10, 'Creationmode', switcher);
        });
      }, this);

      tracker.activeCellChanged.connect(() => {
        const notebookPanel: NotebookPanel = tracker.currentWidget;
        const notebook: Notebook = tracker.currentWidget.content;
        const notebookPaths: string[] = notebookPanel.context.contentsModel.path.split(
          '/'
        );
        if (notebookPaths[0] === 'manualgrade') {
          return;
        }
        const switcher: any = (notebookPanel.toolbar.layout as PanelLayout)
          .widgets[10];

        const cell: Cell = notebook.activeCell;

        //check if in creationmode and new cell was inserted
        if (
          switcher.mode &&
          (cell.layout as PanelLayout).widgets.every(w => {
            if (w instanceof CreationWidget) {
              return false;
            }
            return true;
          })
        ) {
          (cell.layout as PanelLayout).insertWidget(0, new CreationWidget(cell));
        }
      }, this);
    };

    /* ##### Course Manage View Widget ##### */
    let command: string = CourseManageCommandIDs.create;
    app.commands.addCommand(command, {
      execute: () => {
        // Create a blank content widget inside of a MainAreaWidget
        const gradingView = new CourseManageView();
        const gradingWidget = new MainAreaWidget<CourseManageView>({
          content: gradingView
        });
        gradingWidget.id = 'coursemanage-jupyterlab';
        gradingWidget.title.label = 'Course Management';
        gradingWidget.title.closable = true;

        courseManageTracker.add(gradingWidget);

        return gradingWidget;
      }
    });

    command = AssignmentsCommandIDs.create;
    app.commands.addCommand(command, {
      execute: () => {
        // Create a blank content widget inside of a MainAreaWidget
        const assignmentList = new AssignmentList();
        const assignmentWidget = new MainAreaWidget<AssignmentList>({
          content: assignmentList
        });
        assignmentWidget.id = 'assignments-jupyterlab';
        assignmentWidget.title.label = 'Assignments';
        assignmentWidget.title.closable = true;

        assignmentTracker.add(assignmentWidget);

        return assignmentWidget;
      }
    });

    // If the user has no instructor roles in any lecture we do not display the course management
    UserPermissions.loadPermissions().then(() => {
      const permissions = UserPermissions.getPermissions();
      let sum = 0;
      for (const el in permissions) {
        if (permissions.hasOwnProperty(el)) {
          sum += permissions[el];
        }
      }
      if (sum !== 0) {
        console.log(
          'Non-student permissions found! Adding coursemanage launcher and connecting creation mode'
        );
        connectTrackerSignals(tracker);

        command = CourseManageCommandIDs.open;
        app.commands.addCommand(command, {
          label: 'Course Management',
          execute: async () => {
            const gradingWidget = await app.commands.execute(
              CourseManageCommandIDs.create
            );

            if (!gradingWidget.isAttached) {
              // Attach the widget to the main work area if it's not there
              app.shell.add(gradingWidget, 'main');
            }
            // Activate the widget
            app.shell.activateById(gradingWidget.id);
          },
          icon: checkIcon
        });

        // Add the command to the launcher
        console.log('Add course management launcher');
        launcher.add({
          command: command,
          category: 'Assignments',
          rank: 0
        });
      }

      // only add assignment list if user permissions can be loaded
      command = AssignmentsCommandIDs.open;
      app.commands.addCommand(command, {
        label: 'Assignments',
        execute: async () => {
          const assignmentWidget: MainAreaWidget<AssignmentList> = await app.commands.execute(
            AssignmentsCommandIDs.create
          );

          if (!assignmentWidget.isAttached) {
            // Attach the widget to the main work area if it's not there
            app.shell.add(assignmentWidget, 'main');
          }
          // Activate the widget
          app.shell.activateById(assignmentWidget.id);
        },
        icon: editIcon
      });

      // Add the command to the launcher
      console.log('Add assignment launcher');
      launcher.add({
        command: command,
        category: 'Assignments',
        rank: 0
      });
    });
  }
};

export default extension;