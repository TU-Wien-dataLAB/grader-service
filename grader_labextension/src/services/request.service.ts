// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import { URLExt } from '@jupyterlab/coreutils';
import { ServerConnection } from '@jupyterlab/services';
import { from, lastValueFrom } from 'rxjs';
import { switchMap } from 'rxjs/operators';

export enum HTTPMethod {
  GET = 'GET',
  POST = 'POST',
  PUT = 'PUT',
  DELETE = 'DELETE'
}

export function request<T, B = any>(
  method: HTTPMethod,
  endPoint: string,
  body: B = null,
  reload: boolean = false
): Promise<T> {
  const options: RequestInit = {};
  options.method = method;
  if (body) {
    options.body = JSON.stringify(body);
  }

  const settings = ServerConnection.makeSettings();
  let requestUrl = '';

  // ServerConnection only allows requests to notebook baseUrl
  requestUrl = URLExt.join(
    settings.baseUrl,
    '/grader_labextension', // API Namespace
    endPoint
  );

  // set cache always to default,
  // otherwise ServerConnection.makeRequest puts the timestamp as a query parameter resulting in no cache hits
  options.cache = "default";
  if (reload) {
    options.cache = "reload";
  }

  return ServerConnection.makeRequest(requestUrl, options, settings).then(
    async response => {
      if (!response.ok) {
        return response.text().then(text => {
          throw new Error(JSON.parse(text)['message']);
        });
      }
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
    }
  );

  return lastValueFrom(
    from(ServerConnection.makeRequest(requestUrl, options, settings)).pipe(
      switchMap(async response => {
        if (!response.ok) {
          throw new ServerConnection.ResponseError(
            response,
            await response.text()
          );
        }
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
      })
    )
  );
}
