'use client'

import { useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error('Application error:', error)
  }, [error])

  return (
    <main className="min-h-screen bg-gradient-to-b from-background to-secondary/20 flex items-center justify-center p-4">
      <Card className="max-w-lg w-full">
        <CardContent className="p-8 text-center">
          <h2 className="text-2xl font-bold mb-4">Something went wrong!</h2>
          <p className="text-muted-foreground mb-6">
            We encountered an unexpected error. Please try again.
          </p>
          <Button onClick={reset}>Try again</Button>
        </CardContent>
      </Card>
    </main>
  )
}
