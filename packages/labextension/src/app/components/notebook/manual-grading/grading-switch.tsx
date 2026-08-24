// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import { Cell } from '@jupyterlab/cells';
import { PanelLayout } from '@lumino/widgets';
import { GradeBook } from '../../../../services/gradebook.service';
import {
  getProperties,
  getSubmission,
  updateProperties,
  updateSubmission
} from '../../../../services/submissions.service';
import { IModeSwitchProps } from '../slider';
import { Button } from '../../../shadcn-components/ui/button';
import { showErrorMessage } from '@jupyterlab/apputils';
import * as React from 'react';
import { Notebook, NotebookPanel } from '@jupyterlab/notebook';
import { Lecture } from '../../../../model/lecture';
import { Assignment } from '../../../../model/assignment';
import { getAssignment } from '../../../../services/assignments.service';
import { getLectures } from '../../../../services/lectures.service';
import { DataWidget } from './data-widget/data-widget';
import { GradeWidget } from './grade-widget/grade-widget';
import { lectureSubPathsCount } from '../../../../services/local-file.service';
import { ManualStatus } from '../../../../model/manualStatus';
import { Switch } from '../../../shadcn-components/ui/switch';

export class GradingModeSwitch extends React.Component<IModeSwitchProps> {
  public state = {
    mode: false,
    saveButtonText: 'Save'
  };
  protected notebook: Notebook;
  protected notebookpanel: NotebookPanel;
  public lecture: Lecture;
  public assignment: Assignment;
  public gradeBook: GradeBook;
  public onChange: any;
  public subID: number;
  public notebookPaths: string[];

  public constructor(props: IModeSwitchProps) {
    super(props);
    this.state.mode = props.mode || false;
    this.notebook = props.notebook;
    this.notebookpanel = props.notebookpanel;
    this.notebookPaths =
      this.notebookpanel.context.contentsModel.path.split('/');
    this.subID = +this.notebookPaths[lectureSubPathsCount + 3];
    this.onChange = this.props.onChange;
  }

  public async componentDidMount() {
    const lectures = await getLectures({ instructor: true });
    this.lecture = lectures.find(
      l => l.code === this.notebookPaths[lectureSubPathsCount]
    );
    this.assignment = await getAssignment(
      this.lecture.id,
      +this.notebookPaths[lectureSubPathsCount + 2]
    );

    const properties = await getProperties(
      this.lecture.id,
      this.assignment.id,
      this.subID
    );
    this.gradeBook = new GradeBook(properties);
    this.notebookpanel.context.saveState.connect((sender, saveState) => {
      if (saveState === 'started') {
        this.saveProperties();
      }
    });
  }

  private async saveProperties() {
    const model = this.notebook.model;
    //if there were no updates return
    if (!model.getMetadata('updated')) {
      return;
    }
    model.setMetadata('updated', false);
    this.setState({ saveButtonText: 'Saving' });
    try {
      await updateProperties(
        this.lecture.id,
        this.assignment.id,
        this.subID,
        this.gradeBook.properties
      );
      this.setState({ saveButtonText: 'Saved' });
      setTimeout(() => this.setState({ saveButtonText: 'Save' }), 2000);
      const submission = await getSubmission(
        this.lecture.id,
        this.assignment.id,
        this.subID
      );
      submission.manual_status = ManualStatus.BeingEdited;
      updateSubmission(
        this.lecture.id,
        this.assignment.id,
        this.subID,
        submission
      );
    } catch (err) {
      this.setState({ saveButtonText: 'Save' });
      if (err instanceof Error) {
        showErrorMessage('Error saving properties', err);
      } else {
        console.error(
          'Error while trying to interpret type unknown as error',
          err
        );
      }
    }
  }

  protected handleChange = async () => {
    const properties = await getProperties(
      this.lecture.id,
      this.assignment.id,
      this.subID
    );
    this.gradeBook = new GradeBook(properties);

    // TODO This is a dirty bugfix which generates grade dict entries for task cells which should exist
    this.gradeBook.addTaskCellsToGrades();

    this.setState({ mode: !this.state.mode }, () => {
      this.onChange(this.state.mode);
      this.notebook.widgets.map((c: Cell) => {
        const currentLayout = c.layout as PanelLayout;
        if (this.state.mode) {
          currentLayout.insertWidget(
            0,
            new DataWidget(
              c,
              this.gradeBook,
              this.notebookPaths[lectureSubPathsCount + 4]
                .split('.')
                .slice(0, -1)
                .join('.')
            )
          );
          currentLayout.addWidget(
            new GradeWidget(
              c,
              this.notebook,
              this.gradeBook,
              this.notebookPaths[lectureSubPathsCount + 4]
                .split('.')
                .slice(0, -1)
                .join('.')
            )
          );
        } else {
          currentLayout.widgets.map(w => {
            if (w instanceof DataWidget || w instanceof GradeWidget) {
              try {
                currentLayout.removeWidget(w);
              } catch (error: any) {
                console.log('Could not remove widget of cell:' + w.cell.id);
                console.log('Error: ' + error);
              }
            }
          });
        }
      });
    });
  };

  public render() {
    return (
      <div className={'flex flex-row gap-1 items-center'}>
        <Switch checked={this.state.mode} onChange={this.handleChange} />
        <h2>Grading Mode</h2>
        <Button
          className="grader-toolbar-button"
          onClick={() => this.saveProperties()}
          variant="outline"
          size="sm"
        >
          {this.state.saveButtonText}
        </Button>
      </div>
    );
  }
}
