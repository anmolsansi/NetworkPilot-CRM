console.log('NetworkPilot CRM background service worker loaded')

chrome.runtime.onInstalled.addListener(() => {
  console.log('NetworkPilot CRM extension installed')
})
