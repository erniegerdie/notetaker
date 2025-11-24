'use client'

import { useState } from 'react'
import { X } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

interface NewCollectionModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onCreateCollection?: (name: string) => void
}

export function NewCollectionModal({
  open,
  onOpenChange,
  onCreateCollection,
}: NewCollectionModalProps) {
  const [collectionName, setCollectionName] = useState('')

  const handleCreate = () => {
    if (collectionName.trim()) {
      onCreateCollection?.(collectionName.trim())
      setCollectionName('')
      onOpenChange(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleCreate()
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px] p-0 gap-0">
        <DialogHeader className="p-6 pb-4">
          <div className="flex items-center justify-between">
            <DialogTitle className="text-2xl font-bold">New Collection</DialogTitle>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 rounded-full hover:bg-gray-100"
              onClick={() => onOpenChange(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </DialogHeader>

        <div className="px-6 pb-6 space-y-4">
          <div className="space-y-2">
            <Label htmlFor="collection-name" className="text-base font-medium">
              Collection Name
            </Label>
            <Input
              id="collection-name"
              placeholder="Enter collection name..."
              value={collectionName}
              onChange={(e) => setCollectionName(e.target.value)}
              onKeyDown={handleKeyDown}
              className="h-12 text-base border-2 border-blue-600 focus-visible:ring-blue-600"
              autoFocus
            />
          </div>

          <Button
            onClick={handleCreate}
            className="w-full h-12 bg-blue-900 hover:bg-blue-800 text-white text-base font-medium"
            disabled={!collectionName.trim()}
          >
            Create Collection
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
