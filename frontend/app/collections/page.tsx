'use client'

import { useState } from 'react'
import { TopNav } from '@/components/top-nav'
import { Plus, Folder, MoreVertical, Pencil, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

interface Collection {
  id: string
  name: string
  description?: string
  video_count?: number
  created_at: string
}

export default function CollectionsPage() {
  const [collections, setCollections] = useState<Collection[]>([
    {
      id: '1',
      name: 'Client Meetings',
      description: 'Video recordings of client meetings and discussions',
      video_count: 12,
      created_at: new Date().toISOString(),
    },
    {
      id: '2',
      name: 'Training Videos',
      description: 'Educational and training content for onboarding',
      video_count: 8,
      created_at: new Date().toISOString(),
    },
  ])
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [newCollection, setNewCollection] = useState({ name: '', description: '' })

  const handleCreateCollection = () => {
    if (!newCollection.name.trim()) return

    const collection: Collection = {
      id: Date.now().toString(),
      name: newCollection.name,
      description: newCollection.description,
      video_count: 0,
      created_at: new Date().toISOString(),
    }

    setCollections([...collections, collection])
    setNewCollection({ name: '', description: '' })
    setIsCreateOpen(false)
  }

  const handleDeleteCollection = (id: string) => {
    setCollections(collections.filter(c => c.id !== id))
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Top Navigation */}
      <TopNav showSearch={false} showCreateNew={false} />

      {/* Page Header */}
      <div className="bg-white border-b px-6 py-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-blue-100 flex items-center justify-center">
              <Folder className="h-6 w-6 text-blue-700" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Collections</h1>
              <p className="text-sm text-gray-500">
                Organize your videos into collections
              </p>
            </div>
          </div>
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button className="gap-2">
                <Plus className="h-4 w-4" />
                New Collection
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Collection</DialogTitle>
                <DialogDescription>
                  Create a new collection to organize your videos.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Name</Label>
                  <Input
                    id="name"
                    placeholder="e.g., Client Meetings"
                    value={newCollection.name}
                    onChange={(e) =>
                      setNewCollection({ ...newCollection, name: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description (optional)</Label>
                  <Textarea
                    id="description"
                    placeholder="Add a description for this collection..."
                    value={newCollection.description}
                    onChange={(e) =>
                      setNewCollection({ ...newCollection, description: e.target.value })
                    }
                    rows={3}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsCreateOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleCreateCollection}>Create Collection</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Collections Grid */}
      <div className="px-6 py-8">
        {collections.length === 0 ? (
          <div className="text-center py-12">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 mb-4">
              <Folder className="h-8 w-8 text-gray-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              No collections yet
            </h3>
            <p className="text-gray-500 mb-6">
              Create your first collection to organize your videos
            </p>
            <Button onClick={() => setIsCreateOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create Collection
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {collections.map((collection) => (
              <Card
                key={collection.id}
                className="hover:shadow-lg transition-shadow cursor-pointer"
              >
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="h-12 w-12 rounded-lg bg-blue-100 flex items-center justify-center">
                      <Folder className="h-6 w-6 text-blue-700" />
                    </div>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem>
                          <Pencil className="h-4 w-4 mr-2" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          className="text-red-600"
                          onClick={() => handleDeleteCollection(collection.id)}
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {collection.name}
                  </h3>
                  {collection.description && (
                    <p className="text-sm text-gray-500 mb-4 line-clamp-2">
                      {collection.description}
                    </p>
                  )}
                  <div className="flex items-center justify-between text-sm text-gray-500">
                    <span>{collection.video_count || 0} videos</span>
                    <span>
                      {new Date(collection.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
