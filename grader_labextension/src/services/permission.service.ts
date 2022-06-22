// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

// token: 0b79bab50daca910b000d4f1a2b675d604257e42

import { Lecture } from "../model/lecture";
import { HTTPMethod, request } from "./request.service";

export enum Scope {
  student = 0,
  tutor = 1,
  instructor = 2,
  admin = 3,
}

interface PermissionScopes {
  [lecture_code: string]: Scope;
}

export namespace UserPermissions {
  let permissions: PermissionScopes = null;

  export async function loadPermissions(): Promise<void> {
    permissions = {};
    let response = await request<{ lecture_code: string, scope: number }[]>(HTTPMethod.GET, '/permissions');
    response.forEach(role => {
      permissions[role.lecture_code] = role.scope;
    });
  }

  export function getPermissions(): PermissionScopes {
    return permissions;
  }

  export function getScope(lecture: Lecture) {
    if (permissions === null) {
      return null;
    }
    return permissions[lecture.code];
  }
}