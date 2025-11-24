'use client'

import { useState, useEffect } from 'react'
import { FileText, Lightbulb, Hash, MessageSquare, Quote, HelpCircle, TrendingUp, Activity } from 'lucide-react'

interface TocSection {
  id: string
  label: string
  icon: React.ReactNode
}

interface StickyTocProps {
  sections: TocSection[]
}

export function StickyToc({ sections }: StickyTocProps) {
  const [activeSection, setActiveSection] = useState<string>('')

  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY + 150 // Offset for sticky header

      // Find the current section
      for (let i = sections.length - 1; i >= 0; i--) {
        const section = document.getElementById(sections[i].id)
        if (section && section.offsetTop <= scrollPosition) {
          setActiveSection(sections[i].id)
          break
        }
      }
    }

    window.addEventListener('scroll', handleScroll)
    handleScroll() // Initial check

    return () => window.removeEventListener('scroll', handleScroll)
  }, [sections])

  const scrollToSection = (id: string) => {
    const element = document.getElementById(id)
    if (element) {
      const offset = 100 // Account for sticky headers
      const elementPosition = element.getBoundingClientRect().top + window.pageYOffset
      const offsetPosition = elementPosition - offset

      window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth'
      })
    }
  }

  return (
    <div className="sticky top-[100px] h-fit">
      <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-4">
        <h3 className="text-sm font-semibold text-gray-900 mb-3 px-2">Contents</h3>
        <nav className="space-y-1">
          {sections.map((section) => {
            const isActive = activeSection === section.id
            return (
              <button
                key={section.id}
                onClick={() => scrollToSection(section.id)}
                className={`w-full flex items-center gap-2 px-2 py-1.5 rounded text-sm transition-all ${
                  isActive
                    ? 'bg-blue-50 text-blue-700 font-medium border-l-2 border-blue-600 pl-2'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
              >
                <span className="flex-shrink-0">{section.icon}</span>
                <span className="text-left truncate">{section.label}</span>
              </button>
            )
          })}
        </nav>
      </div>
    </div>
  )
}

// Predefined section configurations
export function createTocSections(hasThemes: boolean, hasSentiment: boolean, hasInsights: boolean): TocSection[] {
  const baseSections: TocSection[] = [
    { id: 'summary', label: 'Summary', icon: <FileText className="w-4 h-4" /> },
    { id: 'key-points', label: 'Key Points', icon: <Hash className="w-4 h-4" /> },
    { id: 'detailed-notes', label: 'Detailed Notes', icon: <MessageSquare className="w-4 h-4" /> },
    { id: 'takeaways', label: 'Takeaways', icon: <Lightbulb className="w-4 h-4" /> },
  ]

  const optionalSections: TocSection[] = []

  if (hasThemes) {
    optionalSections.push({ id: 'themes', label: 'Themes & Patterns', icon: <TrendingUp className="w-4 h-4" /> })
  }

  if (hasSentiment) {
    optionalSections.push({ id: 'sentiment', label: 'Sentiment Timeline', icon: <Activity className="w-4 h-4" /> })
  }

  if (hasInsights) {
    optionalSections.push({ id: 'insights', label: 'Actionable Insights', icon: <Lightbulb className="w-4 h-4" /> })
  }

  const endSections: TocSection[] = [
    { id: 'quotes', label: 'Important Quotes', icon: <Quote className="w-4 h-4" /> },
    { id: 'questions', label: 'Questions Raised', icon: <HelpCircle className="w-4 h-4" /> },
  ]

  return [...baseSections, ...optionalSections, ...endSections]
}
