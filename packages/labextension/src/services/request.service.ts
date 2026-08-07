// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import { URLExt } from '@jupyterlab/coreutils';
import { ServerConnection } from '@jupyterlab/services';
import { HTTPMethod } from './enums/http-methods.enum';

export class HTTPError extends Error {
  statusCode: number;
  constructor(statusCode: number, message: string) {
    super(`${statusCode} - ${message}`);
    this.statusCode = statusCode;
    this.name = 'HTTPError';
  }
}

export async function request<T, B = any | null>(
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

  // ServerConnection only allows requests to notebook baseUrl
  const requestUrl = URLExt.join(
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
      // handle non-OK responses
      if (!response.ok) {
        // default error message
        let errorMessage = 'Unknown error';
        try {
          const errorData = await response.json();
          errorMessage =
            errorData['message'] ||
            errorData['reason'] ||
            errorData['error'] ||
            errorMessage;
        } catch (e) {
          errorMessage = await response.text(); // fallback to raw error text if not JSON
        }

        // throw custom HTTPError with status code and message
        throw new HTTPError(response.status, errorMessage);
      }

      // validate response body
      let responseData: T | string = null;
      try {
        responseData = await response.json();
      } catch (e) {
        console.log(
          'Not a JSON response body, handling as plain text.',
          responseData
        );
      }
      return responseData as T;
    }
  );
}
