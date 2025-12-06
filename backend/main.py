from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from workflow_manager import workflow_manager
from phases.phase1_story import phase1

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    idea: str

@app.post("/api/generate")
async def start_generation(request: GenerateRequest, background_tasks: BackgroundTasks):
    # Create new workflow
    workflow_id = workflow_manager.create_workflow(request.idea)
    
    # Start processing in background
    background_tasks.add_task(process_workflow, workflow_id, request.idea)
    
    return {"workflow_id": workflow_id, "status": "started"}

@app.get("/api/status/{workflow_id}")
async def get_status(workflow_id: str):
    workflow = workflow_manager.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow

async def process_workflow(workflow_id: str, idea: str):
    # Phase 1: Story Generation
    workflow_manager.update_phase(workflow_id, 1, "processing")
    story = await phase1.generate(idea)
    workflow_manager.update_phase(workflow_id, 1, "completed", result=story)
    
    # Phase 2: Character Design
    from phases.phase2_character import phase2
    workflow_manager.update_phase(workflow_id, 2, "processing")
    characters = await phase2.generate_characters(story)
    workflow_manager.update_phase(workflow_id, 2, "completed", result=characters)
    
    # Phase 3: Storyboard
    from phases.phase3_storyboard import phase3
    workflow_manager.update_phase(workflow_id, 3, "processing")
    storyboard = await phase3.generate_storyboard(story, characters)
    workflow_manager.update_phase(workflow_id, 3, "completed", result=storyboard)

    # Phase 4: Panel Generation
    from phases.phase4_panel import phase4
    workflow_manager.update_phase(workflow_id, 4, "processing")
    panels = await phase4.generate_panels(storyboard)
    workflow_manager.update_phase(workflow_id, 4, "completed", result=panels)

    # Phase 5-7: Assembly and Export
    from phases.phase5_assembly import phase5
    workflow_manager.update_phase(workflow_id, 5, "processing")
    pdf_url = await phase5.assemble_and_export(panels)
    workflow_manager.update_phase(workflow_id, 7, "completed", result={"pdf_url": pdf_url})
