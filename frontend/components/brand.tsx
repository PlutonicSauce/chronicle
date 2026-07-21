export function BrandMark({ compact = false }: { compact?: boolean }) {
  return (
    <div className="brand-mark" aria-label="Chronicle">
      <svg viewBox="0 0 32 32" role="img" aria-hidden="true">
        <path d="M8 10.5 16 6l8 4.5v9L16 24l-8-4.5v-9Z" fill="none" stroke="currentColor" strokeWidth="1.6" />
        <path d="m8.6 10.8 7.4 4.25 7.4-4.25M16 15v9" fill="none" stroke="currentColor" strokeWidth="1.6" />
        <circle cx="16" cy="15" r="2.25" fill="currentColor" />
      </svg>
      {!compact && <span>chronicle</span>}
    </div>
  );
}
