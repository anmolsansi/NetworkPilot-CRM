const APP_LOG_PREFIX = '[NetworkPilot]'

type LogLevel = 'debug' | 'info' | 'warn' | 'error'

export function logDebug(scope: string, message: string, details?: Record<string, unknown>) {
  writeLog('debug', scope, message, details)
}

export function logInfo(scope: string, message: string, details?: Record<string, unknown>) {
  writeLog('info', scope, message, details)
}

export function logWarn(scope: string, message: string, details?: Record<string, unknown>) {
  writeLog('warn', scope, message, details)
}

export function logError(scope: string, message: string, details?: Record<string, unknown>) {
  writeLog('error', scope, message, details)
}

export function maskId(id: string | null | undefined): string | null {
  if (!id) return null
  if (id.length <= 8) return id
  return `...${id.slice(-8)}`
}

function writeLog(level: LogLevel, scope: string, message: string, details?: Record<string, unknown>) {
  const logMessage = `${APP_LOG_PREFIX} ${scope}: ${message}`
  const logDetails = details ? sanitizeDetails(details) : undefined

  if (logDetails) {
    console[level](logMessage, logDetails)
  } else {
    console[level](logMessage)
  }
}

function sanitizeDetails(details: Record<string, unknown>): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(details).filter(([key]) => {
      const normalizedKey = key.toLowerCase()
      return !normalizedKey.includes('token') && !normalizedKey.includes('email')
    })
  )
}
