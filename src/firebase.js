// Import the functions you need from the SDKs you need
// import { initializeApp } from "firebase/app";
// import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
// const firebaseConfig = {
//   apiKey: "AIzaSyB6oeXokIhQuOj8RJ2mpXPqwqP10gD0Xd0",
//   authDomain: "seniorproject-684c1.firebaseapp.com",
//   projectId: "seniorproject-684c1",
//   storageBucket: "seniorproject-684c1.firebasestorage.app",
//   messagingSenderId: "847138584376",
//   appId: "1:847138584376:web:eface0926c96092daef3cd",
//   measurementId: "G-N0CM5TQBM8"
// };

// Initialize Firebase
// const app = initializeApp(firebaseConfig);
// const analytics = getAnalytics(app);

// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";

// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// ✅ Your web app's Firebase configuration (corrected)
const firebaseConfig = {
  apiKey: "AIzaSyB6oeXokIhQuOj8RJ2mpXPqwqP10gD0Xd0",
  authDomain: "seniorproject-684c1.firebaseapp.com",
  projectId: "seniorproject-684c1",
  storageBucket: "seniorproject-684c1.appspot.com", 
  messagingSenderId: "847138584376",
  appId: "1:847138584376:web:eface0926c96092daef3cd",
  measurementId: "G-N0CM5TQBM8"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
const db = getFirestore(app);
const auth = getAuth(app);