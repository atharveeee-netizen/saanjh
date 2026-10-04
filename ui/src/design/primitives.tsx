import * as RDialog from "@radix-ui/react-dialog";
import * as RPopover from "@radix-ui/react-popover";
import * as RSelect from "@radix-ui/react-select";
import * as RCheckbox from "@radix-ui/react-checkbox";
import * as RSwitch from "@radix-ui/react-switch";
import * as RTabs from "@radix-ui/react-tabs";
import * as RTooltip from "@radix-ui/react-tooltip";
import * as RToggleGroup from "@radix-ui/react-toggle-group";
import * as RToast from "@radix-ui/react-toast";
import { Check, ChevronDown, ChevronRight, Loader2, X } from "lucide-react";
import React, { createContext, useCallback, useContext, useState } from "react";

const cx = (...c: (string | false | null | undefined)[]) => c.filter(Boolean).join(" ");
export { cx };

/* ---------------------------------------------------------------- Button */
type Variant = "primary" | "secondary" | "quiet" | "destructive";
const variants: Record<Variant, string> = {
  primary: "bg-accent text-accent-ink border border-accent hover:brightness-110",
  secondary: "bg-raised text-ink border border-rule hover:border-muted",
  quiet: "bg-transparent text-accent border border-transparent hover:bg-accent-wash",
  destructive: "bg-raised text-alarm border border-alarm hover:bg-alarm hover:text-white",
};

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  loading?: boolean;
  icon?: React.ReactNode;
  size?: "sm" | "md";
}
export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = "secondary", loading, icon, size = "md", className, children, disabled, ...rest }, ref) {
  return (
    <button ref={ref} disabled={disabled || loading}
      className={cx("inline-flex items-center justify-center gap-2 rounded-ctl font-semibold transition-colors",
        size === "md" ? "h-9 px-4 text-base" : "h-8 px-3 text-sm",
        variants[variant], (disabled || loading) && "opacity-60 cursor-not-allowed", className)}
      {...rest}>
      {loading ? <Loader2 size={16} className="animate-spin" aria-hidden /> : icon}
      <span>{children}</span>
    </button>
  );
});

export function IconButton({ label, children, className, ...rest }:
  React.ButtonHTMLAttributes<HTMLButtonElement> & { label: string }) {
  return (
    <Tooltip content={label}>
      <button aria-label={label}
        className={cx("inline-flex h-8 w-8 items-center justify-center rounded-ctl text-muted hover:bg-sunken hover:text-ink", className)}
        {...rest}>{children}</button>
    </Tooltip>
  );
}

/* ---------------------------------------------------------------- Fields */
export function TextField({ label, id, hint, error, className, ...rest }:
  React.InputHTMLAttributes<HTMLInputElement> & { label: string; id: string; hint?: string; error?: string }) {
  return (
    <div className={cx("flex flex-col gap-1", className)}>
      <label htmlFor={id} className="text-sm font-semibold text-ink">{label}</label>
      <input id={id} aria-invalid={!!error} aria-describedby={hint || error ? `${id}-hint` : undefined}
        className={cx("h-9 rounded-ctl border bg-raised px-3 text-base text-ink placeholder:text-faint",
          error ? "border-alarm" : "border-rule focus:border-accent")} {...rest} />
      {(hint || error) && <p id={`${id}-hint`} className={cx("text-xs", error ? "text-alarm" : "text-muted")}>{error || hint}</p>}
    </div>
  );
}

export function Select({ label, id, value, onValueChange, options, className }:
  { label?: string; id: string; value: string; onValueChange: (v: string) => void;
    options: { value: string; label: string }[]; className?: string }) {
  return (
    <div className={cx("flex flex-col gap-1", className)}>
      {label && <label htmlFor={id} className="text-sm font-semibold">{label}</label>}
      <RSelect.Root value={value} onValueChange={onValueChange}>
        <RSelect.Trigger id={id} className="inline-flex h-9 items-center justify-between gap-2 rounded-ctl border border-rule bg-raised px-3 text-base">
          <RSelect.Value />
          <RSelect.Icon><ChevronDown size={16} className="text-muted" /></RSelect.Icon>
        </RSelect.Trigger>
        <RSelect.Portal>
          <RSelect.Content position="popper" sideOffset={4} className="z-50 min-w-[var(--radix-select-trigger-width)] rounded-ctl border border-rule bg-raised p-1 shadow-float">
            <RSelect.Viewport>
              {options.map((o) => (
                <RSelect.Item key={o.value} value={o.value}
                  className="flex cursor-pointer items-center justify-between gap-4 rounded-ctl px-2 py-1.5 text-base outline-none data-[highlighted]:bg-accent-wash">
                  <RSelect.ItemText>{o.label}</RSelect.ItemText>
                  <RSelect.ItemIndicator><Check size={14} /></RSelect.ItemIndicator>
                </RSelect.Item>
              ))}
            </RSelect.Viewport>
          </RSelect.Content>
        </RSelect.Portal>
      </RSelect.Root>
    </div>
  );
}

