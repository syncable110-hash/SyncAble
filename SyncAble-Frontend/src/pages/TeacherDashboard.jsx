import React, { useState } from "react";
import {
  Container, Card, Form, Button, ListGroup, Row, Col, Alert,
  Spinner, InputGroup, FormControl,
} from "react-bootstrap";
import axios from "axios";

const TeacherDashboard = () => {
  // FIX: The non-existent TimetableContext has been removed.
  // TIMESLOTS are now defined directly in the component for self-containment.
  const TIMESLOTS = [
    "9-10", "10-11", "11-12", "12-1", "1-2", "2-3", "3-4", "4-5"
  ];

  // --- SIMPLIFIED STATE ---
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState("");
  const [notifications, setNotifications] = useState([]);
  
  // --- Form Input States ---
  const [teacherName] = useState("Dr. Gamma");
  const [batches, setBatches] = useState(["Batch_A", "Batch_B"]);
  const [newBatch, setNewBatch] = useState("");
  const [rooms, setRooms] = useState([{ name: "R101", type: "Lecture" }, { name: "L201", type: "Lab" }]);
  const [newRoomName, setNewRoomName] = useState("");
  const [newRoomType, setNewRoomType] = useState("Lecture");
  const [subjects, setSubjects] = useState([{ name: "CS_Theory", is_lab: false }, { name: "Physics_Lab", is_lab: true }]);
  const [newSubjectName, setNewSubjectName] = useState("");
  const [newSubjectIsLab, setNewSubjectIsLab] = useState(false);
  const [teachers, setTeachers] = useState([
    { name: "Mr. Alpha", subjects: "Math, Physics", availability: "9-10, 10-11, 11-12" },
    { name: "Dr. Gamma", subjects: "CS_Theory, Physics_Lab", availability: "10-11, 2-3, 3-4" }
  ]);
  const [newTeacherName, setNewTeacherName] = useState("");
  const [newTeacherSubjects, setNewTeacherSubjects] = useState("");
  const [newTeacherAvailability, setNewTeacherAvailability] = useState("");
  const [courseLoad, setCourseLoad] = useState([{ batch: "Batch_A", subject: "CS_Theory", hours: 30 }]);
  const [newLoadBatch, setNewLoadBatch] = useState("");
  const [newLoadSubject, setNewLoadSubject] = useState("");
  const [newLoadHours, setNewLoadHours] = useState(15);
  const [availability, setAvailability] = useState(() => {
    const map = {};
    TIMESLOTS.forEach((t) => (map[t] = false));
    return map;
  });

  const addToList = (item, setter, list) => { if (item && !list.includes(item)) setter([...list, item]); };
  const removeFromList = (index, setter, list) => { setter(list.filter((_, i) => i !== index)); };

  // --- UNIFIED 'Generate & Download' HANDLER ---
  const handleGenerateAndDownload = async () => {
    setError("");
    setNotifications(["🚀 Starting 4-week timetable generation... This may take a moment."]);
    setIsProcessing(true);

    const teacherAvailabilities = Object.fromEntries(
      teachers.map(t => [t.name, t.availability.split(',').map(slot => slot.trim())])
    );
    teacherAvailabilities[teacherName] = TIMESLOTS.filter(slot => availability[slot]);

    const finalConfig = {
      DAYS: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
      TIMESLOTS: TIMESLOTS,
      SEMESTER_WEEKS: 15,
      BATCHES: batches,
      ROOMS: Object.fromEntries(rooms.map(r => [r.name, { type: r.type }])),
      SUBJECTS: Object.fromEntries(subjects.map(s => [s.name, { is_lab: s.is_lab }])),
      TEACHERS: Object.fromEntries(teachers.map(t => [t.name, t.subjects.split(',').map(sub => sub.trim())])),
      TEACHER_AVAILABILITY: teacherAvailabilities,
      CONTRACTED_HOURS: courseLoad.reduce((acc, load) => {
        if (!acc[load.batch]) acc[load.batch] = {};
        acc[load.batch][load.subject] = Number(load.hours);
        return acc;
      }, {}),
      COURSE_LOAD: courseLoad.reduce((acc, load) => {
        if (!acc[load.batch]) acc[load.batch] = {};
        const weeklyHours = Math.round(Number(load.hours) / 15);
        acc[load.batch][load.subject] = weeklyHours > 0 ? weeklyHours : 1;
        return acc;
      }, {}),
    };

    try {
      const token = localStorage.getItem("firebaseIdToken");
      if (!token) throw new Error("Authentication token not found. Please log in again.");

      const response = await axios.post('http://127.0.0.1:5000/api/generate-and-download', finalConfig, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'text/csv' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'timetable_4_weeks.csv');
      document.body.appendChild(link);
      link.click();

      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      setNotifications(prev => [...prev, "✅ Success! Your 4-week timetable CSV is downloading."]);

    } catch (err) {
      console.error("An error occurred during the process:", err);
      if (err.response && err.response.data instanceof Blob) {
        const errorText = await err.response.data.text();
        setError(`Request Failed: ${errorText}`);
        setNotifications(prev => [...prev, `❌ Error: ${errorText}`]);
      } else {
         const errorMsg = err.response?.data?.error || err.message || "An unexpected network error occurred.";
         setError(`Request Failed: ${errorMsg}`);
         setNotifications(prev => [...prev, `❌ Error: ${errorMsg}`]);
      }
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <Container className="my-5">
      <Card className="shadow-lg">
        <Card.Header className="p-4 bg-light">
          <h2 className="mb-0 text-center">Timetable Generator Dashboard</h2>
          <p className="text-center text-muted mb-0">Welcome, {teacherName}</p>
        </Card.Header>
        <Card.Body className="p-4">
          {error && <Alert variant="danger">{error}</Alert>}

          <Row>
            <Col md={6} className="mb-4">
                <Card>
                    <Card.Header><h5>Batches</h5></Card.Header>
                    <Card.Body>
                        <ListGroup>
                            {batches.map((b, i) => (
                                <ListGroup.Item key={i}>
                                    {b}
                                    <Button variant="outline-danger" size="sm" className="float-end" onClick={() => removeFromList(i, setBatches, batches)}>X</Button>
                                </ListGroup.Item>
                            ))}
                        </ListGroup>
                        <InputGroup className="mt-3">
                            <FormControl placeholder="New Batch Name" value={newBatch} onChange={e => setNewBatch(e.target.value)} />
                            <Button onClick={() => { addToList(newBatch, setBatches, batches); setNewBatch(""); }}>Add Batch</Button>
                        </InputGroup>
                    </Card.Body>
                </Card>
            </Col>
            <Col md={6} className="mb-4">
                 <Card>
                    <Card.Header><h5>Rooms</h5></Card.Header>
                    <Card.Body>
                        <ListGroup>
                            {rooms.map((r, i) => (
                                <ListGroup.Item key={i}>
                                    {r.name} ({r.type})
                                    <Button variant="outline-danger" size="sm" className="float-end" onClick={() => removeFromList(i, setRooms, rooms)}>X</Button>
                                </ListGroup.Item>
                            ))}
                        </ListGroup>
                        <InputGroup className="mt-3">
                            <FormControl placeholder="Room Name (e.g., R101)" value={newRoomName} onChange={e => setNewRoomName(e.target.value)} />
                            <Form.Select value={newRoomType} onChange={e => setNewRoomType(e.target.value)}>
                                <option>Lecture</option>
                                <option>Lab</option>
                            </Form.Select>
                            <Button onClick={() => { setRooms([...rooms, { name: newRoomName, type: newRoomType }]); setNewRoomName(""); }}>Add Room</Button>
                        </InputGroup>
                    </Card.Body>
                </Card>
            </Col>
            <Col md={12} className="mb-4">
                <Card>
                    <Card.Header><h5>Subjects</h5></Card.Header>
                    <Card.Body>
                        <ListGroup>
                            {subjects.map((s, i) => (
                                <ListGroup.Item key={i}>
                                    {s.name} {s.is_lab ? '(Lab)' : '(Lecture)'}
                                    <Button variant="outline-danger" size="sm" className="float-end" onClick={() => removeFromList(i, setSubjects, subjects)}>X</Button>
                                </ListGroup.Item>
                            ))}
                        </ListGroup>
                        <InputGroup className="mt-3">
                            <FormControl placeholder="New Subject Name" value={newSubjectName} onChange={e => setNewSubjectName(e.target.value)} />
                            <Form.Check type="switch" id="is-lab-switch" label="Is Lab?" checked={newSubjectIsLab} onChange={e => setNewSubjectIsLab(e.target.checked)} className="ms-3 align-self-center" />
                            <Button onClick={() => { if(newSubjectName) { addToList({ name: newSubjectName, is_lab: newSubjectIsLab }, setSubjects, subjects); setNewSubjectName(""); setNewSubjectIsLab(false); } }}>Add Subject</Button>
                        </InputGroup>
                    </Card.Body>
                </Card>
            </Col>
             <Col md={12} className="mb-4">
                <Card>
                    <Card.Header><h5>Faculty & Their Availability</h5></Card.Header>
                    <Card.Body>
                        <ListGroup>
                            {teachers.map((t, i) => (
                                <ListGroup.Item key={i}>
                                    <strong>{t.name}</strong> <br />
                                    <small><em>Subjects:</em> {t.subjects}</small> <br/>
                                    <small><em>Availability:</em> {t.availability}</small>
                                    <Button variant="outline-danger" size="sm" className="float-end" onClick={() => removeFromList(i, setTeachers, teachers)}>X</Button>
                                </ListGroup.Item>
                            ))}
                        </ListGroup>
                        <InputGroup className="mt-3">
                            <FormControl placeholder="Teacher Name" value={newTeacherName} onChange={e => setNewTeacherName(e.target.value)} />
                            <FormControl placeholder="Subjects (comma-separated)" value={newTeacherSubjects} onChange={e => setNewTeacherSubjects(e.target.value)} />
                            <FormControl placeholder="Availability (e.g., 9-10, 2-3)" value={newTeacherAvailability} onChange={e => setNewTeacherAvailability(e.target.value)} />
                            <Button onClick={() => { if(newTeacherName) { setTeachers([...teachers, { name: newTeacherName, subjects: newTeacherSubjects, availability: newTeacherAvailability }]); setNewTeacherName(""); setNewTeacherSubjects(""); setNewTeacherAvailability(""); } }}>Add Teacher</Button>
                        </InputGroup>
                    </Card.Body>
                </Card>
            </Col>
             <Col md={12} className="mb-4">
                <Card>
                    <Card.Header><h5>Course Load (Total Hours per Batch/Subject for Semester)</h5></Card.Header>
                    <Card.Body>
                        <ListGroup>
                            {courseLoad.map((l, i) => (
                                <ListGroup.Item key={i}>
                                    {l.batch} / {l.subject}: {l.hours} hrs
                                    <Button variant="outline-danger" size="sm" className="float-end" onClick={() => removeFromList(i, setCourseLoad, courseLoad)}>X</Button>
                                </ListGroup.Item>
                            ))}
                        </ListGroup>
                        <InputGroup className="mt-3">
                            <Form.Select value={newLoadBatch} onChange={e => setNewLoadBatch(e.target.value)}>
                                <option value="">Select Batch...</option>
                                {batches.map(b => <option key={b} value={b}>{b}</option>)}
                            </Form.Select>
                            <Form.Select value={newLoadSubject} onChange={e => setNewLoadSubject(e.target.value)}>
                                <option value="">Select Subject...</option>
                                {subjects.map(s => <option key={s.name} value={s.name}>{s.name}</option>)}
                            </Form.Select>
                            <FormControl type="number" placeholder="Total Hours" value={newLoadHours} onChange={e => setNewLoadHours(e.target.value)} />
                            <Button onClick={() => { if(newLoadBatch && newLoadSubject) { setCourseLoad([...courseLoad, { batch: newLoadBatch, subject: newLoadSubject, hours: newLoadHours }]); setNewLoadBatch(""); setNewLoadSubject(""); setNewLoadHours(15); } }}>Add Load</Button>
                        </InputGroup>
                    </Card.Body>
                </Card>
            </Col>
            <Col md={12} className="mb-4">
                <Card>
                    <Card.Header><h5>Your Specific Availability (for {teacherName})</h5></Card.Header>
                    <Card.Body>
                        <Row>
                            {TIMESLOTS.map(slot => (
                                <Col xs={6} md={3} key={slot}>
                                    <Form.Check type="checkbox" label={slot} checked={availability[slot] || false} onChange={() => setAvailability(prev => ({ ...prev, [slot]: !prev[slot] }))} />
                                </Col>
                            ))}
                        </Row>
                    </Card.Body>
                </Card>
            </Col>
          </Row>

          <hr className="my-4" />

          <div className="text-center mb-4">
            <Button
              size="lg"
              variant="primary"
              className="px-5 py-3 shadow"
              onClick={handleGenerateAndDownload}
              disabled={isProcessing}
            >
              {isProcessing ? (
                <>
                  <Spinner animation="border" size="sm" className="me-2" />
                  Generating & Processing 4 Weeks...
                </>
              ) : (
                "Generate & Download 4-Week Timetable"
              )}
            </Button>
          </div>

          <Row className="justify-content-center">
            <Col md={10}>
              <Card border="light" className="bg-light">
                <Card.Header><h6>Process Log</h6></Card.Header>
                <Card.Body style={{ minHeight: '120px', maxHeight: '200px', overflowY: 'auto' }}>
                  {notifications.length > 0 ? (
                    notifications.map((note, index) => (
                      <p key={index} className="mb-1 small">
                        <span className="me-2">{new Date().toLocaleTimeString()}</span>{note}
                      </p>
                    ))
                  ) : (
                    <p className="text-muted small">Configure your settings above and click the button to begin. Notifications will appear here.</p>
                  )}
                </Card.Body>
              </Card>
            </Col>
          </Row>

        </Card.Body>
      </Card>
    </Container>
  );
};

export default TeacherDashboard;

