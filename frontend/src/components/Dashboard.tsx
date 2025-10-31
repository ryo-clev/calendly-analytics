import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import axios from 'axios'
import { motion, AnimatePresence } from 'framer-motion'
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area, RadialBarChart, RadialBar
} from 'recharts'
import {
  Calendar, Users, TrendingUp, Target, RefreshCw, AlertCircle,
  CheckCircle, Clock, BarChart3, Filter, Zap, Star,
  ArrowUp, ArrowDown, Activity
} from 'lucide-react'

// Types
interface AnalyticsData {
  summary: {
    total_events: number
    total_invitees: number
    completion_rate: number
    avg_events_per_day: number
    status_distribution: Record<string, number>
    internal_note_distribution: Record<string, number>
  }
  internal_notes_analysis: Record<string, any>
  temporal_analysis: {
    hourly_distribution: Record<string, number>
    daily_distribution: Record<string, number>
    monthly_distribution: Record<string, number>
  }
  conversion_analysis: {
    overall_conversion_rate: number
    conversion_by_internal_note: Record<string, number>
  }
  question_analysis: {
    service_interests: {
      distribution: Record<string, number>
    }
    discovery_channels: {
      distribution: Record<string, number>
    }
  }
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D']

const Dashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview')
  const queryClient = useQueryClient()

  const { data: analyticsData, isLoading, error } = useQuery<AnalyticsData>(
    'analytics',
    () => axios.get('/api/v1/analytics/cleverly-introduction').then(res => res.data),
    { refetchInterval: 300000 }
  )

