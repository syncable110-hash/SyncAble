const featuresData = [ 
  {
    title: "🎓 Student Portal",
    description: "Choose electives, set credit load, and get instant personalized schedules."
  },
  {
    title: "👩 Faculty Portal",
    description: "Update availability, manage workload, and track assignments with ease."
  },
  {
    title: "⚡ AI-Powered Generation",
    description: "Auto-generate optimized timetables in seconds using intelligent algorithms."
  },
  {
    title: "📅 Clash-Free Scheduling",
    description: "Smart conflict detection ensures no overlaps in rooms, faculty, or courses."
  },
  {
    title: "🎯 High Accuracy",
    description: "Aligned with NEP 2020 guidelines for credits, majors, minors, and skill courses."
  },
  {
    title: "💾 Save & Export",
    description: "Download in PDF/Excel or integrate directly with academic systems."
  }
];

  const Features = () => {
    return (
      <section id="features" className="features">
        {featuresData.map((feature, idx) => (
          <article key={idx} className="card">
            <h3>{feature.title}</h3>
            <p>{feature.description}</p>
          </article>
        ))}
      </section>
    );
  };
export default Features  