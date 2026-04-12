import { Footer } from "@/components/layout/footer";
import { Navbar } from "@/components/layout/navbar";
import { LandingContent } from "@/components/marketing/landing-content";

export default function HomePage() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <LandingContent />
      <Footer />
    </div>
  );
}
