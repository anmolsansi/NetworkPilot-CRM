export function downloadCsvBlob(blob: Blob, filename: string) {
  console.info('[NetworkPilot CSV]', 'Starting CSV download', {
    filename,
    byteSize: blob.size,
  })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  console.info('[NetworkPilot CSV]', 'CSV download triggered', { filename })
}

console.debug('[NetworkPilot Module]', 'module.loaded file=frontend/src/api/csvDownload.ts')
