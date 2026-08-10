// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.
// noinspection TypeScriptValidateTypes

/* eslint-disable no-constant-condition */
/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable no-prototype-builtins */
import {
  ILayoutRestorer,
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import {
  Dialog,
  ICommandPalette,
  IThemeManager,
  MainAreaWidget,
  showDialog,
  showErrorMessage,
  WidgetTracker
} from '@jupyterlab/apputils';

import { ILauncher } from '@jupyterlab/launcher';
import {
  INotebookTools,
  INotebookTracker,
  Notebook,
  NotebookPanel
} from '@jupyterlab/notebook';

import { IMainMenu } from '@jupyterlab/mainmenu';

import { GraderServiceWidget } from './widget';

import { Cell } from '@jupyterlab/cells';

import { Menu, PanelLayout } from '@lumino/widgets';

import { NotebookModeSwitch } from './components/notebook/slider';

import { homeIcon, runIcon } from '@jupyterlab/ui-components';
import { CommandRegistry } from '@lumino/commands';
import { DocumentRegistry } from '@jupyterlab/docregistry';
import { Contents, ServiceManager } from '@jupyterlab/services';
import { IDocumentManager } from '@jupyterlab/docmanager';
import { IFileBrowserFactory } from '@jupyterlab/filebrowser';
import { UserPermissions } from './services/permission.service';
import { CreationWidget } from './components/notebook/create-assignment/creation-widget';
import {
  listIcon,
  undoIcon
} from '@jupyterlab/ui-components/lib/icon/iconimports';
import { HintWidget } from './components/notebook/student-plugin/hint-widget';
import { DeadlineWidget } from './components/notebook/student-plugin/deadline-widget';
import { lectureSubPaths } from './services/file.service';
import { updateMenus } from './menu';
import { loadString } from './services/storage.service';
import IModel = Contents.IModel;

export namespace GraderServiceCommandIDs {
  export const create = 'graderservice:create';

  export const open = 'graderservice:open';
}

namespace NotebookExecuteIDs {
  export const run = 'notebookplugin:run-cell';
}

namespace RevertCellIDs {
  export const revert = 'notebookplugin:revert-cell';
}

namespace ShowHintIDs {
  export const show = 'notebookplugin:show-hint';
}

export class GlobalObjects {
  static commands: CommandRegistry;
  static docRegistry: DocumentRegistry;
  static serviceManager: ServiceManager.IManager;
  static docManager: IDocumentManager;
  static browserFactory: IFileBrowserFactory;
  static tracker: INotebookTracker;
  static themeManager: IThemeManager;
  static graderServiceMenu: Menu;
}

const createGraderServiceCommands = (
  app: JupyterFrontEnd,
  launcher: ILauncher,
  courseManageTracker: WidgetTracker<MainAreaWidget<GraderServiceWidget>>
) => {
  // add create widget command
  app.commands.addCommand(GraderServiceCommandIDs.create, {
    execute: () => {
      // Create a blank content widget inside of a MainAreaWidget
      const graderServiceWidget = new MainAreaWidget<GraderServiceWidget>({
        content: new GraderServiceWidget()
      });
      graderServiceWidget.id = 'grader-service';
      graderServiceWidget.title.label = 'Grader Service';
      graderServiceWidget.title.closable = true;

      courseManageTracker.add(graderServiceWidget);

      return graderServiceWidget;
    }
  });
  // add open widget command
  app.commands.addCommand(GraderServiceCommandIDs.open, {
    label: args =>
      args['label'] ? (args['label'] as string) : 'Grader Service',
    execute: async args => {
      let graderServiceWidget = courseManageTracker.currentWidget;
      if (!graderServiceWidget) {
        graderServiceWidget = await app.commands.execute(
          GraderServiceCommandIDs.create
        );
      }

      let path = args?.path as string;
      if (args?.path === undefined) {
        const savedPath = loadString('grader-service-router-path');
        if (savedPath !== null && savedPath !== '') {
          path = savedPath;
        } else {
          path = '/';
        }
      }
      await graderServiceWidget.content.router.navigate(path);

      if (!graderServiceWidget.isAttached) {
        // Attach the widget to the main work area if it's not there
        app.shell.add(graderServiceWidget, 'main');
      }
      // Activate the widget
      app.shell.activateById(graderServiceWidget.id);
    },
    icon: args => (args['path'] ? undefined : homeIcon)
  });
  // Add the command to the launcher
  launcher.add({
    command: GraderServiceCommandIDs.open,
    category: 'Grader Service',
    rank: 0
  });
};

//Creation of in-cell widget for create assignment
const connectTrackerSignals = (tracker: INotebookTracker) => {
  tracker.currentChanged.connect(async () => {
    const notebookPanel = tracker.currentWidget;
    //Notebook not yet loaded
    if (notebookPanel === null) {
      return;
    }
    const notebook: Notebook = tracker.currentWidget.content;
    const mode = false;

    notebookPanel.context.ready.then(() => {
      //Creation of widget switch
      const switcher: NotebookModeSwitch = new NotebookModeSwitch(
        mode,
        notebookPanel,
        notebook
      );

      tracker.currentWidget.toolbar.insertItem(10, 'Mode', switcher);

      //Creation of deadline widget
      const deadlineWidget = new DeadlineWidget(
        tracker.currentWidget.context.path
      );
      tracker.currentWidget.toolbar.insertItem(11, 'Deadline', deadlineWidget);
    });
  }, this);

  tracker.activeCellChanged.connect(() => {
    const notebookPanel: NotebookPanel | null = tracker.currentWidget;
    // notebook not yet loaded
    if (notebookPanel === null) {
      return;
    }
    const notebook: Notebook = tracker.currentWidget.content;
    const contentsModel: Omit<IModel, 'content'> =
      notebookPanel.context.contentsModel;
    if (contentsModel === null) {
      return;
    }
    const notebookPaths: string[] = contentsModel.path.split('/');

    if (notebookPaths[lectureSubPaths + 1] === 'manualgrade') {
      return;
    }

    let switcher: any = null;
    (notebookPanel.toolbar.layout as PanelLayout).widgets.map(w => {
      if (w instanceof NotebookModeSwitch) {
        switcher = w;
      }
    });

    const cell: Cell = notebook.activeCell;

    //check if in creationmode and new cell was inserted
    if (
      switcher.mode &&
      (cell.layout as PanelLayout).widgets.every(w => {
        return !(w instanceof CreationWidget);
      })
    ) {
      (cell.layout as PanelLayout).insertWidget(0, new CreationWidget(cell));
    }
  }, this);
};

const createNotebookCommands = (
  app: JupyterFrontEnd,
  tracker: INotebookTracker
) => {
  let command = NotebookExecuteIDs.run;
  app.commands.addCommand(command, {
    label: 'Run cell',
    execute: async () => {
      await app.commands.execute('notebook:run-cell');
    },
    icon: runIcon
  });

  command = RevertCellIDs.revert;
  app.commands.addCommand(command, {
    label: 'Revert cell',
    isVisible: () => {
      if (tracker.activeCell === null) {
        return false;
      }
      return tracker.activeCell.model.getMetadata('revert') !== null;
    },
    isEnabled: () => {
      if (tracker.activeCell === null) {
        return false;
      }
      return tracker.activeCell.model.getMetadata('revert') !== null;
    },
    execute: () => {
      showDialog({
        title: "Do you want to revert the cell to it's original state?",
        body: 'This will overwrite your current changes!',
        buttons: [Dialog.cancelButton(), Dialog.okButton({ label: 'Revert' })]
      }).then(result => {
        if (!result.button.accept) {
          return;
        }
        tracker.activeCell.inputArea.model.sharedModel.setSource('');
        tracker.activeCell.inputArea.model.sharedModel.setSource(
          tracker.activeCell.model.getMetadata('revert').toString()
        );
      });
    },
    icon: undoIcon
  });

  command = ShowHintIDs.show;
  app.commands.addCommand(command, {
    label: 'Show hint',
    isVisible: () => {
      if (tracker.activeCell === null) {
        return false;
      }
      return tracker.activeCell.model.getMetadata('hint') !== null;
    },
    isEnabled: () => {
      if (tracker.activeCell === null) {
        return false;
      }
      return tracker.activeCell.model.getMetadata('hint') !== null;
    },
    execute: () => {
      // check if there is an active cell
      if (!tracker.activeCell) {
        return;
      }

      let hintWidget: HintWidget | undefined;

      (tracker.activeCell.layout as PanelLayout).widgets.forEach(widget => {
        if (widget instanceof HintWidget) {
          hintWidget = widget;
        }
      });
      if (hintWidget === undefined) {
        (tracker.activeCell.layout as PanelLayout).addWidget(
          new HintWidget(
            tracker.activeCell.model.getMetadata('hint').toString()
          )
        );
      } else {
        hintWidget.toggleShowAlert();
        hintWidget.setHint(
          tracker.activeCell.model.getMetadata('hint').toString()
        );
        hintWidget.update();
      }
    },
    icon: listIcon
  });
};

/**
 * Initialization data for the grading extension.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: 'grader-labextension:plugin',
  autoStart: true,
  requires: [
    ICommandPalette,
    ILauncher,
    INotebookTools,
    IDocumentManager,
    IFileBrowserFactory,
    INotebookTracker,
    ILayoutRestorer,
    IThemeManager,
    IMainMenu
  ],
  activate: (
    app: JupyterFrontEnd,
    palette: ICommandPalette,
    launcher: ILauncher,
    nbtools: INotebookTools,
    docManager: IDocumentManager,
    browserFactory: IFileBrowserFactory,
    tracker: INotebookTracker,
    restorer: ILayoutRestorer,
    themeManager: IThemeManager,
    mainMenu: IMainMenu
  ) => {
    console.log('JupyterLab extension grader-labextension is activated!');

    GlobalObjects.commands = app.commands;
    GlobalObjects.docRegistry = app.docRegistry;
    GlobalObjects.serviceManager = app.serviceManager;
    GlobalObjects.docManager = docManager;
    GlobalObjects.browserFactory = browserFactory;
    GlobalObjects.tracker = tracker;
    GlobalObjects.themeManager = themeManager;
    const graderServiceTracker = new WidgetTracker<
      MainAreaWidget<GraderServiceWidget>
    >({
      namespace: 'grader-service'
    });

    restorer.restore(graderServiceTracker, {
      command: GraderServiceCommandIDs.open,
      name: () => 'grader-service'
    });
    /* ##### Grader Service View Widget ##### */

    // If the user has no instructor roles in any lecture we do not display the course management
    UserPermissions.loadPermissions()
      .then(() => {
        if (UserPermissions.hasElevatedPermissions) {
          connectTrackerSignals(tracker);
        }
        createGraderServiceCommands(app, launcher, graderServiceTracker);

        // add Menu to JupyterLab main menu
        const menu = new Menu({ commands: app.commands });
        menu.title.label = 'Grader Service';
        mainMenu.addMenu(menu, false, { rank: 200 });

        GlobalObjects.graderServiceMenu = menu;

        updateMenus();
      })
      .catch((error: Error) => {
        showErrorMessage(
          'Grader Labextension Disabled',
          'Please restart your server: ' + error.message
        );
      });
    createNotebookCommands(app, tracker);
  }
};
export default extension;
