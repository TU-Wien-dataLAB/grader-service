import { HTTPMethod, request } from './request.service';

export async function exportGrades(
  lectureId: number,
  filter: 'latest' | 'best' = 'best',
  format: 'json' | 'csv' = 'csv'
): Promise<any> {
  const url = `/api/lectures/${lectureId}/submissions?filter=${filter}&format=${format}`;
  return request<any>(HTTPMethod.GET, url, null);
}
