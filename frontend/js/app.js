/**
 * ResearchPilot — Agentic AI Frontend Application
 * Handles API communication, drag-and-drop ingestion, active document state, and research queries.
 */

// ============================================================================
// Configuration & Dynamic Base URL Detection
// ============================================================================

function getApiBaseUrl() {
  if (window.location.protocol.startsWith("http")) {
    // If served directly from FastAPI backend (port 8000 or standard web port)
    if (window.location.port === "8000" || window.location.port === "") {
      return "";
    }
    // If served via Live Server (5500) or other frontend dev server (3000, 5173)
    // Preserves the hostname so LAN/mobile devices connect to the laptop IP
    return `${window.location.protocol}//${window.location.hostname}:8000`;
  }
  // Fallback for file:// protocol
  return "http://127.0.0.1:8000";
}

let API_BASE_URL = getApiBaseUrl();

// ============================================================================
// DOM Elements
// ============================================================================

// Header & System Status
const backendStatusPill = document.getElementById("backendStatusPill");
const backendPulseDot = document.getElementById("backendPulseDot");
const backendStatusLabel = document.getElementById("backendStatusLabel");

// Document Section: Active Doc vs Upload Dropzone
const activeDocContainer = document.getElementById("activeDocContainer");
const uploadSuccessBanner = document.getElementById("uploadSuccessBanner");
const uploadSuccessDetail = document.getElementById("uploadSuccessDetail");
const activeDocName = document.getElementById("activeDocName");
const statPages = document.getElementById("statPages");
const statChunks = document.getElementById("statChunks");
const uploadAgainBtn = document.getElementById("uploadAgainBtn");

const uploadDropzoneContainer = document.getElementById("uploadDropzoneContainer");
const dropzone = document.getElementById("dropzone");
const pdfInput = document.getElementById("pdfInput");
const selectedFileBar = document.getElementById("selectedFileBar");
const selectedFileName = document.getElementById("selectedFileName");
const selectedFileSize = document.getElementById("selectedFileSize");
const clearFileBtn = document.getElementById("clearFileBtn");
const uploadButton = document.getElementById("uploadButton");
const uploadCancelRow = document.getElementById("uploadCancelRow");
const cancelUploadModeBtn = document.getElementById("cancelUploadModeBtn");
const uploadStatus = document.getElementById("uploadStatus");

// Query & Research Section
const questionInput = document.getElementById("questionInput");
const askButton = document.getElementById("askButton");
const answer = document.getElementById("answer");
const promptChips = document.querySelectorAll(".prompt-chip");

// Current state
let currentActiveDocument = null;
let selectedFile = null;

// ============================================================================
// Markdown Renderer
// ============================================================================

function renderMarkdown(text) {
  if (!text) return "";
  if (typeof marked !== "undefined" && typeof marked.parse === "function") {
    try {
      return marked.parse(text);
    } catch (e) {
      console.warn("Markdown parsing failed, using fallback:", e);
    }
  }
  return text
    .split("\n\n")
    .map(p => `<p>${p.replace(/\n/g, "<br>")}</p>`)
    .join("");
}

// Format bytes
function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

// Copy to Clipboard Utility
async function copyToClipboard(text, btnElement, successLabel = "Copied!") {
  try {
    await navigator.clipboard.writeText(text);
    const origHtml = btnElement.innerHTML;
    btnElement.innerHTML = `<span>✓</span> <span>${successLabel}</span>`;
    setTimeout(() => {
      btnElement.innerHTML = origHtml;
    }, 2000);
  } catch (err) {
    console.error("Failed to copy:", err);
  }
}

// ============================================================================
// Backend Health & Document Status Check
// ============================================================================

