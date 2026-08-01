import { HTMLAttributes, ReactNode } from "react";
import clsx from "clsx";

interface NeoCardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  inset?: boolean;
  className?: string;
}

export default function NeoCard({ children, inset, className, ...rest }: NeoCardProps) {
  return (
    <div
      className={clsx(inset ? "neo-inset" : "neo-card", "p-6", className)}
      {...rest}
    >
      {children}
    </div>
  );
}
