import React, { useState, useEffect } from 'react'
import { ShieldAlert, Users, Clock, AlertOctagon } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

const API_BASE = '/api'

export default function FraudRadar() {
  const [clusters, setClusters] = useState([])
  const [workers, setWorkers] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [clustersRes, statsRes] = await Promise.all([
          fetch(`${API_BASE}/admin/fraud/clusters`),
          fetch(`${API_BASE}/admin/stats`),
        ])
        const clustersData = await clustersRes.json()
        setClusters(clustersData.clusters || [])
      } catch (e) {
        console.error('Error:', e)
      }
      setLoading(false)
    }
    fetchData()
  }, [])

  // Trust score distribution data (synthetic for demo)
  const trustDistribution = [
    { range: '0.0-0.2', count: 1, color: '#E5534B' },
    { range: '0.2-0.4', count: 2, color: '#E5534B' },
    { range: '0.4-0.6', count: 3, color: '#F5C542' },
    { range: '0.6-0.8', count: 5, color: '#F5C542' },
    { range: '0.8-1.0', count: 12, color: '#2ECC8E' },
  ]

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
        <ShieldAlert size={20} className="text-red-400" />
        Fraud Radar — Cluster Detection
      </h3>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trust Score Distribution */}
        <div className="glass-card p-6 animate-fade-in">
          <h4 className="text-lg font-semibold text-white mb-4">Trust Score Distribution</h4>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={trustDistribution}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1E3A7A" />
              <XAxis dataKey="range" stroke="#8A9BBB" fontSize={11} />
              <YAxis stroke="#8A9BBB" fontSize={11} />
              <Tooltip
                contentStyle={{ background: '#112455', border: '1px solid rgba(0,180,150,0.3)', borderRadius: '12px', color: '#E8EFF8' }}
                labelStyle={{ color: '#8A9BBB' }}
              />
              <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                {trustDistribution.map((entry, i) => (
                  <Cell key={i} fill={entry.color} fillOpacity={0.8} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Cluster Summary Stats */}
        <div className="glass-card p-6 animate-fade-in" style={{ animationDelay: '0.1s' }}>
          <h4 className="text-lg font-semibold text-white mb-4">Detection Overview</h4>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-navy-900/50 rounded-xl">
              <p className="text-2xl font-bold text-white">{clusters.length}</p>
              <p className="text-xs text-muted mt-1">Detected Clusters</p>
            </div>
            <div className="p-4 bg-navy-900/50 rounded-xl">
              <p className="text-2xl font-bold text-red-400">
                {clusters.filter(c => c.risk_level === 'high').length}
              </p>
              <p className="text-xs text-muted mt-1">High Risk Clusters</p>
            </div>
            <div className="p-4 bg-navy-900/50 rounded-xl">
              <p className="text-2xl font-bold text-yellow-400">
                {clusters.reduce((sum, c) => sum + c.size, 0)}
              </p>
              <p className="text-xs text-muted mt-1">Workers Flagged</p>
            </div>
            <div className="p-4 bg-navy-900/50 rounded-xl">
              <p className="text-2xl font-bold text-teal-500">Louvain</p>
              <p className="text-xs text-muted mt-1">Algorithm Used</p>
            </div>
          </div>
          
          <div className="mt-4 p-3 bg-teal-500/10 border border-teal-500/20 rounded-xl">
            <p className="text-xs text-teal-500 font-medium">ℹ️ How it works</p>
            <p className="text-xs text-muted mt-1">
              Louvain community detection identifies clusters of workers who submit claims from
              the same IP subnet, device model, and within a 3-minute window — indicators of
              coordinated fraud rings.
            </p>
          </div>
        </div>
      </div>

      {/* Cluster Details */}
      <div className="glass-card p-6 animate-fade-in" style={{ animationDelay: '0.2s' }}>
        <h4 className="text-lg font-semibold text-white mb-4">Detected Clusters</h4>
        {clusters.length === 0 ? (
          <div className="text-center py-12">
            <ShieldAlert size={48} className="text-green-400 mx-auto mb-4 opacity-50" />
            <p className="text-green-400 font-medium">No fraud clusters detected</p>
            <p className="text-xs text-muted mt-2">The Louvain algorithm found no suspicious coordination patterns</p>
          </div>
        ) : (
          <div className="space-y-4">
            {clusters.map((cluster) => (
              <div key={cluster.cluster_id} className={`p-4 rounded-xl border ${
                cluster.risk_level === 'high'
                  ? 'bg-red-500/10 border-red-500/30'
                  : 'bg-yellow-500/10 border-yellow-500/30'
              }`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <AlertOctagon size={20} className={cluster.risk_level === 'high' ? 'text-red-400' : 'text-yellow-400'} />
                    <div>
                      <p className="text-sm font-semibold text-white">Cluster #{cluster.cluster_id}</p>
                      <p className="text-xs text-muted">{cluster.size} workers • {cluster.risk_level} risk</p>
                    </div>
                  </div>
                  <button className="px-3 py-1.5 bg-red-500/20 text-red-400 text-xs font-medium rounded-lg hover:bg-red-500/30 transition-colors">
                    Flag All
                  </button>
                </div>
                <div className="mt-2 flex flex-wrap gap-1">
                  {cluster.workers?.slice(0, 5).map(w => (
                    <span key={w} className="px-2 py-0.5 bg-navy-800 rounded text-[10px] text-muted font-mono">{w}</span>
                  ))}
                  {cluster.workers?.length > 5 && (
                    <span className="px-2 py-0.5 bg-navy-800 rounded text-[10px] text-muted">+{cluster.workers.length - 5} more</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
