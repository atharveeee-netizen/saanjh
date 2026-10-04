import React from "react";
import { cx } from "../design/primitives";

/** A plain phone outline (no device brand) that holds a 360px-wide screen. On narrow
 *  screens the frame disappears and the content fills the width. */
export function PhoneFrame({ children, label, className }: { children: React.ReactNode; label: string; className?: string }) {
  return (
    <figure className={cx("m-0 flex w-full max-w-[392px] flex-col items-center gap-2", className)}>
      <div className="w-full overflow-hidden rounded-[28px] border border-rule bg-raised sm:border-[8px] sm:border-sunken sm:shadow-float">
        <div className="hidden h-5 items-center justify-center bg-sunken sm:flex" aria-hidden>
          <span className="h-1.5 w-16 rounded-full bg-rule" />
        </div>
        <div className="max-h-[720px] overflow-y-auto">{children}</div>
      </div>
      <figcaption className="text-xs text-muted">{label}</figcaption>
    </figure>
  );
}

export function LangSwitch<T extends string>({ value, onChange, options }:
  { value: T; onChange: (v: T) => void; options: { value: T; label: string }[] }) {
  return (
    <div role="radiogroup" aria-label="Language" className="inline-flex rounded-ctl border border-rule bg-raised p-0.5">
      {options.map((o) => (
        <button key={o.value} role="radio" aria-checked={value === o.value} onClick={() => onChange(o.value)}
          className={cx("min-h-[36px] rounded-ctl px-3 text-sm font-deva", value === o.value ? "bg-accent font-semibold text-accent-ink" : "text-muted")}>
          {o.label}
        </button>
      ))}
    </div>
  );
}
