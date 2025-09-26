import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Form, Button, Card, Container, Row, Col, Alert } from 'react-bootstrap';
import axios from 'axios';
import { signInWithEmailAndPassword } from "firebase/auth";
import { auth } from '../context/firebase'; // Import the auth instance from your firebase.js

const Auth = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const role = params.get('role'); // 'student' or 'teacher'

  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    // Student/Teacher specific fields are handled in the payload
  });
  const [error, setError] = useState(''); // For displaying error messages

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError(''); // Clear error on new input
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); // Reset error before submission

    // --- SIGNUP LOGIC ---
    if (!isLogin) {
      try {
        const payload = {
          email: formData.email,
          password: formData.password,
          name: formData.name,
          role: role,
        };
        
        // Your backend API endpoint for signup
        const response = await axios.post('http://127.0.0.1:5000/api/signup', payload);
        
        console.log('Signup successful:', response.data);
        alert('Registration successful! Please log in.');
        setIsLogin(true); // Switch to login form after successful registration
        
      } catch (err) {
        // Display error message from the backend
        const errorMessage = err.response?.data?.error || 'An unexpected error occurred during signup.';
        console.error('Signup error:', errorMessage);
        setError(errorMessage);
      }
    } 
    // --- LOGIN LOGIC ---
    else {
      try {
        // Use Firebase Client SDK to sign in. This is the standard & secure way.
        const userCredential = await signInWithEmailAndPassword(auth, formData.email, formData.password);
        const user = userCredential.user;
        
        console.log('Login successful for user:', user.uid);
        
        // IMPORTANT: Get the ID Token to send to your protected backend routes
        const idToken = await user.getIdToken();
        
        // Store the token for future API calls (e.g., in localStorage)
        localStorage.setItem('firebaseIdToken', idToken);
        
        // Redirect after login
        if (role === 'student') {
          navigate('/student');
        } else if (role === 'teacher') {
          navigate('/teacher');
        }
        
      } catch (err) {
        // Display user-friendly error from Firebase
        const errorMessage = err.message.replace('Firebase: ', '');
        console.error('Login error:', errorMessage);
        setError(errorMessage);
      }
    }
  };

  return (
    <Container className="my-5">
      <Row className="justify-content-center">
        <Col md={6}>
          <Card className="p-4 shadow-sm">
            <h2 className="text-center mb-4">
              {isLogin ? 'Login' : 'Register'} as {role?.charAt(0).toUpperCase() + role?.slice(1)=="Teacher"?"Faculty":"Student"
              }
            </h2>

            {error && <Alert variant="danger">{error}</Alert>}

            <Form onSubmit={handleSubmit}>
              {!isLogin && (
                <Form.Group className="mb-3">
                  <Form.Label>Name</Form.Label>
                  <Form.Control
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    placeholder="Enter your name"
                    required={!isLogin}
                  />
                </Form.Group>
              )}

              <Form.Group className="mb-3">
                <Form.Label>Email</Form.Label>
                <Form.Control
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="Enter your email"
                  required
                />
              </Form.Group>

              <Form.Group className="mb-3">
                <Form.Label>Password</Form.Label>
                <Form.Control
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="Enter your password"
                  minLength="6"
                  required
                />
              </Form.Group>

              <Button variant="primary" type="submit" className="w-100 mb-3">
                {isLogin ? 'Login' : 'Register'}
              </Button>

              <div className="text-center">
                <Button
                  variant="link"
                  onClick={() => {
                    setIsLogin(!isLogin);
                    setError('');
                  }}
                >
                  {isLogin ? "Don't have an account? Register" : 'Already have an account? Login'}
                </Button>
              </div>
            </Form>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default Auth;