import { useEffect, useMemo, useRef, useState } from "react";
import {
  BookOpen,
  Download,
  FileUp,
  LoaderCircle,
  LogOut,
  Mail,
  MailCheck,
  Sparkles,
} from "lucide-react";
import {
  clearStoredToken,
  getProfile,
  getStoredToken,
  login,
  requestPasswordReset,
  resetPassword,
  signup,
  storeToken,
  uploadBook
} from "./api";

const views = {
  home: "home",
  about: "about"
};

function formatDate(value) {
  if (!value) return "Unavailable";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function getAuthErrorMessage(error, mode) {
  const msg = (error.message || "").toLowerCase();
  if (mode === "login") {
    if (msg.includes("invalid") || msg.includes("email") || msg.includes("password")) {
      return error.message;
    }
    return "Something went wrong. Please try again later.";
  }
  if (msg.includes("already") || msg.includes("registered") || msg.includes("exists")) {
    return error.message;
  }
  return "Something went wrong. Please try again later.";
}

function Footer() {
  return (
    <footer className="app-footer">
      <p className="footer-brand">Book Condenser</p>
      <p className="footer-copy">© 2026 Book Condenser. Precision clarity.</p>
    </footer>
  );
}

function ProfileCard({ onClose, onLogout, profile }) {
  const cardRef = useRef(null);
  const initial = (profile?.full_name || profile?.email || "U")[0].toUpperCase();

  useEffect(() => {
    function handlePointerDown(e) {
      if (cardRef.current && !cardRef.current.contains(e.target)) {
        onClose();
      }
    }
    document.addEventListener("pointerdown", handlePointerDown);
    return () => document.removeEventListener("pointerdown", handlePointerDown);
  }, [onClose]);

  return (
    <div className="profile-card" ref={cardRef}>
      <div className="profile-card-top">
        <div className="profile-card-avatar-lg">{initial}</div>
        <div className="profile-card-info">
          <p className="profile-card-name">{profile?.full_name || "User"}</p>
          <p className="profile-card-email">{profile?.email}</p>
          {profile?.created_at && (
            <p className="profile-card-joined">Joined {formatDate(profile.created_at)}</p>
          )}
        </div>
      </div>
      <div className="profile-card-divider" />
      <button className="profile-card-logout" onClick={onLogout} type="button">
        <LogOut size={15} aria-hidden="true" />
        Log out
      </button>
    </div>
  );
}

function ForgotPasswordPage({ onBack }) {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState({ type: "idle", message: "" });

  const isBusy = status.type === "loading";
  const isDone = status.type === "success";

  async function handleSubmit(e) {
    e.preventDefault();
    setStatus({ type: "loading", message: "" });
    try {
      await requestPasswordReset(email);
      setStatus({ type: "success", message: "" });
    } catch (err) {
      setStatus({ type: "error", message: err.message });
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-topbar">
        <div className="auth-logo">
          <BookOpen size={20} aria-hidden="true" />
          <span>Book Condenser</span>
        </div>
      </div>

      <main className="auth-center">
        {isDone ? (
          <>
            <div className="auth-heading">
              <h1>Check your inbox</h1>
              <p>We sent a password reset link to <strong>{email}</strong>.</p>
            </div>
            <section className="auth-card">
              <p style={{ color: "#6b6b8a", fontSize: "0.9rem", margin: "0 0 20px", lineHeight: 1.6 }}>
                Click the link in the email to set a new password. If you don&apos;t see it,
                check your spam folder.
              </p>
              <button className="primary-button" onClick={onBack} type="button">
                Back to log in
              </button>
            </section>
          </>
        ) : (
          <>
            <div className="auth-heading">
              <h1>Reset your password</h1>
              <p>Enter your email and we&apos;ll send you a reset link.</p>
            </div>

            <section className="auth-card" aria-label="Forgot password">
              <form className="auth-form" onSubmit={handleSubmit}>
                <label>
                  <span>Email</span>
                  <input
                    autoComplete="email"
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@example.com"
                    required
                    type="email"
                    value={email}
                  />
                </label>

                {status.type === "error" && (
                  <p className="form-message error" role="alert">{status.message}</p>
                )}

                <button className="primary-button" disabled={isBusy} type="submit">
                  {isBusy ? <LoaderCircle className="spin" size={18} /> : null}
                  Send reset link
                </button>
              </form>
            </section>

            <p className="auth-switch">
              <button className="link-button" onClick={onBack} type="button">
                ← Back to log in
              </button>
            </p>
          </>
        )}
      </main>
    </div>
  );
}

function ResetPasswordPage({ accessToken, onDone, refreshToken }) {
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [status, setStatus] = useState({ type: "idle", message: "" });

  const isBusy = status.type === "loading";
  const isDone = status.type === "success";

  async function handleSubmit(e) {
    e.preventDefault();
    if (password !== confirm) {
      setStatus({ type: "error", message: "Passwords do not match." });
      return;
    }
    setStatus({ type: "loading", message: "" });
    try {
      await resetPassword({ accessToken, refreshToken, newPassword: password });
      setStatus({ type: "success", message: "" });
    } catch (err) {
      setStatus({ type: "error", message: err.message });
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-topbar">
        <div className="auth-logo">
          <BookOpen size={20} aria-hidden="true" />
          <span>Book Condenser</span>
        </div>
      </div>

      <main className="auth-center">
        {isDone ? (
          <>
            <div className="auth-heading">
              <h1>Password updated</h1>
              <p>You can now log in with your new password.</p>
            </div>
            <section className="auth-card">
              <button className="primary-button" onClick={onDone} type="button">
                Go to log in
              </button>
            </section>
          </>
        ) : (
          <>
            <div className="auth-heading">
              <h1>Choose a new password</h1>
              <p>Make it strong and memorable.</p>
            </div>

            <section className="auth-card" aria-label="Reset password">
              <form className="auth-form" onSubmit={handleSubmit}>
                <label>
                  <span>New password</span>
                  <input
                    autoComplete="new-password"
                    minLength={6}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    type="password"
                    value={password}
                  />
                </label>

                <label>
                  <span>Confirm password</span>
                  <input
                    autoComplete="new-password"
                    minLength={6}
                    onChange={(e) => setConfirm(e.target.value)}
                    required
                    type="password"
                    value={confirm}
                  />
                </label>

                {status.type === "error" && (
                  <p className="form-message error" role="alert">{status.message}</p>
                )}

                <button className="primary-button" disabled={isBusy} type="submit">
                  {isBusy ? <LoaderCircle className="spin" size={18} /> : null}
                  Set new password
                </button>
              </form>
            </section>
          </>
        )}
      </main>
    </div>
  );
}

function AuthPage({ onAuthenticated, onForgotPassword, onShowAbout }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ fullName: "", email: "", password: "" });
  const [status, setStatus] = useState({ type: "idle", message: "" });
  const [verification, setVerification] = useState(null);

  const isSignup = mode === "signup";
  const isBusy = status.type === "loading";

  function showLogin() {
    setMode("login");
    setStatus({ type: "idle", message: "" });
    setVerification(null);
  }

  function showSignup() {
    setMode("signup");
    setStatus({ type: "idle", message: "" });
    setVerification(null);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setStatus({ type: "loading", message: isSignup ? "Creating account" : "Signing in" });

    try {
      if (isSignup) {
        const result = await signup(form);
        setVerification({
          email: form.email,
          message: result.message || "Account created! Check your inbox to verify your email before logging in."
        });
        setStatus({ type: "success", message: "" });
        return;
      }

      const session = await login(form);
      storeToken(session.access_token);
      const profile = await getProfile(session.access_token);
      onAuthenticated(session.access_token, profile);
    } catch (error) {
      setStatus({ type: "error", message: getAuthErrorMessage(error, mode) });
    }
  }

  if (verification) {
    return (
      <div className="auth-page">
        <div className="auth-topbar">
          <div className="auth-logo">
            <BookOpen size={20} aria-hidden="true" />
            <span>Book Condenser</span>
          </div>
          <button className="auth-topbar-about" onClick={onShowAbout} type="button">
            About
          </button>
        </div>
        <main className="auth-center">
          <section className="auth-card verification-panel" aria-label="Verify email">
            <div className="verification-icon">
              <MailCheck size={28} aria-hidden="true" />
            </div>
            <h2>Check your email</h2>
            <p>{verification.message}</p>
            <p>
              We sent a verification link to <strong>{verification.email}</strong>.
              Click the link in that email, then come back here to log in.
            </p>
            <button className="primary-button" onClick={showLogin} type="button">
              <Mail size={18} />
              Go to log in
            </button>
          </section>
        </main>
      </div>
    );
  }

  return (
    <div className="auth-page">
      <div className="auth-topbar">
        <div className="auth-logo">
          <BookOpen size={20} aria-hidden="true" />
          <span>Book Condenser</span>
        </div>
        <button className="auth-topbar-about" onClick={onShowAbout} type="button">
          About
        </button>
      </div>

      <main className="auth-center">
        <div className="auth-heading">
          <h1>{isSignup ? "Create an account" : "Welcome Back"}</h1>
          <p>All the insight. None of the filler.</p>
        </div>

        <section className="auth-card" aria-label={isSignup ? "Sign up" : "Log in"}>
          <form className="auth-form" onSubmit={handleSubmit}>
            {isSignup && (
              <label>
                <span>Full name</span>
                <input
                  autoComplete="name"
                  onChange={(event) => setForm({ ...form, fullName: event.target.value })}
                  placeholder="Jane Smith"
                  required
                  type="text"
                  value={form.fullName}
                />
              </label>
            )}

            <label>
              <span>Email</span>
              <input
                autoComplete="email"
                onChange={(event) => setForm({ ...form, email: event.target.value })}
                placeholder="name@example.com"
                required
                type="email"
                value={form.email}
              />
            </label>

            <div className="password-field">
              <label htmlFor="auth-password">
                <span>Password</span>
                {!isSignup && (
                  <button className="link-button" onClick={onForgotPassword} type="button">
                    Forgot password?
                  </button>
                )}
              </label>
              <input
                autoComplete={isSignup ? "new-password" : "current-password"}
                id="auth-password"
                minLength={6}
                onChange={(event) => setForm({ ...form, password: event.target.value })}
                required
                type="password"
                value={form.password}
              />
            </div>

            {status.message && (
              <p className={`form-message ${status.type}`} role="status">
                {status.message}
              </p>
            )}

            <button className="primary-button" disabled={isBusy} type="submit">
              {isBusy ? <LoaderCircle className="spin" size={18} /> : null}
              {isSignup ? "Create account" : "Log in"}
            </button>
          </form>
        </section>

        <p className="auth-switch">
          {isSignup ? (
            <>Already have an account?{" "}
              <button className="link-button" onClick={showLogin} type="button">Log in</button>
            </>
          ) : (
            <>Don&apos;t have an account?{" "}
              <button className="link-button" onClick={showSignup} type="button">Sign up now</button>
            </>
          )}
        </p>
      </main>
    </div>
  );
}

function TopNav({ activeView, onLogout, onNavigate, profile }) {
  const [showProfile, setShowProfile] = useState(false);
  const initial = (profile?.full_name || profile?.email || "U")[0].toUpperCase();

  return (
    <header className="top-nav">
      <button
        aria-label="Book Condenser home"
        className="nav-brand"
        onClick={() => onNavigate(views.home)}
        type="button"
      >
        <BookOpen size={20} aria-hidden="true" />
        <span>Book Condenser</span>
      </button>

      <nav aria-label="Main navigation">
        <button
          className={activeView === views.about ? "active" : ""}
          onClick={() => onNavigate(views.about)}
          type="button"
        >
          About
        </button>
      </nav>

      <div className="nav-avatar-wrap">
        <button
          aria-label="Account menu"
          className="nav-avatar"
          onClick={() => setShowProfile((v) => !v)}
          type="button"
        >
          {initial}
        </button>
        {showProfile && (
          <ProfileCard
            onClose={() => setShowProfile(false)}
            onLogout={onLogout}
            profile={profile}
          />
        )}
      </div>
    </header>
  );
}

function HomePage({ onSelectFile, onUpload, selectedFile, uploadState }) {
  const inputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);

  const isUploading = uploadState.type === "uploading";

  const fileMeta = useMemo(() => {
    if (!selectedFile) return null;
    return `${(selectedFile.size / 1024 / 1024).toFixed(2)} MB`;
  }, [selectedFile]);

  useEffect(() => {
    if (!selectedFile && inputRef.current) {
      inputRef.current.value = "";
    }
  }, [selectedFile]);

  function handleDrop(e) {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) onSelectFile(file);
  }

  function handleDragOver(e) {
    e.preventDefault();
    setIsDragging(true);
  }

  function handleDragLeave(e) {
    if (!e.currentTarget.contains(e.relatedTarget)) {
      setIsDragging(false);
    }
  }

  return (
    <main className="upload-workspace">
      <div className="upload-page-header">
        <div className="upload-page-icon">
          <Sparkles size={16} aria-hidden="true" />
        </div>
        <h1>Upload your book</h1>
        <p>Remove all the fluff and enjoy.</p>
      </div>

      <div
        className={`drop-zone${isDragging ? " dragging" : ""}`}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        <input
          accept=".pdf,.epub,.mobi,.docx,.txt"
          disabled={isUploading}
          onChange={(e) => onSelectFile(e.target.files?.[0] || null)}
          ref={inputRef}
          style={{ display: "none" }}
          type="file"
        />

        <div className="drop-zone-icon">
          <FileUp size={22} aria-hidden="true" />
        </div>

        {selectedFile ? (
          <>
            <p className="drop-zone-title">{selectedFile.name}</p>
            <p className="drop-zone-subtitle">{fileMeta} selected</p>
          </>
        ) : (
          <>
            <p className="drop-zone-title">Drag &amp; drop your file here</p>
            <p className="drop-zone-subtitle">Supports PDF, EPUB, MOBI and TXT (Max 50MB)</p>
          </>
        )}

        <div className="drop-zone-actions">
          <button
            className="primary-button"
            disabled={isUploading}
            onClick={() => inputRef.current?.click()}
            type="button"
          >
            {isUploading
              ? <><LoaderCircle className="spin" size={18} /> Condensing…</>
              : selectedFile
              ? "Change file"
              : <><span aria-hidden="true">+</span> Browse Files</>
            }
          </button>
          {selectedFile && !isUploading && (
            <button
              className="primary-button condense-btn"
              onClick={onUpload}
              type="button"
            >
              <Sparkles size={16} aria-hidden="true" />
              Condense book
            </button>
          )}
        </div>
      </div>

      {uploadState.type === "uploading" && (
        <div className="upload-status uploading-notice" role="status">
          <span>Condensation can take up to 15 minutes — please keep this tab open.</span>
        </div>
      )}

      {uploadState.message && uploadState.type !== "uploading" && (
        <div className={`upload-status ${uploadState.type}`} role="status">
          <span>{uploadState.message}</span>
          {uploadState.downloadUrl && (
            <a href={uploadState.downloadUrl} rel="noreferrer" target="_blank">
              <Download size={18} aria-hidden="true" />
              Download PDF
            </a>
          )}
        </div>
      )}
    </main>
  );
}

