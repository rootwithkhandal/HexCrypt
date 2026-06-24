import os
import csv
import hashlib
import tempfile
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from typing import Optional, List
from cryptography.exceptions import InvalidTag

from hexcrypt_core import core, steg

app = FastAPI(title="HexCrypt API")

class KeyGenRequest(BaseModel):
    mode: str

class CryptoRequest(BaseModel):
    text: str
    key: str
    ttl: Optional[int] = None

@app.post("/api/keygen")
def generate_key(req: KeyGenRequest):
    if req.mode == "symmetric":
        return {"key": core.generate_key()}
    else:
        priv, pub = core.generate_x25519_keypair()
        return {"priv_key": priv, "pub_key": pub}

@app.post("/api/encrypt/symmetric")
def encrypt_sym(req: CryptoRequest):
    try:
        return {"result": core.encrypt_text(req.text, req.key)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/encrypt/asymmetric")
def encrypt_asym(req: CryptoRequest):
    try:
        return {"result": core.encrypt_asymmetric(req.text.encode('utf-8'), req.key)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/decrypt/symmetric")
def decrypt_sym(req: CryptoRequest):
    try:
        return {"result": core.decrypt_text(req.text, req.key, ttl=req.ttl)}
    except core.ExpiredToken:
        raise HTTPException(status_code=400, detail="Token Expired: This message self-destructed.")
    except InvalidTag:
        raise HTTPException(status_code=400, detail="Authentication failed: Invalid key or corrupted data.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e) or "Unknown decryption error.")

@app.post("/api/decrypt/asymmetric")
def decrypt_asym(req: CryptoRequest):
    try:
        result_bytes = core.decrypt_asymmetric(req.text, req.key, ttl=req.ttl)
        return {"result": result_bytes.decode('utf-8')}
    except core.ExpiredToken:
        raise HTTPException(status_code=400, detail="Token Expired: This message self-destructed.")
    except InvalidTag:
        raise HTTPException(status_code=400, detail="Authentication failed: Invalid key or corrupted data.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e) or "Unknown decryption error.")

@app.post("/api/hash")
async def calculate_hash(file: UploadFile = File(...)):
    try:
        h_md5 = hashlib.md5()
        h_sha1 = hashlib.sha1()
        h_sha256 = hashlib.sha256()
        h_sha512 = hashlib.sha512()

        while chunk := await file.read(4096):
            h_md5.update(chunk)
            h_sha1.update(chunk)
            h_sha256.update(chunk)
            h_sha512.update(chunk)

        return {
            "filename": file.filename,
            "MD5": h_md5.hexdigest(),
            "SHA1": h_sha1.hexdigest(),
            "SHA256": h_sha256.hexdigest(),
            "SHA512": h_sha512.hexdigest()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/steg/embed")
async def steg_embed(carrier: UploadFile = File(...), payload: UploadFile = File(...)):
    try:
        carrier_bytes = await carrier.read()
        payload_bytes = await payload.read()
        
        out_bytes = steg.embed_data(carrier_bytes, payload_bytes, filename=payload.filename or "")
        
        return Response(content=out_bytes, media_type="image/png", headers={
            "Content-Disposition": f'attachment; filename="embedded_{carrier.filename}"'
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/steg/extract")
async def steg_extract(carrier: UploadFile = File(...)):
    try:
        carrier_bytes = await carrier.read()
        
        extracted_name, payload_bytes = steg.extract_data(carrier_bytes)
        final_name = extracted_name if extracted_name else "extracted_payload.bin"
        
        return Response(content=payload_bytes, headers={
            "Content-Disposition": f'attachment; filename="{final_name}"'
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def start_server():
    uvicorn.run("hexcrypt.api:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    start_server()
