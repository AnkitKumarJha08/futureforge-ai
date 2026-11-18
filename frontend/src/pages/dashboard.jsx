import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import StatCard from "../components/Statcard";
import ProfileCard from "../components/ProfileCard";
import QuickActions from "../components/QuickActions";

function Dashboard() {
  return (
    <>
      <Navbar />

      <div style={{ display: "flex" }}>
        <Sidebar />

        <div
          style={{
            flex: 1,
            padding: "20px",
            background: "#F3F4F6",
            minHeight: "100vh",
          }}
        >
          <h1>FutureForge AI Dashboard</h1>

          <div
            style={{
              display: "flex",
              gap: "20px",
              flexWrap: "wrap",
            }}
          >
            <StatCard title="ATS Score" value="85%" />
            <StatCard title="Skills" value="12" />
            <StatCard title="Career Match" value="91%" />
            <StatCard title="Roadmap" value="6 Weeks" />
          </div>

          <div style={{ marginTop: "30px" }}>
            <ProfileCard />
          </div>

          <QuickActions />
        </div>
      </div>
    </>
  );
}

export default Dashboard;