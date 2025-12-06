from vertexai.preview.generative_models import GenerativeModel
import json

class Phase3Storyboard:
    def __init__(self):
        self.model = GenerativeModel("gemini-pro")

    async def generate_storyboard(self, story_data: str, characters_data: list) -> list:
        # Format character info for the prompt
        char_info = "\n".join([f"- {c['name']}: {c['description_ja']}" for c in characters_data])
        
        prompt = f"""
        あなたはプロの漫画編集者です。
        以下のプロットとキャラクター設定を元に、漫画のネーム（コマ割り構成）を作成してください。
        全4ページ程度の短編漫画として構成してください。
        
        プロット:
        {story_data}
        
        キャラクター:
        {char_info}
        
        出力フォーマット(JSON):
        [
            {{
                "page_number": 1,
                "panels": [
                    {{
                        "panel_number": 1,
                        "description": "コマの状況説明（誰が何をしているか）",
                        "composition": "構図（アップ、ロング、俯瞰など）",
                        "dialogue": "セリフ（話者名: セリフ）",
                        "image_prompt_en": "Detailed visual description for AI image generation (include character visual tags)"
                    }}
                ]
            }}
        ]
        """
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except Exception as e:
            print(f"Error generating storyboard: {e}")
            return []

phase3 = Phase3Storyboard()
