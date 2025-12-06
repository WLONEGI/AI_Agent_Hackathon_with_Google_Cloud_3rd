from vertexai.preview.vision_models import ImageGenerationModel
from vertexai.preview.generative_models import GenerativeModel
import os
import json

class Phase2CharacterDesign:
    def __init__(self):
        self.text_model = GenerativeModel("gemini-pro")
        # Initialize Imagen model (using nano-banana-pro as requested)
        self.image_model = ImageGenerationModel.from_pretrained("nano-banana-pro")

    async def generate_characters(self, story_data: str) -> list:
        # 1. Extract characters from story
        prompt = f"""
        以下の漫画のプロットから、主要な登場人物（最大3名）を抽出してください。
        各キャラクターについて、画像生成AIに入力するための詳細な外見的特徴（英語）を記述してください。
        
        プロット:
        {story_data}
        
        出力フォーマット(JSON):
        [
            {{
                "name": "キャラクター名",
                "role": "役割（主人公、ライバルなど）",
                "description_ja": "日本語での外見説明",
                "prompt_en": "Detailed visual description in English for image generation (e.g. anime style, young man, messy black hair, red scarf...)"
            }}
        ]
        """
        
        characters = []
        try:
            response = self.text_model.generate_content(prompt)
            # Simple cleanup to ensure JSON parsing (removing markdown code blocks if present)
            text = response.text.replace("```json", "").replace("```", "").strip()
            characters = json.loads(text)
        except Exception as e:
            print(f"Error extracting characters: {e}")
            return []

        # 2. Generate images for each character
        results = []
        for char in characters:
            image_path = ""
            try:
                # Generate image
                images = self.image_model.generate_images(
                    prompt=f"anime style character design, white background, {char['prompt_en']}",
                    number_of_images=1,
                    language="en",
                    aspect_ratio="1:1",
                    safety_filter_level="block_some",
                    person_generation="allow_adult"
                )
                
                # Save image locally
                os.makedirs("backend/output/characters", exist_ok=True)
                filename = f"{char['name']}_{os.urandom(4).hex()}.png"
                save_path = f"backend/output/characters/{filename}"
                images[0].save(location=save_path, include_generation_parameters=False)
                
                # In a real app, this would be a URL served by the backend
                image_path = f"/output/characters/{filename}"
                
            except Exception as e:
                print(f"Error generating image for {char['name']}: {e}")
                image_path = "error_placeholder.png"

            char["image_url"] = image_path
            results.append(char)
            
        return results

phase2 = Phase2CharacterDesign()
