# HackFusion Frontend

React-based frontend for the HackFusion pharmacy automation system.

## Features

- **Camera Capture**: Live webcam feed for prescription capture with guide overlay
- **Prescription Processing**: Real-time OCR and LLM-based text extraction
- **Responsive Design**: Works on desktop and mobile devices
- **Modern UI**: Built with Tailwind CSS v4

## Pages

### Home (`/`)
Landing page with navigation to all features.

### Prescription Capture (`/capture`)
Full prescription capture flow:
1. Start camera
2. Capture prescription image
3. Preview and confirm
4. Process with OCR + LLM
5. View extracted data

### Kiosk Mode (`/kiosk`)
Customer-facing self-service interface (coming soon).

### Dashboard (`/dashboard`)
Admin analytics and monitoring (coming soon).

## Development

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Tech Stack

- **React 19**: Latest React with concurrent features
- **Vite**: Fast build tool and dev server
- **React Router**: Client-side routing
- **Tailwind CSS v4**: Utility-first styling
- **react-webcam**: Camera access and capture
- **React Query**: Server state management
- **Zustand**: Client state management
- **Axios**: HTTP client
- **Recharts**: Data visualization

## Camera Permissions

The camera capture feature requires browser camera permissions. When prompted:
1. Click "Allow" to grant camera access
2. If denied, check browser settings to enable camera for this site

## Browser Support

- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support (iOS 14.3+)
- Mobile browsers: Full support with back camera preference

## Components

### CameraCapture
Reusable camera component with:
- Live preview
- Capture guide overlay
- Image capture and preview
- Retake functionality
- Error handling

Usage:
```jsx
import CameraCapture from './components/CameraCapture';

<CameraCapture
  onCapture={(imageData) => console.log('Captured:', imageData)}
  onCancel={() => console.log('Cancelled')}
/>
```

## API Integration

The frontend is designed to connect to the FastAPI backend at `http://localhost:8000`.

To integrate with backend:
1. Update API base URL in `src/services/api.js` (when created)
2. Implement API calls for prescription processing
3. Handle authentication if needed

## Future Enhancements

- [ ] Voice input integration
- [ ] Text chat interface
- [ ] Real-time agent decision visualization
- [ ] WhatsApp notification preview
- [ ] Audit log viewer
- [ ] Analytics dashboard
- [ ] Multi-language support

## Notes

- Camera capture works best with good lighting
- Prescription should be flat and fully visible
- All text should be clear and readable
- Avoid glare from lights or windows
