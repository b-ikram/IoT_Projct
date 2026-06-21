import { useEffect, useState } from "react";
import { supabase } from "./services/supabaseClient";
import MainLayout from "./layout/MainLayout";

export default function App() {
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    const loadUser = async () => {
      const { data } = await supabase.auth.getSession();

      const role =
        data.session?.user?.user_metadata?.role || "";

      setIsAdmin(role === "admin");
    };

    loadUser();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        const role =
          session?.user?.user_metadata?.role || "";

        setIsAdmin(role === "admin");
      }
    );

    return () => subscription.unsubscribe();
  }, []);

  return <MainLayout isAdmin={isAdmin} />;
}