async function checkBackendConnectivity() {
  try {
    const healthUrl = `${API_BASE_URL}/health`;
    const res = await fetch(healthUrl, {
  method: "GET",
  credentials: "include"
});
    if (res.ok) {
      setSystemStatus(true, "Agent Online • Backend Connected");
      await checkExistingDocumentStatus();
    } else {
      setSystemStatus(false, "Backend Responded with Error");
    }
  } catch (err) {
    // If default URL failed and we're on file:// or localhost, try fallback to 127.0.0.1 or localhost
    if (API_BASE_URL.includes("127.0.0.1")) {
      const fallbackUrl = API_BASE_URL.replace("127.0.0.1", "localhost");
      try {
        const res = await fetch(`${fallbackUrl}/health`, {
  method: "GET",
  credentials: "include"
});
        if (res.ok) {
          API_BASE_URL = fallbackUrl;
          setSystemStatus(true, "Agent Online • Backend Connected");
          await checkExistingDocumentStatus();
          return;
        }
      } catch (e) {}
    }
    setSystemStatus(false, "Backend Offline • Port 8000");
  }
}

function setSystemStatus(isOnline, label) {
  if (isOnline) {
    backendStatusPill.className = "status-pill status-online";
    backendStatusLabel.textContent = label;
  } else {
    backendStatusPill.className = "status-pill status-offline";
    backendStatusLabel.textContent = label;
  }
}

// Query backend to see if a document is already indexed
async function checkExistingDocumentStatus() {
  try {
    const res = await fetch(`${API_BASE_URL}/documents/status`, {
  method: "GET",
  credentials: "include"
});
    if (res.ok) {
      const data = await res.json();
      if (data.active_document && data.total_chunks > 0) {
        showActiveDocumentView({
          filename: data.active_document,
          total_pages: null, // unknown from status
          total_chunks: data.total_chunks,
          isInitialLoad: true
        });
      }
    }
  } catch (e) {
    console.warn("Could not check existing document status:", e);
  }
}

// ============================================================================
// Document Management & State Transitions (Requirement 2)
// ============================================================================

/**
 * Switch to Active Document View
 * Requirement 2: "show document uploaded succesfully and show the document name until clicked on upload document again"
 */
function showActiveDocumentView({ filename, total_pages, total_chunks, isInitialLoad = false }) {
  currentActiveDocument = {
    filename,
    total_pages,
    total_chunks
  };

  // Populate Active Document Details
  activeDocName.textContent = filename;
  activeDocName.title = filename;

  if (total_pages) {
    statPages.textContent = `${total_pages} Pages`;
    statPages.style.display = "inline-block";
  } else {
    statPages.style.display = "none";
  }

  statChunks.textContent = `${total_chunks} Chunks`;

  if (isInitialLoad) {
    uploadSuccessDetail.textContent = "Previous document index loaded from vector database.";
  } else {
    uploadSuccessDetail.textContent = `${total_pages || "All"} pages and ${total_chunks} vector chunks indexed and ready for inquiries.`;
  }

  // Display success banner and active doc card
  uploadSuccessBanner.style.display = "block";
  activeDocContainer.style.display = "flex";

  // Hide upload dropzone
  uploadDropzoneContainer.style.display = "none";

  // Reset any in-progress upload state
  resetUploadInputState();
}

/**
 * Switch back to Upload Mode
 * Triggered when user clicks "Upload Document" (uploadAgainBtn)
 */
function showUploadMode() {
  activeDocContainer.style.display = "none";
  uploadDropzoneContainer.style.display = "flex";

  // If there was an active document previously, show cancel button to return
  if (currentActiveDocument) {
    uploadCancelRow.style.display = "flex";
  } else {
    uploadCancelRow.style.display = "none";
  }

  // Reset file selection
  resetUploadInputState();
  hideUploadStatus();
}

function resetUploadInputState() {
  selectedFile = null;
  pdfInput.value = "";
  selectedFileBar.style.display = "none";
  dropzone.style.display = "block";
  uploadButton.disabled = false;
}

function hideUploadStatus() {
  uploadStatus.style.display = "none";
  uploadStatus.innerHTML = "";
  uploadStatus.className = "status-container";
}

