import firebase from 'firebase/compat/app';
import 'firebase/compat/auth';
import 'firebase/compat/firestore';
import { GoogleAuthProvider } from 'firebase/auth';

export type FirebaseConfig = {
  apiKey?: string;
  authDomain?: string;
  projectId?: string;
  storageBucket?: string;
  messagingSenderId?: string;
  appId?: string;
  measurementId?: string;
  [key: string]: string | undefined;};

let auth: firebase.auth.Auth | undefined;
let googleAuthProvider: GoogleAuthProvider | undefined;

export const setFirebaseConfig = (config: FirebaseConfig): void => {
  firebase.initializeApp(config);
  auth = firebase.auth();

  googleAuthProvider = new GoogleAuthProvider();
};

export { auth, googleAuthProvider };
