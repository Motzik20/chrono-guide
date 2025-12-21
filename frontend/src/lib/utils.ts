import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { jwtDecode } from "jwt-decode";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function isTokenExpired(token: string) {
  const decoded = jwtDecode(token);
  if (!decoded || !decoded.exp) {
    return true;
  }
  return decoded.exp < Date.now() / 1000;
}
