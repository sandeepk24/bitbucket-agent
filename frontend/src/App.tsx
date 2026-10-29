import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AppLayout } from "@/components/layout/AppLayout";
import { Dashboard } from "@/pages/Dashboard";
import { Repositories } from "@/pages/Repositories";
import { PullRequests } from "@/pages/PullRequests";
import { PrDeepAnalysis } from "@/pages/PrDeepAnalysis";
import { BambooBuilds } from "@/pages/BambooBuilds";
import { ProductionInvestigation } from "@/pages/ProductionInvestigation";
import { Settings } from "@/pages/Settings";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/repositories" element={<Repositories />} />
            <Route path="/pull-requests" element={<PullRequests />} />
            <Route path="/pr-analysis" element={<PrDeepAnalysis />} />
            <Route path="/bamboo" element={<BambooBuilds />} />
            <Route path="/production" element={<ProductionInvestigation />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
