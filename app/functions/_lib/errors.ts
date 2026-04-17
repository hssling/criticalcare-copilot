/**
 * Production-safe error codes and rendering for Netlify.
 * Ensures internal state isn't leaked to the client.
 */

export interface SafeError {
  status: number;
  body: {
    error: {
      code: string;
      message: string;
      reference_id: string;
      details?: string;
    };
  };
}

const ERROR_MAP: Record<string, { status: number; message: string }> = {
  INTERNAL_ERROR: {
    status: 500,
    message: "A server-side error occurred. Please contact support.",
  },
  INPUT_VALIDATION_FAILED: {
    status: 400,
    message: "The provided payload did not meet the required schema.",
  },
  PAYLOAD_TOO_LARGE: {
    status: 413,
    message: "The request payload exceeds the 256KB limit.",
  },
  RATE_LIMIT_EXCEEDED: {
    status: 429,
    message: "Too many requests. Please try again later.",
  },
  MODEL_SERVICE_FAILURE: {
    status: 503,
    message: "The inference endpoint is temporarily unavailable.",
  },
};

export function getSafeError(
  code: string,
  referenceId: string,
  details?: string
): SafeError {
  const config = ERROR_MAP[code] || ERROR_MAP.INTERNAL_ERROR;
  return {
    status: config.status,
    body: {
      error: {
        code,
        message: config.message,
        reference_id: referenceId,
        details,
      },
    },
  };
}

export function jsonError(safeErr: SafeError) {
  return {
    statusCode: safeErr.status,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(safeErr.body),
  };
}
