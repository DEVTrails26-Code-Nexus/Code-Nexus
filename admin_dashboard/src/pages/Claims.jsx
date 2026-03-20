import React, { useState, useEffect } from 'react'
import { FileText, Search, Download, ChevronDown, ChevronUp, CheckCircle, XCircle } from 'lucide-react'

const API_BASE = '/api'

function MSTSBreakdown({ breakdown }) {
  if (!breakdown) return null
  
  const signals = [
    { key: 'location_consistency', label: 'Location (L)', color: 'bg-blue-500' },
    { key: 'motion_validity', label: 'Motion (M)', color: 'bg-purple-500' },
    { key: 'network_authenticity', label: 'Network (N)', color: 'bg-teal-500' },
    { key: 'behavioural_history', label: 'Behaviour (B)', color: 'bg-orange-500' },
    { key: 'cluster_isolation', label: 'Cluster (C)', color: 'bg-pink-500' },
  ]

  return (
    <div className="mt-3 p-4 bg-navy-900/60 rounded-xl space-y-3 animate-fade-in">
      <p className="text-xs text-muted font-semibold uppercase tracking-wider">MSTS Breakdown</p>
      {signals.map(({ key, label, color }) => (
        <div key={key} className="flex items-center gap-3">
          <span className="text-xs text-muted w-28">{label}</span>
          <div className="flex-1 h-2 bg-navy-800 rounded-full overflow-hidden">
            <div
              className={`h-full ${color} rounded-full transition-all duration-1000`}
              style={{ width: `${(breakdown[key] || 0) * 100}%` }}
            />
          </div>
          <span className="text-xs text-white font-mono w-12 text-right">{(breakdown[key] || 0).toFixed(3)}</span>
        </div>
      ))}
      {breakdown.forgiveness_applied && (
        <p className="text-xs text-yellow-400 mt-1">⚡ Network forgiveness buffer applied (+0.08)</p>
      )}
    </div>
  )
}

export default function Claims() {
  const [claims, setClaims] = useState([])
  const [loading, setLoading] = useState(true)
  const [expandedId, setExpandedId] = useState(null)
  const [filter, setFilter] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    const fetchClaims = async () => {
      try {
        const res = await fetch(`${API_BASE}/admin/claims/recent?limit=50`)
        const data = await res.json()
        setClaims(data)
      } catch (e) {
        console.error('Error:', e)
      }
      setLoading(false)
    }
    fetchClaims()
    const interval = setInterval(fetchClaims, 10000)
    return () => clearInterval(interval)
  }, [])

  const filteredClaims = claims.filter(c => {
    if (filter !== 'all' && c.status !== filter) return false
    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      return (
        (c.worker_name || '').toLowerCase().includes(term) ||
        (c.worker_id || '').toLowerCase().includes(term) ||
        (c.zone || '').toLowerCase().includes(term)
      )
    }
    return true
  })

  const exportCSV = () => {
    const headers = 'Worker,Zone,Type,Trust Score,Payout,Status,Date\n'
    const rows = filteredClaims.map(c =>
      `${c.worker_name || c.worker_id},${c.zone},${c.disruption_type},${c.trust_score},${c.payout_amount},${c.status},${c.created_at}`
    ).join('\n')
    const blob = new Blob([headers + rows], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'nexurance_claims.csv'
    a.click()
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          <FileText size={20} className="text-teal-500" />
          Claims Management
        </h3>
        <button onClick={exportCSV} className="flex items-center gap-2 px-4 py-2 bg-navy-700 hover:bg-navy-600 text-white rounded-xl text-sm transition-colors">
          <Download size={14} /> Export CSV
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input
            type="text"
            placeholder="Search workers, zones..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-navy-800 border border-navy-700 rounded-xl text-sm text-white placeholder-muted focus:outline-none focus:border-teal-500 transition-colors"
          />
        </div>
        <div className="flex gap-2">
          {['all', 'APPROVED', 'PENDING', 'BLOCKED'].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                filter === f
                  ? 'bg-teal-500/20 text-teal-500 border border-teal-500/30'
                  : 'bg-navy-800 text-muted hover:text-white'
              }`}
            >
              {f === 'all' ? 'All' : f}
            </button>
          ))}
        </div>
      </div>

      {/* Claims Table */}
      <div className="glass-card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-navy-800/50">
              <th className="text-left text-xs text-muted font-medium uppercase tracking-wider py-4 px-4">Worker</th>
              <th className="text-left text-xs text-muted font-medium uppercase tracking-wider py-4 px-4">Zone</th>
              <th className="text-left text-xs text-muted font-medium uppercase tracking-wider py-4 px-4">Disruption</th>
              <th className="text-left text-xs text-muted font-medium uppercase tracking-wider py-4 px-4">Trust Score</th>
              <th className="text-left text-xs text-muted font-medium uppercase tracking-wider py-4 px-4">Payout</th>
              <th className="text-left text-xs text-muted font-medium uppercase tracking-wider py-4 px-4">Status</th>
              <th className="text-left text-xs text-muted font-medium uppercase tracking-wider py-4 px-4">Date</th>
              <th className="text-left text-xs text-muted font-medium uppercase tracking-wider py-4 px-4"></th>
            </tr>
          </thead>
          <tbody>
            {filteredClaims.map((claim, i) => (
              <React.Fragment key={claim._id || i}>
                <tr
                  className="border-t border-navy-700/30 hover:bg-navy-700/20 transition-colors cursor-pointer"
                  onClick={() => setExpandedId(expandedId === claim._id ? null : claim._id)}
                >
                  <td className="py-3 px-4">
                    <p className="text-sm text-white font-medium">{claim.worker_name || 'Unknown'}</p>
                    <p className="text-[10px] text-muted font-mono">{claim.worker_id}</p>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-sm text-muted capitalize">{claim.zone?.replace(/_/g, ' ')}</span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-sm text-white">{claim.disruption_type}</span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <div className={`w-2.5 h-2.5 rounded-full ${claim.trust_score >= 0.8 ? 'bg-green-400' : claim.trust_score >= 0.6 ? 'bg-yellow-400' : 'bg-red-400'}`} />
                      <span className="text-sm font-mono font-bold text-white">{claim.trust_score?.toFixed(3)}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-sm font-bold text-gold-400">₹{claim.payout_amount}</span>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-semibold ${
                      claim.status === 'APPROVED' ? 'bg-green-500/20 text-green-400' :
                      claim.status === 'PENDING' ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-red-500/20 text-red-400'
                    }`}>
                      {claim.status}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-xs text-muted">{new Date(claim.created_at).toLocaleDateString()}</span>
                  </td>
                  <td className="py-3 px-4">
                    {expandedId === claim._id ? <ChevronUp size={14} className="text-muted" /> : <ChevronDown size={14} className="text-muted" />}
                  </td>
                </tr>
                {expandedId === claim._id && (
                  <tr>
                    <td colSpan={8} className="px-4 pb-4">
                      <MSTSBreakdown breakdown={claim.msts_breakdown} />
                      <p className="text-xs text-muted mt-2">Reason: {claim.reason}</p>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
        {filteredClaims.length === 0 && (
          <p className="text-center text-muted py-12 text-sm">No claims match your filters</p>
        )}
      </div>
    </div>
  )
}
