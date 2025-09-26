import Hero from '../components/Hero';
import About from './About';
import Features from './Features';
import Timetable from '../components/common/Timetable';
import Contact from './Contact';

const Home = () => {
  return (
    <>
      <Hero />
      <Features />
      <About />
      <section className="timetable-example" aria-labelledby="demo-title">
        <h2 id="demo-title" className="mt-5">📅 Example Timetable</h2>
        <Timetable />
      </section>
      <Contact />
    </>
  );
};

export default Home;
