import React, { useState, useEffect } from 'react'
import { Users, Shield, DollarSign, AlertTriangle, TrendingUp, TrendingDown } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'

const API_BASE = '/api'

// Mock loss ratio history for line chart
const lossRatioHistory = [
  { week: 'W1', ratio: 45 },
  { week: 'W2', ratio: 52 },
  { week: 'W3', ratio: 48 },
  { week: 'W4', ratio: 61 },
  { week: 'W5', ratio: 55 },
  { week: 'W6', ratio: 42 },
  { week: 'W7', ratio: 38 },
  { week: 'W8', ratio: 50 },
]

function StatCard({ icon: Icon, label, value, suffix = '', trend, color }) {
  const colors = {
    teal: 'from-teal-500/20 to-teal-700/10 border-teal-500/30',
    gold: 'from-gold-400/20 to-gold-500/10 border-gold-400/30',
    blue: 'from-blue-500/20 to-blue-700/10 border-blue-500/30',
    red: 'from-red-500/20 to-red-700/10 border-red-500/30',
  }

  return (
    <div className={`glass-card p-6 bg-gradient-to-br ${colors[color]} animate-fade-in`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-muted font-medium uppercase tracking-wider">{label}</p>
          <p className="text-3xl font-bold text-white mt-2">
            {value}
            <span className="text-lg text-muted ml-1">{suffix}</span>
          </p>
        </div>
        <div className={`p-3 rounded-xl bg-navy-900/50`}>
          <Icon size={22} className={color === 'teal' ? 'text-teal-500' : color === 'gold' ? 'text-gold-400' : color === 'blue' ? 'text-blue-400' : 'text-red-400'} />
        </div>
      </div>
      {trend && (
        <div className="flex items-center gap-1 mt-3">
          {trend > 0 ? <TrendingUp size={14} className="text-green-400" /> : <TrendingDown size={14} className="text-red-400" />}
          <span className={`text-xs font-medium ${trend > 0 ? 'text-green-400' : 'text-red-400'}`}>
            {Math.abs(trend)}% vs last week
          </span>
        </div>
      )}
    </div>
  )
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="glass-card p-3 border border-teal-500/30">
      <p className="text-xs text-muted">{label}</p>
      <p className="text-sm font-bold text-teal-500">{payload[0].value}%</p>
    </div>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [recentClaims, setRecentClaims] = useState([])
  const [zoneRisks, setZoneRisks] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, claimsRes, zonesRes] = await Promise.all([
          fetch(`${API_BASE}/admin/stats`),
          fetch(`${API_BASE}/admin/claims/recent?limit=10`),
          fetch(`${API_BASE}/zones/risk-map`),
        ])
        setStats(await statsRes.json())
        setRecentClaims(await claimsRes.json())
        const zonesData = await zonesRes.json()
        setZoneRisks(zonesData.zones || [])
      } catch (e) {
        console.error('Fetch error:', e)
      }
      setLoading(false)
    }
    fetchData()
    const interval = setInterval(fetchData, 15000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard icon={Users} label="Total Workers" value={stats?.total_workers || 0} color="teal" trend={12} />
        <StatCard icon={Shield} label="Active Policies" value={stats?.active_policies || 0} color="blue" trend={8} />
        <StatCard icon={DollarSign} label="Payouts This Week" value={`₹${stats?.total_payouts_this_week || 0}`} color="gold" trend={-5} />
        <StatCard icon={AlertTriangle} label="Loss Ratio" value={stats?.loss_ratio?.toFixed(1) || 0} suffix="%" color="red" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Loss Ratio Chart */}
        <div className="glass-card p-6 animate-fade-in" style={{ animationDelay: '0.2s' }}>
          <h3 className="text-lg font-semibold text-white mb-4">Loss Ratio Trend</h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={lossRatioHistory}>
              <defs>
                <linearGradient id="lossGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00B496" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#00B496" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1E3A7A" />
              <XAxis dataKey="week" stroke="#8A9BBB" fontSize={12} />
              <YAxis stroke="#8A9BBB" fontSize={12} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="ratio" stroke="#00B496" fill="url(#lossGradient)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Zone Risk Table */}
        <div className="glass-card p-6 animate-fade-in" style={{ animationDelay: '0.3s' }}>
          <h3 className="text-lg font-semibold text-white mb-4">Zone Risk Scores</h3>
          <div className="space-y-2 max-h-[250px] overflow-y-auto">
            {zoneRisks.map((zone, i) => (
              <div key={zone.zone} className="flex items-center justify-between p-3 bg-navy-900/40 rounded-xl hover:bg-navy-900/60 transition-colors">
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${zone.risk_level === 'high' ? 'bg-red-400' : zone.risk_level === 'medium' ? 'bg-yellow-400' : 'bg-green-400'}`} />
                  <span className="text-sm text-white capitalize">{zone.zone.replace(/_/g, ' ')}</span>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-xs text-muted">{zone.claim_count} claims</span>
                  <span className={`text-sm font-bold ${zone.risk_score > 1.2 ? 'text-red-400' : zone.risk_score > 0.9 ? 'text-yellow-400' : 'text-green-400'}`}>
                    {zone.risk_score}x
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Claims Feed */}
      <div className="glass-card p-6 animate-fade-in" style={{ animationDelay: '0.4s' }}>
        <h3 className="text-lg font-semibold text-white mb-4">Recent Claims</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-navy-700/50">
                <th className="text-left text-xs text-muted font-medium uppercase tracking-wider py-3 px-2">Worker</th>
                <th className="text-left text-xs text-muted font-medium uppercase tracking-wider py-3 px-2">Zone</th>
                <th className="text-left text-xs text-muted font-medium uppercase tracking-wider py-3 px-2">Type</th>
                <th className="text-left text-xs text-muted font-medium uppercase tracking-wider py-3 px-2">Trust</th>
                <th className="text-left text-xs text-muted font-medium uppercase tracking-wider py-3 px-2">Payout</th>
                <th className="text-left text-xs text-muted font-medium uppercase tracking-wider py-3 px-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {recentClaims.map((claim, i) => (
                <tr key={claim._id || i} className="border-b border-navy-700/20 hover:bg-navy-700/20 transition-colors">
                  <td className="py-3 px-2">
                    <p className="text-sm text-white">{claim.worker_name || claim.worker_id}</p>
                  </td>
                  <td className="py-3 px-2">
                    <span className="text-sm text-muted capitalize">{claim.zone?.replace(/_/g, ' ')}</span>
                  </td>
                  <td className="py-3 px-2">
                    <span className="text-sm text-white">{claim.disruption_type}</span>
                  </td>
                  <td className="py-3 px-2">
                    <span className={`text-sm font-mono font-bold ${claim.trust_score >= 0.8 ? 'text-green-400' : claim.trust_score >= 0.6 ? 'text-yellow-400' : 'text-red-400'}`}>
                      {claim.trust_score?.toFixed(3)}
                    </span>
                  </td>
                  <td className="py-3 px-2">
                    <span className="text-sm font-bold text-gold-400">₹{claim.payout_amount}</span>
                  </td>
                  <td className="py-3 px-2">
                    <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-semibold ${
                      claim.status === 'APPROVED' ? 'bg-green-500/20 text-green-400' :
                      claim.status === 'PENDING' ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-red-500/20 text-red-400'
                    }`}>
                      {claim.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {recentClaims.length === 0 && (
            <p className="text-center text-muted py-8 text-sm">No claims yet. Try simulating a rainstorm!</p>
          )}
        </div>
      </div>
    </div>
  )
}
