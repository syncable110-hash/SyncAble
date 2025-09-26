import React from "react";

const TIMESLOTS = [
  "09:00 – 10:00",
  "10:00 – 11:00",
  "11:00 – 12:00",
  "12:00 – 01:00",
  "01:00 – 02:00",
  "02:00 – 03:00",
  "03:00 – 04:00"
];

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

// --- FINAL FIX: The prop name is now `customTimetable` to match the parent ---
const Timetable = ({ customTimetable }) => {

  return (
    <section>
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              {DAYS.map((day) => (<th key={day}>{day.slice(0,3)}</th>))}
            </tr>
          </thead>
          <tbody>
            {TIMESLOTS.map((slot, index) => {
              if (slot === "12:00 – 01:00") {
                return (
                  <tr key={slot} style={{ background: 'rgba(255,255,255,0.06)'}}>
                    <th>{slot}</th>
                    <td colSpan="5">Lunch Break</td>
                  </tr>
                );
              }
              return (
                <tr key={slot}>
                  <th>{slot}</th>
                  {DAYS.map((day) => (
                    <td key={day}>
                      {/* --- FINAL FIX: Using the correct prop name and access method --- */}
                      {customTimetable?.[day.slice(0, 3)]?.[index] || "-"}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
};

export default Timetable;