console.log('NetworkPilot CRM background service worker loaded')

chrome.runtime.onInstalled.addListener(() => {
  console.log('NetworkPilot CRM extension installed')
})

console.debug('[NetworkPilot Module]', 'module.loaded file=extension/src/background/service-worker.ts')
