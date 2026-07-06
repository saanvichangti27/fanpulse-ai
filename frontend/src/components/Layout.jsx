import { Outlet } from "react-router-dom";
import Nav from "@/components/Nav";
import CustomCursor from "@/components/CustomCursor";
import Footer from "@/components/Footer";

export default function Layout() {
  return (
    <div className="min-h-screen relative" data-testid="app-shell">
      <CustomCursor />
      <Nav />
      <main className="relative">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}
