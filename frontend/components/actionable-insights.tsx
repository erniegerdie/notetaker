'use client'

import { Lightbulb, Target, AlertCircle, TrendingUp } from 'lucide-react'

interface ActionableInsightsProps {
  insights: string[]
}

const iconOptions = [Lightbulb, Target, AlertCircle, TrendingUp]

export function ActionableInsights({ insights }: ActionableInsightsProps) {
  if (!insights || insights.length === 0) {
    return null
  }

  return (
    <div className="space-y-3">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
        <p className="text-sm text-blue-800">
          <strong>Clinical & Professional Recommendations</strong> - Actionable next steps and areas for further exploration based on the content.
        </p>
      </div>

      <div className="space-y-3">
        {insights.map((insight, index) => {
          const Icon = iconOptions[index % iconOptions.length]
          return (
            <div
              key={index}
              className="flex items-start gap-3 p-4 bg-white border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
            >
              <div className="flex-shrink-0 mt-0.5">
                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                  <Icon className="w-4 h-4 text-blue-600" />
                </div>
              </div>
              <div className="flex-1">
                <p className="text-gray-800 leading-relaxed">{insight}</p>
              </div>
            </div>
          )
        })}
      </div>

      {/* Summary count */}
      <div className="pt-3 mt-3 border-t border-gray-200">
        <p className="text-sm text-gray-500 text-center">
          {insights.length} actionable {insights.length === 1 ? 'insight' : 'insights'} identified
        </p>
      </div>
    </div>
  )
}