function AboutPage({ onBack }) {
  return (
    <main className="workspace about-page">
      {onBack && (
        <button className="about-back-btn" onClick={onBack} type="button">
          ← Back to log in
        </button>
      )}
      <section aria-label="About Book Condenser">
        <p className="eyebrow">About</p>
        <h1>Built by a reader, for readers.</h1>
        <p>
          I love non-fiction. I love the way a great book can reshape my
          perspective, provide new frameworks for decision-making, challenge my
          assumptions and even change my life. Books are incredibly powerful
          tools.
        </p>
        <p>
          But lately, I&apos;ve found myself frustrated. I love reading, but I also
          value my time. There are many times where I find authors droning on
          and on about things irrelevant to the main arguments they are trying
          to make. To such an extent that, in some cases, it even muddies or
          distracts from what they are trying to say. Not only does it create an
          awful reading experience and make it hard for readers to reason about
          the text, it is also a massive waste of time.
        </p>
        <p>
          Book summaries are obviously not an option. A summary has much of the
          essence of the book, its feel, context and process stripped away. If
          you love reading they just won&apos;t do. There is a joy in following the
          author&apos;s thought process, perceiving their voice, the unique way they
          formulate their opinions and witnessing their reasoning in real time.
          Summaries can&apos;t do that. A summary tells you what happened; it
          doesn&apos;t let you <em>experience</em> the logic. It lacks the
          &quot;feel&quot; that makes a book worth reading in the first place.
        </p>
        <p>
          As I work with AI every day, building all manner of AI-powered tools in the
          publishing industry, I realized there was a middle ground:{" "}
          <strong>The Condensed Book</strong> delivered with the author&apos;s
          original voice intact.
        </p>
        <p>
          So, I built the Book Condenser.
        </p>
        <p>
          This isn&apos;t an AI tool designed to replace reading; some books are
          worth wading through the unnecessary stuff, but some books aren&apos;t
          worth it.
        </p>
      </section>
    </main>
  );
}

