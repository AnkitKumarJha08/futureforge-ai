function ProfileCard() {
  return (
    <div
      style={{
        background: "white",
        padding: "20px",
        borderRadius: "15px"
      }}
    >
      <h3>User Profile</h3>

      <p>Name: Ankit</p>
      <p>Email: ankit@test.com</p>
      <p>Target Role: Software Engineer</p>

      <p>
        Profile Completion: 70%
      </p>
    </div>
  );
}

export default ProfileCard;