// Event: User clicks "Upload Document" again
uploadAgainBtn.addEventListener("click", () => {
  showUploadMode();
});

// Event: User cancels upload mode and keeps previous active document
cancelUploadModeBtn.addEventListener("click", () => {
  if (currentActiveDocument) {
    activeDocContainer.style.display = "flex";
    uploadDropzoneContainer.style.display = "none";
  }
});

// ============================================================================
// Drag and Drop & File Picker Handling
// ============================================================================

dropzone.addEventListener("click", () => {
  pdfInput.click();
});

// Prevent defaults on drag events
["dragenter", "dragover", "dragleave", "drop"].forEach(eventName => {
  dropzone.addEventListener(eventName, e => {
    e.preventDefault();
    e.stopPropagation();
  });
  document.body.addEventListener(eventName, e => {
    e.preventDefault();
    e.stopPropagation();
  });
});

["dragenter", "dragover"].forEach(eventName => {
  dropzone.addEventListener(eventName, () => {
    dropzone.classList.add("dragover");
  });
});

["dragleave", "drop"].forEach(eventName => {
  dropzone.addEventListener(eventName, () => {
    dropzone.classList.remove("dragover");
  });
});

dropzone.addEventListener("drop", e => {
  const dt = e.dataTransfer;
  const files = dt.files;
  if (files && files.length > 0) {
    handleFileSelected(files[0]);
  }
});

pdfInput.addEventListener("change", e => {
  if (e.target.files && e.target.files.length > 0) {
    handleFileSelected(e.target.files[0]);
  }
});

function handleFileSelected(file) {
  hideUploadStatus();

  const isPdf =
    file.type === "application/pdf" ||
    file.name.toLowerCase().endsWith(".pdf");

  if (!isPdf) {
    showStatusMessage(
      "Only PDF files are supported. Please select a valid .pdf document.",
      "status-warning"
    );
    return;
  }

  selectedFile = file;
  selectedFileName.textContent = file.name;
  selectedFileSize.textContent = formatFileSize(file.size);

  selectedFileBar.style.display = "flex";
  dropzone.style.display = "none";
}

clearFileBtn.addEventListener("click", () => {
  resetUploadInputState();
  hideUploadStatus();
});

function showStatusMessage(html, className) {
  uploadStatus.className = `status-container ${className}`;
  uploadStatus.innerHTML = html;
  uploadStatus.style.display = "block";
}

// ============================================================================
// Document Upload & Ingestion Execution (Requirement 1 & 2)
// ============================================================================

uploadButton.addEventListener("click", async () => {
  if (!selectedFile) {
    showStatusMessage("Please select a PDF file first.", "status-warning");
    return;
  }

  uploadButton.disabled = true;
  clearFileBtn.disabled = true;

  showStatusMessage(`
    <div class="status-spinner"></div>
    <div>
      <strong>Ingesting Document...</strong>
      <p style="font-size: 12px; margin-top: 2px; color: var(--text-secondary);">
        Extracting PDF text, chunking, and generating vector embeddings with SentenceTransformers...
      </p>
    </div>
  `, "status-loading");

  const formData = new FormData();
  formData.append("file", selectedFile);

  try {
    const uploadEndpoint = `${API_BASE_URL}/documents/upload`;
    const response = await fetch(uploadEndpoint, {
  method: "POST",
  credentials: "include",
  body: formData,
});
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || `Server returned status ${response.status}`);
    }

    // Success! Show active document view with persistent document name (Requirement 2)
    showActiveDocumentView({
      filename: data.filename || selectedFile.name,
      total_pages: data.total_pages,
      total_chunks: data.total_chunks,
      isInitialLoad: false
    });

    // Update system status
    setSystemStatus(true, "Agent Online • Document Indexed");

  } catch (error) {
    console.error("Upload error:", error);

    // Requirement 1: Clear, diagnostic error handling instead of raw "failed to fetch"
    if (error.message.includes("fetch") || error.name === "TypeError") {
      showStatusMessage(`
        <div class="diagnostic-error-card" style="margin-top: 10px;">
          <div class="diagnostic-error-title">
            <span>⚠️</span> Could Not Reach ResearchPilot Backend
          </div>
          <p style="font-size: 13px; color: var(--text-primary); margin-bottom: 8px;">
            Connection to <code>${API_BASE_URL || window.location.origin}</code> failed. Please verify that the FastAPI backend server is running.
          </p>
          <div class="diagnostic-command-box">
            <span>uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000</span>
          </div>
        </div>
      `, "status-error");
      setSystemStatus(false, "Backend Offline");
    } else {
      showStatusMessage(`
        <strong>Upload Failed:</strong> ${error.message}
      `, "status-error");
    }
  } finally {
    uploadButton.disabled = false;
    clearFileBtn.disabled = false;
  }
});

