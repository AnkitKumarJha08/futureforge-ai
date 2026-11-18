import {
  FaHome,
  FaFileUpload,
  FaChartBar,
  FaBook,
  FaBriefcase,
  FaUserTie
} from "react-icons/fa";

function Sidebar() {
  const menu = [
    { icon: <FaHome />, text: "Dashboard" },
    { icon: <FaFileUpload />, text: "Resume Upload" },
    { icon: <FaChartBar />, text: "ATS Score" },
    { icon: <FaBook />, text: "Roadmap" },
    { icon: <FaBriefcase />, text: "Jobs" },
    { icon: <FaUserTie />, text: "Interview" }
  ];

  return (
    <div
      style={{
        width: "250px",
        background: "#1F2937",
        color: "white",
        height: "100vh",
        padding: "20px"
      }}
    >
      {menu.map((item, index) => (
        <div
          key={index}
          style={{
            padding: "15px",
            cursor: "pointer"
          }}
        >
          {item.icon} {item.text}
        </div>
      ))}
    </div>
  );
}

export default Sidebar;