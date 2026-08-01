import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import {
  ScanLine, BrainCircuit, Sparkles, LineChart, ShieldCheck, ArrowRight, CheckCircle2,
} from "lucide-react";

const FEATURES = [
  {
    icon: ScanLine,
    title: "OCR Reading",
    desc: "PaddleOCR-driven handwriting recognition reads scanned answer scripts, tables, and diagrams with high fidelity.",
  },
  {
    icon: BrainCircuit,
    title: "NLP Understanding",
    desc: "Sentence-transformer embeddings capture the meaning of an answer, not just its keywords — paraphrases score fairly.",
  },
  {
    icon: Sparkles,
    title: "Machine Learning",
    desc: "A confidence model trained on teacher corrections learns when to trust the AI and when to escalate for review.",
  },
  {
    icon: CheckCircle2,
    title: "Automatic Marks",
    desc: "Marks are computed per question against faculty rubrics, then rolled up into a transparent, auditable total.",
  },
  {
    icon: ShieldCheck,
    title: "Teacher Verification",
    desc: "Every AI decision stays reviewable — approve, adjust, or send back for re-evaluation in one click.",
  },
  {
    icon: LineChart,
    title: "Analytics",
    desc: "Question-wise performance, class averages, and pass-rate trends surface instantly for every examination.",
  },
];

export default function Landing() {
  return (
    <div className="min-h-screen overflow-hidden bg-surface dark:bg-dark-surface text-ink dark:text-dark-ink">
      {/* Hero */}
      <section className="relative overflow-hidden px-6 pt-10 pb-28">
        {/* floating AI particles */}
        <div className="pointer-events-none absolute inset-0 -z-0">
          {[...Array(10)].map((_, i) => (
            <span
              key={i}
              className="absolute rounded-full bg-accent/20 animate-float"
              style={{
                width: `${20 + (i % 4) * 14}px`,
                height: `${20 + (i % 4) * 14}px`,
                left: `${(i * 9.3) % 100}%`,
                top: `${(i * 17) % 90}%`,
                animationDelay: `${i * 0.4}s`,
                animationDuration: `${5 + (i % 3)}s`,
              }}
            />
          ))}
        </div>

        <nav className="relative z-10 mx-auto flex max-w-7xl items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary text-white shadow-neo-flat">
              <BrainCircuit size={20} />
            </div>
            <span className="text-base font-bold">AnswerEval AI</span>
          </div>
          <Link to="/login">
            <button className="neo-btn bg-primary text-sm text-white">Admin Login</button>
          </Link>
        </nav>

        <div className="relative z-10 mx-auto mt-20 max-w-4xl text-center">
          <motion.span
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="neo-card inline-block rounded-full px-4 py-1.5 text-xs font-semibold text-accent"
          >
            OCR &middot; NLP &middot; Machine Learning
          </motion.span>

          <motion.h1
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="mt-6 text-4xl font-extrabold leading-tight sm:text-5xl lg:text-6xl"
          >
            Intelligent Answer Script Evaluation{" "}
            <span className="text-primary">&amp; Automated Mark Assignment</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="mx-auto mt-6 max-w-2xl text-base text-ink/70 dark:text-dark-ink/70 sm:text-lg"
          >
            An AI-powered automated evaluation platform capable of reading handwritten
            answer scripts, understanding responses using Natural Language Processing,
            and automatically assigning marks with teacher verification.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="mt-10 flex flex-wrap items-center justify-center gap-4"
          >
            <Link to="/login">
              <button className="neo-btn flex items-center gap-2 bg-primary text-white">
                Admin Login <ArrowRight size={16} />
              </button>
            </Link>
            <a href="#features">
              <button className="neo-btn bg-surface dark:bg-dark-card">Learn More</button>
            </a>
          </motion.div>
        </div>

        {/* Hero neomorphic showcase card */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="neo-card relative z-10 mx-auto mt-20 grid max-w-5xl grid-cols-2 gap-4 p-8 sm:grid-cols-4"
        >
          {[
            ["98.2%", "OCR Accuracy"],
            ["0.6s", "Avg. NLP Score Time"],
            ["4,500+", "Scripts Evaluated"],
            ["87%", "Auto-Approval Rate"],
          ].map(([value, label]) => (
            <div key={label} className="text-center">
              <p className="text-2xl font-extrabold text-primary sm:text-3xl">{value}</p>
              <p className="mt-1 text-xs text-ink/60 dark:text-dark-ink/60">{label}</p>
            </div>
          ))}
        </motion.div>
      </section>

      {/* Features */}
      <section id="features" className="mx-auto max-w-7xl px-6 pb-28">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-extrabold sm:text-4xl">Everything the evaluation desk needs</h2>
          <p className="mt-3 text-ink/60 dark:text-dark-ink/60">
            From the moment a script is scanned to the moment marks are published.
          </p>
        </div>

        <div className="mt-14 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map(({ icon: Icon, title, desc }, i) => (
            <motion.div
              key={title}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              className="neo-card group hover:-translate-y-1"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                <Icon size={22} />
              </div>
              <h3 className="mt-5 text-lg font-bold">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-ink/60 dark:text-dark-ink/60">{desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-ink/5 dark:border-white/5 px-6 py-10">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <BrainCircuit size={18} className="text-primary" />
            AnswerEval AI
          </div>
          <p className="text-xs text-ink/50 dark:text-dark-ink/50">
            © {new Date().getFullYear()} AnswerEval AI. Built for academic institutions.
          </p>
        </div>
      </footer>
    </div>
  );
}
