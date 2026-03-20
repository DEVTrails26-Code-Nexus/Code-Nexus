import React, { useState } from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { LayoutDashboard, FileText, ShieldAlert, Map, CloudRain, Activity } from 'lucide-react'
import Dashboard from './pages/Dashboard'
import Claims from './pages/Claims'
import FraudRadar from './pages/FraudRadar'
import RiskHeatmap from './pages/RiskHeatmap'

const API_BASE = '/api'

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/claims', label: 'Claims', icon: FileText },
  { path: '/fraud', label: 'Fraud Radar', icon: ShieldAlert },
  { path: '/risk', label: 'Risk Map', icon: Map },
]

function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 h-full w-64 bg-navy-800 border-r border-navy-700/50 z-50 flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-navy-700/50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-500 to-teal-700 flex items-center justify-center">
            <ShieldAlert size={22} className="text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight">Nexurance AI</h1>
            <p className="text-[10px] text-muted tracking-widest uppercase">Admin Console</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map(({ path, label, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            end={path === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-teal-500/15 text-teal-500 border border-teal-500/20'
                  : 'text-muted hover:text-white hover:bg-navy-700/50'
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Status */}
      <div className="p-4 border-t border-navy-700/50">
        <div className="glass-card p-3">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            <span className="text-xs text-green-400 font-medium">System Online</span>
          </div>
          <p className="text-[10px] text-muted">Team Code Nexus</p>
          <p className="text-[10px] text-muted">DEVTrails 2026</p>
        </div>
      </div>
    </aside>
  )
}

function SimulateButton() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const simulate = async () => {
    setLoading(true)
    setResult(null)
    try {
      const res = await fetch(`${API_BASE}/demo/simulate-rainstorm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ zone: 'koramangala', rainfall_mm_hr: 75, duration_hours: 2 }),
      })
      const data = await res.json()
      setResult(data)
    } catch (e) {
      setResult({ error: e.message })
    }
    setLoading(false)
  }

  return (
    <div className="relative">
      <button
        onClick={simulate}
        disabled={loading}
        className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600 text-white rounded-xl text-sm font-semibold transition-all duration-300 shadow-lg shadow-red-500/20 disabled:opacity-50"
      >
        <CloudRain size={16} />
        {loading ? 'Simulating...' : '⚡ Simulate Rainstorm'}
      </button>
      {result && !result.error && (
        <div className="absolute top-full right-0 mt-2 w-80 glass-card p-4 animate-fade-in z-50">
          <p className="text-green-400 text-sm font-semibold mb-2">✓ Simulation Complete</p>
          <p className="text-xs text-muted">Zone: {result.zone}</p>
          <p className="text-xs text-muted">Workers processed: {result.workers_processed}</p>
          {result.results?.map((r, i) => (
            <div key={i} className="mt-2 p-2 bg-navy-900/50 rounded-lg">
              <p className="text-xs text-white">{r.worker_name}</p>
              <p className={`text-xs font-bold ${r.decision === 'APPROVED' ? 'text-green-400' : r.decision === 'PENDING' ? 'text-yellow-400' : 'text-red-400'}`}>
                {r.decision} — ₹{r.payout_amount}
              </p>
              <p className="text-[10px] text-muted">Trust: {r.trust_score} ({r.trust_tier})</p>
            </div>
          ))}
          <button onClick={() => setResult(null)} className="text-xs text-muted mt-2 hover:text-white">Dismiss</button>
        </div>
      )}
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen bg-navy-900">
        <Sidebar />
        <main className="ml-64 flex-1 p-8">
          {/* Top bar */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                <Activity size={24} className="text-teal-500" />
                Control Center
              </h2>
              <p className="text-sm text-muted mt-1">Real-time parametric insurance monitoring</p>
            </div>
            <SimulateButton />
          </div>
          
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/claims" element={<Claims />} />
            <Route path="/fraud" element={<FraudRadar />} />
            <Route path="/risk" element={<RiskHeatmap />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
