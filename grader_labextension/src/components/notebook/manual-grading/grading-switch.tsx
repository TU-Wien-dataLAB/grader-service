// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import {Cell} from '@jupyterlab/cells';
import {CommandPalette, ContextMenu, PanelLayout} from '@lumino/widgets';
import {GradeBook} from '../../../services/gradebook';
import {
  getProperties,
  getSubmission,
  updateProperties,
  updateSubmission
} from '../../../services/submissions.service';
import {IModeSwitchProps} from '../slider';
import {showErrorMessage} from '@jupyterlab/apputils';
import {Button, Intent, Switch} from '@blueprintjs/core';
import * as React from 'react';
import {Notebook, NotebookPanel} from '@jupyterlab/notebook';
import {Lecture} from '../../../model/lecture';
import {Assignment} from '../../../model/assignment';
import {IconNames} from '@blueprintjs/icons';
import {
  getAllAssignments,
  getAssignment
} from '../../../services/assignments.service';
import {getAllLectures} from '../../../services/lectures.service';
import {DataWidget} from './data-widget/data-widget';
import {GradeWidget} from './grade-widget/grade-widget';
import {GlobalObjects} from '../../..';
import {Box, Grid} from "@mui/material";
import {CreationModeSwitch} from "../create-assignment/creation-switch";
import {Validator} from "../create-assignment/validator";

export class GradingModeSwitch extends React.Component<IModeSwitchProps> {
  public state = {
    mode: false,
    saveButtonText: 'Save',
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
    this.subID = +this.notebookPaths[3];
    this.onChange = this.props.onChange;
  }

  public async componentDidMount() {
    const lectures = await getAllLectures();
    this.lecture = lectures.find(l => l.code === this.notebookPaths[1]);
    this.assignment = await getAssignment(
      this.lecture.id,
      +this.notebookPaths[2]
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
    const metadata = this.notebook.model.metadata;
    //if there were no updates return
    if (!metadata.get('updated')) {
      return;
    }
    metadata.set('updated', false);
    this.setState({saveButtonText: 'Saving'});
    try {
      await updateProperties(
        this.lecture.id,
        this.assignment.id,
        this.subID,
        this.gradeBook.properties
      );
      this.setState({saveButtonText: 'Saved'});
      setTimeout(
        () => this.setState({saveButtonText: 'Save'}),
        2000
      );
      const submission = await getSubmission(
        this.lecture.id,
        this.assignment.id,
        this.subID
      );
      submission.manual_status = 'being_edited';
      updateSubmission(
        this.lecture.id,
        this.assignment.id,
        this.subID,
        submission
      );
    } catch (err) {
      this.setState({saveButtonText: 'Save'});
      showErrorMessage('Error saving properties', err);
    }
  }

  protected handleChange = async () => {
    const properties = await getProperties(
      this.lecture.id,
      this.assignment.id,
      this.subID
    );
    this.gradeBook = new GradeBook(properties);
    this.setState({mode: !this.state.mode}, () => {
      this.onChange(this.state.mode);
      this.notebook.widgets.map((c: Cell) => {
        const currentLayout = c.layout as PanelLayout;
        if (this.state.mode) {
          currentLayout.insertWidget(
            0,
            new DataWidget(
              c,
              this.gradeBook,
              this.notebookPaths[4].split('.').slice(0, -1).join('.')
            )
          );
          currentLayout.addWidget(
            new GradeWidget(
              c,
              this.notebook,
              this.gradeBook,
              this.notebookPaths[4].split('.').slice(0, -1).join('.')
            )
          );
        } else {
          currentLayout.widgets.map(w => {
            if (w instanceof DataWidget || w instanceof GradeWidget) {
              currentLayout.removeWidget(w);
            }
          });
        }
      });
    });
  };

  public render() {
    return (
      <Grid container spacing={2}>
        <Grid item>
          <Switch
            style={{marginTop: "-1px"}}
            checked={this.state.mode}
            label="Grading Mode"
            onChange={this.handleChange}
          />
        </Grid>
        <Grid item>
          <Box>
            <Button
              className="jp-ToolbarButtonComponent grader-toolbar-button"
              onClick={() => this.saveProperties()}
              icon={(this.state.saveButtonText === "Saved" ? IconNames.SAVED : IconNames.FLOPPY_DISK)}
              minimal
              intent="success"
              small={true}
            >
              {this.state.saveButtonText}
            </Button>
          </Box>
        </Grid>
      </Grid>
    )
      ;
  }
}
