import os
from typing import List
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    PROJECT_NAME: str = "Nutri-Well API"
    PROJECT_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Supabase Credentials
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")
    
    # Gemini AI API Key
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # CORS
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "https://nutri-well-frontend01.vercel.app,https://nutri-well-frountend01.vercel.app,http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://localhost:4173")
    
    @property
    def cors_origins(self) -> List[str]:
        default_origins = [
            "https://nutri-well-frontend01.vercel.app",
            "https://nutri-well-frountend01.vercel.app",
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ]
        origins_set = set(default_origins)
        if self.FRONTEND_URL:
            for url in self.FRONTEND_URL.split(","):
                clean = url.strip().rstrip("/")
                if clean:
                    origins_set.add(clean)
        return list(origins_set)

settings = Settings()
