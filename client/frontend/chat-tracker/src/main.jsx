import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'
import { BrowserRouter } from 'react-router-dom'
import { SessionProvider } from './contexts/SessionContext'



ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
    <SessionProvider>
      <App />
    </SessionProvider>
    </BrowserRouter>
  </React.StrictMode>
)
