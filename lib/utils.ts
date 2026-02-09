import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string) {
  return new Date(date).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function statusColor(status: string) {
  switch (status) {
    case "SUCCEEDED":
    case "COMPLETED":
      return "text-green-400";
    case "PENDING":
      return "text-yellow-400";
    case "FAILED":
      return "text-red-400";
    case "CANCELLED":
      return "text-gray-400";
    default:
      return "text-gray-300";
  }
}

export function levelColor(level: string) {
  switch (level) {
    case "error":
      return "text-red-400 bg-red-400/10";
    case "warn":
      return "text-yellow-400 bg-yellow-400/10";
    case "info":
      return "text-blue-400 bg-blue-400/10";
    case "debug":
      return "text-gray-400 bg-gray-400/10";
    default:
      return "text-gray-300";
  }
}
