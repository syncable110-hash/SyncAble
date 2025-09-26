import { Navbar, Nav, Container } from 'react-bootstrap';
import { Link,NavLink } from 'react-router-dom';
import Logo from '../assets/logo3.png'; 

const Header = () => {
  return (
    <Navbar
      expand="lg"
      variant="dark"
      style={{ background: 'white' }}
      sticky="top"
    >
      <Container>
        <Navbar.Brand as={NavLink} to="/" className="d-flex align-items-center logo">
          <img src={Logo} alt="SyncAble Logo" className="logo-img me-2" />
          <span>SyncAble</span>
        </Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="ms-auto" >
            <Nav.Link as={NavLink} to="/">Home</Nav.Link>
            <Nav.Link as={NavLink} to="/auth?role=student">Student Portal</Nav.Link>
            <Nav.Link as={NavLink} to="/auth?role=teacher">Faculty Portal</Nav.Link>
            <Nav.Link as={NavLink} to="/features">Features</Nav.Link>
            <Nav.Link as={NavLink} to="/contact">Contact</Nav.Link>
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
};

export default Header;
