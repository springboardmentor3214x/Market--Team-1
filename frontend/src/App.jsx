
import { useState } from "react";
import "./App.css";

function App() {
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
    password: "",
  });
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };
  const handleSubmit = async (e) => {
  e.preventDefault();

  setMessage("");
  setMessageType("");
  setLoading(true);

  try {
    const endpoint = isLogin ? "/api/auth/login" : "/api/auth/register";

    const payload = isLogin
      ? {
          email: formData.email,
          password: formData.password,
        }
      : {
          full_name: formData.full_name,
          email: formData.email,
          password: formData.password,
        };

    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

   const responseText = await response.text();
   let data = {};
   try {
    data = responseText ? JSON.parse(responseText) : {};
  } catch {
    data = { detail: responseText };
  }

    if (!response.ok) {
      throw new Error(data.detail || "Something went wrong.");
    }

    setMessage(
      isLogin
        ? "Login successful! Your account has been verified."
        : "Account created successfully! You can now sign in."
    );

    setMessageType("success");

    if (!isLogin) {
      setFormData({
        full_name: "",
        email: "",
        password: "",
      });
    }
  } catch (error) {
    setMessage(error.message || "Unable to connect to the server.");
    setMessageType("error");
  } finally {
    setLoading(false);
  }
};


 

  const switchMode = (login) => {
    setIsLogin(login);
    setShowPassword(false);
    setFormData({ full_name: "", email: "", password: "" });
    setMessage("");
    setMessageType("");
  };

  return (
    <main className="page-shell">
      <div className="ambient ambient-one"></div>
      <div className="ambient ambient-two"></div>

      <nav className="topbar">
        <a className="logo" href="/">
          <span className="logo-mark">S</span>
          <span>stock<span className="logo-light">scope</span></span>
        </a>
        <div className="topbar-note">
          <span className="status-dot"></span>
          INTELLIGENCE FOR BETTER RESEARCH
        </div>
      </nav>

      <section className="main-layout">
        <div className="intro-panel">
          <div className="intro-content">
            <div className="eyebrow">
              <span className="eyebrow-line"></span>
              THE SMARTER WAY TO RESEARCH
            </div>

            <h1>
              See the market
              <br />
              <span>with clarity.</span>
            </h1>

            <p className="intro-description">
              Bring your stock research, market insights and
              investment analysis together in one intelligent workspace.
            </p>

            <div className="visual-card">
              <div className="visual-card-top">
                <div>
                  <span className="visual-label">RESEARCH WORKSPACE</span>
                  <h3>Think beyond the numbers.</h3>
                </div>
                <span className="visual-icon">↗</span>
              </div>

              <svg
                className="market-visual"
                viewBox="0 0 520 125"
                preserveAspectRatio="none"
                aria-label="Decorative rising market trend"
              >
                <defs>
                  <linearGradient id="chartFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#25D5A0" stopOpacity=".25" />
                    <stop offset="100%" stopColor="#25D5A0" stopOpacity="0" />
                  </linearGradient>
                </defs>
                <path
                  d="M0 100 L55 82 L100 91 L150 55 L200 68 L250 38 L300 55 L350 25 L405 43 L460 12 L520 20 L520 125 L0 125 Z"
                  fill="url(#chartFill)"
                />
                <path
                  d="M0 100 L55 82 L100 91 L150 55 L200 68 L250 38 L300 55 L350 25 L405 43 L460 12 L520 20"
                  fill="none"
                  stroke="#25D5A0"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>

              <div className="visual-card-bottom">
                <span>Research</span>
                <span>Discover</span>
                <span>Understand</span>
              </div>
            </div>
          </div>

          <p className="intro-footer">
            BUILT FOR CURIOUS MINDS AND INFORMED DECISIONS
          </p>
        </div>

        <div className="auth-panel">
          <div className="auth-card">
            <div className="card-heading">
              <div className="card-symbol">✳</div>
              <span className="card-kicker">
                {isLogin ? "WELCOME BACK" : "YOUR JOURNEY STARTS HERE"}
              </span>
              <h2>
                {isLogin ? "Good to see you." : "Create your account."}
              </h2>
              <p>
                {isLogin
                  ? "Sign in to continue to your research workspace."
                  : "Set up your account and start exploring."}
              </p>
            </div>

            <div className="auth-switch">
              <button
                type="button"
                className={isLogin ? "selected" : ""}
                onClick={() => switchMode(true)}
              >
                Sign in
              </button>
              <button
                type="button"
                className={!isLogin ? "selected" : ""}
                onClick={() => switchMode(false)}
              >
                Create account
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              {!isLogin && (
                <div className="field">
                  <label htmlFor="full_name">FULL NAME</label>
                  <input
                    id="full_name"
                    name="full_name"
                    type="text"
                    placeholder="Your full name"
                    value={formData.full_name}
                    onChange={handleChange}
                    minLength={2}
                    maxLength={100}
                    required
                  />
                </div>
              )}

              <div className="field">
                <label htmlFor="email">EMAIL ADDRESS</label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="name@example.com"
                  value={formData.email}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="field">
                <div className="field-heading">
                  <label htmlFor="password">PASSWORD</label>
                  {isLogin && <span>Secure sign in</span>}
                </div>

                <div className="password-input">
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Enter your password"
                    value={formData.password}
                    onChange={handleChange}
                    minLength={isLogin ? undefined : 8}
                    maxLength={128}
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? "HIDE" : "SHOW"}
                  </button>
                </div>
              </div>

              <button className="primary-button" type="submit" disabled={loading}>
                <span>
                  {loading
                  ? "Please wait..."
                  : isLogin
                  ? "Sign in to workspace"
                  : "Create my account"}
                  </span>
               
                <span className="button-arrow">↗</span>
              </button>
            </form>

            <div className="card-bottom">
              {message && (
                <div className={`form-message ${messageType}`}>
                  <span>{messageType === "success" ? "✓" : "!"}</span>
                  {message}
                  </div>
                )}

              <span className="lock-symbol">◇</span>
              Your account information is handled securely.
            </div>
          </div>

          <p className="copyright">
            © 2026 StockScope <span>•</span> Intelligent Stock Research
          </p>
        </div>
      </section>
    </main>
  );
}

export default App;
