import { HTTPMethod, request } from './request.service';

export function getConfig(reload = false): Promise<any> {
  return request<any>(HTTPMethod.GET, '/config', reload);
}