// ============================================================================
// Research & Query Execution
// ============================================================================

// Prompt Chips functionality
promptChips.forEach(chip => {
  chip.addEventListener("click", () => {
    const promptText = chip.getAttribute("data-prompt");
    if (promptText) {
      questionInput.value = promptText;
      questionInput.focus();
      // Auto-trigger ask if active document exists
      askButton.click();
    }
  });
});

// Submit on Enter (Shift+Enter for newline)
questionInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    askButton.click();
  }
});

askButton.addEventListener("click", async () => {
  const question = questionInput.value.trim();

  if (!question) {
    answer.innerHTML = `
      <div class="status-container status-warning">
        Please enter a research question grounded in your document.
      </div>
    `;
    questionInput.focus();
    return;
  }

  askButton.disabled = true;
  answer.innerHTML = `
    <div class="agent-thinking-card">
      <div class="thinking-orb">
        <div class="thinking-radar"></div>
      </div>
      <div class="thinking-details">
        <h4>Autonomous Research Engine Inquiring...</h4>
        <p>Scanning vector store & synthesizing multi-agent reasoning evidence...</p>
      </div>
    </div>
  `;

  try {
    const response = await fetch(`${API_BASE_URL}/research/ask`, {
  method: "POST",
  credentials: "include",
  headers: {
    "Content-Type": "application/json",
  },
      body: JSON.stringify({
        question: question,
        top_k: 5,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Agent research endpoint returned an error.");
    }

    renderResearchResults(data);

  } catch (error) {
    console.error("Research error:", error);

    let errorHtml = `
      <div class="diagnostic-error-card">
        <div class="diagnostic-error-title">
          <span>⚠️</span> Inquiry Failed
        </div>
        <p style="font-size: 13.5px; color: var(--text-primary); margin-top: 4px;">
          ${error.message || "Could not complete the research query."}
        </p>
    `;

    if (error.message.includes("fetch") || error.name === "TypeError") {
      errorHtml += `
        <p style="font-size: 12.5px; color: var(--text-secondary); margin-top: 6px;">
          The frontend could not connect to <code>${API_BASE_URL || window.location.origin}</code>. Ensure the backend server is active.
        </p>
        <div class="diagnostic-command-box" style="margin-top: 8px;">
          <span>uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000</span>
        </div>
      `;
    }

    errorHtml += `</div>`;
    answer.innerHTML = errorHtml;
  } finally {
    askButton.disabled = false;
  }
});

// Render Synthesized Agent Answer & Citations
function renderResearchResults(data) {
  let html = `
    <div class="answer-result-card">
      <div class="answer-header-row">
        <div class="answer-title-group">
          <span style="font-size: 18px;">✦</span>
          <h3>Agent Research Synthesis</h3>
          <span class="answer-tag">VERIFIED GROUND TRUTH</span>
        </div>
        <button type="button" class="btn-copy" id="copyAnswerBtn">
          <span>📋</span> <span>Copy Answer</span>
        </button>
      </div>

      <div class="answer-markdown-content" id="answerTextContent">
        ${renderMarkdown(data.answer)}
      </div>
  `;

  if (data.main_source) {
    html += `
      <div class="primary-source-bar">
        <div class="primary-source-left">
          <span>📄 <strong>Primary Document:</strong> ${data.main_source.document_name}</span>
        </div>
        <span class="page-pill">Page ${data.main_source.page_number}</span>
      </div>
    `;
  }

  html += `</div>`; // Close answer-result-card

  // Sources & Evidence Section
  const allSources = [];
  if (data.main_source) {
    allSources.push({ ...data.main_source, isPrimary: true });
  }
  if (data.related_content && data.related_content.length > 0) {
    data.related_content.forEach(rc => {
      allSources.push({ ...rc, isPrimary: false });
    });
  }

  if (allSources.length > 0) {
    html += `
      <div class="sources-section">
        <div class="sources-header">
          <h3>Ground Truth Evidence Citations</h3>
          <span class="sources-count-badge">${allSources.length} Evidence Chunks Found</span>
        </div>
    `;

    allSources.forEach((src, idx) => {
      const isPrimary = src.isPrimary;
      html += `
        <div class="evidence-card ${isPrimary ? "primary-evidence" : ""}">
          <div class="evidence-meta-row">
            <span class="evidence-tag">
              ${isPrimary ? "★ Primary Evidence 1" : `Evidence ${idx + 1}`}
            </span>
            <div style="display: flex; gap: 8px; align-items: center;">
              <span class="evidence-doc-pill">${src.document_name}</span>
              <span class="page-pill">Page ${src.page_number}</span>
            </div>
          </div>
          <div class="evidence-text">
            "${src.text}"
          </div>
        </div>
      `;
    });

    html += `</div>`; // Close sources-section
  }

  answer.innerHTML = html;

  // Setup Copy Answer button
  const copyBtn = document.getElementById("copyAnswerBtn");
  if (copyBtn) {
    copyBtn.addEventListener("click", () => {
      copyToClipboard(data.answer, copyBtn, "Copied!");
    });
  }
}

// ============================================================================
// Theme Management (Parchment Gold & Burgundy Noir)
// ============================================================================

const themeToggleBtn = document.getElementById("themeToggleBtn");
const themeLabel = document.getElementById("themeLabel");
const themeIcon = document.getElementById("themeIcon");

function applyTheme(theme) {
  if (theme === "dark" || theme === "burgundy") {
    document.documentElement.setAttribute("data-theme", "dark");
    if (themeLabel) themeLabel.textContent = "Vintage Gold";
    if (themeIcon) themeIcon.textContent = "☀️";
  } else {
    document.documentElement.removeAttribute("data-theme");
    if (themeLabel) themeLabel.textContent = "Burgundy Noir";
    if (themeIcon) themeIcon.textContent = "🌙";
  }
}

const savedTheme = localStorage.getItem("researchpilot_theme") || "parchment";
applyTheme(savedTheme);

if (themeToggleBtn) {
  themeToggleBtn.addEventListener("click", () => {
    const isDark = document.documentElement.getAttribute("data-theme") === "dark";
    const nextTheme = isDark ? "parchment" : "dark";
    applyTheme(nextTheme);
    localStorage.setItem("researchpilot_theme", nextTheme);
  });
}

// ============================================================================
// App Initialization
// ============================================================================

window.addEventListener("DOMContentLoaded", () => {
  checkBackendConnectivity();
});

// Best-effort cleanup when the browser page is being closed.
window.addEventListener("pagehide", () => {
    const apiBaseUrl = getApiBaseUrl();

    const cleanupUrl = `${apiBaseUrl}/documents/session/cleanup`;

    const blob = new Blob(
        [],
        {
            type: "application/json"
        }
    );

    navigator.sendBeacon(
        cleanupUrl,
        blob
    );
});