import { Button } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';

// style={ fontSize: '42px', fontWeight: '700', marginBottom: '16px', 
//                    background: 'linear-gradient(90deg, var(--accent), #4bb6ff)',WebkitBackgroundClip: 'text',WebkitTextFillColor: 'transparent' }
const Hero = () => {
  const navigate = useNavigate();

  return (
    <section className="hero text-center py-5">
      <h1 >
        AI-Generated Timetable
      </h1>
      <p style={{ fontSize: '18px', color: 'var(--muted)', maxWidth: '700px', margin: '0 auto 28px auto' }} className="description">
        Smart India Hackathon (PS25091) — A user-friendly platform to generate
        optimised, clash-free timetables for students and teachers.
      </p>
      <div className="hero-actions d-flex justify-content-center gap-3">
        <Button variant="primary" onClick={() => navigate('/auth?role=student')}>Student Portal</Button>
        <Button variant="outline-light" className='hero-button' onClick={() => navigate('/auth?role=teacher')}>Faculty Portal</Button>


      </div>
    </section>
  );
};

export default Hero;
