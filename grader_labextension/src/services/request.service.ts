// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import { URLExt } from '@jupyterlab/coreutils';
import { ServerConnection } from '@jupyterlab/services';
import { from, throwError } from 'rxjs';
import { switchMap } from 'rxjs/operators';

export enum HTTPMethod {
  GET = 'GET',
  POST = 'POST',
  PUT = 'PUT',
  DELETE = 'DELETE'
}

export function request<T>(
  method: HTTPMethod,
  endPoint: string,
  body: object = null,
  headers: HeadersInit = null
): Promise<T> {
  const options: RequestInit = {};
  options.method = method;
  if (body) {
    options.body = JSON.stringify(body);
  }
  if (headers) {
    options.headers = headers;
  }
  const settings = ServerConnection.makeSettings();
  let requestUrl = '';

  // ServerConnection only allows requests to notebook baseUrl
  requestUrl = URLExt.join(
    settings.baseUrl,
    '/grader_labextension', // API Namespace
    endPoint
  );

  return ServerConnection.makeRequest(requestUrl, options, settings).then(
    async response => {
      let data: any = await response.text();
      if (data.length > 0) {
        try {
          data = JSON.parse(data);
        } catch (error) {
          console.log('Not a JSON response body.', response);
        }
      }
      console.log('Request ' + method.toString() + ' URL: ' + requestUrl);
      console.log(data);
      return data;
    },
    error => {
      return new Error(error);
    }
  );
}
