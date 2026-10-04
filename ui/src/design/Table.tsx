import {
  ColumnDef, flexRender, getCoreRowModel, getSortedRowModel, RowSelectionState, SortingState, useReactTable,
} from "@tanstack/react-table";
import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";
import { useState } from "react";
import { cx } from "./primitives";

export type Density = "comfortable" | "compact";

export function Table<T>({ data, columns, density = "comfortable", onRowClick, selectable, caption, maxHeight = 520 }:
  { data: T[]; columns: ColumnDef<T, any>[]; density?: Density; onRowClick?: (row: T) => void;
    selectable?: boolean; caption: string; maxHeight?: number }) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const table = useReactTable({
    data, columns, state: { sorting, rowSelection }, onSortingChange: setSorting,
    onRowSelectionChange: setRowSelection, enableRowSelection: !!selectable,
    getCoreRowModel: getCoreRowModel(), getSortedRowModel: getSortedRowModel(),
  });
  const pad = density === "compact" ? "py-1" : "py-2";
  return (
    <div className="overflow-auto" style={{ maxHeight }}>
      <table className="w-full border-collapse text-left text-sm">
        <caption className="sr-only">{caption}</caption>
        <thead className="sticky top-0 z-10 bg-sunken">
          {table.getHeaderGroups().map((hg) => (
            <tr key={hg.id}>
              {selectable && <th className="w-8 border-b border-rule px-3" />}
              {hg.headers.map((h) => {
                const sorted = h.column.getIsSorted();
                const align = (h.column.columnDef.meta as any)?.align === "right" ? "text-right" : "";
                return (
                  <th key={h.id} scope="col" aria-sort={sorted === "asc" ? "ascending" : sorted === "desc" ? "descending" : "none"}
                    className={cx("whitespace-nowrap border-b border-rule px-3 py-2 font-cond text-xs font-semibold text-muted", align)}>
                    {h.column.getCanSort() ? (
                      <button className="inline-flex items-center gap-1 hover:text-ink" onClick={h.column.getToggleSortingHandler()}>
                        {flexRender(h.column.columnDef.header, h.getContext())}
                        {sorted === "asc" ? <ArrowUp size={12} /> : sorted === "desc" ? <ArrowDown size={12} /> : <ArrowUpDown size={12} className="opacity-40" />}
                      </button>
                    ) : flexRender(h.column.columnDef.header, h.getContext())}
                  </th>
                );
              })}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id} onClick={() => onRowClick?.(row.original)}
              onKeyDown={(e) => { if (onRowClick && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); onRowClick(row.original); } }}
              tabIndex={onRowClick ? 0 : undefined}
              className={cx("border-b border-rule last:border-b-0", onRowClick && "cursor-pointer hover:bg-accent-wash focus:bg-accent-wash",
                row.getIsSelected() && "bg-accent-wash")}>
              {selectable && (
                <td className="px-3" onClick={(e) => e.stopPropagation()}>
                  <input type="checkbox" aria-label="Select row" checked={row.getIsSelected()} onChange={row.getToggleSelectedHandler()} />
                </td>
              )}
              {row.getVisibleCells().map((c) => (
                <td key={c.id} className={cx("num whitespace-nowrap px-3", pad, (c.column.columnDef.meta as any)?.align === "right" && "text-right")}>
                  {flexRender(c.column.columnDef.cell, c.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
