// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import React from 'react';
import { UserPermissions } from '../../services/permission.service';
import { CreationModeSwitch } from './create-assignment/creation-switch';
import { IModeSwitchProps } from './slider';
import { lectureSubPathsCount } from '../../services/local-file.service';
import { Scope } from '../../services/enums/permissions-scope.enum';

export class SwitchModeFactory {
  public static getSwitch(props: IModeSwitchProps): JSX.Element {
    const paths = props.notebookpanel.context.contentsModel.path.split('/');
    const path = paths[lectureSubPathsCount + 1];
    const permissions = UserPermissions.getPermissions();
    const lecturecode = paths[lectureSubPathsCount];
    let hasPermission = false;
    if (permissions.hasOwnProperty(lecturecode)) {
      hasPermission = permissions[lecturecode] !== Scope.student;
    }

    if (!hasPermission) {
      return null;
    }

    switch (path) {
      case 'source':
        return (
          <CreationModeSwitch
            notebook={props.notebook}
            notebookpanel={props.notebookpanel}
            mode={props.mode}
            onChange={props.onChange}
          />
        );
      default:
        return null;
    }
  }
}
