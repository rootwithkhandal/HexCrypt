import os
import csv
import hashlib
import tempfile
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List

from hexcrypt_core import core, steg

app = FastAPI(title="HexCrypt API")

class KeyGenRequest(BaseModel):
    mode: str

class CryptoRequest(BaseModel):
    text: str
    key: str
    mode: str
    ttl: Optional[int] = None

# ... (Existing endpoints will remain below)
@app.post("/api/keygen")
def generate_key(req: KeyGenRequest):
    if req.mode == "symmetric":
        return {"key": core.generate_key()}
    else:
        priv, pub = core.generate_x25519_keypair()
        return {"priv_key": priv, "pub_key": pub}

@app.post("/api/encrypt")
def encrypt_text(req: CryptoRequest):
    try:
        if req.mode == "asymmetric":
            result = core.encrypt_asymmetric(req.text.encode('utf-8'), req.key)
        else:
            result = core.encrypt_text(req.text, req.key)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

from cryptography.exceptions import InvalidTag

@app.post("/api/decrypt")
def decrypt_text(req: CryptoRequest):
    try:
        if req.mode == "asymmetric":
            result_bytes = core.decrypt_asymmetric(req.text, req.key, ttl=req.ttl)
            result = result_bytes.decode('utf-8')
        else:
            result = core.decrypt_text(req.text, req.key, ttl=req.ttl)
        return {"result": result}
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
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f_carrier, \
             tempfile.NamedTemporaryFile(delete=False) as f_payload, \
             tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f_output:
            
            f_carrier.write(await carrier.read())
            f_payload.write(await payload.read())
            
            carrier_path = f_carrier.name
            payload_path = f_payload.name
            output_path = f_output.name

        steg.embed_data(carrier_path, payload_path, output_path, filename=payload.filename or "")
        
        return FileResponse(output_path, filename="embedded_" + carrier.filename, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/steg/extract")
async def steg_extract(carrier: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f_carrier, \
             tempfile.NamedTemporaryFile(delete=False) as f_output:
            
            f_carrier.write(await carrier.read())
            carrier_path = f_carrier.name
            output_path = f_output.name

        extracted_name = steg.extract_data(carrier_path, output_path)
        final_name = extracted_name if extracted_name else "extracted_payload.bin"
        
        return FileResponse(output_path, filename=final_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def start_server():
    uvicorn.run("hexcrypt.api:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    start_server()
