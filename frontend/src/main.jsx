// d:\Cloud\MMSummary\frontend\src\main.jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom' // 引入
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter> {/* 包裹 App */}
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)