import React, { createContext, useState } from "react";

export const TimetableContext = createContext();

export const TimetableProvider = ({ children }) => {
  const TIMESLOTS = [
    "09:00 – 10:00",
    "10:00 – 11:00",
    "11:00 – 12:00",
    "12:00 – 01:00",
    "01:00 – 02:00",
    "02:00 – 03:00",
    "03:00 – 04:00",
  ];

  const INITIAL_TIMETABLE = {
    Mon: Array(TIMESLOTS.length).fill(""),
    Tue: Array(TIMESLOTS.length).fill(""),
    Wed: Array(TIMESLOTS.length).fill(""),
    Thu: Array(TIMESLOTS.length).fill(""),
    Fri: Array(TIMESLOTS.length).fill(""),
  };

  const [timetable, setTimetable] = useState(INITIAL_TIMETABLE);

  return (
    <TimetableContext.Provider value={{ timetable, setTimetable, TIMESLOTS }}>
      {children}
    </TimetableContext.Provider>
  );
};
