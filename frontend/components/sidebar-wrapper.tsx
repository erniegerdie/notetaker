'use client'

import { Sidebar } from './sidebar'
import { useVideoList } from '@/hooks/use-video-list'
import { useState } from 'react'
import { usePathname } from 'next/navigation'

export function SidebarWrapper() {
  const pathname = usePathname()

  // Don't show sidebar on auth pages
  const isAuthPage = pathname === '/login' || pathname === '/signup' || pathname?.startsWith('/auth/')

  // Only fetch videos when not on auth page to prevent API calls that trigger redirect loop
  const { data: videos } = useVideoList({ enabled: !isAuthPage })
  const notesCount = videos?.videos?.length ?? 0
  const [isCollapsed, setIsCollapsed] = useState(false)

  if (isAuthPage) {
    return null
  }

  return (
    <>
      <Sidebar
        notesCount={notesCount}
        isCollapsed={isCollapsed}
        onToggleCollapse={() => setIsCollapsed(!isCollapsed)}
      />
      {/* Hidden div to push main content */}
      <div className={`hidden lg:block transition-all duration-300 ${isCollapsed ? 'w-[60px]' : 'w-[220px]'}`} />
    </>
  )
}
