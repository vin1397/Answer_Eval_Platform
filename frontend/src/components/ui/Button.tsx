import { ButtonHTMLAttributes, ReactNode } from "react";
import clsx from "clsx";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: "primary" | "ghost" | "danger";
  icon?: ReactNode;
}

export default function Button({
  children,
  variant = "primary",
  icon,
  className,
  ...rest
}: ButtonProps) {
  return (
    <button
      className={clsx(
        "neo-btn inline-flex items-center justify-center gap-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0",
        variant === "primary" && "bg-primary text-white",
        variant === "ghost" && "bg-surface dark:bg-dark-card text-ink dark:text-dark-ink",
        variant === "danger" && "bg-red-500 text-white",
        className
      )}
      {...rest}
    >
      {icon}
      {children}
    </button>
  );
}
