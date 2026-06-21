
import { useState } from "react";
import { Lock, User } from "lucide-react";

const USERNAME = "admin";
const PASSWORD = "esibot2026";

export default function AuthGate({ children }) {
  const [isLoggedIn, setIsLoggedIn] = useState(
    localStorage.getItem("esibot_auth") === "true"
  );
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleLogin = () => {
    if (username === USERNAME && password === PASSWORD) {
      localStorage.setItem("esibot_auth", "true");
      setIsLoggedIn(true);
      setError("");
    } else {
      setError("Invalid username or password");
    }
  };

  if (isLoggedIn) {
    return children;
  }

  return (
    <div className="min-h-screen bg-[#121212] flex items-center justify-center text-white">
      <div className="w-[360px] bg-[#1f1f1f] border border-[#333] rounded-[18px] p-[28px] shadow-[0_10px_40px_rgba(0,0,0,0.5)]">
        <div className="flex flex-col items-center mb-6">
          <div className="w-[56px] h-[56px] rounded-[16px] bg-[#10243a] text-[#148bff] grid place-items-center mb-4">
            <Lock size={26} />
          </div>

          <h1 className="text-[24px] font-extrabold">EsiBot Login</h1>
          <p className="text-[12px] text-[#888] mt-1">
            Secure dashboard access
          </p>
        </div>

        <div className="flex flex-col gap-4">
          <div>
            <label className="text-[11px] text-[#aaa] font-bold">
              Username
            </label>

            <div className="mt-1 flex items-center gap-2 bg-[#111] border border-[#333] rounded-[10px] px-3">
              <User size={15} className="text-[#777]" />
              <input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full h-[42px] bg-transparent outline-none text-white text-[13px]"
                placeholder="admin"
              />
            </div>
          </div>

          <div>
            <label className="text-[11px] text-[#aaa] font-bold">
              Password
            </label>

            <div className="mt-1 flex items-center gap-2 bg-[#111] border border-[#333] rounded-[10px] px-3">
              <Lock size={15} className="text-[#777]" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleLogin()}
                className="w-full h-[42px] bg-transparent outline-none text-white text-[13px]"
                placeholder="Password"
              />
            </div>
          </div>

          {error && (
            <p className="text-[12px] text-[#ff5050] font-bold">{error}</p>
          )}

          <button
            onClick={handleLogin}
            className="h-[44px] rounded-[12px] bg-[#148bff] text-black font-extrabold text-[13px] hover:bg-[#0f7ee8] active:scale-[0.97] transition"
          >
            LOGIN
          </button>
        </div>
      </div>
    </div>
  );
}