export default function App() {
  const [token, setToken] = useState(getStoredToken);
  const [profile, setProfile] = useState(null);
  const [view, setView] = useState(views.home);
  const [bootState, setBootState] = useState("loading");
  const [unauthView, setUnauthView] = useState("auth");
  const [resetTokens, setResetTokens] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadState, setUploadState] = useState({
    type: "idle",
    message: "",
    downloadUrl: ""
  });
  const dismissTimerRef = useRef(null);

  // Detect Supabase password-recovery tokens in the URL hash on first load.
  useEffect(() => {
    const hash = window.location.hash.slice(1);
    if (!hash) return;
    const params = new URLSearchParams(hash);
    if (params.get("type") === "recovery") {
      const accessToken = params.get("access_token");
      const refreshToken = params.get("refresh_token");
      if (accessToken && refreshToken) {
        setResetTokens({ accessToken, refreshToken });
        setUnauthView("reset-password");
        // Clean the tokens out of the URL bar.
        window.history.replaceState(null, "", window.location.pathname);
      }
    }
  }, []);

  useEffect(() => {
    let isMounted = true;

    async function loadProfile() {
      if (!token) {
        setBootState("ready");
        return;
      }

      try {
        const currentProfile = await getProfile(token);
        if (isMounted) {
          setProfile(currentProfile);
          setBootState("ready");
        }
      } catch {
        clearStoredToken();
        if (isMounted) {
          setToken(null);
          setProfile(null);
          setBootState("ready");
        }
      }
    }

    loadProfile();
    return () => {
      isMounted = false;
    };
  }, [token]);

  function handleAuthenticated(nextToken, nextProfile) {
    setToken(nextToken);
    setProfile(nextProfile);
    setView(views.home);
    setUnauthView("auth");
  }

  function handleLogout() {
    clearStoredToken();
    clearTimeout(dismissTimerRef.current);
    setToken(null);
    setProfile(null);
    setView(views.home);
    setSelectedFile(null);
    setUploadState({ type: "idle", message: "", downloadUrl: "" });
  }

  async function handleUpload() {
    if (!selectedFile || uploadState.type === "uploading") return;

    const TIMEOUT_MS = 15 * 60 * 1000;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

    setUploadState({ type: "uploading", message: "Condensing your book…", downloadUrl: "" });

    const DISMISS_MS = 30 * 60 * 1000;

    function scheduleDismiss() {
      clearTimeout(dismissTimerRef.current);
      dismissTimerRef.current = setTimeout(() => {
        setUploadState({ type: "idle", message: "", downloadUrl: "" });
      }, DISMISS_MS);
    }

    try {
      const result = await uploadBook({ file: selectedFile, token, signal: controller.signal });
      clearTimeout(timeoutId);
      setUploadState({
        type: "success",
        message: result.message || "Your book is ready",
        downloadUrl: result.download_url
      });
      setSelectedFile(null);
      scheduleDismiss();
    } catch (error) {
      clearTimeout(timeoutId);
      const isTimeout = error.name === "AbortError";
      setUploadState({
        type: "error",
        message: isTimeout
          ? "Condensation timed out after 15 minutes. Please try again or contact support if the problem persists."
          : error.message,
        downloadUrl: ""
      });
      scheduleDismiss();
    }
  }

  if (bootState === "loading") {
    return (
      <main className="loading-screen" aria-label="Loading">
        <LoaderCircle className="spin" size={28} />
      </main>
    );
  }

  if (!token) {
    if (unauthView === "about") {
      return (
        <div className="app-layout">
          <header className="top-nav">
            <button
              aria-label="Book Condenser home"
              className="nav-brand"
              onClick={() => setUnauthView("auth")}
              type="button"
            >
              <BookOpen size={20} aria-hidden="true" />
              <span>Book Condenser</span>
            </button>
          </header>
          <AboutPage onBack={() => setUnauthView("auth")} />
          <Footer />
        </div>
      );
    }

    if (unauthView === "forgot-password") {
      return <ForgotPasswordPage onBack={() => setUnauthView("auth")} />;
    }

    if (unauthView === "reset-password" && resetTokens) {
      return (
        <ResetPasswordPage
          accessToken={resetTokens.accessToken}
          onDone={() => {
            setResetTokens(null);
            setUnauthView("auth");
          }}
          refreshToken={resetTokens.refreshToken}
        />
      );
    }

    return (
      <AuthPage
        onAuthenticated={handleAuthenticated}
        onForgotPassword={() => setUnauthView("forgot-password")}
        onShowAbout={() => setUnauthView("about")}
      />
    );
  }

  return (
    <div className="app-layout">
      <TopNav
        activeView={view}
        onLogout={handleLogout}
        onNavigate={setView}
        profile={profile}
      />
      {view === views.home && (
        <HomePage
          onSelectFile={setSelectedFile}
          onUpload={handleUpload}
          selectedFile={selectedFile}
          uploadState={uploadState}
        />
      )}
      {view === views.about && <AboutPage />}
      <Footer />
    </div>
  );
}
