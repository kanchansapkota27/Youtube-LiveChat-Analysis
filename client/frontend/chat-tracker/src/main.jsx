import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'
import { BrowserRouter } from 'react-router-dom'
import { ViewerProvider } from './contexts/ViewerContext'



ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
    <ViewerProvider>
      <App />
    </ViewerProvider>
    </BrowserRouter>
  </React.StrictMode>
)
