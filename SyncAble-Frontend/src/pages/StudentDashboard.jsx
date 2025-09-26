import React, { useContext } from "react";
import { Card, ListGroup, Button } from "react-bootstrap";
import Timetable from "../components/common/Timetable";
import { useNavigate } from "react-router-dom";
import { TimetableContext } from "../context/TimetableContext";

const StudentDashboard = () => {
  const navigate = useNavigate();
  const { timetable } = useContext(TimetableContext);

  const student = {
    name: "John Doe",
    course: "BCA",
    semester: "4th Semester",
    notifications: [
      "No classes on 25th Sep due to holiday",
      "DBMS room changed to Lab 3",
      "Assignment 2 submission deadline: 27th Sep",
    ],
  };

  const handleLogout = () => navigate("/");

  return (
    <div className="container my-5">
      <h2 className="mb-4">Welcome, {student.name}</h2>

      <Card className="mb-4">
        <Card.Header>
          <h5>📅 Weekly Timetable</h5>
        </Card.Header>
        <Card.Body>
          <Timetable customTimetable={timetable} title={`${student.name}-timetable`} />
        </Card.Body>
      </Card>

      <Card>
        <Card.Header>
          <h5>🔔 Notifications</h5>
        </Card.Header>
        <ListGroup variant="flush">
          {student.notifications.map((note, idx) => (
            <ListGroup.Item key={idx}>{note}</ListGroup.Item>
          ))}
        </ListGroup>
      </Card>

      <div className="mt-4">
        <Button variant="danger" onClick={handleLogout}>
          Logout
        </Button>
      </div>
    </div>
  );
};

export default StudentDashboard;
