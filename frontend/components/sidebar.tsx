'use client'

import { FileText, Layers, FolderKanban, Archive, ChevronDown, Folder, Video, ChevronLeft, ChevronRight, LogOut, User } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '@/lib/auth-context'
import { Button } from '@/components/ui/button'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { NewCollectionModal } from '@/components/new-collection-modal'
import { useCollections, useCreateCollection } from '@/hooks/use-collections'

interface NavItem {
  label: string
  icon: React.ReactNode
  count?: number
  active?: boolean
  href?: string
}

interface NavSection {
  title: string
  items: NavItem[]
}

interface SidebarProps {
  notesCount?: number
  isCollapsed: boolean
  onToggleCollapse: () => void
}

export function Sidebar({ notesCount = 0, isCollapsed, onToggleCollapse }: SidebarProps) {
  const router = useRouter()
  const pathname = usePathname()
  const [activeItem, setActiveItem] = useState('Notes')
  const [showNewCollectionModal, setShowNewCollectionModal] = useState(false)
  const { user, signOut } = useAuth()

  const { data: collections = [], isLoading: collectionsLoading } = useCollections()
  const createCollectionMutation = useCreateCollection()

  const navigationItems: NavItem[] = [
    { label: 'All Notes', icon: <FileText className="h-4 w-4" />, href: '/' },
  ]

  const handleNavClick = (item: NavItem) => {
    setActiveItem(item.label)
    if (item.href) {
      router.push(item.href)
    }
  }

  const handleCreateCollection = async (name: string) => {
    try {
      await createCollectionMutation.mutateAsync({ name })
    } catch (error) {
      console.error('Failed to create collection:', error)
    }
  }

  return (
    <TooltipProvider>
      <aside className={cn(
        "fixed left-0 top-0 h-screen border-r border-gray-200 bg-white flex flex-col z-50 lg:block hidden transition-all duration-300",
        isCollapsed ? "w-[60px]" : "w-[220px]"
      )}>
        {/* Branding */}
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <div className={cn("flex items-center gap-2", isCollapsed && "hidden")}>
            <div className="h-8 w-8 rounded bg-blue-600 flex items-center justify-center">
              <Video className="h-4 w-4 text-white" />
            </div>
            <span className="text-base font-semibold text-gray-900">VideoNotes</span>
          </div>
          {isCollapsed && (
            <div className="h-8 w-8 rounded bg-blue-600 flex items-center justify-center mx-auto">
              <Video className="h-4 w-4 text-white" />
            </div>
          )}
          <Button
            variant="ghost"
            size="sm"
            className={cn(
              "h-8 w-8 p-0 hover:bg-gray-100",
              isCollapsed && "mx-auto mt-2"
            )}
            onClick={onToggleCollapse}
          >
            {isCollapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </Button>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto">
          {/* Navigation Section */}
          <div className="py-3 px-3">
            <nav className="space-y-1">
              {navigationItems.map((item) => (
                <Tooltip key={item.label} delayDuration={0}>
                  <TooltipTrigger asChild>
                    <button
                      onClick={() => handleNavClick(item)}
                      className={cn(
                        'flex items-center gap-3 w-full px-3 py-2 rounded-md text-sm transition-colors',
                        pathname === item.href
                          ? 'bg-gray-100 text-gray-900 font-medium'
                          : 'hover:bg-gray-50 text-gray-600',
                        isCollapsed && 'justify-center'
                      )}
                    >
                      {item.icon}
                      {!isCollapsed && <span className="flex-1 text-left">{item.label}</span>}
                    </button>
                  </TooltipTrigger>
                  {isCollapsed && (
                    <TooltipContent side="right">
                      <p>{item.label}</p>
                    </TooltipContent>
                  )}
                </Tooltip>
              ))}
            </nav>
          </div>

          {/* Collections Section */}
          <div className="py-3 px-3">
            {!isCollapsed && (
              <div className="mb-2 px-2 flex items-center justify-between">
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Collections
                </h3>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-5 w-5 p-0 hover:bg-gray-100"
                  onClick={() => setShowNewCollectionModal(true)}
                >
                  <span className="text-gray-400 text-lg leading-none">+</span>
                </Button>
              </div>
            )}
            {isCollapsed && (
              <Tooltip delayDuration={0}>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0 hover:bg-gray-100 mx-auto mb-2"
                    onClick={() => setShowNewCollectionModal(true)}
                  >
                    <span className="text-gray-400 text-lg leading-none">+</span>
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="right">
                  <p>New Collection</p>
                </TooltipContent>
              </Tooltip>
            )}
            <nav className="space-y-1">
              {collectionsLoading ? (
                !isCollapsed && <div className="px-3 py-2 text-sm text-gray-400">Loading...</div>
              ) : collections.length === 0 ? (
                !isCollapsed && <div className="px-3 py-2 text-sm text-gray-400">No collections yet</div>
              ) : (
                collections.map((collection) => (
                  <Tooltip key={collection.id} delayDuration={0}>
                    <TooltipTrigger asChild>
                      <button
                        onClick={() => router.push(`/collections/${collection.id}`)}
                        className={cn(
                          "flex items-center gap-3 w-full px-3 py-2 rounded-md text-sm hover:bg-gray-50 text-gray-600 transition-colors",
                          isCollapsed && "justify-center"
                        )}
                      >
                        <Folder className="h-4 w-4" />
                        {!isCollapsed && <span className="flex-1 text-left truncate">{collection.name}</span>}
                      </button>
                    </TooltipTrigger>
                    {isCollapsed && (
                      <TooltipContent side="right">
                        <p>{collection.name}</p>
                      </TooltipContent>
                    )}
                  </Tooltip>
                ))
              )}
            </nav>
          </div>
        </div>

        {/* User Section */}
        {user && (
          <div className="border-t border-gray-200 p-3">
            {!isCollapsed ? (
              <div className="flex items-center gap-3 px-2 py-2 rounded-md bg-gray-50">
                <div className="h-8 w-8 rounded-full bg-blue-600 flex items-center justify-center">
                  <User className="h-4 w-4 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {user.email?.split('@')[0]}
                  </p>
                  <p className="text-xs text-gray-500 truncate">{user.email}</p>
                </div>
                <Tooltip delayDuration={0}>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0 hover:bg-gray-200"
                      onClick={() => signOut()}
                    >
                      <LogOut className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="right">
                    <p>Sign out</p>
                  </TooltipContent>
                </Tooltip>
              </div>
            ) : (
              <Tooltip delayDuration={0}>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0 hover:bg-gray-100 mx-auto"
                    onClick={() => signOut()}
                  >
                    <LogOut className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="right">
                  <p>Sign out</p>
                </TooltipContent>
              </Tooltip>
            )}
          </div>
        )}
      </aside>

      {/* New Collection Modal */}
      <NewCollectionModal
        open={showNewCollectionModal}
        onOpenChange={setShowNewCollectionModal}
        onCreateCollection={handleCreateCollection}
      />
    </TooltipProvider>
  )
}
