import os, json
from fastapi import FastAPI
from pydantic import BaseModel
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = FastAPI()
# Root endpoint
@app.get("/")
def root():
    return {"message": "🚀 Adora Blinds API is running on Vercel!"}

# Health-check endpoint
@app.get("/ping")
def ping():
    return {"status": "ok", "message": "pong"}    
# Load credentials from Vercel Environment Variables
sa_json = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]   # full JSON string
SHEET_ID = os.environ["SHEET_ID"]                     # Sheet ID

scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(sa_json), scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).sheet1


# 🔹 Models
class BlindInput(BaseModel):
    width: float
    height: float
    pcs: int = 1

class OrderRequest(BaseModel):
    items: list[BlindInput]
    clear: bool = False

# 🔹 API endpoint
@app.post("/calculate")
def calculate(req: OrderRequest):
    if req.clear:
        sheet.batch_clear(["A2:G"])  # clear old rows

    total_area = 0
    unit_price = 39.0
    lines = []

    for item in req.items:
        for _ in range(item.pcs):
            area = round(item.width * item.height, 2)
            moq_area = max(area, 1.5)
            total_area += moq_area
            sheet.append_row([item.width, item.height, area, moq_area])
            lines.append({
                "width": item.width,
                "height": item.height,
                "area": area,
                "moq_area": moq_area
            })

    net = round(total_area * unit_price, 2)
    vat = round(net * 0.05, 2)
    total = round(net + vat, 2)

    return {
        "ok": True,
        "lines": lines,
        "total_area": total_area,
        "net": net,
        "vat": vat,
        "total": total
    }


