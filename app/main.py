from fastapi import FastAPI, Request
import uvicorn
import subprocess

app = FastAPI()

# Basic webhook endpoint
@app.post("/webhook")
async def webhook(request: Request):
    # Run the shell script asynchronously
    res = subprocess.run(["bash", "/app/deploy_scripts/whatsapp-deploy.sh"])
    # if res.returncode == 0:
    #     print("Script executed successfully!")
    # else:
    #     print(f"Script failed with return code: {res.returncode}")

    return {"message": "Webhook received successfully"}

# Health check endpoint (optional)
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8001)