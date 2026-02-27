import { useState } from 'react';

const AgentTimeline = ({ 
  conversationData = null, 
  prescriptionData = null,
  isProcessing = false,
  mode = 'conversation'
}) => {
  const [expandedAgent, setExpandedAgent] = useState(null);

  if (!conversationData && !prescriptionData && !isProcessing) return null;

  const data = mode === 'prescription' ? prescriptionData : conversationData;

  const getAgents = () => {
    if (mode === 'prescription') {
      return [
        {
          name: 'Front Desk Agent',
          icon: '🎯',
          description: 'Request Classification',
          status: data || isProcessing ? 'complete' : 'pending',
          details: data || isProcessing ? 'Intent classified: Prescription upload' : null,
        },
        {
          name: 'Vision Agent',
          icon: '👁️',
          description: 'OCR & Text Extraction',
          status: data?.extracted_items ? 'complete' : isProcessing ? 'processing' : 'pending',
          details: data?.extracted_items ? `Extracted ${data.extracted_items.length} medicine(s)` : isProcessing ? 'Running OCR extraction...' : null,
        },
        {
          name: 'Medical Validation Agent',
          icon: '⚕️',
          description: 'Safety & Compliance Check',
          status: data?.decision ? 'complete' : isProcessing ? 'processing' : 'pending',
          details: data?.decision === 'approved' ? 'Prescription approved' : 
                   data?.decision === 'needs_review' ? 'Manual review required' :
                   data?.decision === 'rejected' ? 'Prescription rejected' :
                   isProcessing ? 'Checking safety...' : null,
        },
        {
          name: 'Inventory Agent',
          icon: '📦',
          description: 'Stock Availability',
          status: data?.inventory_status ? 'complete' : data?.decision === 'rejected' ? 'skipped' : isProcessing ? 'processing' : 'pending',
          details: data?.inventory_status?.in_stock > 0 ? 'Stock confirmed' :
                   data?.inventory_status?.out_of_stock > 0 ? 'Proposing alternatives' :
                   data?.decision === 'rejected' ? 'Skipped' :
                   isProcessing ? 'Checking stock...' : null,
        },
        {
          name: 'Fulfillment Agent',
          icon: '✅',
          description: 'Order Creation',
          status: data?.order_id ? 'complete' : data?.decision === 'rejected' ? 'skipped' : isProcessing ? 'processing' : 'pending',
          details: data?.order_id ? `Order created` : 
                   data?.decision === 'rejected' ? 'Skipped' :
                   isProcessing ? 'Creating order...' : null,
        },
        {
          name: 'Notification Agent',
          icon: '📱',
          description: 'Telegram Notification',
          status: 'async',
          details: 'Runs asynchronously',
          isAsync: true,
        },
      ];
    } else {
      return [
        {
          name: 'Front Desk Agent',
          icon: '🎯',
          description: 'Understanding request',
          status: data?.intent ? 'complete' : isProcessing ? 'processing' : 'pending',
          details: data?.intent ? `Intent: ${data.intent}` : isProcessing ? 'Classifying...' : null,
        },
        {
          name: 'Medical Validation Agent',
          icon: '⚕️',
          description: 'Assessing severity',
          status: data?.recommendations ? 'complete' : isProcessing ? 'processing' : 'pending',
          details: data?.recommendations ? `${data.recommendations.length} medicine(s) recommended` : isProcessing ? 'Analyzing...' : null,
        },
        {
          name: 'Inventory Agent',
          icon: '📦',
          description: 'Checking stock',
          status: data?.recommendations ? 'complete' : isProcessing ? 'processing' : 'pending',
          details: data?.recommendations ? 'Stock verified' : isProcessing ? 'Checking...' : null,
        },
        {
          name: 'Fulfillment Agent',
          icon: '✅',
          description: 'Preparing order',
          status: data?.order_id ? 'complete' : 'pending',
          details: data?.order_id ? 'Order ready' : 'Awaiting confirmation',
        },
        {
          name: 'Notification Agent',
          icon: '📱',
          description: 'Sending Telegram update',
          status: 'async',
          details: 'Runs asynchronously',
          isAsync: true,
        },
      ];
    }
  };

  const agents = getAgents();

  return (
    <div className="bg-white rounded-2xl shadow-xl p-4 border border-gray-100" aria-label="Agent Timeline">
      <div className="mb-4">
        <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
          <span>🤖</span>
          <span>AI Agent Pipeline</span>
        </h3>
        <p className="text-xs text-gray-500 mt-1">
          {mode === 'prescription' ? 'Prescription Processing' : 'Conversational Flow'}
        </p>
      </div>
      
      <div className="space-y-2">
        {agents.map((agent, idx) => (
          <div key={idx} className="relative">
            {idx < agents.length - 1 && (
              <div className={`absolute left-5 top-12 w-0.5 h-4 transition-colors ${
                agent.status === 'complete' ? 'bg-green-400' : 'bg-gray-300'
              }`}></div>
            )}
            
            <div className={`rounded-xl border-2 transition-all ${
              agent.isAsync 
                ? 'bg-teal-50 border-teal-300 opacity-60'
                : agent.status === 'complete' 
                ? 'bg-green-50 border-green-300' 
                : agent.status === 'skipped'
                ? 'bg-gray-50 border-gray-300'
                : agent.status === 'processing'
                ? 'bg-blue-50 border-blue-300 animate-pulse'
                : 'bg-gray-50 border-gray-200'
            }`}>
              <div className="flex items-start gap-3 p-3">
                <div className={`text-2xl flex-shrink-0 ${
                  agent.status === 'processing' ? 'animate-bounce' : ''
                }`}>
                  {agent.icon}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1 gap-2">
                    <h4 className="font-semibold text-gray-900 text-sm">{agent.name}</h4>
                    {agent.isAsync && (
                      <span className="text-xs font-semibold px-2 py-0.5 rounded bg-teal-200 text-teal-800">
                        Async
                      </span>
                    )}
                    {!agent.isAsync && (
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded ${
                        agent.status === 'complete'
                          ? 'bg-green-200 text-green-800'
                          : agent.status === 'skipped'
                          ? 'bg-gray-200 text-gray-600'
                          : agent.status === 'processing'
                          ? 'bg-blue-200 text-blue-800'
                          : 'bg-gray-200 text-gray-500'
                      }`}>
                        {agent.status === 'complete' ? '✓' : 
                         agent.status === 'skipped' ? 'Skip' : 
                         agent.status === 'processing' ? '⏳' : 
                         '○'}
                      </span>
                    )}
                  </div>
                  
                  <p className="text-xs text-gray-600 mb-1">{agent.description}</p>
                  
                  {agent.details && (
                    <p className="text-xs font-medium text-gray-700">{agent.details}</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="text-center">
          <p className="text-sm font-semibold text-gray-900">
            {mode === 'prescription' && data?.order_id ? '✅ Complete' : 
             mode === 'prescription' && data?.decision === 'rejected' ? '❌ Rejected' :
             mode === 'conversation' && data?.recommendations ? '✅ Complete' :
             isProcessing ? '⏳ Processing...' : 
             '⏸️ Ready'}
          </p>
        </div>
      </div>
    </div>
  );
};

export default AgentTimeline;
