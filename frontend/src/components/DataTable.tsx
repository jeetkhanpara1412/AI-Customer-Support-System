import type { ReactNode } from 'react'

export interface DataColumn<Row> {
  key: string
  header: string
  render: (row: Row) => ReactNode
}

export function DataTable<Row extends { id: string | number }>({
  columns,
  rows,
  emptyMessage = 'No data to display.',
}: {
  columns: DataColumn<Row>[]
  rows: Row[]
  emptyMessage?: string
}) {
  if (!rows.length) return <p className="panel">{emptyMessage}</p>
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <table className="w-full text-left text-sm">
        <thead><tr>{columns.map((column) => <th key={column.key}>{column.header}</th>)}</tr></thead>
        <tbody>{rows.map((row) => <tr key={row.id}>{columns.map((column) => <td key={column.key}>{column.render(row)}</td>)}</tr>)}</tbody>
      </table>
    </div>
  )
}
