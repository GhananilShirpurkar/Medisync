import { useState, useEffect } from 'react';
import AppLayout from '../components/AppLayout';
import WorkspaceCanvas from '../components/WorkspaceCanvas';
import OmniInputBar from '../components/OmniInputBar';
import AgentActivityPanel from '../components/AgentActivityPanel';
import SidebarCart from '../components/SidebarCart';
import CameraModal from '../components/CameraModal';
import StatusAmbience from '../components/StatusAmbience';
import TheatreLayout from '../components/TheatreLayout';
import ClinicalRecord from '../components/ClinicalRecord';
import IntelligenceTrace from '../components/IntelligenceTrace';
import IntelShelf from '../components/IntelShelf';

const Kiosk = () => {
  // sessionId is lifted here so AgentActivityPanel (and StatusAmbience) can subscribe to the WebSocket
  const [sessionId, setSessionId] = useState(null);
  const [currentOrder, setCurrentOrder] = useState(null);
  const [workObjects, setWorkObjects] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showCamera, setShowCamera] = useState(false);

  // Initialize Session
  useEffect(() => {
    const createSession = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/conversation/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: `operator_${Date.now()}` }),
        });
        const data = await response.json();
        setSessionId(data.session_id);
      } catch (err) {
        console.error("Failed to init session", err);
      }
    };
    createSession();
  }, []);

  // Handle Voice or Text Input
  const handleInputSubmit = async (text) => {
    setIsProcessing(true);
    
    // 1. Spatially Spawn the Work Object instantly
    const newObjId = `wo_${Date.now()}`;
    const initialObject = {
      id: newObjId,
      type: 'transcript',
      status: 'processing',
      payload: { text },
      annotations: []
    };
    
    
    setWorkObjects(prev => [...prev, initialObject]);

    try {
      // 2. Send to Orchestrator Vector Space
      const response = await fetch('http://localhost:8000/api/conversation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message: text,
        }),
      });

      const data = await response.json();

      // 3. Map backend JSON into pure Annotations attached to *this* object
      setWorkObjects(prev => prev.map(obj => {
        if (obj.id === newObjId) {
          const newAnnotations = [];
          
          if (data.severity && data.severity.score > 3) {
             newAnnotations.push({ agent: 'Triage', text: `Severity: ${data.severity.score}/10` });
          }
          if (data.intent) {
             newAnnotations.push({ agent: 'Medical', text: `Intent: ${data.intent}` });
          }
          if (data.recommendations && data.recommendations.length > 0) {
             data.recommendations.forEach(med => {
               newAnnotations.push({ agent: 'Inventory', text: `${med.medicine_name} - ${med.stock}` });
             });
             
             // Update Global Cart if recommendations came back
             setCurrentOrder({
                patientName: 'Patient',
                prescriptionId: sessionId?.substring(0, 8),
                medications: data.recommendations,
                interactionStatus: data.intent,
                severity: data.severity,
             });
          }

          // Check for client-side triggers from the API Gateway
          if (data.client_action === 'OPEN_CAMERA') {
            setShowCamera(true);
          }

          return { 
            ...obj, 
            status: 'resolved', 
            payload: { ...obj.payload, response: data.message },
            annotations: newAnnotations 
          };
        }
        return obj;
      }));

      // Room Settles: Append closure to local log
      setTimeout(() => {
        setWorkObjects(prev => [...prev, {
          id: `closure_${Date.now()}`,
          type: 'status',
          payload: { text: `Consultation closed · ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` }
        }]);
      }, 1500);

    } catch (err) {
      console.error(err);
      setWorkObjects(prev => prev.map(obj => 
        obj.id === newObjId ? { ...obj, status: 'failed' } : obj
      ));
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle Image Document Drops
  const handleImageSubmit = async (file) => {
    setIsProcessing(true);
    
    // 1. Spatially Spawn the Document Artifact
    const newObjId = `wo_img_${Date.now()}`;
    const localImageUrl = URL.createObjectURL(file);
    
    const initialObject = {
      id: newObjId,
      type: 'document',
      status: 'processing',
      payload: { imageUrl: localImageUrl },
      annotations: []
    };
    

    setWorkObjects(prev => [...prev, initialObject]);

    try {
      const formData = new FormData();
      formData.append('image', file, 'prescription.jpg');

      const response = await fetch(`http://localhost:8000/api/prescription/upload?session_id=${sessionId}`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      // Parse JSON into Agent Annotations
      setWorkObjects(prev => prev.map(obj => {
        if (obj.id === newObjId) {
           const newAnnotations = [];
           
           if (data.medicines && data.medicines.length > 0) {
             data.medicines.forEach(med => {
               // Vision highlights what it sees
               newAnnotations.push({ agent: 'Vision', text: med.name });
             });
             
             const mappedMedicines = data.medicines.map(med => {
                const inStock = data.inventory_check?.in_stock?.find(i => i.name.toLowerCase() === med.name.toLowerCase());
                return {
                  medicine_name: med.name,
                  price: inStock ? inStock.price : 0,
                  stock: inStock ? inStock.stock : 'Out of Stock'
                };
             });

             // Update context cart
             setCurrentOrder({
               patientName: data.patient_info?.patient_name || 'Patient',
               prescriptionId: sessionId?.substring(0, 8) || 'DOC-01',
               medications: mappedMedicines,
               interactionStatus: 'prescription_processed',
             });
           }
           
           return { ...obj, status: 'resolved', annotations: newAnnotations };
        }
        return obj;
      }));

    } catch (err) {
      console.error(err);
      setWorkObjects(prev => prev.map(obj => 
        obj.id === newObjId ? { ...obj, status: 'failed' } : obj
      ));
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <AppLayout>
      <TheatreLayout
        leftZone={
          <div className="flex flex-col h-full overflow-hidden">
            <div className={`flex-[4] border-b transition-colors duration-1000 ${isProcessing ? 'border-gray-100/50' : 'border-gray-300'}`}>
              <ClinicalRecord 
                entries={workObjects.map(obj => {
                   if (obj.type === 'status') return { timestamp: 'LOG', text: obj.payload.text };
                   return {
                     timestamp: new Date(parseInt(obj.id.split('_').pop())).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                     text: obj.payload.text
                   };
                })} 
              />
            </div>
            <div className="flex-[6]">
              <IntelligenceTrace sessionId={sessionId} />
            </div>
          </div>
        }
        rightZone={
          <div className="h-full bg-white/5">
            <IntelShelf currentOrder={currentOrder} />
          </div>
        }
      >
        <div className="flex-1 flex flex-col relative overflow-hidden">
          <WorkspaceCanvas objects={workObjects} />
          
          <OmniInputBar 
            onInputSubmit={handleInputSubmit} 
            onImageSubmit={handleImageSubmit}
            sessionId={sessionId}
            isLoading={isProcessing}
            isSettled={!isProcessing && workObjects.some(obj => obj.type === 'status')}
          />
        </div>
      </TheatreLayout>

      <SidebarCart currentOrder={currentOrder} />
      
      <StatusAmbience 
        sessionId={sessionId} 
        severity={currentOrder?.severity?.score || 0} 
      />

      <CameraModal 
        isOpen={showCamera}
        onClose={() => setShowCamera(false)}
        onCapture={(blob) => {
          const file = new File([blob], "captured_prescription.jpg", { type: "image/jpeg" });
          handleImageSubmit(file);
        }}
      />
    </AppLayout>
  );
};

export default Kiosk;
