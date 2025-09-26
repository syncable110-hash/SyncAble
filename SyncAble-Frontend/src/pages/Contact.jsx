import { Container, Row, Col, Form, Button } from "react-bootstrap";

const Contact = () => {
  return (
    <section id="contact" className="py-5">
      <Container>
        <h2 className="text-center mb-4 heading">Contact Us</h2>
        <Row>
          {/* Contact Info */}
          <Col md={6} className="mb-4 d-flex justify-content-center flex-column description">
            <h5>📍 Address</h5>
            <p>123 AI Street, Tech City, India</p>

            <h5>📧 Email</h5>
            <p>support@syncable.com</p>

            <h5>📞 Phone</h5>
            <p>+91 98765 43210</p>
          </Col>

          {/* Feedback Form */}
          <Col md={6}>
            <Form className="contact-card">
              <Form.Group className="mb-3 text-start " controlId="name">
                <Form.Label className="px-2 description">Name</Form.Label>
                <Form.Control type="text" placeholder="Enter your name" />
              </Form.Group>

              <Form.Group className="mb-3 text-start" controlId="email">
                <Form.Label className="px-2 description">Email</Form.Label>
                <Form.Control type="email" placeholder="Enter your email" />
              </Form.Group>

              <Form.Group className="mb-3 text-start" controlId="message">
                <Form.Label className="px- description">Message</Form.Label>
                <Form.Control as="textarea" rows={4} placeholder="Write your feedback..." />
              </Form.Group>

              <Button variant="primary" type="submit">
                Submit
              </Button>
            </Form>
          </Col>
        </Row>
      </Container>
    </section>
  );
};

export default Contact;
