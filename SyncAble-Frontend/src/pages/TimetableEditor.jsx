import React, { useState, useEffect } from 'react';

// A simple loader component
const Loader = () => (
  <div
    style={{
      border: '4px solid #f3f3f3',
      borderTop: '4px solid #3498db',
      borderRadius: '50%',
      width: '40px',
      height: '40px',
      animation: 'spin 2s linear infinite',
    }}
  >
    <style>{`
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `}</style>
  </div>
);

const TimetableEditor = () => {
  const API_BASE_URL = 'http://127.0.0.1:5000';
  const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];

  // State Management
  const [authToken, setAuthToken] = useState(null);
  const [generationId, setGenerationId] = useState(
    localStorage.getItem('generationId') || null
  );
  const [schedule, setSchedule] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [status, setStatus] = useState({ message: '', isError: false });

  // Form State
  const [selectedTeacher, setSelectedTeacher] = useState('');
  const [selectedWeek, setSelectedWeek] = useState(1);
  const [selectedDays, setSelectedDays] = useState(new Set());

  useEffect(() => {
    const token = localStorage.getItem('firebaseIdToken');
    if (token) {
      setAuthToken(token);
    } else {
      setStatus({
        message:
          'Authentication Token not found in local storage. Please log in.',
        isError: true,
      });
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (authToken) {
      fetchLatestTimetable();
    }
  }, [authToken]);

  const setStatusMessage = (message, isError = false) => {
    setStatus({ message, isError });
  };

  const handleDayChange = (day) => {
    const newSelectedDays = new Set(selectedDays);
    if (newSelectedDays.has(day)) {
      newSelectedDays.delete(day);
    } else {
      newSelectedDays.add(day);
    }
    setSelectedDays(newSelectedDays);
  };

  const fetchLatestTimetable = async () => {
    setIsLoading(true);
    setStatusMessage('Fetching latest timetable...');
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/latest-timetable-details`,
        {
          headers: { Authorization: `Bearer ${authToken}` },
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.generationId) {
        setGenerationId(data.generationId);
        localStorage.setItem('generationId', data.generationId);
      }

      setSchedule(data.schedule || {});
      setStatusMessage('Timetable loaded successfully.', false);
    } catch (error) {
      setStatusMessage(`Failed to load timetable: ${error.message}`, true);
    } finally {
      setIsLoading(false);
    }
  };

  const downloadCSV = async (id) => {
    try {
      setStatusMessage('Downloading updated CSV...', false);
      const response = await fetch(`${API_BASE_URL}/api/download-csv/${id}`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (!response.ok) throw new Error('Download failed');

      const newGenId = response.headers.get('X-Generation-ID');
      if (newGenId) {
        setGenerationId(newGenId);
        localStorage.setItem('generationId', newGenId);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `updated_timetable_${id}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
      setStatusMessage('CSV downloaded successfully.', false);
    } catch (error) {
      setStatusMessage(`Could not download file: ${error.message}`, true);
    }
  };

  const handleUpdate = async () => {
    if (!generationId) {
      setStatusMessage('Cannot update: No generation ID loaded.', true);
      return;
    }
    if (!selectedTeacher) {
      setStatusMessage('Please select a teacher.', true);
      return;
    }
    const unavailable_days = Array.from(selectedDays);
    if (unavailable_days.length === 0) {
      setStatusMessage('Please select at least one day.', true);
      return;
    }

    setIsUpdating(true);
    setStatusMessage('Updating timetable...', false);

    try {
      const response = await fetch(`${API_BASE_URL}/api/dynamic-request`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({
          generationId,
          teacher_name: selectedTeacher,
          unavailable_days,
          week_num: selectedWeek,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || `HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      if (result.generationId) {
        setGenerationId(result.generationId);
        localStorage.setItem('generationId', result.generationId);
      }

      setStatusMessage(result.message, false);

      await downloadCSV(generationId);
      await fetchLatestTimetable(); // Refresh the data view
      setSelectedDays(new Set()); // Reset checkboxes
    } catch (error) {
      setStatusMessage(`Update failed: ${error.message}`, true);
    } finally {
      setIsUpdating(false);
    }
  };

  const teachers = Object.keys(schedule).sort();

  return (
    <div className="bg-gray-900 text-gray-200 min-h-screen flex items-center justify-center p-4 font-['Inter',_sans-serif]">
      <div className="w-full max-w-4xl mx-auto">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white">
            Timetable Viewer & Editor
          </h1>
          <p className="text-gray-400 mt-2">
            View the latest generated schedule and make dynamic changes.
          </p>
        </header>

        <main className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Timetable Details Section */}
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
            <h2 className="text-2xl font-semibold mb-4 border-b border-gray-700 pb-2">
              Latest Schedule Details
            </h2>
            {isLoading ? (
              <div className="flex justify-center items-center h-48">
                <Loader />
              </div>
            ) : (
              <div className="space-y-4 max-h-96 overflow-y-auto pr-2">
                {teachers.length === 0 ? (
                  <p>No schedule details found in the latest timetable.</p>
                ) : (
                  teachers.map((teacher) => (
                    <div
                      key={teacher}
                      className="bg-gray-700/50 p-3 rounded-md"
                    >
                      <h3 className="font-semibold text-white">{teacher}</h3>
                      <ul className="list-disc list-inside text-gray-400 text-sm mt-1">
                        {Object.entries(schedule[teacher]).map(
                          ([week, days]) => (
                            <li key={week}>
                              <strong>{week}:</strong> {days.join(', ')}
                            </li>
                          )
                        )}
                      </ul>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          {/* Editor Section */}
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
            <h2 className="text-2xl font-semibold mb-4 border-b border-gray-700 pb-2">
              Make a Change
            </h2>
            <div className="space-y-4">
              <div>
                <label
                  htmlFor="teacher-select"
                  className="block mb-2 text-sm font-medium text-gray-300"
                >
                  Select Teacher
                </label>
                <select
                  id="teacher-select"
                  className="bg-gray-700 border border-gray-600 text-white text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
                  disabled={isLoading || teachers.length === 0}
                  value={selectedTeacher}
                  onChange={(e) => setSelectedTeacher(e.target.value)}
                >
                  <option value="">
                    {isLoading ? 'Loading...' : '-- Select a teacher --'}
                  </option>
                  {teachers.map((teacher) => (
                    <option key={teacher} value={teacher}>
                      {teacher}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block mb-2 text-sm font-medium text-gray-300">
                  Select Day(s) to Make Unavailable
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 p-3 bg-gray-700 rounded-lg">
                  {daysOfWeek.map((day) => (
                    <div key={day} className="flex items-center">
                      <input
                        type="checkbox"
                        id={`day-${day}`}
                        value={day}
                        checked={selectedDays.has(day)}
                        onChange={() => handleDayChange(day)}
                        className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-600 ring-offset-gray-800 focus:ring-2"
                      />
                      <label
                        htmlFor={`day-${day}`}
                        className="ml-2 text-sm font-medium text-gray-300"
                      >
                        {day}
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <label
                  htmlFor="week-select"
                  className="block mb-2 text-sm font-medium text-gray-300"
                >
                  For Week Number
                </label>
                <input
                  type="number"
                  id="week-select"
                  min="1"
                  max="4"
                  value={selectedWeek}
                  onChange={(e) => setSelectedWeek(Number(e.target.value))}
                  className="bg-gray-700 border border-gray-600 text-white text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
                  disabled={isLoading}
                />
              </div>

              <button
                type="button"
                onClick={handleUpdate}
                className="w-full text-white bg-blue-600 hover:bg-blue-700 focus:ring-4 focus:outline-none focus:ring-blue-800 font-medium rounded-lg text-sm px-5 py-2.5 text-center disabled:bg-gray-600 disabled:cursor-not-allowed"
                disabled={isLoading || isUpdating}
              >
                {isUpdating
                  ? 'Processing...'
                  : 'Update & Download New Timetable'}
              </button>
            </div>
          </div>
        </main>

        <footer className="text-center mt-8 h-10">
          {status.message && (
            <div
              className={`text-sm p-2 rounded-md ${
                status.isError
                  ? 'text-red-400 bg-red-900/50'
                  : 'text-green-400 bg-green-900/50'
              }`}
            >
              {status.message}
            </div>
          )}
        </footer>
      </div>
    </div>
  );
};

export default TimetableEditor;
