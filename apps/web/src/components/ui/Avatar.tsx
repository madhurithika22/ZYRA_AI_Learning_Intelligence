"use client";

import React from "react";

export type AvatarSize = "xs" | "sm" | "md" | "lg" | "xl";

export interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
  name?: string;
  src?: string | null;
  size?: AvatarSize;
  status?: "online" | "offline" | "busy" | "away";
  className?: string;
}

export function Avatar({
  name = "Learner",
  src,
  size = "md",
  status,
  className = "",
  ...props
}: AvatarProps) {
  const [imageError, setImageError] = React.useState(false);

  const sizeMap: Record<AvatarSize, { container: string; text: string; badge: string }> = {
    xs: { container: "h-6 w-6 rounded-lg", text: "text-[10px]", badge: "h-1.5 w-1.5" },
    sm: { container: "h-8 w-8 rounded-xl", text: "text-xs", badge: "h-2 w-2" },
    md: { container: "h-10 w-10 rounded-xl", text: "text-sm", badge: "h-2.5 w-2.5" },
    lg: { container: "h-12 w-12 rounded-2xl", text: "text-base", badge: "h-3 w-3" },
    xl: { container: "h-16 w-16 rounded-2xl", text: "text-xl", badge: "h-4 w-4" },
  };

  const statusColor = {
    online: "bg-accent-mint border-surface",
    offline: "bg-text-muted border-surface",
    busy: "bg-accent-rose border-surface",
    away: "bg-accent-amber border-surface",
  };

  const initials = name
    ? name
        .split(" ")
        .map((part) => part[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "U";

  const { container, text, badge } = sizeMap[size];

  return (
    <div className={`relative inline-block shrink-0 ${className}`} {...props}>
      <div
        className={`${container} bg-accent-primary text-white font-bold flex items-center justify-center shadow-xs overflow-hidden select-none border border-black/10 dark:border-white/10`}
      >
        {src && !imageError ? (
          <img
            src={src}
            alt={name}
            onError={() => setImageError(true)}
            className="h-full w-full object-cover"
          />
        ) : (
          <span className={`${text} tracking-tight`}>{initials}</span>
        )}
      </div>

      {status && (
        <span
          className={`absolute bottom-0 right-0 rounded-full border-2 ${badge} ${statusColor[status]}`}
          aria-label={`Status: ${status}`}
        />
      )}
    </div>
  );
}
