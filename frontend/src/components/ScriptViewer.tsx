import { useEffect, useRef, useState } from "react";
import { X, FileText, AlertTriangle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { fetchProtectedFileUrl, revokeObjectUrl } from "../services/files";

/**
 * Full-screen viewer for an uploaded sheet (answer script or question paper).
 * PDFs are rendered page-by-page with pdf.js onto canvases (works in any
 * browser, no plugin needed); images render directly. The file is fetched
 * with the caller's JWT and handed to the DOM as a temporary object URL.
 */

async function renderPdfToCanvases(
  data: ArrayBuffer,
  container: HTMLDivElement,
  onProgress: (done: number, total: number) => void
) {
  const pdfjs = await import("pdfjs-dist");
  // Vite bundles a worker entry; pointing the library at it keeps rendering off the main thread.
  pdfjs.GlobalWorkerOptions.workerSrc = new URL(
    "pdfjs-dist/build/pdf.worker.min.mjs",
    import.meta.url
  ).toString();

  const pdf = await pdfjs.getDocument({ data }).promise;
  container.innerHTML = "";

  for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
    const page = await pdf.getPage(pageNum);
    const viewport = page.getViewport({ scale: 1.6 });
    const canvas = document.createElement("canvas");
    canvas.width = viewport.width;
    canvas.height = viewport.height;
    canvas.className = "mx-auto block max-w-full rounded-xl bg-white shadow-lg";
    const ctx = canvas.getContext("2d")!;
    await page.render({ canvasContext: ctx, viewport }).promise;
    container.appendChild(canvas);
    onProgress(pageNum, pdf.numPages);
  }
}
export default function ScriptViewer({
  open,
  onClose,
  fileId,
  fileType,
  title,
  subtitle,
  fileUrl,
}: {
  open: boolean;
  onClose: () => void;
  fileId: number | null;
  fileType: string | null;
  title: string;
  subtitle?: string;
  /** API path for the file; defaults to the answer-scripts endpoint. */
  fileUrl?: string;
}) {
  const [url, setUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [renderStatus, setRenderStatus] = useState("");
  const pdfContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open || fileId == null) {
      setUrl(null);
      setError(null);
      return;
    }
    let cancelled = false;
    let loadedUrl: string | null = null;

    fetchProtectedFileUrl(fileUrl ?? `/answer-scripts/${fileId}/file`)
      .then(async (objectUrl) => {
        if (cancelled) {
          revokeObjectUrl(objectUrl);
          return;
        }
        loadedUrl = objectUrl;
        setUrl(objectUrl);
        if (fileType !== "jpg" && fileType !== "jpeg" && fileType !== "png") {
          // PDF path: render pages to canvases (iframe PDFs need a browser plugin).
          try {
            const res = await fetch(objectUrl);
            const data = await res.arrayBuffer();
            if (cancelled || !pdfContainerRef.current) return;
            await renderPdfToCanvases(data, pdfContainerRef.current, (done, total) =>
              setRenderStatus(done < total ? `Rendering page ${done} / ${total}…` : "")
            );
          } catch {
            if (!cancelled) setError("Could not render this PDF.");
          }
        }
      })
      .catch(() => {
        if (!cancelled) setError("Could not load the file. It may be missing on the server.");
      });

    return () => {
      cancelled = true;
      if (loadedUrl) revokeObjectUrl(loadedUrl);
    };
  }, [open, fileId, fileUrl]);

  const isImage = fileType === "jpg" || fileType === "jpeg" || fileType === "png";

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex flex-col bg-black/60 backdrop-blur-sm p-4 md:p-8"
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 16 }}
            className="neo-card flex h-full w-full max-w-5xl flex-col overflow-hidden !p-0 mx-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-ink/5 px-5 py-4">
              <div>
                <h3 className="text-base font-bold">{title}</h3>
                {subtitle && <p className="text-xs text-ink/50">{subtitle}</p>}
              </div>
              <button onClick={onClose} className="rounded-xl p-2 hover:bg-black/5">
                <X size={20} />
              </button>
            </div>

            <div className="flex-1 overflow-auto bg-neutral-100 p-4">
              {error && (
                <div className="flex h-full flex-col items-center justify-center gap-2 text-sm text-red-500">
                  <AlertTriangle size={28} />
                  {error}
                </div>
              )}
              {!error && !url && (
                <div className="flex h-full flex-col items-center justify-center gap-2 text-sm text-ink/40">
                  <FileText size={28} className="animate-pulse" />
                  Loading document…
                </div>
              )}
              {!error && renderStatus && (
                <p className="mb-2 text-center text-xs font-semibold text-ink/50">{renderStatus}</p>
              )}
              {!error && url && isImage && (
                <img src={url} alt={title} className="mx-auto max-h-full max-w-full rounded-xl shadow-lg" />
              )}
              {!error && url && !isImage && <div ref={pdfContainerRef} className="space-y-4" />}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