  const refreshMutation = useMutation(
    () => axios.post('/api/v1/analytics/refresh-data'),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('analytics')
      }
    }
  )

  if (error) {
    return (
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="min-h-screen flex items-center justify-center"
      >
        <div className="text-center glass-card p-8 max-w-md">
          <AlertCircle className="mx-auto h-16 w-16 text-red-400 mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">Failed to load analytics</h2>
          <p className="text-white/70">{(error as Error).message}</p>
        </div>
      </motion.div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <motion.div 
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex flex-col lg:flex-row justify-between items-start lg:items-center mb-8"
      >
        <div>
          <h1 className="text-4xl font-bold text-white mb-2">
            Calendly Analytics
          </h1>
          <p className="text-white/70 text-lg">
            Advanced insights for Cleverly Introduction events
          </p>
        </div>
        <motion.div 
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="flex gap-4 mt-4 lg:mt-0"
        >
          <button
            onClick={() => refreshMutation.mutate()}
            disabled={refreshMutation.isLoading}
            className="btn-secondary flex items-center gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${refreshMutation.isLoading ? 'animate-spin' : ''}`} />
            Refresh Data
          </button>
        </motion.div>
      </motion.div>

      {/* Summary Metrics */}
      {!isLoading && analyticsData && (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
        >
          <MetricCard
            icon={<Users className="h-8 w-8" />}
            title="Total Events"
            value={analyticsData.summary.total_events}
            change={`${analyticsData.summary.avg_events_per_day.toFixed(1)}/day`}
            trend="up"
          />
          <MetricCard
            icon={<Target className="h-8 w-8" />}
            title="Conversion Rate"
            value={`${analyticsData.summary.completion_rate.toFixed(1)}%`}
            change="Overall"
            trend="up"
          />
          <MetricCard
            icon={<Calendar className="h-8 w-8" />}
            title="Internal Notes"
            value={Object.keys(analyticsData.summary.internal_note_distribution).length}
            change="Categories"
            trend="neutral"
          />
          <MetricCard
            icon={<TrendingUp className="h-8 w-8" />}
            title="Active Events"
            value={analyticsData.summary.status_distribution.active || 0}
            change="Currently"
            trend="up"
          />
        </motion.div>
      )}

      {/* Navigation Tabs */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="glass-card p-2 mb-8"
      >
        <nav className="flex space-x-2">
          {[
            { id: 'overview', label: 'Overview', icon: <BarChart3 className="h-4 w-4" /> },
            { id: 'internal-notes', label: 'Internal Notes', icon: <Filter className="h-4 w-4" /> },
            { id: 'temporal', label: 'Temporal', icon: <Clock className="h-4 w-4" /> },
            { id: 'conversion', label: 'Conversion', icon: <Target className="h-4 w-4" /> },
            { id: 'questions', label: 'Questions', icon: <Activity className="h-4 w-4" /> }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 py-3 px-6 rounded-lg font-medium transition-all duration-300 ${
                activeTab === tab.id
                  ? 'bg-white/20 text-white shadow-lg'
                  : 'text-white/70 hover:text-white hover:bg-white/10'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </nav>
      </motion.div>

      {/* Loading State */}
      {isLoading && (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex justify-center items-center py-20"
        >
          <div className="text-center">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            >
              <RefreshCw className="h-12 w-12 text-white mx-auto mb-4" />
            </motion.div>
            <p className="text-white/70 text-lg">Loading advanced analytics...</p>
          </div>
        </motion.div>
      )}

      {/* Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3 }}
        >
          {!isLoading && analyticsData && (
            <>
              {activeTab === 'overview' && <OverviewTab data={analyticsData} />}
              {activeTab === 'internal-notes' && <InternalNotesTab data={analyticsData} />}
              {activeTab === 'temporal' && <TemporalTab data={analyticsData} />}
              {activeTab === 'conversion' && <ConversionTab data={analyticsData} />}
              {activeTab === 'questions' && <QuestionsTab data={analyticsData} />}
            </>
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  )
}

const MetricCard: React.FC<{
  icon: React.ReactNode
  title: string
  value: string | number
  change: string
  trend: 'up' | 'down' | 'neutral'
}> = ({ icon, title, value, change, trend }) => (
  <motion.div
    whileHover={{ scale: 1.05, y: -5 }}
    className="metric-card"
  >
    <div className="flex items-center justify-between">
      <div>
        <p className="text-white/70 text-sm font-medium mb-1">{title}</p>
        <p className="text-3xl font-bold text-white mb-2">{value}</p>
        <div className="flex items-center gap-1">
          {trend === 'up' && <ArrowUp className="h-4 w-4 text-green-400" />}
          {trend === 'down' && <ArrowDown className="h-4 w-4 text-red-400" />}
          <span className="text-white/60 text-sm">{change}</span>
        </div>
      </div>
      <div className="p-3 bg-white/10 rounded-xl">
        {icon}
      </div>
    </div>
  </motion.div>
)

const OverviewTab: React.FC<{ data: AnalyticsData }> = ({ data }) => (
  <div className="space-y-6">
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Status Distribution */}
      <motion.div 
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="chart-container"
      >
        <h3 className="text-xl font-semibold text-white mb-4">Event Status Distribution</h3>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={Object.entries(data.summary.status_distribution).map(([name, value]) => ({
                name,
                value
              }))}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={5}
              dataKey="value"
            >
              {Object.entries(data.summary.status_distribution).map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                backdropFilter: 'blur(10px)',
                borderRadius: '8px',
                color: 'white'
              }}
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </motion.div>

      {/* Internal Notes Distribution */}
      <motion.div 
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="chart-container"
      >
        <h3 className="text-xl font-semibold text-white mb-4">Internal Notes Distribution</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart 
            data={Object.entries(data.summary.internal_note_distribution).map(([name, value]) => ({
              name: name.length > 15 ? name.substring(0, 15) + '...' : name,
              value
            }))}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis 
              dataKey="name" 
              angle={-45} 
              textAnchor="end" 
              height={80}
              stroke="rgba(255,255,255,0.7)"
            />
            <YAxis stroke="rgba(255,255,255,0.7)" />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                backdropFilter: 'blur(10px)',
                borderRadius: '8px',
                color: 'white'
              }}
            />
            <Bar dataKey="value" fill="#8884d8" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </motion.div>
    </div>

    {/* Recent Activity Trend */}
    <motion.div 
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ delay: 0.3 }}
      className="chart-container"
    >
      <h3 className="text-xl font-semibold text-white mb-4">Activity Trends</h3>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart
          data={Object.entries(data.temporal_analysis.monthly_distribution).map(([month, count]) => ({
            month,
            count
          }))}
        >
          <defs>
            <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#8884d8" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
          <XAxis 
            dataKey="month" 
            stroke="rgba(255,255,255,0.7)"
          />
          <YAxis stroke="rgba(255,255,255,0.7)" />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              backdropFilter: 'blur(10px)',
              borderRadius: '8px',
              color: 'white'
            }}
          />
          <Area 
            type="monotone" 
            dataKey="count" 
            stroke="#8884d8" 
            fillOpacity={1} 
            fill="url(#colorCount)" 
            strokeWidth={3}
          />
        </AreaChart>
      </ResponsiveContainer>
    </motion.div>
  </div>
)

