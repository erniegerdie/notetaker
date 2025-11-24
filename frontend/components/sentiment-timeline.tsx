'use client'

import { Card, CardContent } from '@/components/ui/card'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import type { SentimentTimelineItem } from '@/lib/types'

interface SentimentTimelineProps {
  timeline: SentimentTimelineItem[]
}

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function getSentimentColor(sentiment: string): string {
  switch (sentiment) {
    case 'positive':
      return '#10b981' // green-500
    case 'negative':
      return '#ef4444' // red-500
    default:
      return '#6b7280' // gray-500
  }
}

export function SentimentTimeline({ timeline }: SentimentTimelineProps) {
  if (!timeline || timeline.length === 0) {
    return null
  }

  // Sort by timestamp
  const sortedTimeline = [...timeline].sort((a, b) => a.timestamp_seconds - b.timestamp_seconds)

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg max-w-xs">
          <p className="font-semibold text-sm mb-1">{formatTime(data.timestamp_seconds)}</p>
          <p className="text-sm text-gray-700 mb-1">{data.description}</p>
          <div className="flex items-center gap-2 mt-2">
            <span
              className="text-xs font-medium px-2 py-1 rounded"
              style={{
                backgroundColor: getSentimentColor(data.sentiment) + '20',
                color: getSentimentColor(data.sentiment)
              }}
            >
              {data.sentiment}
            </span>
            <span className="text-xs text-gray-500">
              Intensity: {data.intensity > 0 ? '+' : ''}{data.intensity}
            </span>
          </div>
        </div>
      )
    }
    return null
  }

  return (
    <div className="space-y-4">
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={sortedTimeline}>
            <defs>
              <linearGradient id="sentimentGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                <stop offset="50%" stopColor="#6b7280" stopOpacity={0.1}/>
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0.3}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="timestamp_seconds"
              tickFormatter={formatTime}
              stroke="#6b7280"
              style={{ fontSize: '12px' }}
            />
            <YAxis
              domain={[-100, 100]}
              stroke="#6b7280"
              style={{ fontSize: '12px' }}
              label={{ value: 'Intensity', angle: -90, position: 'insideLeft', style: { fontSize: '12px' } }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="intensity"
              stroke="#3b82f6"
              strokeWidth={2}
              fill="url(#sentimentGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-green-500"></div>
          <span className="text-gray-600">Positive</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-gray-500"></div>
          <span className="text-gray-600">Neutral</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500"></div>
          <span className="text-gray-600">Negative</span>
        </div>
      </div>

      {/* Timeline markers */}
      <div className="space-y-2 pt-4 border-t">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Key Emotional Moments</h3>
        {sortedTimeline.map((item, index) => (
          <div key={index} className="flex items-start gap-3 text-sm">
            <span className="text-cyan-500 font-mono text-xs mt-0.5 w-12 flex-shrink-0">
              {formatTime(item.timestamp_seconds)}
            </span>
            <div className="flex-1">
              <p className="text-gray-700">{item.description}</p>
            </div>
            <span
              className="text-xs font-medium px-2 py-1 rounded flex-shrink-0"
              style={{
                backgroundColor: getSentimentColor(item.sentiment) + '20',
                color: getSentimentColor(item.sentiment)
              }}
            >
              {item.sentiment}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
