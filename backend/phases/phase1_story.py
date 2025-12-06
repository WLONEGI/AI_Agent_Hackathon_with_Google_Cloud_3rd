from vertexai.preview.generative_models import GenerativeModel
import vertexai
import os

# Initialize Vertex AI
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "your-project-id")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "asia-northeast1")

try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
except Exception as e:
    print(f"Warning: Vertex AI init failed (expected during build): {e}")

class Phase1StoryGeneration:
    def __init__(self):
        self.model = GenerativeModel("gemini-pro")

    async def generate(self, user_input: str) -> str:
        prompt = f"""
        あなたはプロの漫画原作者です。
        以下のユーザーのアイデアを元に、面白い漫画のプロットを作成してください。
        
        ユーザーのアイデア:
        {user_input}
        
        出力フォーマット:
        タイトル: [タイトル]
        ジャンル: [ジャンル]
        あらすじ: [200文字程度のあらすじ]
        プロット:
        - 起: [詳細]
        - 承: [詳細]
        - 転: [詳細]
        - 結: [詳細]
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error generating story: {e}")
            # Return dummy data for development if API fails
            return f"Error: {e}. (Dummy Story: Title: Test Manga, Plot: Hero saves the world.)"

phase1 = Phase1StoryGeneration()
