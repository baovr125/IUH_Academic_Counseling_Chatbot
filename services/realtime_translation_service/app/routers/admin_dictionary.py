from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from app.services.supabase_client import get_supabase
from app.services.domain_dict_service import sync_dictionary_to_redis
from app.utils.logger import logger
from app.schemas.translation import ApiResult

router = APIRouter(tags=["Dictionary Admin"])

class DictionaryEntry(BaseModel):
    domain: str
    word: str
    translation: str
    phonetic: Optional[str] = None
    pos: Optional[str] = None
    audio_url: Optional[str] = None

class DictionaryEntryResponse(DictionaryEntry):
    id: str

class BulkDeleteRequest(BaseModel):
    ids: List[str]

@router.get("/admin/dictionary", response_model=ApiResult)
def get_dictionary():
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    try:
        res = supabase.table("domain_dictionaries").select("*").order("created_at", desc=True).execute()
        return ApiResult(ok=True, data=res.data)
    except Exception as e:
        logger.error(f"Error fetching dictionary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/dictionary", response_model=ApiResult)
def add_dictionary_entry(background_tasks: BackgroundTasks, entry: DictionaryEntry):
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    try:
        # Check if exists
        existing = supabase.table("domain_dictionaries").select("id").eq("domain", entry.domain).eq("word", entry.word).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Entry already exists in this domain.")
            
        res = supabase.table("domain_dictionaries").insert({
            "domain": entry.domain,
            "word": entry.word.lower(),
            "translation": entry.translation,
            "phonetic": entry.phonetic,
            "pos": entry.pos,
            "audio_url": entry.audio_url
        }).execute()
        
        # Sync to Redis
        sync_dictionary_to_redis()
        
        # Tạo âm thanh ngầm nếu chưa có
        if res.data:
            background_tasks.add_task(generate_audio_for_entries, res.data)
        
        return ApiResult(ok=True, data=res.data[0])
    except Exception as e:
        logger.error(f"Error adding dictionary entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/admin/dictionary/{entry_id}", response_model=ApiResult)
def delete_dictionary_entry(entry_id: str):
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    try:
        supabase.table("domain_dictionaries").delete().eq("id", entry_id).execute()
        sync_dictionary_to_redis()
        return ApiResult(ok=True, data=None)
    except Exception as e:
        logger.error(f"Error deleting dictionary entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/dictionary/bulk-delete", response_model=ApiResult)
def bulk_delete_dictionary_entries(req: BulkDeleteRequest):
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    try:
        supabase.table("domain_dictionaries").delete().in_("id", req.ids).execute()
        sync_dictionary_to_redis()
        return ApiResult(ok=True, data=None)
    except Exception as e:
        logger.error(f"Error bulk deleting dictionary entries: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/admin/dictionary/{entry_id}", response_model=ApiResult)
def update_dictionary_entry(entry_id: str, background_tasks: BackgroundTasks, entry: DictionaryEntry):
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    try:
        # Check if entry exists and fetch old word
        existing = supabase.table("domain_dictionaries").select("*").eq("id", entry_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        old_word = existing.data[0]["word"]
        new_word = entry.word.lower()

        # Update
        res = supabase.table("domain_dictionaries").update({
            "domain": entry.domain,
            "word": new_word,
            "translation": entry.translation,
            "phonetic": entry.phonetic,
            "pos": entry.pos,
        }).eq("id", entry_id).execute()
        
        sync_dictionary_to_redis()
        
        # Nếu word thay đổi, ta xoá file cũ (tùy chọn) và sinh lại audio mới
        if res.data and old_word != new_word:
            background_tasks.add_task(generate_audio_for_entries, res.data)
        
        return ApiResult(ok=True, data=res.data[0])
    except Exception as e:
        logger.error(f"Error updating dictionary entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import UploadFile, File
import csv
import io
import json
from app.services.audio_generator import generate_audio_for_entries

@router.post("/admin/dictionary/import", response_model=ApiResult)
async def import_dictionary(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
        
    try:
        contents = await file.read()
        entries_to_insert = []
        
        if file.filename.endswith(".csv"):
            # Parse CSV
            decoded = contents.decode("utf-8")
            reader = csv.DictReader(io.StringIO(decoded))
            for row in reader:
                if "domain" in row and "word" in row and "translation" in row:
                    entries_to_insert.append({
                        "domain": row["domain"].strip(),
                        "word": row["word"].strip().lower(),
                        "translation": row["translation"].strip(),
                        "phonetic": row.get("phonetic", "").strip(),
                        "pos": row.get("pos", "").strip()
                    })
        elif file.filename.endswith(".json"):
            # Parse JSON
            data = json.loads(contents)
            if isinstance(data, list):
                for row in data:
                    if "domain" in row and "word" in row and "translation" in row:
                        entries_to_insert.append({
                            "domain": str(row["domain"]).strip(),
                            "word": str(row["word"]).strip().lower(),
                            "translation": str(row["translation"]).strip(),
                            "phonetic": str(row.get("phonetic", "")).strip(),
                            "pos": str(row.get("pos", "")).strip()
                        })
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload .csv or .json")
            
        if not entries_to_insert:
            raise HTTPException(status_code=400, detail="No valid entries found in file. Ensure columns/keys are: domain, word, translation.")

        # Batch insert into Supabase
        res = supabase.table("domain_dictionaries").upsert(
            entries_to_insert, 
            on_conflict="domain,word"
        ).execute()
        
        sync_dictionary_to_redis()
        
        # Thêm Background Task xử lý sinh âm thanh Edge-TTS
        if res.data:
            background_tasks.add_task(generate_audio_for_entries, res.data)
        
        return ApiResult(ok=True, data={"imported_count": len(entries_to_insert)})
    except Exception as e:
        logger.error(f"Error importing dictionary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
