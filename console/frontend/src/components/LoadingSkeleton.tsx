import { colors } from '@/lib/theme';

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  borderRadius?: number;
  style?: React.CSSProperties;
}

export function Skeleton({ width = '100%', height = 20, borderRadius = 8, style }: SkeletonProps) {
  return (
    <div
      style={{
        width,
        height,
        borderRadius,
        backgroundColor: colors.lightGray,
        position: 'relative',
        overflow: 'hidden',
        ...style,
      }}
    >
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent)',
          animation: 'shimmer 1.5s infinite',
        }}
      />
      <style jsx>{`
        @keyframes shimmer {
          0% {
            transform: translateX(-100%);
          }
          100% {
            transform: translateX(100%);
          }
        }
      `}</style>
    </div>
  );
}

export function TableRowSkeleton({ columns = 6 }: { columns?: number }) {
  return (
    <tr>
      {Array.from({ length: columns }).map((_, idx) => (
        <td key={idx} style={{ padding: '16px 24px' }}>
          <Skeleton height={16} />
        </td>
      ))}
    </tr>
  );
}

export function TableSkeleton({ rows = 5, columns = 6 }: { rows?: number; columns?: number }) {
  return (
    <div style={{
      backgroundColor: '#fff',
      borderRadius: 16,
      border: `1.5px solid ${colors.lightGray}`,
      overflow: 'hidden',
    }}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ backgroundColor: colors.lightGray }}>
            {Array.from({ length: columns }).map((_, idx) => (
              <th key={idx} style={{ padding: '14px 24px' }}>
                <Skeleton height={14} />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: rows }).map((_, idx) => (
            <TableRowSkeleton key={idx} columns={columns} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function StatCardSkeleton() {
  return (
    <div style={{
      backgroundColor: '#fff',
      borderRadius: 16,
      padding: 24,
      border: `1.5px solid ${colors.lightGray}`,
    }}>
      <Skeleton width={100} height={12} style={{ marginBottom: 12 }} />
      <Skeleton width={60} height={32} />
    </div>
  );
}

export function DashboardSkeleton() {
  return (
    <div style={{ padding: 40 }}>
      <Skeleton width={200} height={32} style={{ marginBottom: 40 }} />

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: 24,
        marginBottom: 40,
      }}>
        {Array.from({ length: 4 }).map((_, idx) => (
          <StatCardSkeleton key={idx} />
        ))}
      </div>

      <TableSkeleton rows={5} columns={5} />
    </div>
  );
}
