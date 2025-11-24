import { Badge } from '@/components/ui/badge'
import { Loader2, CheckCircle2, XCircle, Clock } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { VideoStatus } from '@/lib/types'

interface StatusBadgeProps {
  status: VideoStatus
  className?: string
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = {
    uploaded: {
      label: 'Queued',
      icon: Clock,
      variant: 'secondary' as const,
      iconClassName: undefined,
    },
    processing: {
      label: 'Processing',
      icon: Loader2,
      variant: 'default' as const,
      iconClassName: 'animate-spin',
    },
    completed: {
      label: 'Completed',
      icon: CheckCircle2,
      variant: 'success' as const,
      iconClassName: undefined,
    },
    failed: {
      label: 'Failed',
      icon: XCircle,
      variant: 'destructive' as const,
      iconClassName: undefined,
    },
  }

  const { label, icon: Icon, variant, iconClassName } = config[status]

  return (
    <Badge variant={variant} className={className}>
      <Icon className={cn('mr-1 h-3 w-3', iconClassName)} />
      {label}
    </Badge>
  )
}
