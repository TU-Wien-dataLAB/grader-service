export function writeString(key: string, value: string): void {
  localStorage.setItem(key, value);
}

export function loadString(key: string): string | null {
  return localStorage.getItem(key);
}

export function writeBoolean(key: string, value: boolean): void {
  writeString(key, String(value))
}

export function loadBoolean(key: string): boolean | null {
  const v = loadString(key);
  if (v === null) {
    return null;
  } else {
    return v === "true";
  }
}

export function writeNumber(key: string, value: number): void {
  writeString(key, String(value));
}

export function loadNumber(key: string): number | null {
  const v = loadString(key);
  if (v === null) {
    return null;
  } else {
    return +v;
  }
}

export function writeObject(key: string, value: any): void {
  writeString(key, JSON.stringify(value));
}

export function loadObject(key: string): any | null {
  return JSON.parse(loadString(key));
}

