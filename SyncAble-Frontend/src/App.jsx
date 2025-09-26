import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Header from "./components/Header";
import Footer from "./components/Footer";
import Home from "./pages/Home";
import Auth from "./pages/Auth";
import StudentDashboard from "./pages/StudentDashboard";
import TeacherDashboard from "./pages/TeacherDashboard";
import { TimetableProvider } from "./context/TimetableContext";
import TimetableEditor from "./pages/TimetableEditor";
import Features from "./pages/Features";
import Contact from "./pages/Contact";

function App() {
  return (
    <TimetableProvider>
      <Router>
        <Header />
        <main className="homepage">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/auth" element={<Auth />} />
            <Route path="/student" element={<StudentDashboard />} />
            <Route path="/teacher" element={<TeacherDashboard />} />
            <Route path="/timetable-editor" element={<TimetableEditor />} />
            <Route path="/features" element={<Features />} />
            <Route path="/contact" element={<Contact />} />
          </Routes>
        </main>
        <Footer />
      </Router>
    </TimetableProvider>
  );
}

export default App;
