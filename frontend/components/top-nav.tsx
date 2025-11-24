'use client'

import { Search, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useState } from 'react'

interface TopNavProps {
  onSearch?: (query: string) => void
  onCreateNew?: () => void
  showSearch?: boolean
  showCreateNew?: boolean
}

export function TopNav({
  onSearch,
  onCreateNew,
  showSearch = true,
  showCreateNew = true,
}: TopNavProps) {
  const [searchQuery, setSearchQuery] = useState('')

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value)
    onSearch?.(e.target.value)
  }

  return (
    <div className="bg-white border-b border-gray-200 sticky top-0 z-40">
      <div className="flex items-center justify-between px-6 py-3">
        {/* Center - Search */}
        {showSearch && (
          <div className="flex-1 max-w-2xl">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search notes..."
                value={searchQuery}
                onChange={handleSearchChange}
                className="w-full pl-9 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        )}

        {/* Right side - Upload Button */}
        {showCreateNew && (
          <Button
            size="sm"
            className="gap-2 bg-blue-600 hover:bg-blue-700 text-white ml-4"
            onClick={onCreateNew}
          >
            <Plus className="h-4 w-4" />
            <span>Upload Video</span>
          </Button>
        )}
      </div>
    </div>
  )
}
