'use client'

import { useState, useEffect } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'

interface CollapsibleSectionProps {
  id: string
  title: string
  children: React.ReactNode
  defaultExpanded?: boolean
  icon?: React.ReactNode
}

export function CollapsibleSection({
  id,
  title,
  children,
  defaultExpanded = true,
  icon
}: CollapsibleSectionProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)

  // Load saved state from localStorage
  useEffect(() => {
    const saved = localStorage.getItem(`notes-section-${id}`)
    if (saved !== null) {
      setIsExpanded(saved === 'expanded')
    }
  }, [id])

  // Save state to localStorage
  const toggleExpanded = () => {
    const newState = !isExpanded
    setIsExpanded(newState)
    localStorage.setItem(`notes-section-${id}`, newState ? 'expanded' : 'collapsed')
  }

  return (
    <Card className="border border-gray-200" id={id}>
      <div
        onClick={toggleExpanded}
        className="px-6 py-4 cursor-pointer hover:bg-gray-50 transition-colors flex items-center justify-between"
        role="button"
        aria-expanded={isExpanded}
        aria-controls={`${id}-content`}
      >
        <div className="flex items-center gap-2">
          {icon}
          <h2 className="text-lg font-bold">{title}</h2>
        </div>
        {isExpanded ? (
          <ChevronDown className="h-5 w-5 text-gray-500" />
        ) : (
          <ChevronRight className="h-5 w-5 text-gray-500" />
        )}
      </div>
      <div
        id={`${id}-content`}
        className={`transition-all duration-200 overflow-hidden ${
          isExpanded ? 'max-h-[10000px] opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <CardContent className="px-6 pb-6">
          {children}
        </CardContent>
      </div>
    </Card>
  )
}
