import { useEffect, useState } from 'react';

const Footer = () => {
  const [year, setYear] = useState(new Date().getFullYear());

  return (
    <footer id="contact">
      © {year} Smart India Hackathon — PS25091 | AI-Generated Timetable
    </footer>
  );
};

export default Footer;
