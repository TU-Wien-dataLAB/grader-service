import { HTTPMethod } from './enums/http-methods.enum';
import { request } from './request.service';

export function getCurrentUser(): Promise<string> {
  const url = 'api/user';
  return request<string>(HTTPMethod.GET, url, null, false);
}
