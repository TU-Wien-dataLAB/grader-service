// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import { URLExt } from '@jupyterlab/coreutils';
import { ServerConnection } from '@jupyterlab/services';

export enum HTTPMethod {
  GET = 'GET',
  POST = 'POST',
  PUT = 'PUT',
  DELETE = 'DELETE'
}

export class HTTPError extends Error {
  statusCode: number;
  constructor(statusCode: number, message: string) {
    super(`${statusCode} - ${message}`);
    this.statusCode = statusCode;
    this.name = 'HTTPError';
  }
}

export function request<T, B = any | null>(
  method: HTTPMethod,
  endPoint: string,
  body: B,
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
  options.cache = 'default';
  if (reload) {
    options.cache = 'reload';
  }

  return ServerConnection.makeRequest(requestUrl, options, settings).then(
    async response => {
      const method = options.method || 'GET'; // assuming `method` is part of options.

      // handle non-OK responses
      if (!response.ok) {
        const errorText = await response.text();
        // default error message
        let errorMessage = 'Unknown error';

        try {
          const errorData = JSON.parse(errorText);
          errorMessage =
            errorData['reason'] ||
            errorData['message'] ||
            errorData['error'] ||
            errorMessage;
        } catch (e) {
          errorMessage = errorText; // fallback to raw error text if not JSON
        }

        // throw custom HTTPError with status code and message
        throw new HTTPError(response.status, errorMessage);
      }

      let data: any = await response.text();
      // validate response body
      if (data.length > 0) {
        try {
          data = JSON.parse(data);
        } catch (error) {
          console.log(
            'Not a JSON response body, handling as plain text.',
            response
          );
        }
      }

      console.log(`Request ${method} URL: ${requestUrl}`);
      console.log(data);
      return data;
    }
  );
}
