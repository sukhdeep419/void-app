export type StreamParseResult = {
  content: string
  statusLine: string
  confirmationToken?: string
}

const STATUS_REGEX = /\[\[VOID_STATUS:([^\]]+)\]\]/g

export function parseStreamBuffer(buffer: string): StreamParseResult {
  let statusLine = ''
  let match: RegExpExecArray | null
  const statusRegex = new RegExp(STATUS_REGEX.source, 'g')

  while ((match = statusRegex.exec(buffer)) !== null) {
    statusLine = match[1]
  }

  let content = buffer.replace(/\[\[VOID_STATUS:[^\]]+\]\]/g, '')
  let confirmationToken: string | undefined

  const confirmMatch = content.match(/^\[\[VOID_CONFIRM:([a-f0-9]+)\]\]([\s\S]*)$/)
  if (confirmMatch) {
    confirmationToken = confirmMatch[1]
    content = confirmMatch[2]
  }

  return {
    content: content.trim(),
    statusLine,
    confirmationToken,
  }
}

export function isStatusOnly(buffer: string): boolean {
  const { content, statusLine } = parseStreamBuffer(buffer)
  return Boolean(statusLine) && !content
}
