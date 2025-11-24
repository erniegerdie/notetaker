import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { FileVideo } from 'lucide-react'

export default function NotFound() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-background to-secondary/20 flex items-center justify-center p-4">
      <Card className="max-w-lg w-full">
        <CardContent className="p-8 text-center">
          <FileVideo className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2">Page Not Found</h2>
          <p className="text-muted-foreground mb-6">
            The page you&apos;re looking for doesn&apos;t exist.
          </p>
          <Link href="/">
            <Button>Go Home</Button>
          </Link>
        </CardContent>
      </Card>
    </main>
  )
}
