import React from 'react'
import ReactDOM from 'react-dom/client'
import { PopupApp } from './PopupApp'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <PopupApp />
  </React.StrictMode>,
)

console.debug('[NetworkPilot Module]', 'module.loaded file=extension/src/popup/main.tsx')
