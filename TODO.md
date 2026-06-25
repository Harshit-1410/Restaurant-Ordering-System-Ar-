# Roadmap & TODO List

This document lists the prioritized roadmap, technical debt cleanup, and future enhancements for the AR Restaurant Ordering System.

---

## 1. High Priority

### Database Performance
- **Category & Item Prefetching**: Optimize category queries on the menu landing page. Currently, we prefetch `items` (which is good), but we should ensure category and item queries utilize database indexing on fields like `slug` and `is_active`.
- **Session Expiry Cleanup**: Implement a background cron task to expire and close table sessions that have been inactive for more than 4 hours without being closed by the cashier.

### Testing Integration
- **Unit Test Coverage**: Add unit tests for the Views (`cart_add`, `place_order`, `request_bill`) in `ordering/tests.py` and `restaurants/tests.py` using Django's TestCase class to automate the verification pipeline in CI/CD.
- **End-to-End Testing**: Set up Playwright or Cypress to automate front-end responsive layout and checkout flow testing across standard viewports.

---

## 2. Medium Priority

### Kitchen Dashboard Enhancements
- **Sound Alerts**: Add audio notification alerts to the Kitchen Dashboard when a new order is received or when a bill is requested. (Already implemented WebSocket reconnection handlers with exponential backoff on kitchen and billing dashboards).

### Customer UX
- **Order History Section**: Create an inline "Orders List" modal on the mobile bottom navigation tab so customers can see items they have already ordered during their current session.

---

## 3. Nice to Have

### Analytics & Reporting
- **Counter Sales Analytics**: Build a simple analytics page showing daily revenue, popular items, average dining times, and order volume.
- **AR Model Viewer Customization**: Implement camera filter controls in model-viewer (e.g. ambient lighting controls, rotation speeds) to enhance item exploration.
