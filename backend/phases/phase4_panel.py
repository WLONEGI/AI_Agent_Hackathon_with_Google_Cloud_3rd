from vertexai.preview.vision_models import ImageGenerationModel
import os

class Phase4PanelGeneration:
    def __init__(self):
        self.image_model = ImageGenerationModel.from_pretrained("nano-banana-pro")

    async def generate_panels(self, storyboard_data: list) -> list:
        updated_storyboard = []
        
        for page in storyboard_data:
            updated_panels = []
            for panel in page["panels"]:
                image_path = ""
                try:
                    # Construct prompt
                    prompt = f"manga style, black and white, {panel['image_prompt_en']}, high quality, detailed"
                    
                    # Generate image
                    images = self.image_model.generate_images(
                        prompt=prompt,
                        number_of_images=1,
                        language="en",
                        aspect_ratio="1:1", # Ideally this should match panel composition
                        safety_filter_level="block_some",
                        person_generation="allow_adult"
                    )
                    
                    # Save image locally
                    os.makedirs("backend/output/panels", exist_ok=True)
                    filename = f"p{page['page_number']}_pan{panel['panel_number']}_{os.urandom(4).hex()}.png"
                    save_path = f"backend/output/panels/{filename}"
                    images[0].save(location=save_path, include_generation_parameters=False)
                    
                    image_path = f"/output/panels/{filename}"
                    
                except Exception as e:
                    print(f"Error generating panel {panel['panel_number']}: {e}")
                    image_path = "error_placeholder.png"

                panel["image_url"] = image_path
                updated_panels.append(panel)
            
            page["panels"] = updated_panels
            updated_storyboard.append(page)
            
        return updated_storyboard

phase4 = Phase4PanelGeneration()
