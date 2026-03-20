import React, { useState, useEffect } from 'react'
import { Map, TrendingUp, CloudRain, Thermometer } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis } from 'recharts'

const API_BASE = '/api'

function RiskCell({ level }) {
  const colors = {
    high: 'bg-red-500/30 text-red-400',
    medium: 'bg-yellow-500/30 text-yellow-400',
    low: 'bg-green-500/30 text-green-400',
  }
  return (
    <span className={`inline-flex px-2 py-0.5 rounded-md text-xs font-medium ${colors[level] || colors.low}`}>
      {level}
    </span>
  )
}

export default function RiskHeatmap() {
  const [zones, setZones] = useState([])
  const [predictions, setPredictions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [zonesRes, predRes] = await Promise.all([
          fetch(`${API_BASE}/admin/zones/risk-map`),
          fetch(`${API_BASE}/admin/predictions/weekly`),
        ])
        const zonesData = await zonesRes.json()
        const predData = await predRes.json()
        setZones(zonesData.zones || [])
        setPredictions(predData.predictions || [])
      } catch (e) {
        console.error('Error:', e)
      }
      setLoading(false)
    }
    fetchData()
  }, [])

  const chartData = predictions.map(p => ({
    zone: p.zone.replace(/_/g, ' ').split(' ').map(w => w[0]?.toUpperCase() + w.slice(1)).join(' '),
    claims: p.predicted_claims,
    rain: Math.round(p.rain_probability * 100),
  }))

  const radarData = zones.slice(0, 6).map(z => ({
    zone: z.zone.replace(/_/g, ' ').split(' ').map(w => w[0]?.toUpperCase() + w.slice(1)).join(' '),
    risk: z.risk_score * 10,
  }))

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <h3 className="text-xl font-bold text-white flex items-center gap-2">
        <Map size={20} className="text-teal-500" />
        Risk Heatmap & Predictive Analytics
      </h3>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Predicted Claims */}
        <div className="glass-card p-6 animate-fade-in">
          <h4 className="text-lg font-semibold text-white mb-1">Next Week — Predicted Claims</h4>
          <p className="text-xs text-muted mb-4">XGBoost forecast by zone</p>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={chartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#1E3A7A" />
              <XAxis type="number" stroke="#8A9BBB" fontSize={11} />
              <YAxis type="category" dataKey="zone" stroke="#8A9BBB" fontSize={10} width={100} />
              <Tooltip
                contentStyle={{ background: '#112455', border: '1px solid rgba(0,180,150,0.3)', borderRadius: '12px', color: '#E8EFF8' }}
              />
              <Bar dataKey="claims" radius={[0, 6, 6, 0]}>
                {chartData.map((entry, i) => (
                  <Cell key={i} fill={entry.claims > 4 ? '#E5534B' : entry.claims > 2 ? '#F5C542' : '#2ECC8E'} fillOpacity={0.8} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Zone Risk Radar */}
        <div className="glass-card p-6 animate-fade-in" style={{ animationDelay: '0.1s' }}>
          <h4 className="text-lg font-semibold text-white mb-1">Zone Risk Radar</h4>
          <p className="text-xs text-muted mb-4">Multi-dimensional risk assessment</p>
          <ResponsiveContainer width="100%" height={280}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#1E3A7A" />
              <PolarAngleAxis dataKey="zone" stroke="#8A9BBB" fontSize={10} />
              <PolarRadiusAxis stroke="#1E3A7A" fontSize={10} />
              <Radar dataKey="risk" stroke="#00B496" fill="#00B496" fillOpacity={0.25} strokeWidth={2} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Weather + Risk Overlay Table */}
      <div className="glass-card p-6 animate-fade-in" style={{ animationDelay: '0.2s' }}>
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-lg font-semibold text-white">Zone Details</h4>
          <div className="flex items-center gap-2 text-xs text-muted">
            <CloudRain size={14} />
            Rain probability overlay
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-navy-700/50">
                <th className="text-left text-xs text-muted font-medium uppercase tracking-wider py-3 px-3">Zone</th>
                <th className="text-left text-xs text-muted font-medium uppercase tracking-wider py-3 px-3">Risk Score</th>
                <th className="text-left text-xs text-muted font-medium uppercase tracking-wider py-3 px-3">Risk Level</th>
                <th className="text-left text-xs text-muted font-medium uppercase tracking-wider py-3 px-3">Claims</th>
                <th className="text-left text-xs text-muted font-medium uppercase tracking-wider py-3 px-3">Rain Prob.</th>
                <th className="text-left text-xs text-muted font-medium uppercase tracking-wider py-3 px-3">Predicted</th>
                <th className="text-left text-xs text-muted font-medium uppercase tracking-wider py-3 px-3">Risk Bar</th>
              </tr>
            </thead>
            <tbody>
              {zones.map((zone, i) => {
                const pred = predictions.find(p => p.zone === zone.zone) || {}
                return (
                  <tr key={zone.zone} className="border-b border-navy-700/20 hover:bg-navy-700/20 transition-colors">
                    <td className="py-3 px-3">
                      <span className="text-sm text-white font-medium capitalize">{zone.zone.replace(/_/g, ' ')}</span>
                    </td>
                    <td className="py-3 px-3">
                      <span className="text-sm font-mono font-bold text-white">{zone.risk_score}x</span>
                    </td>
                    <td className="py-3 px-3">
                      <RiskCell level={zone.risk_level} />
                    </td>
                    <td className="py-3 px-3">
                      <span className="text-sm text-muted">{zone.claim_count}</span>
                    </td>
                    <td className="py-3 px-3">
                      <span className="text-sm text-blue-400">{Math.round((pred.rain_probability || 0) * 100)}%</span>
                    </td>
                    <td className="py-3 px-3">
                      <span className="text-sm font-bold text-gold-400">{pred.predicted_claims || 0}</span>
                    </td>
                    <td className="py-3 px-3 w-32">
                      <div className="w-full h-2 bg-navy-800 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${zone.risk_score > 1.2 ? 'bg-red-500' : zone.risk_score > 0.9 ? 'bg-yellow-500' : 'bg-green-500'}`}
                          style={{ width: `${Math.min(100, zone.risk_score * 70)}%` }}
                        />
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Predicted Loss Calendar (simplified) */}
      <div className="glass-card p-6 animate-fade-in" style={{ animationDelay: '0.3s' }}>
        <h4 className="text-lg font-semibold text-white mb-4">7-Day Risk Forecast</h4>
        <div className="grid grid-cols-7 gap-3">
          {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day, i) => {
            const risk = [0.3, 0.5, 0.7, 0.85, 0.6, 0.4, 0.2][i]
            return (
              <div key={day} className="text-center">
                <p className="text-xs text-muted mb-2">{day}</p>
                <div
                  className={`w-full aspect-square rounded-xl flex items-center justify-center text-sm font-bold transition-all hover:scale-105 ${
                    risk > 0.7 ? 'bg-red-500/30 text-red-400' :
                    risk > 0.4 ? 'bg-yellow-500/30 text-yellow-400' :
                    'bg-green-500/30 text-green-400'
                  }`}
                >
                  {Math.round(risk * 100)}%
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
