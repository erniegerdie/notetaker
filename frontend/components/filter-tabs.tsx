'use client'

import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Search, Plus, ChevronDown, Calendar, Hash, X } from 'lucide-react'
import { useState } from 'react'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { Badge } from '@/components/ui/badge'

interface FilterTabsProps {
  totalCount: number
  onSearch?: (query: string) => void
  onCreateNew?: () => void
  onTagFilter?: (tags: string[]) => void
  onDateRangeFilter?: (startDate: string | null, endDate: string | null) => void
  availableTags?: string[]
}

export function FilterTabs({
  totalCount = 45,
  onSearch,
  onCreateNew,
  onTagFilter,
  onDateRangeFilter,
  availableTags = [],
}: FilterTabsProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [startDate, setStartDate] = useState<string>('')
  const [endDate, setEndDate] = useState<string>('')

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value)
    onSearch?.(e.target.value)
  }

  const handleTagToggle = (tag: string) => {
    const newTags = selectedTags.includes(tag)
      ? selectedTags.filter(t => t !== tag)
      : [...selectedTags, tag]
    setSelectedTags(newTags)
    onTagFilter?.(newTags)
  }

  const handleDateRangeApply = () => {
    onDateRangeFilter?.(startDate || null, endDate || null)
  }

  const handleClearDateRange = () => {
    setStartDate('')
    setEndDate('')
    onDateRangeFilter?.(null, null)
  }

  const hasActiveFilters = selectedTags.length > 0 || startDate || endDate

  return (
    <TooltipProvider>
      <div className="border-b bg-white sticky top-0 z-10">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between px-4 lg:px-6 py-4 gap-4">
        <div className="flex items-center gap-4 flex-1">
          {/* All Notes Label */}
          <div className="font-medium text-gray-900">
            • All notes
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Tag Filter */}
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" size="sm" className="gap-2">
                <Hash className="h-4 w-4" />
                <span>Tags</span>
                {selectedTags.length > 0 && (
                  <Badge variant="secondary" className="ml-1 px-1.5 py-0.5 text-xs">
                    {selectedTags.length}
                  </Badge>
                )}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-64" align="end">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="font-semibold text-sm">Filter by Tags</h4>
                  {selectedTags.length > 0 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setSelectedTags([])
                        onTagFilter?.([])
                      }}
                      className="h-auto p-1 text-xs"
                    >
                      Clear
                    </Button>
                  )}
                </div>
                <div className="flex flex-wrap gap-2 max-h-64 overflow-y-auto">
                  {availableTags.length > 0 ? (
                    availableTags.map((tag) => (
                      <Badge
                        key={tag}
                        variant={selectedTags.includes(tag) ? "default" : "outline"}
                        className="cursor-pointer"
                        onClick={() => handleTagToggle(tag)}
                      >
                        {tag}
                      </Badge>
                    ))
                  ) : (
                    <p className="text-sm text-gray-500">No tags available</p>
                  )}
                </div>
              </div>
            </PopoverContent>
          </Popover>

          {/* Date Range Filter */}
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" size="sm" className="gap-2">
                <Calendar className="h-4 w-4" />
                <span>Date</span>
                {(startDate || endDate) && (
                  <Badge variant="secondary" className="ml-1 px-1.5 py-0.5 text-xs">
                    •
                  </Badge>
                )}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-80" align="end">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="font-semibold text-sm">Filter by Date Range</h4>
                  {(startDate || endDate) && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleClearDateRange}
                      className="h-auto p-1 text-xs"
                    >
                      Clear
                    </Button>
                  )}
                </div>
                <div className="space-y-3">
                  <div>
                    <label className="text-sm text-gray-600 mb-1 block">From</label>
                    <input
                      type="date"
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                      className="w-full px-3 py-2 border rounded-md text-sm"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-gray-600 mb-1 block">To</label>
                    <input
                      type="date"
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                      className="w-full px-3 py-2 border rounded-md text-sm"
                    />
                  </div>
                  <Button
                    onClick={handleDateRangeApply}
                    className="w-full"
                    size="sm"
                  >
                    Apply
                  </Button>
                </div>
              </div>
            </PopoverContent>
          </Popover>

          {/* Note Count */}
          <span className="text-sm text-gray-500 hidden sm:inline">
            {totalCount} notes
          </span>
          </div>
        </div>
      </div>
    </TooltipProvider>
  )
}
