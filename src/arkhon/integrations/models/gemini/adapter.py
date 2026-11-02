"""Google Gemini generateContent adapter."""
from __future__ import annotations
import json, os, urllib.error, urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from arkhon.integrations.base import Integration, IntegrationInfo, IntegrationResponse
@dataclass(frozen=True)
class GeminiConfig:
 endpoint: str="https://generativelanguage.googleapis.com/v1beta/models"
 model: str="gemini-2.5-flash"
 max_tokens: int=8192
 temperature: float=0.0
 timeout_seconds: int=120
class GeminiAdapter(Integration):
 def __init__(self,config: GeminiConfig|None=None)->None:
  self.config=config or GeminiConfig(); self._prompts_dir=Path(__file__).parent/"prompts"
 @property
 def info(self)->IntegrationInfo:
  return IntegrationInfo(id="gemini",kind="model",provider="google",version="1.0.0",
   capabilities=("code-generation","long-context","multimodal"))
 def health_check(self)->bool: return bool(os.environ.get("GOOGLE_API_KEY"))
 def system_prompt(self)->str:
  p=self._prompts_dir/"system.md"; return p.read_text(encoding="utf-8") if p.is_file() else ""
 def governance_injection(self)->str:
  p=self._prompts_dir/"governance-injection.md"; return p.read_text(encoding="utf-8") if p.is_file() else ""
 def send(self,user_message:str)->IntegrationResponse:
  key=os.environ.get("GOOGLE_API_KEY")
  if not key:return IntegrationResponse(ok=False,reason="GOOGLE_API_KEY not set")
  body:dict[str,Any]={"contents":[{"role":"user","parts":[{"text":user_message}]}],
   "generationConfig":{"maxOutputTokens":self.config.max_tokens,"temperature":self.config.temperature}}
  system=self.system_prompt()
  if system:body["systemInstruction"]={"parts":[{"text":system}]}
  req=urllib.request.Request(f"{self.config.endpoint}/{self.config.model}:generateContent",
   data=json.dumps(body).encode(),headers={"content-type":"application/json","x-goog-api-key":key},method="POST")
  try:
   with urllib.request.urlopen(req,timeout=self.config.timeout_seconds) as resp: raw=resp.read().decode()
  except urllib.error.HTTPError as exc:return IntegrationResponse(ok=False,reason=f"HTTP {exc.code}: {exc.reason}")
  except urllib.error.URLError as exc:return IntegrationResponse(ok=False,reason=f"network error: {exc.reason}")
  except TimeoutError:return IntegrationResponse(ok=False,reason=f"timeout after {self.config.timeout_seconds}s")
  try: parsed=json.loads(raw)
  except (json.JSONDecodeError,UnicodeDecodeError) as exc:return IntegrationResponse(ok=False,reason=f"invalid JSON response: {exc}")
  if not isinstance(parsed,dict):return IntegrationResponse(ok=False,reason="invalid response: expected JSON object")
  text=""; candidates=parsed.get("candidates",[])
  if isinstance(candidates,list) and candidates and isinstance(candidates[0],dict):
   content=candidates[0].get("content",{})
   if isinstance(content,dict):
    parts=content.get("parts",[])
    if isinstance(parts,list):text="".join(p.get("text","") for p in parts if isinstance(p,dict) and isinstance(p.get("text",""),str))
  return IntegrationResponse(ok=True,payload={"text":text,"raw":parsed,"model":self.config.model})
