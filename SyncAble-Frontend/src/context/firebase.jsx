import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

// TODO: Replace the following with your app's Firebase project configuration
// You can find this in your Firebase project settings -> General -> Your apps -> Web app
const firebaseConfig = {
  apiKey: "AIzaSyAWrI5fVM2iz30B-eI3lDEPnX6gNryDRj8",
  authDomain: "timetable-generator-89f28.firebaseapp.com",
  databaseURL: "https://timetable-generator-89f28-default-rtdb.asia-southeast1.firebasedatabase.app",
  projectId: "timetable-generator-89f28",
  storageBucket: "timetable-generator-89f28.firebasestorage.app",
  messagingSenderId: "380410114771",
  appId: "1:380410114771:web:0df4b0058f9a8e8bc8da26",
  measurementId: "G-GZZNCW0K37"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Authentication and get a reference to the service
export const auth = getAuth(app);