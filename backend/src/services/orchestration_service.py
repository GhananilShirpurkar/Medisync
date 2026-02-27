"""
ORCHESTRATION SERVICE
=====================
Coordinates multi-agent workflow for prescription processing.
"""

from typing import Dict, Any
import logging

from ..agents.vision_agent import VisionAgent

logger = logging.getLogger(__name__)


class OrchestrationService:
    """
    Orchestrates the prescription processing workflow.
    
    Workflow:
    1. Vision Agent extracts data from image
    2. Medical Validation Agent validates medicines (TODO: integrate)
    3. Inventory Agent checks stock availability (TODO: integrate)
    4. Returns consolidated results
    """
    
    def __init__(self):
        """Initialize orchestration service with agents."""
        self.vision_agent = VisionAgent()
        # TODO: Integrate medical and inventory agents when ready
    
    async def process_prescription(
        self, 
        image_bytes: bytes, 
        session_id: str
    ) -> Dict[str, Any]:
        """
        Process prescription through multi-agent workflow.
        
        Args:
            image_bytes: Raw prescription image bytes
            session_id: Session identifier for context
            
        Returns:
            Consolidated results from all agents
        """
        from src.services.observability_service import trace_manager
        
        logger.info(f"Starting prescription processing for session {session_id}")
        
        # Step 0: Gateway
        await trace_manager.emit(
            session_id=session_id,
            agent_name="API Gateway",
            step_name="Received prescription image",
            action_type="event",
            status="started",
            details={"type": "prescription_upload"}
        )
        
        # Step 1: Extract data using Vision Agent
        logger.info("Step 1: Vision Agent extraction")
        await trace_manager.emit(
            session_id=session_id,
            agent_name="Vision Agent",
            step_name="Thinking: Reading your prescription details carefully...",
            action_type="thinking",
            status="started"
        )
        
        extraction_result = self.vision_agent.extract_prescription_data(image_bytes)
        
        if not extraction_result["success"]:
            logger.error(f"Vision extraction failed: {extraction_result.get('error')}")
            await trace_manager.emit(
                session_id=session_id,
                agent_name="Vision Agent",
                step_name="Thinking: Reading your prescription details carefully...",
                action_type="error",
                status="failed",
                details={"error": extraction_result.get('error')}
            )
            return {
                "extraction": extraction_result,
                "validation": None,
                "inventory": None
            }
            
        prescription_data = extraction_result["data"]
        medicines = prescription_data.get("medicines", [])
        
        await trace_manager.emit(
            session_id=session_id,
            agent_name="Vision Agent",
            step_name="Thinking: Reading your prescription details carefully...",
            action_type="tool_use",
            status="completed",
            details={"medicines_found": len(medicines), "patient": prescription_data.get("patient_name")}
        )
        logger.info(f"Extracted {len(medicines)} medicines")
        
        # Step 2: Validate using Medical Agent
        logger.info("Step 2: Medical validation")
        await trace_manager.emit(
            session_id=session_id,
            agent_name="Medical Agent",
            step_name="Thinking: Verifying the medical safety of these items...",
            action_type="thinking",
            status="started"
        )
        validation_result = self._validate_medicines(medicines, prescription_data)
        await trace_manager.emit(
            session_id=session_id,
            agent_name="Medical Agent",
            step_name="Thinking: Verifying the medical safety of these items...",
            action_type="decision",
            status="completed",
            details={"warnings": len(validation_result.get("warnings", [])), "is_valid": validation_result.get("is_valid")}
        )
        
        # Step 3: Check inventory
        logger.info("Step 3: Inventory check")
        await trace_manager.emit(
            session_id=session_id,
            agent_name="Inventory Agent",
            step_name="Thinking: Checking the current stock in our pharmacy...",
            action_type="tool_use",
            status="started"
        )
        inventory_result = self._check_inventory(medicines)
        await trace_manager.emit(
            session_id=session_id,
            agent_name="Inventory Agent",
            step_name="Thinking: Checking the current stock in our pharmacy...",
            action_type="tool_use",
            status="completed",
            details={"in_stock": len(inventory_result.get("in_stock", []))}
        )
        
        # Step 4: Consolidate results
        consolidated = {
            "extraction": extraction_result,
            "validation": validation_result,
            "inventory": inventory_result
        }
        
        # Trace: Final response
        await trace_manager.emit(
            session_id=session_id,
            agent_name="ORCHESTRATOR",
            step_name="Responding with prescription analysis results...",
            action_type="response",
            status="completed"
        )

        await trace_manager.emit(
            session_id=session_id,
            agent_name="API Gateway",
            step_name="Waiting for response",
            action_type="event",
            status="completed"
        )
        
        logger.info("Prescription processing complete")
        return consolidated
    
    def _validate_medicines(
        self, 
        medicines: list, 
        prescription_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate medicines using basic checks.
        
        Args:
            medicines: List of extracted medicines
            prescription_data: Full prescription data
            
        Returns:
            Validation results with warnings/errors
        """
        try:
            warnings = []
            errors = []
            
            for medicine in medicines:
                medicine_name = medicine.get("name")
                if not medicine_name:
                    errors.append("Medicine found without name")
                    continue
                
                # Basic validation
                if not medicine.get("dosage"):
                    warnings.append(f"{medicine_name}: Missing dosage information")
                if not medicine.get("frequency"):
                    warnings.append(f"{medicine_name}: Missing frequency information")
            
            # Check if doctor name is present for prescription medicines
            if not prescription_data.get("doctor_name"):
                warnings.append("No doctor name found on prescription")
            
            return {
                "is_valid": len(errors) == 0,
                "warnings": warnings,
                "errors": errors,
                "checked_interactions": False  # TODO: Implement interaction checking
            }
            
        except Exception as e:
            logger.error(f"Validation error: {str(e)}", exc_info=True)
            return {
                "is_valid": False,
                "warnings": [],
                "errors": [f"Validation failed: {str(e)}"],
                "checked_interactions": False
            }
    
    def _check_inventory(self, medicines: list) -> Dict[str, Any]:
        """
        Check inventory availability for medicines using InventoryService.
        
        Args:
            medicines: List of extracted medicines
            
        Returns:
            Inventory check results
        """
        try:
            from src.services.inventory_service import InventoryService
            inventory_service = InventoryService()
            
            # Prepare items for check
            items_to_check = []
            for medicine in medicines:
                medicine_name = medicine.get("name")
                if medicine_name:
                    items_to_check.append({
                        "medicine_name": medicine_name,
                        "quantity": 1 # Default to 1 if not parsed
                    })
            
            # Call smart inventory check
            result = inventory_service.check_availability(items_to_check)
            
            # Map result to expected format
            availability_info = {
                "available": result["available_items"] == result["total_items"],
                "partial": 0 < result["available_items"] < result["total_items"],
                "in_stock": [],
                "out_of_stock": [],
                "alternatives": [], # Flattened list of alternatives for easy specific access if needed
                "recommendations": result.get("recommendations", [])
            }

            for item in result["items"]:
                if item["available"]:
                    availability_info["in_stock"].append({
                        "name": item["medicine"],
                        "stock": item["stock"],
                        "price": item.get("price", 0)
                    })
                else:
                    out_entry = {
                        "name": item["medicine"],
                        "reason": item["reason"]
                    }
                    if "alternatives" in item:
                        out_entry["alternatives"] = item["alternatives"]
                        availability_info["alternatives"].extend(item["alternatives"])
                    
                    availability_info["out_of_stock"].append(out_entry)
            
            return availability_info
            
        except Exception as e:
            logger.error(f"Inventory check error: {str(e)}", exc_info=True)
            return {
                "available": False,
                "partial": False,
                "in_stock": [],
                "out_of_stock": [],
                "alternatives": [],
                "recommendations": [],
                "error": str(e)
            }
