import { useQuery } from "@tanstack/react-query";
import { apiGet } from "./api/client";

export default function App() {
  const api = useQuery({ queryKey: ["health"], queryFn: () => apiGet<{ status: string }>("/health") });
  const db = useQuery({ queryKey: ["health", "db"], queryFn: () => apiGet<{ status: string }>("/health/db") });

  const label = (q: typeof api) => (q.isPending ? "checking…" : q.isError ? "unreachable" : q.data.status);

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", padding: 24 }}>
      <h1>Warehouse Management</h1>
      <p>API: {label(api)}</p>
      <p>Database: {label(db)}</p>
    </main>
  );
}
