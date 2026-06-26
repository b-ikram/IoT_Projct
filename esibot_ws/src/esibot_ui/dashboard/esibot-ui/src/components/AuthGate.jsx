import { useEffect, useState } from "react";
import { Lock, Mail, LogOut, ShieldCheck } from "lucide-react";
import { supabase } from "../services/supabaseClient";

function GoogleIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 48 48">
      <path
        fill="#FFC107"
        d="M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.3 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.1 6.1 29.3 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.4-.4-3.5z"
      />
      <path
        fill="#FF3D00"
        d="M6.3 14.7l6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.1 6.1 29.3 4 24 4 16.3 4 9.6 8.3 6.3 14.7z"
      />
      <path
        fill="#4CAF50"
        d="M24 44c5.2 0 10-2 13.5-5.3l-6.2-5.2C29.3 35.1 26.8 36 24 36c-5.3 0-9.7-3.3-11.3-8l-6.5 5C9.5 39.5 16.2 44 24 44z"
      />
      <path
        fill="#1976D2"
        d="M43.6 20.5H42V20H24v8h11.3c-.8 2.3-2.3 4.2-4.1 5.5l6.2 5.2C36.9 39.1 44 34 44 24c0-1.3-.1-2.4-.4-3.5z"
      />
    </svg>
  );
}

export default function AuthGate({ children }) {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authMode, setAuthMode] = useState("signin");
  const [message, setMessage] = useState("");

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setLoading(false);
    });

    const { data: listener } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setSession(session);
        setLoading(false);
      }
    );

    return () => listener.subscription.unsubscribe();
  }, []);

  const signInWithEmail = async () => {
    setMessage("");

    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) setMessage(error.message);
  };

  const signUpWithEmail = async () => {
    setMessage("");

    const { error } = await supabase.auth.signUp({
      email,
      password,
    });

    if (error) {
      setMessage(error.message);
      return;
    }

    setMessage("Account created. You can now log in.");
  };

  const signInWithGoogle = async () => {
    setMessage("");

    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: window.location.origin,
      },
    });

    if (error) setMessage(error.message);
  };

  const signOut = async () => {
    await supabase.auth.signOut();
  };

  const inputBaseStyle = {
    color: "#ffffff",
    caretColor: "#148bff",
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#101010] flex items-center justify-center text-white">
        Loading...
      </div>
    );
  }

  if (session) {
  return <>{children}</>;
}

  return (
    <div className="min-h-screen bg-[#101010] flex items-center justify-center text-white px-4">
      <div className="w-full max-w-[430px] bg-[#202020] border border-[#3a3a3a] rounded-[24px] px-[36px] py-[38px]  shadow-[0_20px_60px_rgba(0,0,0,0.55)]">
        <div className="flex flex-col items-center mb-8">
          <div className="w-[64px] h-[64px] rounded-[18px] bg-[#10243a] text-[#148bff] grid place-items-center mb-5 shadow-[0_0_25px_rgba(20,139,255,0.18)]">
            <ShieldCheck size={30} />
          </div>

          <h1 className="text-[28px] font-extrabold tracking-[-0.5px] text-white">
            EsiBot Access
          </h1>

          <p className="text-[13px] text-[#8e8e8e] mt-[6px] tracking-wide">
            Secure robot dashboard
          </p>
        </div>

        <button
          type="button"
          onClick={signInWithGoogle}
          className="mb-[30px]
            w-full
            h-[50px]
            rounded-[14px]
            bg-white
            text-black
            font-bold
            text-[14px]
            flex
            items-center
            justify-center
            gap-3
            shadow-[0_2px_8px_rgba(0,0,0,0.25)] hover:bg-[#efefef]
            active:scale-[0.97]
            transition
          "
        >
          <span className="w-[20px] h-[20px] flex items-center justify-center">
            <GoogleIcon />
          </span>
          <span>Continue with Google</span>
        </button>

        <div className="flex items-center gap-3 my-6">
          <div className="h-[1px] flex-1 bg-[#3a3a3a]" />
          <span className="text-[11px] text-[#777] font-bold">OR</span>
          <div className="h-[1px] flex-1 bg-[#3a3a3a]" />
        </div>

        <div className="flex flex-col gap-4">
          <div>
            <label className="text-[12px] text-[#bcbcbc] font-semibold">
              Email
            </label>

            <div className="mt-[6px] flex items-center gap-3 bg-[#121212] border border-[#3a3a3a] rounded-[12px] px-3 focus-within:border-[#148bff] transition">
              <Mail size={15} className="text-[#888] shrink-0" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                style={inputBaseStyle}
                className="
                  w-full
  h-[46px]
  bg-transparent
  outline-none
  border-none
  text-white
  text-[14px]
  placeholder:text-[#7f7f7f]
                "
                placeholder="name@example.com"
              />
            </div>
          </div>

          <div>
            <label className="text-[12px] text-[#bcbcbc] font-semibold">
              Password
            </label>

            <div className="mt-[6px] mb-[30px] flex items-center gap-3 bg-[#121212] border border-[#3a3a3a] rounded-[12px] px-3 focus-within:border-[#148bff] transition">
              
              <Lock size={15} className="text-[#888] shrink-0" />

              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    authMode === "signin"
                      ? signInWithEmail()
                      : signUpWithEmail();
                  }
                }}
                style={inputBaseStyle}
                className="
                 w-full
  h-[46px]
  bg-transparent
  outline-none
  border-none
  text-white
  text-[14px]
  placeholder:text-[#7f7f7f]
   
                "
                placeholder="Password"
              />
            </div>
          </div>

          {message && (
            <div className="rounded-[10px] bg-[#2a1d10] border border-[#ffa92755] px-3 py-2">
              <p className="text-[12px] text-[#ffa927] font-bold leading-5">
                {message}
              </p>
            </div>
          )}

          <button
            type="button"
            onClick={authMode === "signin" ? signInWithEmail : signUpWithEmail}
            className="
              
              h-[48px]
              rounded-[14px]
              bg-[#148bff]
              text-black
              font-extrabold
              text-[14px]
              hover:bg-[#0f7ee8]
              active:scale-[0.97]
              transition
            "
          >
            {authMode === "signin" ? "LOGIN" : "CREATE ACCOUNT"}
          </button>

          <button
            type="button"
            onClick={() => {
              setMessage("");
              setAuthMode(authMode === "signin" ? "signup" : "signin");
            }}
            className="mt-[30px]
              bg-transparent
              border-none
              outline-none
              text-[13px]
              text-[#148bff]
              font-semibold
              hover:text-[#49a1ff]
              hover:underline
              transition
            "
          >
            {authMode === "signin"
              ? "Create an account"
              : "Already have an account? Login"}
          </button>
        </div>
      </div>
    </div>
  );
}