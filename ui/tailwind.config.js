/** Tailwind is driven entirely by the CSS variables in src/design/tokens.css. */
const v = (name) => `var(--${name})`;
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: ["selector", '[data-theme="dark"]'],
  theme: {
    colors: {
      transparent: "transparent",
      current: "currentColor",
      surface: v("surface"),
      raised: v("surface-raised"),
      sunken: v("surface-sunken"),
      ink: v("ink"),
      muted: v("ink-muted"),
      faint: v("ink-faint"),
      rule: v("rule"),
      accent: v("accent"),
      "accent-ink": v("accent-ink"),
      "accent-wash": v("accent-wash"),
      "phase-r": v("phase-r"),
      "phase-y": v("phase-y"),
      "phase-b": v("phase-b"),
      ok: v("status-ok"),
      warn: v("status-warn"),
      alarm: v("status-alarm"),
      offline: v("status-offline"),
      white: "#ffffff",
    },
    fontFamily: {
      sans: ['"IBM Plex Sans"', '"Noto Sans Devanagari"', "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
      cond: ['"IBM Plex Sans Condensed"', '"IBM Plex Sans"', "system-ui", "sans-serif"],
      deva: ['"Noto Sans Devanagari"', '"IBM Plex Sans"', "sans-serif"],
    },
    fontSize: {
      xs: ["12px", "16px"], sm: ["13px", "18px"], base: ["14px", "20px"], md: ["16px", "22px"],
      lg: ["20px", "26px"], xl: ["24px", "30px"], "2xl": ["32px", "38px"],
    },
    fontWeight: { normal: "400", semibold: "600" },
    borderRadius: { none: "0", panel: "2px", ctl: "4px", full: "9999px" },
    boxShadow: { float: v("shadow-float"), none: "none" },
    extend: { spacing: { 4.5: "18px" } },
  },
  plugins: [],
};