export function SegmentedControl({ value, onValueChange, options, label }:
  { value: string; onValueChange: (v: string) => void; options: { value: string; label: string }[]; label: string }) {
  return (
    <RToggleGroup.Root type="single" value={value} aria-label={label}
      onValueChange={(v) => v && onValueChange(v)}
      className="inline-flex rounded-ctl border border-rule bg-raised p-0.5">
      {options.map((o) => (
        <RToggleGroup.Item key={o.value} value={o.value}
          className="h-7 rounded-ctl px-3 text-sm text-muted data-[state=on]:bg-accent data-[state=on]:font-semibold data-[state=on]:text-accent-ink">
          {o.label}
        </RToggleGroup.Item>
      ))}
    </RToggleGroup.Root>
  );
}

export function Checkbox({ id, label, checked, onCheckedChange }:
  { id: string; label: string; checked: boolean; onCheckedChange: (v: boolean) => void }) {
  return (
    <div className="flex items-center gap-2">
      <RCheckbox.Root id={id} checked={checked} onCheckedChange={(v) => onCheckedChange(v === true)}
        className="flex h-4 w-4 items-center justify-center rounded-[3px] border border-muted bg-raised data-[state=checked]:border-accent data-[state=checked]:bg-accent">
        <RCheckbox.Indicator><Check size={12} className="text-accent-ink" strokeWidth={3} /></RCheckbox.Indicator>
      </RCheckbox.Root>
      <label htmlFor={id} className="text-base">{label}</label>
    </div>
  );
}

export function Toggle({ id, label, checked, onCheckedChange }:
  { id: string; label: string; checked: boolean; onCheckedChange: (v: boolean) => void }) {
  return (
    <div className="flex items-center gap-2">
      <RSwitch.Root id={id} checked={checked} onCheckedChange={onCheckedChange}
        className="relative h-5 w-9 rounded-full border border-rule bg-sunken data-[state=checked]:border-accent data-[state=checked]:bg-accent">
        <RSwitch.Thumb className="block h-4 w-4 translate-x-0.5 rounded-full bg-raised shadow-float transition-transform data-[state=checked]:translate-x-[17px]" />
      </RSwitch.Root>
      <label htmlFor={id} className="text-base">{label}</label>
    </div>
  );
}

/* ---------------------------------------------------------------- Overlays */
export function Tooltip({ content, children }: { content: React.ReactNode; children: React.ReactNode }) {
  return (
    <RTooltip.Root delayDuration={300}>
      <RTooltip.Trigger asChild>{children}</RTooltip.Trigger>
      <RTooltip.Portal>
        <RTooltip.Content sideOffset={6} className="z-50 max-w-xs rounded-ctl bg-ink px-2 py-1 text-xs text-surface shadow-float">
          {content}
        </RTooltip.Content>
      </RTooltip.Portal>
    </RTooltip.Root>
  );
}

export function Popover({ trigger, children }: { trigger: React.ReactNode; children: React.ReactNode }) {
  return (
    <RPopover.Root>
      <RPopover.Trigger asChild>{trigger}</RPopover.Trigger>
      <RPopover.Portal>
        <RPopover.Content sideOffset={6} className="z-50 w-72 rounded-ctl border border-rule bg-raised p-3 shadow-float">
          {children}
        </RPopover.Content>
      </RPopover.Portal>
    </RPopover.Root>
  );
}

export function Dialog({ open, onOpenChange, title, description, children, footer }:
  { open: boolean; onOpenChange: (o: boolean) => void; title: string; description?: string;
    children: React.ReactNode; footer?: React.ReactNode }) {
  return (
    <RDialog.Root open={open} onOpenChange={onOpenChange}>
      <RDialog.Portal>
        <RDialog.Overlay className="fixed inset-0 z-40 bg-[rgba(10,14,12,0.45)]" />
        <RDialog.Content className="fixed left-1/2 top-1/2 z-50 flex max-h-[85vh] w-[min(560px,calc(100vw-32px))] -translate-x-1/2 -translate-y-1/2 flex-col rounded-panel border border-rule bg-raised shadow-float">
          <div className="flex items-start justify-between gap-4 border-b border-rule px-5 py-4">
            <div>
              <RDialog.Title className="text-md font-semibold">{title}</RDialog.Title>
              {description && <RDialog.Description className="mt-1 text-sm text-muted">{description}</RDialog.Description>}
            </div>
            <RDialog.Close asChild><IconButton label="Close"><X size={16} /></IconButton></RDialog.Close>
          </div>
          <div className="overflow-y-auto px-5 py-4">{children}</div>
          {footer && <div className="flex justify-end gap-2 border-t border-rule px-5 py-3">{footer}</div>}
        </RDialog.Content>
      </RDialog.Portal>
    </RDialog.Root>
  );
}

