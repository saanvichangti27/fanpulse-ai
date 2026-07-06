import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "@/components/Layout";
import Landing from "@/pages/Landing";
import Heatmap from "@/pages/Heatmap";
import Strategies from "@/pages/Strategies";
import Matches from "@/pages/Matches";
import { Toaster } from "sonner";

function App() {
  return (
    <div className="App">
      <Toaster theme="dark" position="bottom-right" />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Landing />} />
            <Route path="heatmap" element={<Heatmap />} />
            <Route path="strategies" element={<Strategies />} />
            <Route path="matches" element={<Matches />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
