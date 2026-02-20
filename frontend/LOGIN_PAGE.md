# Login Page

## Overview
A beautiful circular flip-card login page with smooth 3D animations for SignVista.

## Features

### Design
- **Circular Container**: The login form is contained in a circular design that creates a unique, modern aesthetic
- **3D Flip Animation**: Smooth 180-degree rotation transition between Sign In and Sign Up forms
- **Responsive**: Adapts to mobile devices by switching to rounded rectangles on smaller screens

### Sign In Form
- Email input with icon
- Password input with show/hide toggle
- Remember me checkbox
- Forgot password link
- Smooth transition to Sign Up

### Sign Up Form
- Full name input
- Email input
- Password input with show/hide toggle
- Confirm password input with show/hide toggle
- Terms of Service and Privacy Policy agreement
- Smooth transition back to Sign In

### Visual Effects
- Gradient backgrounds with animated blur effects
- Floating emoji decorations (👋, 🤟, ✌️)
- Hover effects on the circular container
- Smooth input focus states
- Gradient text for headings
- Icon animations

### Theme Support
- Full dark mode support
- Consistent with SignVista's color palette:
  - Primary: #344C3D, #105F68
  - Secondary: #3A9295, #9ED5D1
  - Accent: #BFCFBB, #C8E6E2

## Usage

Navigate to `/login` to access the login page.

### Flip Between Forms
Click the "Sign Up" button on the Sign In form or "Sign In" button on the Sign Up form to trigger the 3D flip animation.

## Technical Details

### Components
- `SignVista/frontend/src/app/login/page.tsx` - Next.js App Router page
- `SignVista/frontend/src/app/pages/LoginPage.tsx` - Reusable component

### Styling
Custom CSS classes in `globals.css`:
- `.perspective-container` - 3D perspective wrapper
- `.flip-card` - Main flip animation container
- `.flip-card-front` / `.flip-card-back` - Front and back faces
- `.auth-circle` - Circular form container
- `.input-group` - Input wrapper with icon positioning
- `.auth-input` - Styled input fields

### Animation
- Uses CSS transforms for 3D rotation
- `transform: rotateY(180deg)` for flip effect
- `backface-visibility: hidden` to hide the back face
- Smooth cubic-bezier easing for natural motion

## Customization

### Colors
Update the gradient colors in the component to match your brand:
```tsx
style={{ background: 'linear-gradient(135deg, #344C3D, #105F68)' }}
```

### Circle Size
Adjust the height in `.flip-card` class in `globals.css`:
```css
.flip-card {
  height: 600px; /* Adjust as needed */
}
```

### Mobile Breakpoint
Modify the media query in `globals.css` to change when the circle becomes a rounded rectangle:
```css
@media (max-width: 640px) {
  .auth-circle {
    border-radius: 30px; /* Rounded rectangle on mobile */
  }
}
```
