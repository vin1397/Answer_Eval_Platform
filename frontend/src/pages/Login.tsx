import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion } from "framer-motion";
import { Navigate, useNavigate } from "react-router-dom";
import { Lock, User as UserIcon, BrainCircuit, Eye, EyeOff } from "lucide-react";
import { useAuth } from "../context/AuthContext";

const schema = z.object({
  username: z.string().min(3, "Username must be at least 3 characters"),
  password: z.string().min(6, "Password must be at least 6 characters"),
  rememberMe: z.boolean().optional(),
});
type FormValues = z.infer<typeof schema>;

export default function Login() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  if (isAuthenticated) return <Navigate to="/app/dashboard" replace />;

  async function onSubmit(values: FormValues) {
    setServerError(null);
    try {
      await login(values.username, values.password, !!values.rememberMe);
      navigate("/app/dashboard");
    } catch (err: any) {
      setServerError(err?.response?.data?.detail || "Invalid username or password");
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface dark:bg-dark-surface px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="neo-card w-full max-w-md p-10"
      >
        <div className="flex flex-col items-center text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary text-white shadow-neo-flat">
            <BrainCircuit size={26} />
          </div>
          <h1 className="mt-5 text-2xl font-extrabold">Admin Login</h1>
          <p className="mt-1 text-sm text-ink/60 dark:text-dark-ink/60">
            Sign in to manage evaluations
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="mt-8 space-y-5">
          <div>
            <label className="mb-1.5 block text-xs font-semibold text-ink/70 dark:text-dark-ink/70">
              Username
            </label>
            <div className="relative">
              <UserIcon size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-ink/40" />
              <input
                {...register("username")}
                className="neo-input pl-11"
                placeholder="admin"
                autoComplete="username"
              />
            </div>
            {errors.username && (
              <p className="mt-1 text-xs text-red-500">{errors.username.message}</p>
            )}
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-semibold text-ink/70 dark:text-dark-ink/70">
              Password
            </label>
            <div className="relative">
              <Lock size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-ink/40" />
              <input
                {...register("password")}
                type={showPassword ? "text" : "password"}
                className="neo-input pl-11 pr-11"
                placeholder="••••••••"
                autoComplete="current-password"
              />
              <button
                type="button"
                onClick={() => setShowPassword((s) => !s)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-ink/40"
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            {errors.password && (
              <p className="mt-1 text-xs text-red-500">{errors.password.message}</p>
            )}
          </div>

          <div className="flex items-center justify-between text-xs">
            <label className="flex items-center gap-2 text-ink/70 dark:text-dark-ink/70">
              <input type="checkbox" {...register("rememberMe")} className="rounded accent-primary" />
              Remember Me
            </label>
            <a href="#" className="font-semibold text-accent">
              Forgot Password?
            </a>
          </div>

          {serverError && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="rounded-xl bg-red-50 px-4 py-2 text-center text-xs font-medium text-red-600"
            >
              {serverError}
            </motion.p>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="neo-btn w-full bg-primary text-white disabled:opacity-60"
          >
            {isSubmitting ? "Signing in..." : "Login"}
          </button>
        </form>
      </motion.div>
    </div>
  );
}
