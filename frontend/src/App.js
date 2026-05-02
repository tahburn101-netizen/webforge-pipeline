import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import "@/App.css";
import { Shell } from "@/components/Shell";
import PipelinePage from "@/pages/PipelinePage";
import JobsPage from "@/pages/JobsPage";
import JobDetailPage from "@/pages/JobDetailPage";

function App() {
  return (
    <BrowserRouter>
      <Shell>
        <Routes>
          <Route path="/" element={<PipelinePage />} />
          <Route path="/jobs" element={<JobsPage />} />
          <Route path="/jobs/:id" element={<JobDetailPage />} />
        </Routes>
      </Shell>
      <Toaster theme="dark" position="bottom-right" richColors closeButton />
    </BrowserRouter>
  );
}

export default App;