export function Drawer({ open, onOpenChange, title, subtitle, children }:
  { open: boolean; onOpenChange: (o: boolean) => void; title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <RDialog.Root open={open} onOpenChange={onOpenChange}>
      <RDialog.Portal>
        <RDialog.Overlay className="fixed inset-0 z-40 bg-[rgba(10,14,12,0.25)]" />
        <RDialog.Content className="fixed bottom-0 right-0 top-0 z-50 flex w-[min(460px,100vw)] flex-col border-l border-rule bg-raised shadow-float">
          <div className="flex items-start justify-between gap-4 border-b border-rule px-5 py-4">
            <div>
              <RDialog.Title className="text-md font-semibold">{title}</RDialog.Title>
              {subtitle && <RDialog.Description className="mt-0.5 text-sm text-muted">{subtitle}</RDialog.Description>}
            </div>
            <RDialog.Close asChild><IconButton label="Close panel"><X size={16} /></IconButton></RDialog.Close>
          </div>
          <div className="flex-1 overflow-y-auto px-5 py-4">{children}</div>
        </RDialog.Content>
      </RDialog.Portal>
    </RDialog.Root>
  );
}

/* ---------------------------------------------------------------- Tabs */
export function Tabs({ value, onValueChange, items, label }:
  { value: string; onValueChange: (v: string) => void; label: string;
    items: { value: string; label: string; content: React.ReactNode }[] }) {
  return (
    <RTabs.Root value={value} onValueChange={onValueChange}>
      <RTabs.List aria-label={label} className="flex gap-4 border-b border-rule">
        {items.map((i) => (
          <RTabs.Trigger key={i.value} value={i.value}
            className="-mb-px border-b-2 border-transparent pb-2 text-base text-muted data-[state=active]:border-accent data-[state=active]:font-semibold data-[state=active]:text-ink">
            {i.label}
          </RTabs.Trigger>
        ))}
      </RTabs.List>
      {items.map((i) => <RTabs.Content key={i.value} value={i.value} className="pt-4">{i.content}</RTabs.Content>)}
    </RTabs.Root>
  );
}

/* ---------------------------------------------------------------- Breadcrumb, Kbd */
export function Breadcrumb({ items }: { items: { label: string; onClick?: () => void }[] }) {
  return (
    <nav aria-label="Breadcrumb">
      <ol className="flex flex-wrap items-center gap-1 text-sm text-muted">
        {items.map((it, i) => (
          <li key={i} className="flex items-center gap-1">
            {i > 0 && <ChevronRight size={14} aria-hidden className="text-faint" />}
            {it.onClick ? <button className="hover:text-accent hover:underline" onClick={it.onClick}>{it.label}</button>
              : <span className={i === items.length - 1 ? "font-semibold text-ink" : ""} aria-current={i === items.length - 1 ? "page" : undefined}>{it.label}</span>}
          </li>
        ))}
      </ol>
    </nav>
  );
}

export function Kbd({ keys }: { keys: string[] }) {
  return (
    <span className="inline-flex gap-1">
      {keys.map((k) => <kbd key={k} className="rounded-[3px] border border-rule bg-sunken px-1.5 font-cond text-xs text-muted">{k}</kbd>)}
    </span>
  );
}

/* ---------------------------------------------------------------- Toast */
type ToastItem = { id: number; title: string; body?: string; tone?: "ok" | "warn" | "alarm" };
const ToastCtx = createContext<(t: Omit<ToastItem, "id">) => void>(() => {});
export const useToast = () => useContext(ToastCtx);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const push = useCallback((t: Omit<ToastItem, "id">) => setItems((x) => [...x, { ...t, id: Date.now() + Math.random() }]), []);
  return (
    <ToastCtx.Provider value={push}>
      <RToast.Provider swipeDirection="right" duration={5000}>
        {children}
        {items.map((t) => (
          <RToast.Root key={t.id} onOpenChange={(o) => !o && setItems((x) => x.filter((y) => y.id !== t.id))}
            className={cx("flex items-start gap-3 rounded-ctl border border-rule border-l-4 bg-raised px-4 py-3 shadow-float",
              t.tone === "alarm" ? "border-l-alarm" : t.tone === "warn" ? "border-l-warn" : "border-l-ok")}>
            <div className="flex-1">
              <RToast.Title className="text-base font-semibold">{t.title}</RToast.Title>
              {t.body && <RToast.Description className="text-sm text-muted">{t.body}</RToast.Description>}
            </div>
            <RToast.Close aria-label="Dismiss" className="text-muted hover:text-ink"><X size={14} /></RToast.Close>
          </RToast.Root>
        ))}
        <RToast.Viewport className="fixed bottom-4 right-4 z-[60] flex w-[min(380px,calc(100vw-32px))] flex-col gap-2 outline-none" />
      </RToast.Provider>
    </ToastCtx.Provider>
  );
}

export const TooltipProvider = RTooltip.Provider;
