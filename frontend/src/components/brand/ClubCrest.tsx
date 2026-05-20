/**
 * Club crest — TV Fischbek shield with Hamburg-harbor waves + monogram.
 * Sourced from the brand design package; SVG so it scales cleanly into
 * the sidebar header, the login screen, and the favicon.
 */
interface Props {
  size?: number;
  ring?: boolean;
  className?: string;
}

export const ClubCrest = ({ size = 40, ring = false, className }: Props) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 64 64"
    className={className}
    style={{ flex: '0 0 auto' }}
    aria-hidden="true"
  >
    <defs>
      <linearGradient id="tvf-crest-navy" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor="#15375F" />
        <stop offset="1" stopColor="#081A2D" />
      </linearGradient>
    </defs>
    {/* shield */}
    <path
      d="M32 4 8 11v18c0 16 11 25 24 29 13-4 24-13 24-29V11L32 4Z"
      fill="url(#tvf-crest-navy)"
      stroke="#E9C775"
      strokeWidth="1.5"
    />
    {/* red banner */}
    <path d="M8 19h48v9H8z" fill="#D62027" />
    {/* harbor waves */}
    <path
      d="M8 38c4-2 8 2 12 0s8-2 12 0 8 2 12 0 8-2 12 0v6c-4 2-8-2-12 0s-8 2-12 0-8-2-12 0-8 2-12 0v-6Z"
      fill="#F4F1EA"
      opacity="0.9"
    />
    {/* monogram */}
    <text
      x="32"
      y="27"
      textAnchor="middle"
      fontFamily="Anton, Impact"
      fontSize="11"
      fill="#F4F1EA"
      letterSpacing="1"
    >
      TVF
    </text>
    {ring && <circle cx="32" cy="32" r="30" fill="none" stroke="#E9C775" strokeWidth="1" />}
  </svg>
);
