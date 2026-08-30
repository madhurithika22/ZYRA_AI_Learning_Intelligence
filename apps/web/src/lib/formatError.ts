/**
 * Safely formats any API error or exception into a human-readable string.
 * Guarantees that '[object Object]' is never rendered to the user.
 */
export function formatApiError(error: unknown): string {
  if (!error) {
    return "An unknown error occurred. Please try again.";
  }

  if (typeof error === "string") {
    return error === "[object Object]" ? "An unexpected API error occurred." : error;
  }

  if (error instanceof Error) {
    if (error.message && error.message !== "[object Object]") {
      return error.message;
    }
  }

  if (typeof error === "object") {
    const errObj = error as Record<string, unknown>;

    if (typeof errObj.detail === "string") {
      return errObj.detail;
    }

    if (Array.isArray(errObj.detail)) {
      return errObj.detail
        .map((item) => {
          if (typeof item === "string") return item;
          if (typeof item === "object" && item !== null) {
            const itemObj = item as Record<string, unknown>;
            const locStr = Array.isArray(itemObj.loc) ? itemObj.loc.join(".") + ": " : "";
            const msgStr = typeof itemObj.msg === "string" ? itemObj.msg : JSON.stringify(item);
            return locStr + msgStr;
          }
          return JSON.stringify(item);
        })
        .join("; ");
    }

    if (typeof errObj.message === "string" && errObj.message !== "[object Object]") {
      return errObj.message;
    }

    if (typeof errObj.error === "string") {
      return errObj.error;
    }
  }

  return "An unexpected API response was received. Please try again.";
}

export function isValidUUID(str: unknown): boolean {
  if (!str || typeof str !== "string") return false;
  const uuidRegex = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;
  return uuidRegex.test(str.trim());
}

