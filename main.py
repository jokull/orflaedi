import uvicorn
from dotenv import load_dotenv

load_dotenv()

from orflaedi.main import app


if __name__ == "__main__":
    uvicorn.run(
        "orflaedi.main:app",
        host="0.0.0.0",
        port=5000,
        log_level="info",
        reload=True,
        reload_dirs=["./orflaedi"],
        proxy_headers=True,
    )
