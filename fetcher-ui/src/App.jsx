import { NavLink, Route, Routes } from "react-router-dom";

import FetchPage from "./pages/FetchPage.jsx";
import HistoryPage from "./pages/HistoryPage.jsx";

export default function App() {
  return (
    <>
      <header className="topbar">
        <span className="brand">GitHub Repo Fetcher</span>
        <nav>
          <NavLink to="/" end>
            Fetch
          </NavLink>
          <NavLink to="/history">History</NavLink>
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<FetchPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="*" element={<p>Page not found.</p>} />
        </Routes>
      </main>
    </>
  );
}
