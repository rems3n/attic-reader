/** Attic Academy mark: an Ionic column. Inherits the text colour. */
export default function Logo({ size = 32 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="currentColor"
      aria-hidden="true"
      focusable="false"
    >
      <rect x="12" y="9" width="40" height="4" rx="1" />
      <rect x="16" y="15" width="32" height="4" />
      <circle cx="15" cy="20" r="5" fill="none" stroke="currentColor" strokeWidth="2.6" />
      <circle cx="15" cy="20" r="1.6" />
      <circle cx="49" cy="20" r="5" fill="none" stroke="currentColor" strokeWidth="2.6" />
      <circle cx="49" cy="20" r="1.6" />
      <rect x="20" y="25" width="4.5" height="25" />
      <rect x="26.5" y="25" width="4.5" height="25" />
      <rect x="33" y="25" width="4.5" height="25" />
      <rect x="39.5" y="25" width="4.5" height="25" />
      <rect x="17" y="51" width="30" height="3" />
      <rect x="13" y="55" width="38" height="4" rx="1" />
    </svg>
  );
}