const InternalNotesTab: React.FC<{ data: AnalyticsData }> = ({ data }) => (
  <div className="space-y-6">
    {Object.entries(data.internal_notes_analysis).map(([note, analysis], index) => (
      <motion.div
        key={note}
        initial={{ x: -50, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ delay: index * 0.1 }}
        className="chart-container"
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-white/10 rounded-lg">
            <Zap className="h-6 w-6 text-yellow-400" />
          </div>
          <h3 className="text-xl font-semibold text-white">{note || 'Uncategorized'}</h3>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="text-center p-4 bg-white/5 rounded-xl">
            <p className="text-2xl font-bold text-white">{analysis.total_events}</p>
            <p className="text-white/60 text-sm">Total Events</p>
          </div>
          <div className="text-center p-4 bg-white/5 rounded-xl">
            <p className="text-2xl font-bold text-green-400">{analysis.conversion_rate?.toFixed(1)}%</p>
            <p className="text-white/60 text-sm">Conversion Rate</p>
          </div>
          <div className="text-center p-4 bg-white/5 rounded-xl">
            <p className="text-2xl font-bold text-purple-400">{analysis.peak_hours?.join(', ')}</p>
            <p className="text-white/60 text-sm">Peak Hours</p>
          </div>
          <div className="text-center p-4 bg-white/5 rounded-xl">
            <p className="text-2xl font-bold text-orange-400">
              {analysis.response_time_stats?.mean?.toFixed(1)}h
            </p>
            <p className="text-white/60 text-sm">Avg Response</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-white mb-3">Top Services</h4>
            <div className="space-y-2">
              {Object.entries(analysis.popular_services || {}).slice(0, 5).map(([service, count]) => (
                <div key={service} className="flex justify-between items-center p-2 hover:bg-white/5 rounded">
                  <span className="text-white/80 text-sm">{service}</span>
                  <span className="font-medium text-white">{count}</span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h4 className="font-medium text-white mb-3">Discovery Channels</h4>
            <div className="space-y-2">
              {Object.entries(analysis.discovery_channels || {}).slice(0, 5).map(([channel, count]) => (
                <div key={channel} className="flex justify-between items-center p-2 hover:bg-white/5 rounded">
                  <span className="text-white/80 text-sm">{channel}</span>
                  <span className="font-medium text-white">{count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </motion.div>
    ))}
  </div>
)

const TemporalTab: React.FC<{ data: AnalyticsData }> = ({ data }) => (
  <div className="space-y-6">
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <motion.div 
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="chart-container"
      >
        <h3 className="text-xl font-semibold text-white mb-4">Hourly Distribution</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={Object.entries(data.temporal_analysis.hourly_distribution).map(([hour, count]) => ({
            hour: `${hour}:00`,
            count
          }))}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis dataKey="hour" stroke="rgba(255,255,255,0.7)" />
            <YAxis stroke="rgba(255,255,255,0.7)" />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                backdropFilter: 'blur(10px)',
                borderRadius: '8px',
                color: 'white'
              }}
            />
            <Bar dataKey="count" fill="#00C49F" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </motion.div>

      <motion.div 
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="chart-container"
      >
        <h3 className="text-xl font-semibold text-white mb-4">Daily Distribution</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={Object.entries(data.temporal_analysis.daily_distribution).map(([day, count]) => ({
            day,
            count
          }))}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis dataKey="day" stroke="rgba(255,255,255,0.7)" />
            <YAxis stroke="rgba(255,255,255,0.7)" />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                backdropFilter: 'blur(10px)',
                borderRadius: '8px',
                color: 'white'
              }}
            />
            <Bar dataKey="count" fill="#FF8042" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </motion.div>
    </div>
  </div>
)

const ConversionTab: React.FC<{ data: AnalyticsData }> = ({ data }) => (
  <div className="space-y-6">
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <motion.div 
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="chart-container"
      >
        <h3 className="text-xl font-semibold text-white mb-4">Conversion by Internal Note</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={Object.entries(data.conversion_analysis.conversion_by_internal_note).map(([note, rate]) => ({
            note: note.length > 15 ? note.substring(0, 15) + '...' : note,
            rate: typeof rate === 'number' ? rate : 0
          }))}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis dataKey="note" angle={-45} textAnchor="end" height={80} stroke="rgba(255,255,255,0.7)" />
            <YAxis stroke="rgba(255,255,255,0.7)" />
            <Tooltip 
              formatter={(value) => [`${(value as number)?.toFixed(1)}%`, 'Conversion Rate']}
              contentStyle={{ 
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                backdropFilter: 'blur(10px)',
                borderRadius: '8px',
                color: 'white'
              }}
            />
            <Bar dataKey="rate" fill="#0088FE" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </motion.div>

      <motion.div 
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="chart-container"
      >
        <h3 className="text-xl font-semibold text-white mb-4">Conversion Performance</h3>
        <div className="space-y-4">
          <div className="text-center p-6 bg-white/5 rounded-xl">
            <p className="text-4xl font-bold text-green-400">
              {data.conversion_analysis.overall_conversion_rate.toFixed(1)}%
            </p>
            <p className="text-white/60 mt-2">Overall Conversion Rate</p>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-4 bg-white/5 rounded-lg">
              <p className="text-2xl font-bold text-white">
                {Math.max(...Object.values(data.conversion_analysis.conversion_by_internal_note)).toFixed(1)}%
              </p>
              <p className="text-white/60 text-sm">Best Performing</p>
            </div>
            <div className="text-center p-4 bg-white/5 rounded-lg">
              <p className="text-2xl font-bold text-white">
                {Math.min(...Object.values(data.conversion_analysis.conversion_by_internal_note)).toFixed(1)}%
              </p>
              <p className="text-white/60 text-sm">Worst Performing</p>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  </div>
)

const QuestionsTab: React.FC<{ data: AnalyticsData }> = ({ data }) => (
  <div className="space-y-6">
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <motion.div 
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="chart-container"
      >
        <h3 className="text-xl font-semibold text-white mb-4">Service Interests</h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart
            data={Object.entries(data.question_analysis.service_interests.distribution).map(([service, count]) => ({
              service: service.length > 20 ? service.substring(0, 20) + '...' : service,
              count
            }))}
            layout="vertical"
          >
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis type="number" stroke="rgba(255,255,255,0.7)" />
            <YAxis 
              type="category" 
              dataKey="service" 
              width={100}
              stroke="rgba(255,255,255,0.7)"
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                backdropFilter: 'blur(10px)',
                borderRadius: '8px',
                color: 'white'
              }}
            />
            <Bar dataKey="count" fill="#8884d8" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </motion.div>

      <motion.div 
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="chart-container"
      >
        <h3 className="text-xl font-semibold text-white mb-4">Discovery Channels</h3>
        <ResponsiveContainer width="100%" height={400}>
          <PieChart>
            <Pie
              data={Object.entries(data.question_analysis.discovery_channels.distribution).slice(0, 6).map(([channel, count]) => ({
                name: channel,
                value: count
              }))}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
              outerRadius={120}
              fill="#8884d8"
              dataKey="value"
            >
              {Object.entries(data.question_analysis.discovery_channels.distribution).slice(0, 6).map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                backdropFilter: 'blur(10px)',
                borderRadius: '8px',
                color: 'white'
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </motion.div>
    </div>
  </div>
)

export default Dashboard