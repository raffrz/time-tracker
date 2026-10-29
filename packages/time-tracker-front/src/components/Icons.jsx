// Icones SVG inline (traco), herdam a cor via currentColor.
const base = {
  width: 20,
  height: 20,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round",
  strokeLinejoin: "round",
  "aria-hidden": true,
};

const make = (paths) =>
  function Icon({ size = 20, ...rest }) {
    return (
      <svg {...base} width={size} height={size} {...rest}>
        {paths}
      </svg>
    );
  };

export const IconClock = make(
  <>
    <circle cx="12" cy="13" r="8" />
    <path d="M12 9v4l2.5 2.5M10 2h4" />
  </>
);
export const IconHome = make(<path d="M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z" />);
export const IconHistory = make(
  <>
    <path d="M3 12a9 9 0 1 0 3-6.7L3 8" />
    <path d="M3 3v5h5M12 7v5l3 2" />
  </>
);
export const IconPause = make(<path d="M9 6v12M15 6v12" />);
export const IconPlay = make(<path d="M8 5.5v13l10.5-6.5z" fill="currentColor" />);
export const IconSwap = make(<path d="M4 8h14l-3.5-3.5M20 16H6l3.5 3.5" />);
export const IconPlus = make(<path d="M12 5v14M5 12h14" />);
export const IconStop = make(<rect x="7" y="7" width="10" height="10" rx="1.5" fill="currentColor" />);
export const IconCoffee = make(
  <>
    <path d="M4 9h12v5a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5z" />
    <path d="M16 11h1.5a2.5 2.5 0 0 1 0 5H16M8 3v3M12 3v3" />
  </>
);
export const IconTarget = make(
  <>
    <circle cx="12" cy="12" r="8" />
    <circle cx="12" cy="12" r="4" />
    <circle cx="12" cy="12" r="0.6" fill="currentColor" />
  </>
);
export const IconCalendar = make(
  <>
    <rect x="3.5" y="5" width="17" height="15" rx="2" />
    <path d="M3.5 10h17M8 3v4M16 3v4" />
  </>
);
export const IconTerminal = make(
  <>
    <rect x="3" y="4" width="18" height="16" rx="3" />
    <path d="M7 9l3 3-3 3M12 15h5" />
  </>
);
export const IconList = make(<path d="M9 6h11M9 12h11M9 18h11M4 6h.01M4 12h.01M4 18h.01" />);
export const IconChevronRight = make(<path d="M9 6l6 6-6 6" />);
export const IconChevronDown = make(<path d="M6 9l6 6 6-6" />);
export const IconFlag = make(<path d="M5 21V4M5 4h11l-2 4 2 4H5" />);
export const IconX = make(<path d="M6 6l12 12M18 6L6 18" />);
export const IconMountain = make(<path d="M2 20l7-11 4 6 3-4 6 9zM9 9l1.5 2.5" />);
