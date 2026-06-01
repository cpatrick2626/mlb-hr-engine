/* Generic baseball-player headshot — stylized silhouette with a team-colored cap.
   Placeholder for real photos (no copyrighted imagery embedded). */
const HeadAvatar = ({ cap = "#005a9c", seed = 0 }) => {
  const skin = ["#caa17a", "#a9805c", "#8a6a4a", "#d8b48f"][seed % 4];
  const gid = `hg${seed}-${Math.round(cap.length * 7)}`;
  return (
    <div className="md-head">
      <svg viewBox="0 0 60 56" preserveAspectRatio="xMidYMax meet">
        <defs>
          <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#212c33" />
            <stop offset="1" stopColor="#0b1217" />
          </linearGradient>
        </defs>
        <rect width="60" height="56" fill={`url(#${gid})`} />
        {/* shoulders / jersey */}
        <path d="M8 56 C8 44 18 39 30 39 C42 39 52 44 52 56 Z" fill="#161f25" />
        <path d="M30 39 L26 56 M30 39 L34 56" stroke="#0b1217" strokeWidth="1" opacity="0.6" />
        {/* neck */}
        <rect x="25" y="32" width="10" height="9" rx="3" fill={skin} />
        {/* head */}
        <ellipse cx="30" cy="25" rx="10.5" ry="11.5" fill={skin} />
        {/* ears */}
        <circle cx="19.8" cy="25" r="2.2" fill={skin} />
        <circle cx="40.2" cy="25" r="2.2" fill={skin} />
        {/* cap */}
        <path d="M18 22 C18 12 42 12 42 22 L42 23 L18 23 Z" fill={cap} />
        <path d="M42 22 C49 22 51 26 50 28 L42 26 Z" fill={cap} opacity="0.85" />
        <path d="M18 22 C18 12 42 12 42 22" fill="none" stroke="rgba(255,255,255,0.18)" strokeWidth="0.8" />
        <circle cx="30" cy="14.6" r="1.1" fill="rgba(255,255,255,0.7)" />
      </svg>
    </div>
  );
};

Object.assign(window, { HeadAvatar });
