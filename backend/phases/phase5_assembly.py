from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os

class Phase5AssemblyExport:
    def __init__(self):
        pass

    async def assemble_and_export(self, panels_data: list) -> str:
        # This combines Phase 5 (Assembly), 6 (Dialogue), and 7 (Export)
        
        output_filename = f"manga_{os.urandom(4).hex()}.pdf"
        os.makedirs("backend/output/products", exist_ok=True)
        output_path = f"backend/output/products/{output_filename}"
        
        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4
        
        for page in panels_data:
            c.drawString(100, height - 50, f"Page {page['page_number']}")
            
            # Simple layout: 2x2 grid for up to 4 panels per page
            # This is a very basic implementation
            y_positions = [height - 300, height - 300, height - 550, height - 550]
            x_positions = [50, 300, 50, 300]
            
            for i, panel in enumerate(page["panels"]):
                if i >= 4: break # Limit to 4 panels for this prototype
                
                image_rel_path = panel["image_url"]
                # Convert relative web path to local file path
                # /output/panels/filename -> backend/output/panels/filename
                local_image_path = f"backend{image_rel_path}"
                
                if os.path.exists(local_image_path):
                    try:
                        c.drawImage(local_image_path, x_positions[i], y_positions[i], width=200, height=200, preserveAspectRatio=True)
                    except Exception as e:
                        print(f"Error drawing image: {e}")
                
                # Draw dialogue (very basic)
                text = c.beginText(x_positions[i], y_positions[i] - 20)
                text.setFont("Helvetica", 10)
                # Split dialogue into lines
                dialogue = panel.get("dialogue", "")
                for line in dialogue.split("\n"):
                    text.textLine(line)
                c.drawText(text)
            
            c.showPage()
            
        c.save()
        
        return f"/output/products/{output_filename}"

phase5 = Phase5AssemblyExport()
