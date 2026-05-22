from fastapi import FastAPI
from pydantic import BaseModel
import erp

app = FastAPI()

class MCPRequest(BaseModel):
    tool: str
    input: dict = {}

@app.get("/")
def health():
    return {"status": "MCP server running"}

@app.post("/mcp")
def mcp(req: MCPRequest):

    if req.tool == "get_stock":
        return erp.get_stock(req.input)

    if req.tool == "create_order":
        return erp.create_order(req.input)

    if req.tool == "list_orders":
        return erp.list_orders()

    return {"error": "unknown tool"}