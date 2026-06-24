from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import PersonaCreateRequest, PersonaCreateResponse
from app.agents.persona_agent import PersonaAgent
from app.llm.client import client, LLM_MODEL
from app.llm.client import client, LLM_MODEL

from pydantic import BaseModel, Field



app = FastAPI(title="Social Lab Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

persona_agent = PersonaAgent()

@app.get("/")
async def root():
    return {
        "message": "Social Lab Agent API is running",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/persona/create")
async def create_persona(request: PersonaCreateRequest):
    try:
        result = await persona_agent.run(request)
        return {
            "ok": True,
            "data": result
        }
    except Exception as exc:
        return {
            "ok": False,
            "error_type": exc.__class__.__name__,
            "error": str(exc)
        }

@app.get("/api/debug/llm")
async def debug_llm():
    response = await client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": "你是一个测试助手，只返回一句中文。"
            },
            {
                "role": "user",
                "content": "请回复：LLM 接入成功。"
            }
        ],
        temperature=0
    )

    return {
        "model": LLM_MODEL,
        "content": response.choices[0].message.content
    }

class DebugChatRequest(BaseModel):
    system_prompt: str = Field(
        default="你是 Social Lab 的测试助手，请自然、灵活、具体地回答用户问题。",
        description="系统提示词"
    )
    user_message: str = Field(
        description="用户输入"
    )
    temperature: float = Field(
        default=0.7,
        ge=0,
        le=1.5,
        description="回答随机性，越高越灵活"
    )


@app.post("/api/debug/chat")
async def debug_chat(request: DebugChatRequest):
    try:
        response = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": request.system_prompt,
                },
                {
                    "role": "user",
                    "content": request.user_message,
                },
            ],
            temperature=request.temperature,
        )

        return {
            "ok": True,
            "model": LLM_MODEL,
            "content": response.choices[0].message.content,
        }

    except Exception as exc:
        return {
            "ok": False,
            "model": LLM_MODEL,
            "error_type": exc.__class__.__name__,
            "error": str(exc),
        }
