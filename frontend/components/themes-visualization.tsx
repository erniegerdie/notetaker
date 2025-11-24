'use client'

import { Badge } from '@/components/ui/badge'
import type { ThemeItem } from '@/lib/types'

interface ThemesVisualizationProps {
  themes: ThemeItem[]
}

export function ThemesVisualization({ themes }: ThemesVisualizationProps) {
  if (!themes || themes.length === 0) {
    return null
  }

  // Sort by frequency (descending) and take top 10
  const sortedThemes = [...themes]
    .sort((a, b) => b.frequency - a.frequency)
    .slice(0, 10)

  // Calculate min/max for scaling
  const maxFrequency = Math.max(...sortedThemes.map(t => t.frequency))
  const minFrequency = Math.min(...sortedThemes.map(t => t.frequency))

  // Scale font size between 12px and 24px based on frequency
  const getFontSize = (frequency: number): number => {
    if (maxFrequency === minFrequency) return 16
    const normalized = (frequency - minFrequency) / (maxFrequency - minFrequency)
    return 12 + normalized * 12
  }

  // Color palette for themes (blue spectrum for professional context)
  const colors = [
    'bg-blue-100 text-blue-700 hover:bg-blue-200',
    'bg-cyan-100 text-cyan-700 hover:bg-cyan-200',
    'bg-indigo-100 text-indigo-700 hover:bg-indigo-200',
    'bg-sky-100 text-sky-700 hover:bg-sky-200',
    'bg-teal-100 text-teal-700 hover:bg-teal-200',
    'bg-violet-100 text-violet-700 hover:bg-violet-200',
  ]

  return (
    <div className="space-y-4">
      {/* Tag Cloud */}
      <div className="flex flex-wrap gap-2 items-center justify-center py-4">
        {sortedThemes.map((theme, index) => (
          <Badge
            key={index}
            variant="secondary"
            className={`${colors[index % colors.length]} cursor-default transition-all`}
            style={{ fontSize: `${getFontSize(theme.frequency)}px` }}
          >
            {theme.theme} ({theme.frequency})
          </Badge>
        ))}
      </div>

      {/* Detailed Theme Breakdown */}
      <div className="space-y-3 pt-4 border-t">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Theme Details</h3>
        {sortedThemes.map((theme, index) => (
          <div key={index} className="border-l-4 border-cyan-500 pl-4 py-2">
            <div className="flex items-baseline justify-between mb-1">
              <h4 className="font-medium text-gray-900">{theme.theme}</h4>
              <span className="text-sm text-gray-500">
                Mentioned {theme.frequency} {theme.frequency === 1 ? 'time' : 'times'}
              </span>
            </div>
            {theme.key_moments && theme.key_moments.length > 0 && (
              <div className="mt-2 space-y-1">
                <p className="text-xs text-gray-500 uppercase tracking-wide">Key Moments:</p>
                <ul className="space-y-1">
                  {theme.key_moments.map((moment, idx) => (
                    <li key={idx} className="text-sm text-gray-700 italic">
                      &ldquo;{moment}&rdquo;
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Visual Frequency Bar */}
      <div className="pt-4 border-t">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Frequency Distribution</h3>
        <div className="space-y-2">
          {sortedThemes.map((theme, index) => {
            const percentage = (theme.frequency / maxFrequency) * 100
            return (
              <div key={index} className="flex items-center gap-3">
                <span className="text-sm text-gray-700 w-40 truncate flex-shrink-0">
                  {theme.theme}
                </span>
                <div className="flex-1 h-6 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-cyan-400 to-blue-500 rounded-full transition-all"
                    style={{ width: `${percentage}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-gray-600 w-8 text-right">
                  {theme.frequency}
                </span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
