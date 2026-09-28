// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

// token: 0b79bab50daca910b000d4f1a2b675d604257e42

import { Lecture } from '../model/lecture';
import { HTTPMethod } from './enums/http-methods.enum';
import { Scope } from './enums/permissions-scope.enum';
import { request } from './request.service';

interface IPermissionScopes {
  [lecture_code: string]: Scope;
}

export namespace UserPermissions {
  let permissions: IPermissionScopes;

  export async function loadPermissions(): Promise<void> {
    permissions = {};
    const response = await request<{ lecture_code: string; scope: number }[]>(
      HTTPMethod.GET,
      '/api/permissions',
      null
    );
    response.forEach(role => {
      permissions[role.lecture_code] = role.scope;
    });
  }

  export function getPermissions(): IPermissionScopes {
    return permissions;
  }

  export function getScope(lecture: Lecture) {
    return permissions?.[lecture.code] ?? null;
  }
  export function hasElevatedPermissions() {
    const sum = Object.values(permissions).reduce((acc, v) => acc + v, 0);
    return sum > 0;
  }
}
