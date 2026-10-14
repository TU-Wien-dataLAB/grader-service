import { Lecture } from '../model/lecture';
import { Assignment } from '../model/assignment';

function getKey(
  key: string,
  lecture?: Lecture,
  assignment?: Assignment
): string {
  if (lecture) {
    key = key + `-l${lecture.id}`;
  }
  if (assignment) {
    key = key + `-a${assignment.id}`;
  }
  return 'grader:' + key;
}

export function deleteKey(
  key: string,
  lecture?: Lecture,
  assignment?: Assignment
) {
  localStorage.removeItem(getKey(key, lecture, assignment));
}

export function storeString(
  key: string,
  value: string,
  lecture?: Lecture,
  assignment?: Assignment
): void {
  key = getKey(key, lecture, assignment);
  localStorage.setItem(key, value);
}

export function loadString(
  key: string,
  lecture?: Lecture,
  assignment?: Assignment
): string | null {
  key = getKey(key, lecture, assignment);
  return localStorage.getItem(key);
}

export function storeBoolean(
  key: string,
  value: boolean,
  lecture?: Lecture,
  assignment?: Assignment
): void {
  storeString(key, String(value), lecture, assignment);
}

export function loadBoolean(
  key: string,
  lecture?: Lecture,
  assignment?: Assignment
): boolean | null {
  const v = loadString(key, lecture, assignment);
  return v === null ? null : v === 'true';
}

export function storeNumber(
  key: string,
  value: number,
  lecture?: Lecture,
  assignment?: Assignment
): void {
  storeString(key, String(value), lecture, assignment);
}

export function loadNumber(
  key: string,
  lecture?: Lecture,
  assignment?: Assignment
): number | null {
  const v = loadString(key, lecture, assignment);
  return v === null ? null : Number(v);
}

export function storeObject<T>(
  key: string,
  value: T,
  lecture?: Lecture,
  assignment?: Assignment
): void {
  storeString(key, JSON.stringify(value), lecture, assignment);
}

export function loadObject<T>(
  key: string,
  lecture?: Lecture,
  assignment?: Assignment
): T | null {
  const jsonString = loadString(key, lecture, assignment);
  return !jsonString ? null : JSON.parse(jsonString);
}
